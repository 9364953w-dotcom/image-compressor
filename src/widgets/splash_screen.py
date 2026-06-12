"""启动画面"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QSplashScreen

from src.config import APP_NAME, __version__

_SPLASH_BG = "#1f1f1f"
_SPLASH_TEXT = "#f2f2f2"
_SPLASH_MUTED = "#8b8b9b"
_SPLASH_ACCENT = "#f39c12"


def _resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "src" / "resources"
    return Path(__file__).resolve().parent.parent / "resources"


def _make_splash_pixmap(width: int = 480, height: int = 280) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(_SPLASH_BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.fillRect(0, 0, width, 4, QColor(_SPLASH_ACCENT))

    icon_path = _resource_dir() / "icon.icns"
    icon_loaded = False
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            icon_pix = icon.pixmap(72, 72)
            if not icon_pix.isNull():
                painter.drawPixmap((width - 72) // 2, 48, icon_pix)
                icon_loaded = True

    title_y = 140 if icon_loaded else 90

    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(QColor(_SPLASH_TEXT))
    title_width = QFontMetrics(title_font).horizontalAdvance(APP_NAME)
    painter.drawText((width - title_width) // 2, title_y, APP_NAME)

    version_font = QFont()
    version_font.setPointSize(10)
    painter.setFont(version_font)
    painter.setPen(QColor(_SPLASH_MUTED))
    version = f"v{__version__}"
    version_width = QFontMetrics(version_font).horizontalAdvance(version)
    painter.drawText((width - version_width) // 2, title_y + 28, version)

    painter.end()
    return pixmap


def create_splash_screen(app: QApplication) -> QSplashScreen:
    splash = QSplashScreen(_make_splash_pixmap(), Qt.WindowStaysOnTopHint)
    splash.showMessage(
        "正在启动...",
        Qt.AlignBottom | Qt.AlignHCenter,
        QColor(_SPLASH_MUTED),
    )
    return splash
