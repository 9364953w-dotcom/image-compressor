"""识别系统里正在进行的文件拖放，而不是普通点击。"""

import ctypes
import sys

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

_FILE_TYPES = {
    "NSFilenamesPboardType",
    "public.file-url",
    "NSPasteboardTypeFileURL",
    "com.apple.finder.node",
}

_OBJC = None
_SEND = None


def _objc():
    global _OBJC, _SEND
    if _OBJC is None:
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        _OBJC = objc
        _SEND = objc.objc_msgSend
    return _OBJC, _SEND


def _msg(restype, *extra):
    _, send = _objc()
    send.restype = restype
    send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, *extra]
    return send


def _sel(name: str):
    objc, _ = _objc()
    return objc.sel_registerName(name.encode())


def _hid_left_down() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cg.CGEventSourceButtonState.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        cg.CGEventSourceButtonState.restype = ctypes.c_bool
        # kCGEventSourceStateHIDSystemState = 1，左键 = 0。
        # Finder 拖放时本进程的按键状态是松开的，硬件状态仍然按着。
        return bool(cg.CGEventSourceButtonState(1, 0))
    except Exception:
        return False


def _drag_board_state():
    """返回 (changeCount, 是否带文件)。读不到时当作没有拖放。"""
    if sys.platform != "darwin":
        return 0, False
    try:
        objc, _ = _objc()
        libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
        libc.dlsym.restype = ctypes.c_void_p
        libc.dlsym.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        addr = libc.dlsym(ctypes.c_void_p(-2), b"NSPasteboardNameDrag")
        if not addr:
            return 0, False
        board_name = ctypes.cast(addr, ctypes.POINTER(ctypes.c_void_p)).contents.value
        pasteboard_cls = objc.objc_getClass(b"NSPasteboard")
        board = _msg(ctypes.c_void_p, ctypes.c_void_p)(
            pasteboard_cls, _sel("pasteboardWithName:"), board_name
        )
        if not board:
            return 0, False
        count = int(_msg(ctypes.c_long)(board, _sel("changeCount")))
        types = _msg(ctypes.c_void_p)(board, _sel("types"))
        if not types:
            return count, False
        total = int(_msg(ctypes.c_ulong)(types, _sel("count")))
        has_files = False
        for index in range(min(total, 16)):
            item = _msg(ctypes.c_void_p, ctypes.c_ulong)(
                types, _sel("objectAtIndex:"), index
            )
            raw = _msg(ctypes.c_char_p)(item, _sel("UTF8String"))
            if raw and raw.decode("utf-8", "replace") in _FILE_TYPES:
                has_files = True
                break
        return count, has_files
    except Exception:
        return 0, False


class DragProximityWatcher(QObject):
    """系统出现新的文件拖放时发出信号，拖放结束再收回。"""

    drag_near_top = pyqtSignal()
    drag_left_top = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._baseline = None
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    def set_anchor(self, rect) -> None:
        return

    def _tick(self) -> None:
        active = self._file_drag_active()
        if active and not self._dragging:
            self._dragging = True
            self.drag_near_top.emit()
        elif not active and self._dragging:
            self._dragging = False
            self.drag_left_top.emit()

    def _file_drag_active(self) -> bool:
        count, has_files = _drag_board_state()
        if not _hid_left_down():
            self._baseline = count
            return False
        if not has_files or self._baseline is None or count == self._baseline:
            return False
        return True
