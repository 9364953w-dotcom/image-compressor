"""
输入与文件源面板。
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QListWidget,
)

from src.widgets.drag_drop import DragDropLineEdit, DragDropListWidget


class InputPanel(QWidget):
    """输入路径、历史、文件列表、任务队列。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        path_group = QGroupBox("输入与输出")
        path_layout = QVBoxLayout(path_group)

        path_layout.addWidget(QLabel("输入文件夹"))
        input_row = QHBoxLayout()
        self.input_edit = DragDropLineEdit()
        self.browse_input_btn = QPushButton("浏览")
        self.browse_input_btn.setFixedWidth(64)
        self.browse_input_btn.setToolTip("选择包含图片的文件夹 (Ctrl+O)")
        input_row.addWidget(self.input_edit)
        input_row.addWidget(self.browse_input_btn)
        path_layout.addLayout(input_row)

        path_layout.addWidget(QLabel("输出文件夹（留空表示覆盖原文件）"))
        output_row = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("可选")
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.setFixedWidth(64)
        self.browse_output_btn.setToolTip("选择输出文件夹（留空则覆盖原文件）")
        output_row.addWidget(self.output_edit)
        output_row.addWidget(self.browse_output_btn)
        path_layout.addLayout(output_row)

        path_layout.addWidget(QLabel("历史记录"))
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("选择历史目录")
        path_layout.addWidget(self.history_combo)

        root.addWidget(path_group)

        files_group = QGroupBox("文件源（支持拖入图片或文件夹）")
        files_layout = QVBoxLayout(files_group)
        self.file_list = DragDropListWidget()
        self.file_info_label = QLabel("0 个文件")
        self.file_info_label.setObjectName("subtle")
        files_layout.addWidget(self.file_list)
        files_layout.addWidget(self.file_info_label)
        root.addWidget(files_group, 1)

        queue_group = QGroupBox("任务队列")
        queue_layout = QVBoxLayout(queue_group)
        queue_btn_row = QHBoxLayout()
        self.enqueue_btn = QPushButton("添加当前任务")
        self.enqueue_btn.setToolTip("将当前参数添加到队列，可连续处理多个目录")
        self.clear_queue_btn = QPushButton("清空")
        self.clear_queue_btn.setToolTip("清空任务队列")
        queue_btn_row.addWidget(self.enqueue_btn)
        queue_btn_row.addStretch()
        queue_btn_row.addWidget(self.clear_queue_btn)
        queue_layout.addLayout(queue_btn_row)

        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(100)
        queue_layout.addWidget(self.queue_list)
        root.addWidget(queue_group, 0)
