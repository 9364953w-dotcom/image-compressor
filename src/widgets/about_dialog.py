"""
关于对话框 - 主题跟随主窗口
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
from src.widgets.theme import ThemeTokens, build_dialog_stylesheet


class AboutDialog(QDialog):
    """精简且专业的关于窗口，样式跟随主题。"""

    def __init__(self, tokens: ThemeTokens, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(560, 440)
        self.setStyleSheet(build_dialog_stylesheet(tokens))
        self._tokens = tokens
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel(APP_NAME)
        title.setObjectName("title")
        root.addWidget(title)

        version_label = QLabel(f"版本 {__version__}")
        version_label.setObjectName("valueAccent")
        root.addWidget(version_label)

        desc = QLabel("专业的批量图片压缩与格式处理工具")
        desc.setObjectName("subtitle")
        root.addWidget(desc)

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(14, 14, 14, 14)
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
        support_layout.setContentsMargins(14, 14, 14, 14)
        support_layout.setSpacing(8)
        support_layout.addWidget(QLabel("技术支持与反馈："))

        link = QLabel(
            f"<a style='color:{self._tokens.accent};' "
            f"href='https://github.com/9364953w-dotcom/image-compressor'>"
            f"github.com/9364953w-dotcom/image-compressor</a>"
        )
        link.setOpenExternalLinks(True)
        support_layout.addWidget(link)
        root.addWidget(support_card)

        root.addStretch()

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
        btn_row.addSpacing(8)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)
