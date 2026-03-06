"""
应用程序入口点 - 使用 Qt Fusion 风格

使用方式:
    python -m src
    或直接运行: python src/__main__.py
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyleFactory

from src.config import APP_NAME


STARTUP_LOG = Path.home() / ".image-compressor" / "startup_error.log"


def _append_startup_log(stage: str, exc: BaseException) -> None:
    """记录启动/运行异常，避免 windowed 模式静默退出。"""
    STARTUP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(STARTUP_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] {stage}\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))


def main():
    """主函数"""
    try:
        # 启用高 DPI 支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)

        # 使用 Qt Fusion 风格（跨平台最一致的现代风格）
        app.setStyle(QStyleFactory.create("Fusion"))

        # 应用深色调色板
        from PyQt5.QtGui import QPalette, QColor
        palette = QPalette()

        # 深色主题配色
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))

        app.setPalette(palette)

        def _handle_exception(exc_type, exc_value, exc_tb):
            exc = exc_value if isinstance(exc_value, BaseException) else Exception(str(exc_value))
            _append_startup_log("runtime", exc)
            QMessageBox.critical(
                None,
                "程序异常",
                f"程序运行时发生异常：{exc}\n\n日志已写入：\n{STARTUP_LOG}",
            )

        sys.excepthook = _handle_exception

        try:
            from src.widgets import MainWindow
            window = MainWindow()
            window.show()
        except Exception as exc:
            _append_startup_log("startup", exc)
            QMessageBox.critical(
                None,
                "启动失败",
                f"程序启动失败：{exc}\n\n日志已写入：\n{STARTUP_LOG}",
            )
            return 1

        return app.exec_()
    except Exception as exc:
        _append_startup_log("bootstrap", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
