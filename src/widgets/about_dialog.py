"""
关于对话框 - 与主程序一致的专业风格
"""

import platform

from PyQt5.QtCore import QT_VERSION_STR, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.config import APP_NAME, __version__


class AboutDialog(QDialog):
    """精简且专业的关于窗口。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(560, 420)
        self._setup_style()
        self._setup_ui()

    def _setup_style(self) -> None:
        self.setStyleSheet(
            """
            QDialog { background-color: #1f1f1f; color: #f2f2f2; }
            QLabel { background: transparent; color: #f2f2f2; }
            QLabel#title { font-size: 22px; font-weight: 700; color: #f39c12; }
            QLabel#subtitle { font-size: 13px; color: #b5b5b5; }
            QFrame#card {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
            }
            QLabel#key { color: #b5b5b5; font-weight: 600; }
            QLabel#value { color: #f2f2f2; }
            QPushButton {
                background-color: #333333;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #f2f2f2;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton#primary {
                background-color: #f39c12;
                border-color: #f39c12;
                color: #1a1a1a;
                font-weight: 700;
            }
            """
        )

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel(APP_NAME)
        title.setObjectName("title")
        subtitle = QLabel(f"版本 {__version__}")
        subtitle.setObjectName("subtitle")
        desc = QLabel("专业的批量图片压缩与格式处理工具")
        desc.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(desc)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setHorizontalSpacing(18)
        info_layout.setVerticalSpacing(10)

        rows = [
            ("产品名称", APP_NAME),
            ("软件版本", __version__),
            ("运行环境", f"Python {platform.python_version()} / Qt {QT_VERSION_STR}"),
            ("系统平台", f"{platform.system()} {platform.release()} ({platform.machine()})"),
            ("专用标识", "成都一禾视觉专用"),
            ("技术栈", "PyQt5, Pillow"),
        ]

        for idx, (k, v) in enumerate(rows):
            key = QLabel(k)
            key.setObjectName("key")
            value = QLabel(v)
            value.setObjectName("value")
            value.setWordWrap(True)
            info_layout.addWidget(key, idx, 0, alignment=Qt.AlignTop)
            info_layout.addWidget(value, idx, 1)

        root.addWidget(info_card)

        support_card = QFrame()
        support_card.setObjectName("card")
        support_layout = QVBoxLayout(support_card)
        support_layout.setContentsMargins(12, 12, 12, 12)
        support_layout.setSpacing(8)
        support_layout.addWidget(QLabel("技术支持与反馈："))

        link = QLabel(
            "<a style='color:#f39c12;' href='https://github.com/9364953w-dotcom/image-compressor'>"
            "github.com/9364953w-dotcom/image-compressor</a>"
        )
        link.setOpenExternalLinks(True)
        support_layout.addWidget(link)
        root.addWidget(support_card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        github_btn = QPushButton("打开项目主页")
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/9364953w-dotcom/image-compressor"))
        )
        close_btn = QPushButton("确定")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(github_btn)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)
