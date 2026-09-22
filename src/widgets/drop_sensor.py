"""屏幕顶端可见投放区：Finder 拖放需要不透明、足够大的窗口才能命中。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.widgets.drag_drop import path_from_mime
from src.widgets.theme import DEFAULT_THEME
from src.widgets.window_level import elevate_window


class DropSensor(QWidget):
    """菜单栏下方常驻的投放条。"""

    drag_entered = pyqtSignal()
    drag_left = pyqtSignal()
    folder_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAcceptDrops(True)
        self._hot = False
        self.setFixedSize(320, 56)
        self._setup_ui()
        elevate_window(self)

    def _setup_ui(self) -> None:
        tokens = DEFAULT_THEME
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        self.label = QLabel("文件拖到这")
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.label.setFont(font)
        root.addWidget(self.label)
        self._apply_style()

    def _apply_style(self) -> None:
        tokens = DEFAULT_THEME
        bg = tokens.accent if self._hot else tokens.surface_elevated
        fg = tokens.text_on_accent if self._hot else tokens.text_primary
        border = tokens.accent
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg};
                color: {fg};
                border: 2px solid {border};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {fg};
            }}
            """
        )
        self.label.setText("松开以添加" if self._hot else "文件拖到这")

    def reposition(self, x: int, y: int) -> None:
        self.move(x, y)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if path_from_mime(event.mimeData()):
            event.acceptProposedAction()
            self._hot = True
            self._apply_style()
            self.drag_entered.emit()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if path_from_mime(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._hot = False
        self._apply_style()
        self.drag_left.emit()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._hot = False
        self._apply_style()
        path = path_from_mime(event.mimeData())
        if path:
            event.acceptProposedAction()
            self.folder_dropped.emit(path)
        else:
            event.ignore()
