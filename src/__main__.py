"""
应用程序入口点 - 使用 Qt Fusion 风格

使用方式:
    python -m src
    或直接运行: python src/__main__.py
"""

import ctypes
import faulthandler
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QEventLoop, Qt, QElapsedTimer, QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory

from src.config import APP_NAME, ICON_PATH
from src.widgets.theme import DEFAULT_THEME, build_palette_from_tokens

STARTUP_LOG = Path.home() / ".image-compressor" / "startup_error.log"
CRASH_LOG = Path.home() / ".image-compressor" / "crash.log"
_MIN_SPLASH_MS = 150
_CRASH_FP = None
# 主窗口与托盘互相引用，没有外部强引用时会被 GC 回收并连带销毁运行中的压缩线程。
_KEEP_ALIVE = []


def _claim_dock_icon() -> None:
    """一启动就登记为普通应用，避免主窗口出来之前 Dock 图标消失。"""
    if sys.platform != "darwin":
        return
    try:
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        send = objc.objc_msgSend
        app_cls = objc.objc_getClass(b"NSApplication")
        send.restype = ctypes.c_void_p
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        nsapp = send(app_cls, objc.sel_registerName(b"sharedApplication"))
        if not nsapp:
            return
        send.restype = ctypes.c_bool
        send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
        send(nsapp, objc.sel_registerName(b"setActivationPolicy:"), 0)
    except Exception:
        pass


def _update_splash(splash, app, message: str) -> None:
    splash.showMessage(message, Qt.AlignBottom | Qt.AlignHCenter, QColor("#8b8b9b"))
    app.processEvents(QEventLoop.AllEvents, 50)


def _append_startup_log(stage: str, exc: BaseException) -> None:
    """记录启动/运行异常，避免 windowed 模式静默退出。"""
    STARTUP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(STARTUP_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {stage}\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))


def _enable_crash_logging() -> None:
    global _CRASH_FP
    CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
    _CRASH_FP = open(CRASH_LOG, "a", encoding="utf-8")
    faulthandler.enable(file=_CRASH_FP, all_threads=True)

    def _thread_hook(args) -> None:
        exc = args.exc_value if isinstance(args.exc_value, BaseException) else Exception(str(args.exc_value))
        _append_startup_log("thread", exc)

    threading.excepthook = _thread_hook


def main():
    """主函数"""
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        _claim_dock_icon()
        app.setApplicationName(APP_NAME)
        if ICON_PATH.exists():
            app.setWindowIcon(QIcon(str(ICON_PATH)))
        app.setQuitOnLastWindowClosed(False)
        app.setStyle(QStyleFactory.create("Fusion"))
        app.setPalette(build_palette_from_tokens(DEFAULT_THEME))

        _enable_crash_logging()

        def _handle_exception(exc_type, exc_value, exc_tb):
            exc = exc_value if isinstance(exc_value, BaseException) else Exception(str(exc_value))
            _append_startup_log("runtime", exc)
            QMessageBox.critical(
                None,
                "程序异常",
                f"程序运行时发生异常：{exc}\n\n日志已写入：\n{STARTUP_LOG}",
            )

        sys.excepthook = _handle_exception

        from src.widgets.splash_screen import create_splash_screen, present_splash

        splash = create_splash_screen(app)
        splash_timer = QElapsedTimer()
        splash_timer.start()
        present_splash(splash, app)

        startup_error = {"code": 0}

        def _finish_startup(window) -> None:
            def _close_splash() -> None:
                if window.isVisible():
                    splash.finish(window)
                else:
                    splash.close()

            remaining = _MIN_SPLASH_MS - splash_timer.elapsed()
            if remaining > 0:
                QTimer.singleShot(remaining, _close_splash)
            else:
                _close_splash()

        def _load_main_window() -> None:
            try:
                _update_splash(splash, app, "正在加载组件...")
                from src.widgets import MainWindow
                from src.widgets.tray_controller import TrayController

                _update_splash(splash, app, "正在初始化界面...")
                window = MainWindow()
                window._tray = TrayController(window)
                _KEEP_ALIVE.append(window)
                _KEEP_ALIVE.append(window._tray)
                app.aboutToQuit.connect(window.shutdown_jobs)
                app.aboutToQuit.connect(window._tray.cleanup)
                if window.should_show_on_startup():
                    window.show()
                _finish_startup(window)
            except Exception as exc:
                splash.close()
                _append_startup_log("startup", exc)
                QMessageBox.critical(
                    None,
                    "启动失败",
                    f"程序启动失败：{exc}\n\n日志已写入：\n{STARTUP_LOG}",
                )
                startup_error["code"] = 1
                app.quit()

        QTimer.singleShot(0, _load_main_window)
        exit_code = app.exec_()
        return startup_error["code"] or exit_code
    except Exception as exc:
        _append_startup_log("bootstrap", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
