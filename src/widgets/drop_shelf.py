"""菜单栏下方的简洁投放架。"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)

from src.widgets.drag_drop import path_from_mime
from src.widgets.theme import DEFAULT_THEME, build_stylesheet
from src.widgets.window_level import release_window


class DropShelf(QWidget):
    """投放架四态：空 / 已放入 / 压缩中 / 完成。"""

    STATE_EMPTY = "empty"
    STATE_STAGED = "staged"
    STATE_RUNNING = "running"
    STATE_DONE = "done"

    start_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    hover_changed = pyqtSignal(bool)
    folder_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        self.state = self.STATE_EMPTY
        self._folder_name = ""
        self._file_count_text = "扫描中…"
        self._settings_text = ""
        self._overwrite = False
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(300)
        self._hide_timer.timeout.connect(self._try_hide)
        self._done_timer = QTimer(self)
        self._done_timer.setSingleShot(True)
        self._done_timer.setInterval(2000)
        self._done_timer.timeout.connect(self.reset_and_hide)

        self.setFixedWidth(320)
        self._setup_ui()
        self.apply_theme()
        self._apply_state()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        self.title_label = QLabel("松开以添加文件夹")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        root.addWidget(self.title_label)

        self.folder_label = QLabel("")
        self.folder_label.setWordWrap(True)
        root.addWidget(self.folder_label)

        self.count_label = QLabel("")
        self.count_label.setObjectName("subtle")
        root.addWidget(self.count_label)

        self.settings_label = QLabel("")
        self.settings_label.setObjectName("subtle")
        self.settings_label.setWordWrap(True)
        root.addWidget(self.settings_label)

        self.warning_label = QLabel("将覆盖原图")
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.hide()
        root.addWidget(self.warning_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("subtle")
        self.status_label.hide()
        root.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("取消")
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setObjectName("primaryBtn")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.start_btn.clicked.connect(self.start_requested.emit)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.start_btn)
        root.addLayout(btn_row)

    def apply_theme(self) -> None:
        tokens = DEFAULT_THEME
        extra = f"""
        QWidget {{
            background-color: {tokens.surface};
            color: {tokens.text_primary};
            border: 1px solid {tokens.border};
            border-radius: 8px;
        }}
        QLabel#warningLabel {{
            color: {tokens.warning};
            font-weight: 600;
        }}
        """
        self.setStyleSheet(build_stylesheet(tokens) + extra)

    def is_pinned(self) -> bool:
        return self.state in {self.STATE_STAGED, self.STATE_RUNNING}

    def schedule_hide(self) -> None:
        if self.is_pinned():
            return
        self._hide_timer.start()

    def cancel_hide(self) -> None:
        self._hide_timer.stop()

    def _try_hide(self) -> None:
        if not self.is_pinned() and self.state != self.STATE_DONE:
            self.hide()

    def reset_and_hide(self) -> None:
        self.state = self.STATE_EMPTY
        self._apply_state()
        self.hide()

    def show_empty(self) -> None:
        self._done_timer.stop()
        self.state = self.STATE_EMPTY
        self._apply_state()
        self.show()
        self.raise_()

    def set_staged(self, folder_name: str, settings_text: str, overwrite: bool) -> None:
        self._done_timer.stop()
        self.state = self.STATE_STAGED
        self._folder_name = folder_name
        self._file_count_text = "扫描中…"
        self._settings_text = settings_text
        self._overwrite = overwrite
        self._apply_state()
        self.show()
        self.raise_()

    def set_file_count(self, count: int) -> None:
        if count <= 0:
            self._file_count_text = "未找到图片"
        else:
            self._file_count_text = f"{count} 张图片"
        if self.state == self.STATE_STAGED:
            self.count_label.setText(self._file_count_text)

    def set_running(self, current: int = 0, total: int = 0, percent: int = 0) -> None:
        self._done_timer.stop()
        self.state = self.STATE_RUNNING
        self.progress_bar.setValue(percent)
        if total:
            self.status_label.setText(f"处理中 {current}/{total}")
        else:
            self.status_label.setText("准备中…")
        self._apply_state()

    def reveal(self) -> None:
        self.show()

    def set_done(self, processed: int, saved_text: str) -> None:
        self.state = self.STATE_DONE
        self.status_label.setText(f"{processed} 张已完成，节省 {saved_text}")
        self._apply_state()
        self._done_timer.start()

    def _on_cancel(self) -> None:
        if self.state == self.STATE_RUNNING:
            self.cancel_requested.emit()
            return
        self.reset_and_hide()
        self.cancel_requested.emit()

    def _apply_state(self) -> None:
        empty = self.state == self.STATE_EMPTY
        staged = self.state == self.STATE_STAGED
        running = self.state == self.STATE_RUNNING
        done = self.state == self.STATE_DONE

        if empty:
            self.title_label.setText("松开以添加文件夹")
        elif staged:
            self.title_label.setText("已放入文件夹")
        elif running:
            self.title_label.setText("正在压缩")
        else:
            self.title_label.setText("压缩完成")

        self.folder_label.setVisible(staged or running)
        self.folder_label.setText(self._folder_name)
        self.count_label.setVisible(staged)
        self.count_label.setText(self._file_count_text)
        self.settings_label.setVisible(staged)
        self.settings_label.setText(self._settings_text)
        self.warning_label.setVisible(staged and self._overwrite)
        self.progress_bar.setVisible(running)
        self.status_label.setVisible(running or done)
        self.start_btn.setVisible(staged)
        self.cancel_btn.setVisible(staged or running)
        self.cancel_btn.setText("取消")
        self.adjustSize()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if path_from_mime(event.mimeData()):
            event.acceptProposedAction()
            self.cancel_hide()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if path_from_mime(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        path = path_from_mime(event.mimeData())
        if path:
            event.acceptProposedAction()
            self.folder_dropped.emit(path)
        else:
            event.ignore()

    def enterEvent(self, event) -> None:
        self.cancel_hide()
        self.hover_changed.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.hover_changed.emit(False)
        self.schedule_hide()
        super().leaveEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        release_window(self)
