"""
日志面板。
"""

from datetime import datetime

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit


class LogPanel(QWidget):
    """任务日志展示。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        tools = QHBoxLayout()
        tools.addStretch()
        self.clear_btn = QPushButton("清空日志")
        tools.addWidget(self.clear_btn)
        layout.addLayout(tools)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.clear_btn.clicked.connect(self.log_text.clear)

    def append(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{stamp}] {message}")

