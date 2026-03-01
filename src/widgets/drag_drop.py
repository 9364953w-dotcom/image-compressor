"""
自定义拖拽组件模块
"""

from pathlib import Path

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class DragDropLineEdit(QLineEdit):
    """
    支持拖拽文件夹的输入框
    
    用户可以将文件夹拖拽到输入框中，自动填充路径
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(32)
        self.setPlaceholderText("拖拽文件夹到此处或点击浏览选择...")
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                path = Path(urls[0].toLocalFile())
                if path.is_dir():
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """处理拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self.setText(str(path))
        event.acceptProposedAction()
