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
    QListWidget,
    QGroupBox,
)

from src.widgets.drag_drop import DragDropLineEdit


class InputPanel(QWidget):
    """输入路径、历史、文件列表。"""

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
        input_row.addWidget(self.input_edit)
        input_row.addWidget(self.browse_input_btn)
        path_layout.addLayout(input_row)

        path_layout.addWidget(QLabel("输出文件夹（留空表示覆盖原文件）"))
        output_row = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("可选")
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.setFixedWidth(64)
        output_row.addWidget(self.output_edit)
        output_row.addWidget(self.browse_output_btn)
        path_layout.addLayout(output_row)

        path_layout.addWidget(QLabel("历史记录"))
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("选择历史目录")
        path_layout.addWidget(self.history_combo)

        root.addWidget(path_group)

        files_group = QGroupBox("文件源")
        files_layout = QVBoxLayout(files_group)
        self.file_list = QListWidget()
        self.file_info_label = QLabel("0 个文件")
        self.file_info_label.setObjectName("subtle")
        files_layout.addWidget(self.file_list)
        files_layout.addWidget(self.file_info_label)
        root.addWidget(files_group, 1)

