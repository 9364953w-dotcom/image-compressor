"""
自定义拖拽组件模块
"""

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import QLineEdit, QListWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from src.config import IMAGE_EXTENSIONS


class DragDropLineEdit(QLineEdit):
    """支持拖拽文件夹的输入框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(32)
        self.setPlaceholderText("拖拽文件夹到此处或点击浏览选择...")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                path = Path(urls[0].toLocalFile())
                if path.is_dir():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = Path(urls[0].toLocalFile())
            if path.is_dir():
                self.setText(str(path))
        event.acceptProposedAction()


class DragDropListWidget(QListWidget):
    """支持拖拽图片文件和文件夹的列表。"""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: List[Path] = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            p = Path(url.toLocalFile())
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                paths.append(p)
            elif p.is_dir():
                paths.extend(
                    f for f in sorted(p.rglob("*"))
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                )
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()
