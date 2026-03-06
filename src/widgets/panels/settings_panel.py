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
    QLineEdit,
)

from src.config import DEFAULT_MIN_SIZE_MB, DEFAULT_QUALITY, RENAME_PATTERN_LABELS
from src.widgets.compare_slider import CompareSlider


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
        self.exif_btn.setToolTip("查看选中图片的 EXIF 信息")
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
        self.format_combo.addItems(["保持原格式", "JPG", "PNG", "WebP", "AVIF", "HEIF"])
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

        rename_row = QHBoxLayout()
        rename_row.addWidget(QLabel("重命名"))
        self.rename_combo = QComboBox()
        for label, _pattern in RENAME_PATTERN_LABELS:
            self.rename_combo.addItem(label)
        rename_row.addWidget(self.rename_combo)
        rename_row.addWidget(QLabel("前缀"))
        self.rename_prefix_edit = QLineEdit()
        self.rename_prefix_edit.setPlaceholderText("自定义前缀")
        self.rename_prefix_edit.setMaximumWidth(120)
        self.rename_prefix_edit.setEnabled(False)
        rename_row.addWidget(self.rename_prefix_edit)
        rename_row.addStretch()
        settings_layout.addLayout(rename_row)

        adv_row = QHBoxLayout()
        adv_row.addWidget(QLabel("失败重试"))
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 3)
        self.retry_spin.setValue(1)
        self.retry_spin.setSuffix(" 次")
        self.retry_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        adv_row.addWidget(self.retry_spin)
        adv_row.addStretch()
        settings_layout.addLayout(adv_row)

        root.addWidget(settings_group, 0)

        preview_group = QGroupBox("实时预览（左原图 / 右压缩后 · 拖动滑块对比 · 滚轮缩放 · 双击切换100%）")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(6)

        preview_toolbar = QHBoxLayout()
        self.live_preview_cb = QCheckBox("实时预览")
        self.live_preview_cb.setChecked(True)
        preview_toolbar.addWidget(self.live_preview_cb)
        preview_toolbar.addSpacing(12)
        self.zoom_fit_btn = QPushButton("适应窗口")
        self.zoom_fit_btn.setFixedWidth(72)
        self.zoom_100_btn = QPushButton("100%")
        self.zoom_100_btn.setFixedWidth(52)
        preview_toolbar.addWidget(self.zoom_fit_btn)
        preview_toolbar.addWidget(self.zoom_100_btn)
        preview_toolbar.addStretch()
        preview_layout.addLayout(preview_toolbar)

        self.compare_slider = CompareSlider()
        self.compare_slider.setMinimumHeight(120)
        self.zoom_fit_btn.clicked.connect(self.compare_slider.zoom_fit)
        self.zoom_100_btn.clicked.connect(self.compare_slider.zoom_100)
        preview_layout.addWidget(self.compare_slider, 1)

        root.addWidget(preview_group, 1)

        action_group = QGroupBox("任务操作")
        action_layout = QHBoxLayout(action_group)
        action_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.setSpacing(8)
        self.convert_only_btn = QPushButton("仅转换格式")
        self.convert_only_btn.setToolTip("只转换图片格式，不压缩质量")
        self.convert_only_btn.setMinimumHeight(38)
        self.convert_only_btn.setMinimumWidth(120)
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.setToolTip("按照当前参数开始批量压缩 (Ctrl+Enter)")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.setMinimumWidth(120)
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setToolTip("暂停/继续当前任务")
        self.pause_btn.setMinimumHeight(38)
        self.pause_btn.setEnabled(False)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip("取消当前压缩任务 (Esc)")
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setMinimumWidth(100)
        action_layout.addStretch()
        action_layout.addWidget(self.convert_only_btn)
        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.pause_btn)
        action_layout.addWidget(self.cancel_btn)
        root.addWidget(action_group)

        self.quality_slider.valueChanged.connect(self.quality_spin.setValue)
        self.quality_spin.valueChanged.connect(self.quality_slider.setValue)
        self.resize_cb.toggled.connect(self.max_width_spin.setEnabled)
        self.resize_cb.toggled.connect(self.max_height_spin.setEnabled)
        self.smart_cb.toggled.connect(self.target_size_spin.setEnabled)
        self.smart_cb.toggled.connect(lambda checked: self.quality_slider.setEnabled(not checked))
        self.smart_cb.toggled.connect(lambda checked: self.quality_spin.setEnabled(not checked))
        self.rename_combo.currentIndexChanged.connect(self._on_rename_changed)

        self._original_pixmap = None
        self._compressed_pixmap = None

    def _on_rename_changed(self, index: int) -> None:
        pattern = RENAME_PATTERN_LABELS[index][1] if index < len(RENAME_PATTERN_LABELS) else "{name}"
        self.rename_prefix_edit.setEnabled("{prefix}" in pattern)

    def rename_pattern_value(self):
        idx = self.rename_combo.currentIndex()
        if idx <= 0:
            return None
        pattern = RENAME_PATTERN_LABELS[idx][1]
        if "{prefix}" in pattern:
            prefix = self.rename_prefix_edit.text().strip()
            if prefix:
                pattern = pattern.replace("{prefix}", prefix)
            else:
                return None
        return pattern

    def set_preview_images(self, original_pixmap, compressed_pixmap) -> None:
        self._original_pixmap = original_pixmap
        self._compressed_pixmap = compressed_pixmap
        self.compare_slider.set_images(original_pixmap, compressed_pixmap)

    def clear_preview(self, message: str) -> None:
        self._original_pixmap = None
        self._compressed_pixmap = None
        self.compare_slider.clear(message)

    def refresh_preview_widget(self) -> None:
        if self._original_pixmap and self._compressed_pixmap:
            self.compare_slider.set_images(self._original_pixmap, self._compressed_pixmap)

    def output_format_value(self) -> str:
        return ["original", "jpg", "png", "webp", "avif", "heif"][self.format_combo.currentIndex()]
