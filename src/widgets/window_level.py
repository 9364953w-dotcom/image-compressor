"""把投放窗口抬到接近菜单栏的层级，方便 Finder 命中。"""

import ctypes
import sys

# kCGStatusWindowLevel / kCGFloatingWindowLevel
_STATUS_LEVEL = 25
_FLOATING_LEVEL = 3


def elevate_window(widget) -> None:
    """拖放感应条需要盖过普通窗口，才能接住 Finder 拖放。"""
    _set_level(widget, _STATUS_LEVEL, hides_on_deactivate=False)


def release_window(widget) -> None:
    """进度面板切到其他应用时让开，避免挡住正在做的事。"""
    _set_level(widget, _FLOATING_LEVEL, hides_on_deactivate=True)


def _set_level(widget, level: int, hides_on_deactivate: bool) -> None:
    if sys.platform != "darwin":
        return
    try:
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        send = objc.objc_msgSend
        view = ctypes.c_void_p(int(widget.winId()))

        send.restype = ctypes.c_void_p
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        window = send(view, objc.sel_registerName(b"window"))
        if not window:
            return

        send.restype = None
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        send(window, objc.sel_registerName(b"setLevel:"), level)
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
        send(window, objc.sel_registerName(b"setHidesOnDeactivate:"), hides_on_deactivate)
        send(window, objc.sel_registerName(b"setIgnoresMouseEvents:"), False)
    except Exception:
        pass
