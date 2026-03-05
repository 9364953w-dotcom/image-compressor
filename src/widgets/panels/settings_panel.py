"""
预览与参数设置面板。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QDoubleSpinBox,
    QSlider,
    QSpinBox,
    QCheckBox,
    QScrollArea,
)

from src.config import DEFAULT_MIN_SIZE_MB, DEFAULT_QUALITY


class SettingsPanel(QWidget):
    """核心压缩参数与预览入口。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        top_group = QGroupBox("操作与预设")
        top_layout = QVBoxLayout(top_group)
        top_layout.setSpacing(6)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预设"))
        self.preset_combo = QComboBox()
        preset_row.addWidget(self.preset_combo, 1)
        self.save_preset_btn = QPushButton("保存当前预设")
        preset_row.addWidget(self.save_preset_btn)
        top_layout.addLayout(preset_row)

        self.preset_desc_label = QLabel("")
        self.preset_desc_label.setObjectName("subtle")
        top_layout.addWidget(self.preset_desc_label)

        preview_row = QHBoxLayout()
        self.exif_btn = QPushButton("查看 EXIF")
        preview_row.addWidget(self.exif_btn)
        preview_row.addStretch()
        top_layout.addLayout(preview_row)

        self.preview_notice_label = QLabel("预览为临时计算，不会覆盖源文件。")
        self.preview_notice_label.setObjectName("subtle")
        top_layout.addWidget(self.preview_notice_label)

        preview_info_row = QHBoxLayout()
        self.preview_original_label = QLabel("原始: -")
        self.preview_compressed_label = QLabel("压缩后: -")
        self.preview_savings_label = QLabel("节省: -")
        preview_info_row.addWidget(self.preview_original_label)
        preview_info_row.addWidget(self.preview_compressed_label)
        preview_info_row.addWidget(self.preview_savings_label)
        preview_info_row.addStretch()
        top_layout.addLayout(preview_info_row)
        root.addWidget(top_group)

        settings_group = QGroupBox("压缩参数")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("格式"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["保持原格式", "JPG", "PNG", "WebP"])
        row1.addWidget(self.format_combo)
        row1.addWidget(QLabel("最小体积"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        row1.addWidget(self.min_size_spin)
        row1.addStretch()
        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("质量"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setValue(DEFAULT_QUALITY)
        self.quality_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        row2.addWidget(self.quality_slider, 1)
        row2.addWidget(self.quality_spin)
        settings_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.resize_cb = QCheckBox("限制尺寸")
        self.keep_ratio_cb = QCheckBox("保持比例")
        self.keep_ratio_cb.setChecked(True)
        row3.addWidget(self.resize_cb)
        row3.addWidget(self.keep_ratio_cb)
        row3.addWidget(QLabel("宽"))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(0, 20000)
        self.max_width_spin.setEnabled(False)
        self.max_width_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        row3.addWidget(self.max_width_spin)
        row3.addWidget(QLabel("高"))
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 20000)
        self.max_height_spin.setEnabled(False)
        self.max_height_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        row3.addWidget(self.max_height_spin)
        settings_layout.addLayout(row3)

        row4 = QHBoxLayout()
        self.smart_cb = QCheckBox("智能压缩")
        row4.addWidget(self.smart_cb)
        row4.addWidget(QLabel("目标"))
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 50000)
        self.target_size_spin.setValue(200)
        self.target_size_spin.setSuffix(" KB")
        self.target_size_spin.setEnabled(False)
        self.target_size_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        row4.addWidget(self.target_size_spin)
        row4.addStretch()
        settings_layout.addLayout(row4)

        row5 = QHBoxLayout()
        self.include_subfolders_cb = QCheckBox("包含子文件夹")
        self.incremental_cb = QCheckBox("跳过已处理文件")
        self.incremental_cb.setChecked(True)
        self.keep_exif_cb = QCheckBox("保留 EXIF")
        self.keep_exif_cb.setChecked(True)
        self.auto_rotate_cb = QCheckBox("自动旋转")
        self.auto_rotate_cb.setChecked(True)
        row5.addWidget(self.include_subfolders_cb)
        row5.addWidget(self.incremental_cb)
        row5.addWidget(self.keep_exif_cb)
        row5.addWidget(self.auto_rotate_cb)
        row5.addStretch()
        settings_layout.addLayout(row5)

        root.addWidget(settings_group, 0)

        preview_group = QGroupBox("实时预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(6)

        preview_toolbar = QHBoxLayout()
        self.preview_100_cb = QCheckBox("100%显示")
        self.live_preview_cb = QCheckBox("实时预览")
        self.live_preview_cb.setChecked(True)
        preview_toolbar.addWidget(QLabel("默认显示：压缩后预览"))
        preview_toolbar.addSpacing(8)
        preview_toolbar.addWidget(self.preview_100_cb)
        preview_toolbar.addWidget(self.live_preview_cb)
        preview_toolbar.addStretch()
        preview_layout.addLayout(preview_toolbar)

        self.preview_area = QScrollArea()
        self.preview_area.setMinimumHeight(190)
        self.preview_area.setWidgetResizable(False)
        self.preview_image_label = QLabel("请选择输入目录后查看预览")
        self.preview_image_label.setAlignment(Qt.AlignCenter)
        self.preview_area.setWidget(self.preview_image_label)
        preview_layout.addWidget(self.preview_area)

        root.addWidget(preview_group, 1)

        action_group = QGroupBox("任务操作")
        action_layout = QHBoxLayout(action_group)
        action_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.setSpacing(8)
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setObjectName("primaryBtn")
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        action_layout.addStretch()
        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.cancel_btn)
        root.addWidget(action_group)

        self.quality_slider.valueChanged.connect(self.quality_spin.setValue)
        self.quality_spin.valueChanged.connect(self.quality_slider.setValue)
        self.resize_cb.toggled.connect(self.max_width_spin.setEnabled)
        self.resize_cb.toggled.connect(self.max_height_spin.setEnabled)
        self.smart_cb.toggled.connect(self.target_size_spin.setEnabled)
        self.smart_cb.toggled.connect(lambda checked: self.quality_slider.setEnabled(not checked))
        self.smart_cb.toggled.connect(lambda checked: self.quality_spin.setEnabled(not checked))

        self._original_pixmap = None
        self._compressed_pixmap = None

    def set_preview_images(self, original_pixmap, compressed_pixmap) -> None:
        self._original_pixmap = original_pixmap
        self._compressed_pixmap = compressed_pixmap
        self.refresh_preview_widget()

    def clear_preview(self, message: str) -> None:
        self._original_pixmap = None
        self._compressed_pixmap = None
        self.preview_image_label.setText(message)
        self.preview_image_label.adjustSize()

    def refresh_preview_widget(self) -> None:
        pixmap = self._compressed_pixmap
        if pixmap is None or pixmap.isNull():
            return
        if self.preview_100_cb.isChecked():
            self.preview_image_label.setPixmap(pixmap)
            self.preview_image_label.resize(pixmap.size())
            return

        viewport = self.preview_area.viewport().size()
        target_w = max(10, viewport.width() - 8)
        target_h = max(10, viewport.height() - 8)
        scaled = pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_image_label.setPixmap(scaled)
        self.preview_image_label.resize(scaled.size())

    def output_format_value(self) -> str:
        return ["original", "jpg", "png", "webp"][self.format_combo.currentIndex()]

