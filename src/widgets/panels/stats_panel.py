"""
进度与统计面板。
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from src.utils import format_bytes

STATUS_LABELS = {
    "processed": "成功",
    "skipped": "跳过",
    "too_small": "过小",
    "failed": "失败",
    "cached": "缓存",
}


class StatsPanel(QWidget):
    """运行反馈与详细结果展示。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        summary_group = QGroupBox("任务状态")
        summary_layout = QVBoxLayout(summary_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.status_label = QLabel("等待开始")
        self.metrics_label = QLabel("速度: - | ETA: -")
        self.metrics_label.setObjectName("subtle")
        summary_layout.addWidget(self.progress_bar)
        summary_layout.addWidget(self.status_label)
        summary_layout.addWidget(self.metrics_label)

        counts_row = QHBoxLayout()
        self.success_count_label = QLabel("成功: 0")
        self.skip_count_label = QLabel("跳过: 0")
        self.error_count_label = QLabel("失败: 0")
        self.saved_label = QLabel("节省: 0 B")
        counts_row.addWidget(self.success_count_label)
        counts_row.addWidget(self.skip_count_label)
        counts_row.addWidget(self.error_count_label)
        counts_row.addWidget(self.saved_label)
        counts_row.addStretch()
        summary_layout.addLayout(counts_row)
        root.addWidget(summary_group)

        detail_group = QGroupBox("结果详情")
        detail_layout = QVBoxLayout(detail_group)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("筛选"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "失败", "成功", "跳过", "过小", "缓存"])
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        self.export_btn = QPushButton("导出统计")
        self.export_btn.setEnabled(False)
        self.export_btn.setToolTip("导出压缩统计为 CSV 文件 (Ctrl+E)")
        filter_row.addWidget(self.export_btn)
        detail_layout.addLayout(filter_row)

        self.stats_table = QTableWidget(0, 5)
        self.stats_table.setHorizontalHeaderLabels(["文件名", "状态", "原始大小", "压缩后", "节省比例"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        detail_layout.addWidget(self.stats_table)
        root.addWidget(detail_group, 1)

        self._all_records = []
        self.filter_combo.currentTextChanged.connect(self.refresh_table)

    def update_summary(self, result_payload: dict) -> None:
        self.success_count_label.setText(f"成功: {result_payload.get('processed', 0)}")
        skip_val = result_payload.get("skipped", 0) + result_payload.get("too_small", 0) + result_payload.get("cached", 0)
        self.skip_count_label.setText(f"跳过: {skip_val}")
        self.error_count_label.setText(f"失败: {result_payload.get('failed', 0)}")
        self.saved_label.setText(f"节省: {format_bytes(int(result_payload.get('saved', 0)))}")

    def set_records(self, records: list) -> None:
        self._all_records = records or []
        self.refresh_table()

    def refresh_table(self) -> None:
        filter_text = self.filter_combo.currentText()
        if filter_text == "全部":
            records = self._all_records
        else:
            status_key = {
                "失败": "failed",
                "成功": "processed",
                "跳过": "skipped",
                "过小": "too_small",
                "缓存": "cached",
            }[filter_text]
            records = [r for r in self._all_records if r.get("status") == status_key]

        self.stats_table.setRowCount(len(records))
        for row, rec in enumerate(records):
            orig = int(rec.get("original_size", 0))
            comp = int(rec.get("compressed_size", 0))
            pct = (orig - comp) / orig * 100 if orig > 0 else 0
            self.stats_table.setItem(row, 0, QTableWidgetItem(rec.get("filename", "")))
            self.stats_table.setItem(row, 1, QTableWidgetItem(STATUS_LABELS.get(rec.get("status", ""), rec.get("status", ""))))
            self.stats_table.setItem(row, 2, QTableWidgetItem(format_bytes(orig)))
            self.stats_table.setItem(row, 3, QTableWidgetItem(format_bytes(comp)))
            self.stats_table.setItem(row, 4, QTableWidgetItem(f"{pct:.1f}%"))

