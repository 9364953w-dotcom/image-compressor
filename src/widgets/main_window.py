"""
主窗口模块 - 现代深色玻璃拟态风格
"""

from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QCheckBox, QProgressBar,
    QSlider, QSpinBox, QTextEdit, QDoubleSpinBox, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QSplitter,
    QAbstractItemView, QMenuBar, QMenu, QAction, QFrame,
    QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QIcon

from src.config import (
    APP_NAME, __version__, DEFAULT_QUALITY, DEFAULT_MIN_SIZE_MB,
    RENAME_PATTERNS, OUTPUT_FORMATS, config_manager
)
from src.utils import format_bytes, setup_logging
from src.widgets.drag_drop import DragDropLineEdit
from src.widgets.about_dialog import AboutDialog
from src.widgets.exif_dialog import ExifDialog
from src.core.worker import CompressWorker
from src.core.compressor import get_exif_info, compress_image


class MainWindow(QWidget):
    """图片压缩工具主窗口 - 现代深色玻璃拟态风格"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = setup_logging()
        self._is_running = False
        self.worker = None
        self.thread = None
        self.current_detailed_stats = []
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 应用现代深色样式
        self._setup_modern_style()
        self._setup_ui()
        self._connect_signals()
        self._load_history()
        self._load_presets()
    
    def _setup_modern_style(self):
        """设置现代深色玻璃拟态风格 - 直角版本"""
        self.setStyleSheet("""
            /* 全局样式 - 深黑背景 */
            QWidget {
                background-color: #0d0d12;
                color: #e8e8ed;
                font-size: 13px;
            }
            
            /* 玻璃拟态卡片 - 无圆角 */
            QGroupBox {
                background-color: #1a1a24;
                border: 1px solid #333;
                border-radius: 0px;
                margin-top: 8px;
                padding: 12px;
            }
            
            QGroupBox::title {
                color: #a29bfe;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                font-size: 12px;
            }
            
            /* 输入框 - 无圆角 */
            QLineEdit {
                background-color: #252530;
                border: 1px solid #444;
                border-radius: 0px;
                padding: 8px 10px;
                color: #ffffff;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border-color: #6c5ce7;
            }
            
            QLineEdit::placeholder {
                color: #666;
            }
            
            /* 主按钮 - 无圆角 */
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 0px;
                padding: 8px 12px;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #7d6cf0;
            }
            
            QPushButton:pressed {
                background-color: #5b4dd6;
            }
            
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
            
            /* 次要按钮 */
            QPushButton#secondaryBtn {
                background-color: #2a2a35;
                border: 1px solid #444;
                color: #e8e8ed;
            }
            
            QPushButton#secondaryBtn:hover {
                background-color: #353540;
                border-color: #555;
            }
            
            /* 复选框 - 带打勾样式 */
            QCheckBox {
                color: #e8e8ed;
                font-size: 13px;
                spacing: 8px;
                background: transparent;
                border: none;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 0px;
                border: 2px solid #6c5ce7;
                background-color: transparent;
            }
            
            QCheckBox::indicator:checked {
                background-color: #6c5ce7;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNOCAyTDQgN0wyIDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
            }
            
            QCheckBox::indicator:hover {
                border-color: #a29bfe;
            }
            
            QCheckBox::indicator:unchecked:hover {
                background-color: rgba(108, 92, 231, 0.1);
            }
            
            /* 下拉框 - 无圆角 */
            QComboBox {
                background-color: #252530;
                border: 1px solid #444;
                border-radius: 0px;
                padding: 8px 10px;
                color: #ffffff;
                min-width: 100px;
            }
            
            QComboBox:hover {
                border-color: #6c5ce7;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1a1a24;
                border: 1px solid #444;
                selection-background-color: #6c5ce7;
            }
            
            /* 滑块 - 优化样式 */
            QSlider::groove:horizontal {
                height: 6px;
                background-color: #252530;
                border: 1px solid #444;
            }
            
            QSlider::sub-page:horizontal {
                background-color: #6c5ce7;
            }
            
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -6px 0;
                background-color: #fff;
                border: 1px solid #888;
            }
            
            QSlider::handle:horizontal:hover {
                background-color: #a29bfe;
                border-color: #6c5ce7;
            }
            
            /* 数值框 - 带箭头按钮 */
            QSpinBox, QDoubleSpinBox {
                background-color: #252530;
                border: 1px solid #444;
                border-radius: 0px;
                color: #ffffff;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                height: 50%;
                border-left: 1px solid #444;
                border-bottom: 1px solid #444;
                background-color: #2a2a35;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                height: 50%;
                border-left: 1px solid #444;
                background-color: #2a2a35;
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #6c5ce7;
            }
            
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #6c5ce7;
            }
            
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #888;
                width: 0px;
                height: 0px;
            }
            
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #888;
                width: 0px;
                height: 0px;
            }
            
            QDoubleSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #888;
                width: 0px;
                height: 0px;
            }
            
            QDoubleSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #888;
                width: 0px;
                height: 0px;
            }
            
            /* 进度条 */
            QProgressBar {
                background-color: #252530;
                border-radius: 0px;
                text-align: center;
                height: 16px;
                color: #e8e8ed;
                font-size: 11px;
                border: 1px solid #444;
            }
            
            QProgressBar::chunk {
                background-color: #6c5ce7;
                border-radius: 0px;
            }
            
            /* 标签页 */
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            
            QTabBar::tab {
                background-color: #1a1a24;
                border: 1px solid #333;
                color: #8b8b9b;
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: 0px;
            }
            
            QTabBar::tab:selected {
                background-color: #6c5ce7;
                border-color: #6c5ce7;
                color: #ffffff;
            }
            
            /* 文本框 */
            QTextEdit {
                background-color: #1a1a24;
                border: 1px solid #444;
                border-radius: 0px;
                padding: 10px;
                color: #e8e8ed;
                font-size: 12px;
            }
            
            /* 表格 */
            QTableWidget {
                background-color: #1a1a24;
                border: 1px solid #444;
                border-radius: 0px;
                gridline-color: #333;
            }
            
            QTableWidget::item {
                padding: 8px;
                color: #e8e8ed;
                border-bottom: 1px solid #333;
            }
            
            QTableWidget::item:selected {
                background-color: #6c5ce7;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #252530;
                color: #a29bfe;
                padding: 10px;
                border: none;
                border-right: 1px solid #333;
                font-size: 12px;
            }
            
            /* 标签 */
            QLabel {
                color: #e8e8ed;
                background: transparent;
            }
            
            /* 菜单栏 */
            QMenuBar {
                background-color: transparent;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                color: #8b8b9b;
            }
            
            QMenuBar::item:selected {
                background-color: #6c5ce7;
                color: #ffffff;
                border-radius: 0px;
            }
            
            QMenu {
                background-color: #1a1a24;
                border: 1px solid #444;
                border-radius: 0px;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 8px 16px;
                border-radius: 0px;
                color: #e8e8ed;
            }
            
            QMenu::item:selected {
                background-color: #6c5ce7;
            }
        """)
    
    def _setup_ui(self):
        """设置用户界面 - 现代布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # ========== 顶部标题栏 ==========
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧标题
        title_container = QWidget()
        title_vlayout = QVBoxLayout(title_container)
        title_vlayout.setSpacing(4)
        title_vlayout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; font-weight: 700;")
        title_vlayout.addWidget(title_label)
        
        version_label = QLabel(f"v{__version__} • 智能批量图片压缩")
        version_label.setObjectName("subtitleLabel")
        version_label.setStyleSheet("color: #6b6b7b; font-size: 13px;")
        title_vlayout.addWidget(version_label)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        # 右侧菜单按钮
        about_btn = QPushButton("关于")
        about_btn.setObjectName("secondaryBtn")
        about_btn.setFixedWidth(60)
        about_btn.clicked.connect(self._show_about)
        header_layout.addWidget(about_btn)
        
        main_layout.addWidget(header)
        
        # ========== 主内容区（三栏布局）==========
        content = QHBoxLayout()
        content.setSpacing(20)
        
        # 左侧面板 - 输入和预设
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 路径设置卡片
        path_card = QGroupBox("📁 输入输出")
        path_layout = QVBoxLayout(path_card)
        path_layout.setSpacing(12)
        
        # 输入路径行
        input_label = QLabel("输入文件夹")
        input_label.setStyleSheet("color: #8b8b9b; font-size: 12px;")
        path_layout.addWidget(input_label)
        
        input_row = QHBoxLayout()
        self.input_edit = DragDropLineEdit()
        self.input_edit.setPlaceholderText("拖拽或选择输入文件夹...")
        self.input_edit.setMinimumHeight(36)
        input_row.addWidget(self.input_edit)
        
        browse_input = QPushButton("浏览")
        browse_input.setFixedWidth(70)
        browse_input.setMinimumWidth(60)
        browse_input.clicked.connect(self._select_input)
        browse_input.setObjectName("secondaryBtn")
        input_row.addWidget(browse_input)
        path_layout.addLayout(input_row)
        
        # 输出路径行
        output_label = QLabel("输出文件夹")
        output_label.setStyleSheet("color: #8b8b9b; font-size: 12px;")
        path_layout.addWidget(output_label)
        
        output_row = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("留空则覆盖原文件...")
        self.output_edit.setMinimumHeight(36)
        output_row.addWidget(self.output_edit)
        
        browse_output = QPushButton("浏览")
        browse_output.setFixedWidth(70)
        browse_output.setMinimumWidth(60)
        browse_output.clicked.connect(self._select_output)
        browse_output.setObjectName("secondaryBtn")
        output_row.addWidget(browse_output)
        path_layout.addLayout(output_row)
        
        # 历史记录行
        history_row = QHBoxLayout()
        history_label = QLabel("历史记录")
        history_label.setStyleSheet("color: #8b8b9b; font-size: 12px;")
        history_row.addWidget(history_label)
        
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("选择历史记录...")
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        history_row.addWidget(self.history_combo, 1)
        path_layout.addLayout(history_row)
        
        left_layout.addWidget(path_card)
        
        # 预设配置卡片
        preset_card = QGroupBox("🎯 预设配置")
        preset_layout = QVBoxLayout(preset_card)
        
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setPlaceholderText("选择预设...")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo)
        
        save_preset_btn = QPushButton("保存")
        save_preset_btn.setObjectName("secondaryBtn")
        save_preset_btn.setFixedWidth(70)
        save_preset_btn.setMinimumWidth(60)
        save_preset_btn.clicked.connect(self._save_preset)
        preset_row.addWidget(save_preset_btn)
        
        preset_layout.addLayout(preset_row)
        
        self.preset_desc_label = QLabel("")
        self.preset_desc_label.setStyleSheet("color: #6b6b7b; font-size: 12px;")
        preset_layout.addWidget(self.preset_desc_label)
        
        left_layout.addWidget(preset_card)
        left_layout.addStretch()
        
        content.addWidget(left_panel, 1)
        
        # 中间面板 - 压缩选项
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(16)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # 压缩选项卡片
        options_card = QGroupBox("📤 输出设置")
        options_layout = QVBoxLayout(options_card)
        options_layout.setSpacing(16)
        
        # 输出格式和最小大小
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["保持原格式", "JPG", "PNG", "WebP"])
        self.format_combo.setFixedWidth(140)
        row1.addWidget(self.format_combo)
        
        row1.addSpacing(20)
        
        row1.addWidget(QLabel("最小大小:"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedWidth(110)
        row1.addWidget(self.min_size_spin)
        row1.addStretch()
        
        options_layout.addLayout(row1)
        
        # 压缩质量
        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("压缩质量:"))
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        quality_row.addWidget(self.quality_slider, 1)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(DEFAULT_QUALITY)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setFixedWidth(80)
        quality_row.addWidget(self.quality_spin)
        
        options_layout.addLayout(quality_row)
        
        # 尺寸调整
        resize_group = QWidget()
        resize_group.setStyleSheet("background: transparent;")
        resize_layout = QHBoxLayout(resize_group)
        resize_layout.setContentsMargins(0, 0, 0, 0)
        
        self.resize_cb = QCheckBox("调整尺寸")
        self.resize_cb.stateChanged.connect(self._on_resize_toggled)
        resize_layout.addWidget(self.resize_cb)
        
        resize_layout.addWidget(QLabel("最大宽:"))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(0, 10000)
        self.max_width_spin.setValue(0)
        self.max_width_spin.setSuffix(" px")
        self.max_width_spin.setFixedWidth(90)
        self.max_width_spin.setEnabled(False)
        resize_layout.addWidget(self.max_width_spin)
        
        resize_layout.addWidget(QLabel("最大高:"))
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 10000)
        self.max_height_spin.setValue(0)
        self.max_height_spin.setSuffix(" px")
        self.max_height_spin.setFixedWidth(90)
        self.max_height_spin.setEnabled(False)
        resize_layout.addWidget(self.max_height_spin)
        
        self.keep_ratio_cb = QCheckBox("保持比例")
        self.keep_ratio_cb.setChecked(True)
        self.keep_ratio_cb.setEnabled(False)
        resize_layout.addWidget(self.keep_ratio_cb)
        resize_layout.addStretch()
        
        options_layout.addWidget(resize_group)
        
        # 智能压缩
        smart_group = QWidget()
        smart_group.setStyleSheet("background: transparent;")
        smart_layout = QHBoxLayout(smart_group)
        smart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.smart_cb = QCheckBox("智能压缩")
        self.smart_cb.stateChanged.connect(self._on_smart_toggled)
        smart_layout.addWidget(self.smart_cb)
        
        smart_layout.addWidget(QLabel("目标大小:"))
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 10000)
        self.target_size_spin.setValue(200)
        self.target_size_spin.setSuffix(" KB")
        self.target_size_spin.setFixedWidth(90)
        self.target_size_spin.setEnabled(False)
        smart_layout.addWidget(self.target_size_spin)
        smart_layout.addStretch()
        
        options_layout.addWidget(smart_group)
        
        # EXIF 选项
        exif_group = QWidget()
        exif_group.setStyleSheet("background: transparent;")
        exif_layout = QHBoxLayout(exif_group)
        exif_layout.setContentsMargins(0, 0, 0, 0)
        
        self.keep_exif_cb = QCheckBox("保留 EXIF")
        self.keep_exif_cb.setChecked(True)
        exif_layout.addWidget(self.keep_exif_cb)
        
        self.auto_rotate_cb = QCheckBox("自动旋转")
        self.auto_rotate_cb.setChecked(True)
        exif_layout.addWidget(self.auto_rotate_cb)
        
        exif_btn = QPushButton("查看 EXIF")
        exif_btn.setObjectName("secondaryBtn")
        exif_btn.setFixedWidth(80)
        exif_btn.clicked.connect(self._show_exif)
        exif_layout.addWidget(exif_btn)
        exif_layout.addStretch()
        
        options_layout.addWidget(exif_group)
        
        center_layout.addWidget(options_card)
        
        # 预览卡片
        preview_card = QGroupBox("👁️ 压缩预览")
        preview_layout = QVBoxLayout(preview_card)
        
        preview_btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("预览第一张图片")
        self.preview_btn.setMinimumWidth(140)
        self.preview_btn.clicked.connect(self._preview_compression)
        preview_btn_row.addWidget(self.preview_btn)
        preview_btn_row.addStretch()
        preview_layout.addLayout(preview_btn_row)
        
        preview_result = QHBoxLayout()
        self.preview_original_label = QLabel("原图: -")
        self.preview_original_label.setStyleSheet("color: #6b6b7b;")
        preview_result.addWidget(self.preview_original_label)
        
        preview_result.addWidget(QLabel("→", styleSheet="color: #6c5ce7; font-weight: bold;"))
        
        self.preview_compressed_label = QLabel("压缩后: -")
        self.preview_compressed_label.setStyleSheet("color: #a29bfe; font-weight: 600;")
        preview_result.addWidget(self.preview_compressed_label)
        
        preview_result.addSpacing(20)
        
        self.preview_savings_label = QLabel("节省: -")
        self.preview_savings_label.setStyleSheet("color: #00d9a5; font-weight: 600;")
        preview_result.addWidget(self.preview_savings_label)
        preview_result.addStretch()
        
        preview_layout.addLayout(preview_result)
        center_layout.addWidget(preview_card)
        
        content.addWidget(center_panel, 2)
        
        # 右侧面板 - 操作和日志
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 操作按钮卡片
        action_card = QGroupBox("🚀 操作")
        action_layout = QVBoxLayout(action_card)
        action_layout.setSpacing(10)
        
        # 选项行 - 水平排列
        options_row = QHBoxLayout()
        self.subfolder_cb = QCheckBox("包含子文件夹")
        self.subfolder_cb.setChecked(True)
        options_row.addWidget(self.subfolder_cb)
        
        self.incremental_cb = QCheckBox("跳过已处理文件")
        self.incremental_cb.setChecked(True)
        options_row.addWidget(self.incremental_cb)
        options_row.addStretch()
        action_layout.addLayout(options_row)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        action_layout.addWidget(self.progress_bar)
        
        self.stats_label = QLabel("准备就绪")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #6b6b7b; padding: 4px;")
        action_layout.addWidget(self.stats_label)
        
        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_compression)
        btn_row.addWidget(self.cancel_btn)
        
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setDefault(True)
        self.start_btn.setMinimumWidth(100)
        self.start_btn.clicked.connect(self._start_compression)
        btn_row.addWidget(self.start_btn, 1)
        
        action_layout.addLayout(btn_row)
        
        self.export_btn = QPushButton("导出统计")
        self.export_btn.setObjectName("secondaryBtn")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_stats)
        action_layout.addWidget(self.export_btn)
        
        right_layout.addWidget(action_card)
        
        content.addWidget(right_panel, 1)
        
        main_layout.addLayout(content, 1)
        
        # ========== 底部日志区 ==========
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # 日志标签页
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("等待开始...")
        self.tab_widget.addTab(self.log_text, "📝 处理日志")
        
        # 详细统计标签页
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels([
            "序号", "文件名", "状态", "原始大小", "压缩后", "节省", "尺寸变化"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stats_table.setAlternatingRowColors(True)
        self.tab_widget.addTab(self.stats_table, "📊 详细统计")
        
        main_layout.addWidget(self.tab_widget, 1)
    
    def _connect_signals(self):
        """连接信号与槽"""
        self.start_btn.clicked.connect(self._start_compression)
        self.cancel_btn.clicked.connect(self._cancel_compression)
        self.quality_slider.valueChanged.connect(self.quality_spin.setValue)
        self.quality_spin.valueChanged.connect(self.quality_slider.setValue)
    
    def _on_resize_toggled(self, state):
        """尺寸调整开关切换"""
        enabled = state == Qt.Checked
        self.max_width_spin.setEnabled(enabled)
        self.max_height_spin.setEnabled(enabled)
        self.keep_ratio_cb.setEnabled(enabled)
    
    def _on_smart_toggled(self, state):
        """智能压缩开关切换"""
        enabled = state == Qt.Checked
        self.target_size_spin.setEnabled(enabled)
        self.quality_slider.setEnabled(not enabled)
        self.quality_spin.setEnabled(not enabled)
    
    def _on_rename_toggled(self, state):
        """重命名开关切换"""
        enabled = state == Qt.Checked
        self.rename_combo.setEnabled(enabled)
        self._on_rename_pattern_changed()
    
    def _on_rename_pattern_changed(self):
        """重命名模式改变"""
        if not hasattr(self, 'rename_cb') or not self.rename_cb.isChecked():
            return
    
    def _load_history(self):
        """加载历史记录"""
        try:
            history = config_manager.load_history()
            self.history_combo.clear()
            self.history_combo.addItem("")
            for item in history:
                if isinstance(item, dict) and 'input_path' in item:
                    try:
                        display = f"{Path(item['input_path']).name}"
                        self.history_combo.addItem(display, item)
                    except Exception:
                        pass
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def _load_presets(self):
        """加载预设列表"""
        try:
            self.preset_combo.clear()
            self.preset_combo.addItem("-- 自定义 --", None)
            
            presets = config_manager.load_presets()
            for preset in presets:
                name = preset.get("name", "未命名")
                self.preset_combo.addItem(name, preset)
        except Exception as e:
            print(f"加载预设失败: {e}")
    
    def _on_history_selected(self, text):
        """选择历史记录"""
        if not text:
            return
        try:
            data = self.history_combo.currentData()
            if data and isinstance(data, dict):
                input_path = data.get("input_path", "")
                output_path = data.get("output_path", "")
                if input_path:
                    self.input_edit.setText(input_path)
                if output_path:
                    self.output_edit.setText(output_path)
                self.log_text.append(f"[历史] 已加载: {Path(input_path).name}")
        except Exception as e:
            print(f"选择历史记录失败: {e}")
    
    def _on_preset_selected(self, index):
        """选择预设"""
        if index <= 0:
            return
        
        preset = self.preset_combo.currentData()
        if not preset:
            return
        
        settings = preset.get("settings", {})
        
        # 应用预设设置
        self.quality_spin.setValue(settings.get("quality", DEFAULT_QUALITY))
        self.quality_slider.setValue(settings.get("quality", DEFAULT_QUALITY))
        
        format_map = {"original": 0, "jpg": 1, "png": 2, "webp": 3}
        self.format_combo.setCurrentIndex(format_map.get(settings.get("output_format"), 0))
        
        self.resize_cb.setChecked(settings.get("max_width", 0) > 0 or settings.get("max_height", 0) > 0)
        self.max_width_spin.setValue(settings.get("max_width", 0))
        self.max_height_spin.setValue(settings.get("max_height", 0))
        self.keep_ratio_cb.setChecked(settings.get("keep_ratio", True))
        
        self.smart_cb.setChecked(settings.get("smart_mode", False))
        self.target_size_spin.setValue(settings.get("target_size_kb", 200))
        
        self.min_size_spin.setValue(settings.get("min_size_mb", DEFAULT_MIN_SIZE_MB))
        
        # 显示描述
        desc = preset.get("description", "")
        self.preset_desc_label.setText(f"({desc})")
        
        self.log_text.append(f"[预设] 已加载: {preset.get('name')}")
    
    def _save_preset(self):
        """保存当前设置为预设"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        
        name, ok = QInputDialog.getText(self, "保存预设", "预设名称:", QLineEdit.Normal, "")
        if not ok or not name:
            return
        
        # 检查是否已存在
        presets = config_manager.load_presets()
        default_names = {"网页用", "手机分享", "高质量存档", "缩略图"}
        
        if name in default_names:
            QMessageBox.warning(self, "保存失败", "不能使用内置预设名称")
            return
        
        desc, ok = QInputDialog.getText(self, "保存预设", "描述:", QLineEdit.Normal, "")
        
        settings = {
            "quality": self.quality_spin.value(),
            "output_format": self._get_output_format(),
            "max_width": self.max_width_spin.value() if self.resize_cb.isChecked() else 0,
            "max_height": self.max_height_spin.value() if self.resize_cb.isChecked() else 0,
            "keep_ratio": self.keep_ratio_cb.isChecked(),
            "smart_mode": self.smart_cb.isChecked(),
            "target_size_kb": self.target_size_spin.value(),
            "min_size_mb": self.min_size_spin.value(),
        }
        
        if config_manager.save_custom_preset(name, desc, settings):
            self._load_presets()
            # 选中新保存的预设
            for i in range(self.preset_combo.count()):
                if self.preset_combo.itemText(i) == name:
                    self.preset_combo.setCurrentIndex(i)
                    break
            QMessageBox.information(self, "保存成功", f"预设 '{name}' 已保存")
        else:
            QMessageBox.warning(self, "保存失败", "保存预设时出错")
    
    def _select_input(self):
        """选择输入文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_edit.setText(folder)
            self.log_text.append(f"[输入] {folder}")
    
    def _select_output(self):
        """选择输出文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_edit.setText(folder)
            self.log_text.append(f"[输出] {folder}")
    
    def _get_output_format(self):
        """获取输出格式"""
        formats = ["original", "jpg", "png", "webp"]
        return formats[self.format_combo.currentIndex()]
    
    def _start_compression(self):
        """开始压缩任务"""
        if self._is_running:
            QMessageBox.warning(self, "提示", "压缩任务正在进行中...")
            return
        
        input_dir = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        
        if not input_dir:
            QMessageBox.warning(self, "输入错误", "请选择输入文件夹。")
            return
        
        # 保存历史记录
        settings = {
            "quality": self.quality_spin.value(),
            "format": self._get_output_format(),
            "resize": self.resize_cb.isChecked(),
        }
        config_manager.add_history_item(input_dir, output_dir, settings)
        self._load_history()
        
        is_overwrite_mode = False
        if not output_dir:
            reply = QMessageBox.question(
                self, "确认覆盖",
                "未选择输出文件夹，是否直接覆盖原文件？\n\n"
                "⚠️ 警告：此操作将直接修改原始文件，无法撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return
            output_dir = input_dir
            is_overwrite_mode = True
            self.log_text.append("[模式] 覆盖原文件")
        elif input_dir == output_dir:
            QMessageBox.warning(self, "输入错误", "输入和输出文件夹不能相同！")
            return
        
        # 清空统计表格
        self.stats_table.setRowCount(0)
        self.current_detailed_stats = []
        
        self._is_running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.stats_label.setText("正在初始化...")
        self.stats_label.setStyleSheet("color: #a29bfe; padding: 8px;")
        self.tab_widget.setCurrentIndex(0)
        
        # 创建工作线程
        self.worker = CompressWorker()
        self.worker.signals.progress.connect(self._update_progress)
        self.worker.signals.file_completed.connect(self._on_file_completed)
        self.worker.signals.result.connect(self._show_result)
        self.worker.signals.finished.connect(self._on_finished)
        
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # 获取参数
        max_width = self.max_width_spin.value() if self.resize_cb.isChecked() else 0
        max_height = self.max_height_spin.value() if self.resize_cb.isChecked() else 0
        keep_ratio = self.keep_ratio_cb.isChecked()
        output_format = self._get_output_format()
        smart_mode = self.smart_cb.isChecked()
        target_size_kb = self.target_size_spin.value() if smart_mode else 0
        keep_exif = self.keep_exif_cb.isChecked()
        auto_rotate = self.auto_rotate_cb.isChecked()
        
        self.thread.started.connect(
            lambda: self.worker.run(
                input_dir, output_dir,
                self.quality_spin.value(),
                self.subfolder_cb.isChecked(),
                self.min_size_spin.value(),
                is_overwrite_mode,
                max_width, max_height, keep_ratio,
                output_format,
                smart_mode, target_size_kb,
                None,  # rename_pattern
                keep_exif, auto_rotate,
            )
        )
        
        self.thread.start()
    
    def _cancel_compression(self):
        """取消压缩任务"""
        if self.worker and self._is_running:
            self.worker.cancel()
            self.stats_label.setText("正在取消...")
            self.stats_label.setStyleSheet("color: #ff6b6b; padding: 8px;")
            self.cancel_btn.setEnabled(False)
    
    def _update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.log_text.append(message)
        self.stats_label.setText(f"处理中... {value}%")
    
    def _on_file_completed(self, stat_record):
        """单个文件完成"""
        self.current_detailed_stats.append(stat_record)
        
        # 添加到表格
        row = self.stats_table.rowCount()
        self.stats_table.insertRow(row)
        
        self.stats_table.setItem(row, 0, QTableWidgetItem(str(stat_record["index"])))
        self.stats_table.setItem(row, 1, QTableWidgetItem(stat_record["filename"]))
        
        status_item = QTableWidgetItem(stat_record["status"])
        if stat_record["status"] == "processed":
            status_item.setForeground(QColor("#00d9a5"))
        elif stat_record["status"] == "failed":
            status_item.setForeground(QColor("#ff6b6b"))
        elif stat_record["status"] == "skipped":
            status_item.setForeground(QColor("#ffd166"))
        self.stats_table.setItem(row, 2, status_item)
        
        self.stats_table.setItem(row, 3, QTableWidgetItem(format_bytes(stat_record["original_size"])))
        self.stats_table.setItem(row, 4, QTableWidgetItem(format_bytes(stat_record["compressed_size"])))
        
        savings = stat_record["original_size"] - stat_record["compressed_size"]
        savings_pct = stat_record.get("savings_percent", 0)
        self.stats_table.setItem(row, 5, QTableWidgetItem(f"{format_bytes(savings)} ({savings_pct:.1f}%)"))
        
        dim_before = stat_record.get("dimensions_before", "")
        dim_after = stat_record.get("dimensions_after", "")
        dim_text = f"{dim_before} → {dim_after}" if dim_before else "-"
        self.stats_table.setItem(row, 6, QTableWidgetItem(dim_text))
    
    def _show_result(self, result):
        """显示结果"""
        if "canceled" in result:
            self.stats_label.setText("⚠️ 任务已被用户取消")
            self.stats_label.setStyleSheet("color: #ff6b6b; padding: 8px;")
            return
        
        if "error" in result:
            self.stats_label.setText(f"❌ 错误: {result['error']}")
            self.stats_label.setStyleSheet("color: #ff6b6b; padding: 8px;")
            return
        
        p, s, t, f, c = result["processed"], result["skipped"], result["too_small"], result["failed"], result["cached"]
        orig = format_bytes(result["total_orig"])
        comp = format_bytes(result["total_comp"])
        saved = format_bytes(result["saved"])
        threads = result.get("thread_count", 0)
        
        msg = f"✅ 完成！处理:{p} 跳过:{s} 太小:{t} 失败:{f} 缓存:{c} | 原始:{orig} → 压缩后:{comp} | 节省:{saved}"
        self.stats_label.setText(msg)
        self.stats_label.setStyleSheet("color: #00d9a5; padding: 8px;")
        self.export_btn.setEnabled(True)
        self.tab_widget.setCurrentIndex(1)
    
    def _export_stats(self):
        """导出统计到 CSV"""
        if not self.current_detailed_stats:
            QMessageBox.information(self, "提示", "没有可导出的统计数据")
            return
        
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出统计", f"compress_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "序号", "文件名", "状态", "原始大小(B)", "压缩后大小(B)",
                    "节省(B)", "节省(%)", "原尺寸", "新尺寸"
                ])
                
                for stat in self.current_detailed_stats:
                    writer.writerow([
                        stat.get("index", 0),
                        stat.get("filename", ""),
                        stat.get("status", ""),
                        stat.get("original_size", 0),
                        stat.get("compressed_size", 0),
                        stat.get("original_size", 0) - stat.get("compressed_size", 0),
                        f"{stat.get('savings_percent', 0):.2f}",
                        stat.get("dimensions_before", ""),
                        stat.get("dimensions_after", ""),
                    ])
            
            QMessageBox.information(self, "导出成功", f"统计已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出失败:\n{str(e)}")
    
    def _on_finished(self):
        """任务完成后的清理工作"""
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
        
        if self.worker:
            self.worker.deleteLater()
        
        self.thread = None
        self.worker = None
        self._is_running = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if "准备就绪" not in self.stats_label.text():
            self.log_text.append("-" * 40)
            self.log_text.append("任务结束")
    
    def _preview_compression(self):
        """预览第一张图片的压缩效果"""
        input_dir = self.input_edit.text().strip()
        
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择输入文件夹")
            return
        
        input_path = Path(input_dir)
        if not input_path.exists():
            QMessageBox.warning(self, "错误", "输入文件夹不存在")
            return
        
        # 查找第一张图片
        from src.config import IMAGE_EXTENSIONS
        image_files = [
            p for p in input_path.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        if not image_files:
            QMessageBox.information(self, "提示", "输入文件夹中没有图片")
            return
        
        first_image = image_files[0]
        
        # 执行压缩预览
        try:
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=first_image.suffix, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            # 压缩参数
            quality = self.quality_spin.value()
            max_width = self.max_width_spin.value() if self.resize_cb.isChecked() else 0
            max_height = self.max_height_spin.value() if self.resize_cb.isChecked() else 0
            keep_ratio = self.keep_ratio_cb.isChecked()
            output_format = self._get_output_format()
            keep_exif = self.keep_exif_cb.isChecked()
            auto_rotate = self.auto_rotate_cb.isChecked()
            
            # 执行压缩
            _, status, orig_size, new_size, details = compress_image(
                src_path=first_image,
                input_root=input_path,
                output_root=tmp_path.parent,
                quality=quality,
                min_size_bytes=0,
                overwrite=False,
                max_width=max_width,
                max_height=max_height,
                keep_ratio=keep_ratio,
                output_format=output_format,
                smart_mode=self.smart_cb.isChecked(),
                target_size_kb=self.target_size_spin.value() if self.smart_cb.isChecked() else 0,
                keep_exif=keep_exif,
                auto_rotate=auto_rotate,
            )
            
            # 清理临时文件
            if tmp_path.exists():
                tmp_path.unlink()
            
            # 显示预览结果
            if status == "processed":
                self.preview_original_label.setText(f"原图: {format_bytes(orig_size)}")
                self.preview_compressed_label.setText(f"压缩后: {format_bytes(new_size)}")
                
                savings = orig_size - new_size
                savings_pct = (savings / orig_size * 100) if orig_size > 0 else 0
                self.preview_savings_label.setText(f"节省: {format_bytes(savings)} ({savings_pct:.1f}%)")
                
                # 显示详细信息
                dim_info = ""
                if details.get("resized"):
                    dim_info = f" 尺寸: {details.get('dimensions_before')} → {details.get('dimensions_after')}"
                
                QMessageBox.information(
                    self, "预览结果",
                    f"文件: {first_image.name}\n"
                    f"原大小: {format_bytes(orig_size)}\n"
                    f"压缩后: {format_bytes(new_size)}\n"
                    f"节省: {format_bytes(savings)} ({savings_pct:.1f}%)\n"
                    f"状态: {status}{dim_info}"
                )
            else:
                QMessageBox.information(self, "预览结果", f"无法预览: {status}")
                
        except Exception as e:
            QMessageBox.warning(self, "预览失败", f"预览时出错: {str(e)}")
    
    def _show_exif(self):
        """显示第一张图片的EXIF信息"""
        input_dir = self.input_edit.text().strip()
        
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择输入文件夹")
            return
        
        input_path = Path(input_dir)
        if not input_path.exists():
            QMessageBox.warning(self, "错误", "输入文件夹不存在")
            return
        
        # 查找第一张图片
        from src.config import IMAGE_EXTENSIONS
        image_files = [
            p for p in input_path.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        if not image_files:
            QMessageBox.information(self, "提示", "输入文件夹中没有图片")
            return
        
        first_image = image_files[0]
        
        # 显示EXIF对话框
        dialog = ExifDialog(first_image, self)
        dialog.exec_()
    
    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self._is_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "压缩任务正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._cancel_compression()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
