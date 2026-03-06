"""
历史任务记录对话框。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from src.config import config_manager
from src.utils import format_bytes


class HistoryDialog(QDialog):
    """展示历史任务列表，支持查看详情和复用配置。"""

    def __init__(self, tokens=None, parent=None):
        super().__init__(parent)
        self._tokens = tokens
        self._selected_settings = None
        self.setWindowTitle("历史任务记录")
        self.setMinimumSize(720, 420)
        self._setup_ui()
        self._load_records()

    @property
    def selected_settings(self):
        return self._selected_settings

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels([
            "时间", "输入路径", "文件数", "成功", "节省空间", "耗时",
        ])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        self._reuse_btn = QPushButton("使用此配置")
        self._reuse_btn.setToolTip("加载选中记录的压缩参数到主界面")
        self._reuse_btn.clicked.connect(self._on_reuse)
        btn_row.addWidget(self._reuse_btn)

        self._clear_btn = QPushButton("清空历史")
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._clear_btn)

        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _load_records(self) -> None:
        self._records = config_manager.load_task_records()
        self._table.setRowCount(0)
        for rec in reversed(self._records):
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(rec.get("timestamp", "-")))
            self._table.setItem(row, 1, QTableWidgetItem(rec.get("input_path", "-")))
            self._table.setItem(row, 2, QTableWidgetItem(str(rec.get("total_files", 0))))
            self._table.setItem(row, 3, QTableWidgetItem(str(rec.get("processed", 0))))
            self._table.setItem(row, 4, QTableWidgetItem(format_bytes(int(rec.get("saved", 0)))))
            elapsed = rec.get("elapsed_seconds", 0)
            self._table.setItem(row, 5, QTableWidgetItem(f"{elapsed:.1f}s"))

    def _current_record(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        visual_row = rows[0].row()
        real_index = len(self._records) - 1 - visual_row
        if 0 <= real_index < len(self._records):
            return self._records[real_index]
        return None

    def _on_reuse(self) -> None:
        rec = self._current_record()
        if not rec:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return
        self._selected_settings = rec.get("settings")
        self.accept()

    def _on_clear(self) -> None:
        reply = QMessageBox.question(
            self, "确认", "确定清空所有历史任务记录？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            config_manager.clear_task_records()
            self._load_records()
