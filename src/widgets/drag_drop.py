"""
自定义拖拽组件模块
"""

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import QLineEdit, QListWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from src.config import IMAGE_EXTENSIONS


def path_from_mime(mime) -> str:
    """从拖放数据取出文件夹路径；单张图片则取其父目录。"""
    if mime is None or not mime.hasUrls():
        return ""
    for url in mime.urls():
        if not url.isLocalFile():
            continue
        path = Path(url.toLocalFile())
        if path.is_dir():
            return str(path)
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            return str(path.parent)
    return ""


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
    """支持拖拽图片文件和文件夹的列表。文件夹只回传路径，不在 UI 线程扫描。"""

    files_dropped = pyqtSignal(list)
    folder_dropped = pyqtSignal(str)

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
        folders: List[Path] = []
        files: List[Path] = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_dir():
                folders.append(path)
            elif path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                files.append(path)
        if folders:
            self.folder_dropped.emit(str(folders[0]))
        elif files:
            self.folder_dropped.emit(str(files[0].parent))
            self.files_dropped.emit(files)
        event.acceptProposedAction()
