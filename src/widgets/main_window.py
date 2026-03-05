"""
主窗口模块 - VS Code 风格设计
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
    QSizePolicy, QSpacerItem, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

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
    """图片压缩工具主窗口 - VS Code 风格"""
    
    # VS Code Dark+ 主题颜色
    BG_PRIMARY = "#1e1e1e"        # 主背景
    BG_SECONDARY = "#252526"      # 侧边栏背景
    BG_TERTIARY = "#2d2d30"       # 活动栏/面板背景
    BORDER = "#3c3c3c"            # 边框
    BORDER_ACTIVE = "#007acc"     # 活动边框（蓝色）
    TEXT_PRIMARY = "#cccccc"      # 主文字
    TEXT_SECONDARY = "#858585"    # 次要文字
    TEXT_ACTIVE = "#ffffff"       # 活动文字
    ACCENT = "#007acc"            # 强调色（蓝色）
    ACCENT_HOVER = "#1177bb"      # 悬停色
    BUTTON_BG = "#0e639c"         # 按钮背景
    BUTTON_HOVER = "#1177bb"      # 按钮悬停
    INPUT_BG = "#3c3c3c"          # 输入框背景
    
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
        
        self._setup_vscode_style()
        self._setup_ui()
        self._connect_signals()
        self._load_history()
        self._load_presets()
    
    def _setup_vscode_style(self):
        """设置 VS Code 风格样式"""
        self.setStyleSheet(f"""
            /* 全局样式 */
            QWidget {{
                background-color: {self.BG_PRIMARY};
                color: {self.TEXT_PRIMARY};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 13px;
                border: none;
                outline: none;
            }}
            
            /* 侧边栏样式 */
            QGroupBox {{
                background-color: {self.BG_SECONDARY};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                margin: 0px;
                padding: 12px;
                font-weight: normal;
            }}
            
            QGroupBox::title {{
                color: {self.TEXT_SECONDARY};
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            /* 输入框 */
            QLineEdit {{
                background-color: {self.INPUT_BG};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                padding: 6px 10px;
                color: {self.TEXT_PRIMARY};
                font-size: 13px;
                selection-background-color: {self.ACCENT};
            }}
            
            QLineEdit:focus {{
                border-color: {self.ACCENT};
            }}
            
            QLineEdit::placeholder {{
                color: {self.TEXT_SECONDARY};
            }}
            
            /* 主按钮 - 蓝色 */
            QPushButton {{
                background-color: {self.BUTTON_BG};
                color: white;
                border: none;
                border-radius: 0px;
                padding: 6px 14px;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {self.BUTTON_HOVER};
            }}
            
            QPushButton:pressed {{
                background-color: {self.ACCENT};
            }}
            
            QPushButton:disabled {{
                background-color: {self.BG_TERTIARY};
                color: {self.TEXT_SECONDARY};
            }}
            
            /* 次要按钮 */
            QPushButton#secondaryBtn {{
                background-color: {self.BG_TERTIARY};
                border: 1px solid {self.BORDER};
                color: {self.TEXT_PRIMARY};
            }}
            
            QPushButton#secondaryBtn:hover {{
                background-color: #3c3c3c;
                border-color: {self.TEXT_SECONDARY};
            }}
            
            /* 复选框 - VS Code 风格 */
            QCheckBox {{
                color: {self.TEXT_PRIMARY};
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 0px;
                border: 1px solid {self.BORDER};
                background-color: {self.INPUT_BG};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {self.TEXT_SECONDARY};
            }}
            
            /* 下拉框 */
            QComboBox {{
                background-color: {self.INPUT_BG};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                padding: 6px 10px;
                color: {self.TEXT_PRIMARY};
                min-width: 100px;
            }}
            
            QComboBox:hover {{
                border-color: {self.TEXT_SECONDARY};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.BG_SECONDARY};
                border: 1px solid {self.BORDER};
                selection-background-color: {self.ACCENT};
                outline: none;
            }}
            
            /* 滑块 - VS Code 风格 */
            QSlider::groove:horizontal {{
                height: 4px;
                background-color: {self.INPUT_BG};
            }}
            
            QSlider::sub-page:horizontal {{
                background-color: {self.ACCENT};
            }}
            
            QSlider::add-page:horizontal {{
                background-color: {self.BORDER};
            }}
            
            QSlider::handle:horizontal {{
                width: 12px;
                height: 12px;
                margin: -4px 0;
                background-color: white;
                border: 1px solid {self.BORDER};
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
            
            /* 数值框 */
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.INPUT_BG};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                padding: 4px 8px;
                padding-right: 18px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                height: 50%;
                border-left: 1px solid {self.BORDER};
                background-color: transparent;
            }}
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                height: 50%;
                border-left: 1px solid {self.BORDER};
                background-color: transparent;
            }}
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {self.BG_TERTIARY};
            }}
            
            QSpinBox::up-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-bottom: 4px solid {self.TEXT_SECONDARY};
            }}
            
            QSpinBox::down-arrow {{
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid {self.TEXT_SECONDARY};
            }}
            
            /* 进度条 */
            QProgressBar {{
                background-color: {self.INPUT_BG};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                text-align: center;
                height: 22px;
                color: {self.TEXT_PRIMARY};
                font-size: 11px;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.ACCENT};
            }}
            
            /* 标签页 - VS Code 风格 */
            QTabWidget::pane {{
                border: none;
                background-color: {self.BG_PRIMARY};
            }}
            
            QTabBar::tab {{
                background-color: {self.BG_SECONDARY};
                border: 1px solid {self.BORDER};
                border-bottom: none;
                color: {self.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 0px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.BG_PRIMARY};
                border-top: 2px solid {self.ACCENT};
                color: {self.TEXT_ACTIVE};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {self.BG_TERTIARY};
                color: {self.TEXT_PRIMARY};
            }}
            
            /* 文本框 */
            QTextEdit {{
                background-color: {self.BG_PRIMARY};
                border: 1px solid {self.BORDER};
                border-radius: 0px;
                padding: 10px;
                color: {self.TEXT_PRIMARY};
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 12px;
            }}
            
            /* 表格 */
            QTableWidget {{
                background-color: {self.BG_PRIMARY};
                border: 1px solid {self.BORDER};
                gridline-color: {self.BORDER};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                color: {self.TEXT_PRIMARY};
                border-bottom: 1px solid {self.BORDER};
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.ACCENT};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {self.BG_SECONDARY};
                color: {self.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                border-right: 1px solid {self.BORDER};
                font-size: 12px;
                font-weight: normal;
            }}
            
            /* 标签 */
            QLabel {{
                color: {self.TEXT_PRIMARY};
                background: transparent;
            }}
            
            /* 分隔线 */
            QFrame[frameShape="4"] {{
                color: {self.BORDER};
            }}
            
            /* 菜单栏 */
            QMenuBar {{
                background-color: {self.BG_SECONDARY};
                border-bottom: 1px solid {self.BORDER};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.BG_TERTIARY};
                color: {self.TEXT_ACTIVE};
            }}
            
            QMenu {{
                background-color: {self.BG_SECONDARY};
                border: 1px solid {self.BORDER};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 8px 16px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QMenu::item:selected {{
                background-color: {self.ACCENT};
                color: white;
            }}
            
            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {self.BG_SECONDARY};
                width: 14px;
                border-left: 1px solid {self.BORDER};
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.INPUT_BG};
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.TEXT_SECONDARY};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def _setup_ui(self):
        """设置用户界面 - VS Code 风格"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== 左侧边栏 (1/3) ==========
        left_sidebar = QWidget()
        left_sidebar.setFixedWidth(400)
        left_sidebar.setStyleSheet(f"background-color: {self.BG_SECONDARY}; border-right: 1px solid {self.BORDER};")
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # 标题栏
        header = QWidget()
        header.setStyleSheet(f"background-color: {self.BG_SECONDARY}; border-bottom: 1px solid {self.BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title_label = QLabel("EXPLORER")
        title_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(title_label)
        left_layout.addWidget(header)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(16)
        
        # ===== 输入输出组 =====
        io_group = self._create_vscode_group("输入输出")
        io_layout = QVBoxLayout(io_group)
        io_layout.setSpacing(8)
        
        # 输入路径
        input_label = QLabel("输入文件夹")
        input_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        io_layout.addWidget(input_label)
        
        input_row = QHBoxLayout()
        self.input_edit = DragDropLineEdit()
        self.input_edit.setPlaceholderText("选择或拖拽文件夹...")
        input_row.addWidget(self.input_edit)
        
        browse_input = QPushButton("...")
        browse_input.setFixedWidth(28)
        browse_input.setToolTip("浏览")
        browse_input.clicked.connect(self._select_input)
        browse_input.setObjectName("secondaryBtn")
        input_row.addWidget(browse_input)
        io_layout.addLayout(input_row)
        
        # 输出路径
        output_label = QLabel("输出文件夹")
        output_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        io_layout.addWidget(output_label)
        
        output_row = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("留空则覆盖原文件")
        output_row.addWidget(self.output_edit)
        
        browse_output = QPushButton("...")
        browse_output.setFixedWidth(28)
        browse_output.setToolTip("浏览")
        browse_output.clicked.connect(self._select_output)
        browse_output.setObjectName("secondaryBtn")
        output_row.addWidget(browse_output)
        io_layout.addLayout(output_row)
        
        # 历史记录
        history_label = QLabel("历史记录")
        history_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        io_layout.addWidget(history_label)
        
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("选择历史记录...")
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        io_layout.addWidget(self.history_combo)
        
        scroll_layout.addWidget(io_group)
        
        # ===== 预设配置组 =====
        preset_group = self._create_vscode_group("预设配置")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(8)
        
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setPlaceholderText("选择预设...")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo)
        
        save_preset_btn = QPushButton("保存")
        save_preset_btn.setFixedWidth(50)
        save_preset_btn.setObjectName("secondaryBtn")
        save_preset_btn.clicked.connect(self._save_preset)
        preset_row.addWidget(save_preset_btn)
        preset_layout.addLayout(preset_row)
        
        self.preset_desc_label = QLabel("")
        self.preset_desc_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        preset_layout.addWidget(self.preset_desc_label)
        
        scroll_layout.addWidget(preset_group)
        
        # ===== 输出设置组（左侧）=====
        settings_group = self._create_vscode_group("输出设置")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        # 输出格式
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["保持原格式", "JPG", "PNG", "WebP"])
        self.format_combo.setFixedWidth(110)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        settings_layout.addLayout(format_row)
        
        # 最小大小
        minsize_row = QHBoxLayout()
        minsize_row.addWidget(QLabel("最小大小:"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedWidth(90)
        minsize_row.addWidget(self.min_size_spin)
        minsize_row.addStretch()
        settings_layout.addLayout(minsize_row)
        
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
        self.quality_spin.setFixedWidth(50)
        quality_row.addWidget(self.quality_spin)
        
        settings_layout.addLayout(quality_row)
        
        # 尺寸调整
        resize_row = QHBoxLayout()
        self.resize_cb = QCheckBox("调整尺寸")
        self.resize_cb.stateChanged.connect(self._on_resize_toggled)
        resize_row.addWidget(self.resize_cb)
        
        resize_row.addWidget(QLabel("宽:"))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(0, 10000)
        self.max_width_spin.setValue(0)
        self.max_width_spin.setSuffix(" px")
        self.max_width_spin.setFixedWidth(70)
        self.max_width_spin.setEnabled(False)
        resize_row.addWidget(self.max_width_spin)
        
        resize_row.addWidget(QLabel("高:"))
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 10000)
        self.max_height_spin.setValue(0)
        self.max_height_spin.setSuffix(" px")
        self.max_height_spin.setFixedWidth(70)
        self.max_height_spin.setEnabled(False)
        resize_row.addWidget(self.max_height_spin)
        
        self.keep_ratio_cb = QCheckBox("保持比例")
        self.keep_ratio_cb.setChecked(True)
        self.keep_ratio_cb.setEnabled(False)
        resize_row.addWidget(self.keep_ratio_cb)
        resize_row.addStretch()
        
        settings_layout.addLayout(resize_row)
        
        # 智能压缩
        smart_row = QHBoxLayout()
        self.smart_cb = QCheckBox("智能压缩")
        self.smart_cb.stateChanged.connect(self._on_smart_toggled)
        smart_row.addWidget(self.smart_cb)
        
        smart_row.addWidget(QLabel("目标:"))
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 10000)
        self.target_size_spin.setValue(200)
        self.target_size_spin.setSuffix(" KB")
        self.target_size_spin.setFixedWidth(70)
        self.target_size_spin.setEnabled(False)
        smart_row.addWidget(self.target_size_spin)
        smart_row.addStretch()
        
        settings_layout.addLayout(smart_row)
        
        # EXIF 选项
        exif_row = QHBoxLayout()
        self.keep_exif_cb = QCheckBox("保留 EXIF")
        self.keep_exif_cb.setChecked(True)
        exif_row.addWidget(self.keep_exif_cb)
        
        self.auto_rotate_cb = QCheckBox("自动旋转")
        self.auto_rotate_cb.setChecked(True)
        exif_row.addWidget(self.auto_rotate_cb)
        exif_row.addStretch()
        
        settings_layout.addLayout(exif_row)
        
        scroll_layout.addWidget(settings_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)
        
        main_layout.addWidget(left_sidebar)
        
        # ========== 右侧主区域 (2/3) ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 16, 20, 16)
        right_layout.setSpacing(16)
        
        # 顶部标题栏
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel(f"{APP_NAME}  v{__version__}")
        title.setStyleSheet(f"color: {self.TEXT_ACTIVE}; font-size: 20px; font-weight: 600;")
        top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        about_btn = QPushButton("关于")
        about_btn.setFixedWidth(60)
        about_btn.setObjectName("secondaryBtn")
        about_btn.clicked.connect(self._show_about)
        top_layout.addWidget(about_btn)
        
        right_layout.addWidget(top_bar)
        
        # 压缩预览组
        preview_group = self._create_vscode_group("压缩预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(12)
        
        preview_btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("预览第一张图片")
        self.preview_btn.setFixedWidth(140)
        self.preview_btn.clicked.connect(self._preview_compression)
        preview_btn_row.addWidget(self.preview_btn)
        
        exif_btn = QPushButton("查看 EXIF")
        exif_btn.setFixedWidth(90)
        exif_btn.setObjectName("secondaryBtn")
        exif_btn.clicked.connect(self._show_exif)
        preview_btn_row.addWidget(exif_btn)
        preview_btn_row.addStretch()
        preview_layout.addLayout(preview_btn_row)
        
        preview_info = QHBoxLayout()
        self.preview_original_label = QLabel("原图: -")
        self.preview_original_label.setStyleSheet(f"color: {self.TEXT_SECONDARY};")
        preview_info.addWidget(self.preview_original_label)
        
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {self.ACCENT}; padding: 0 8px;")
        preview_info.addWidget(arrow)
        
        self.preview_compressed_label = QLabel("压缩后: -")
        self.preview_compressed_label.setStyleSheet(f"color: {self.TEXT_ACTIVE};")
        preview_info.addWidget(self.preview_compressed_label)
        
        preview_info.addSpacing(20)
        
        self.preview_savings_label = QLabel("节省: -")
        self.preview_savings_label.setStyleSheet("color: #4ec9b0;")
        preview_info.addWidget(self.preview_savings_label)
        preview_info.addStretch()
        
        preview_layout.addLayout(preview_info)
        right_layout.addWidget(preview_group)
        
        # 操作组
        action_group = self._create_vscode_group("操作")
        action_layout = QVBoxLayout(action_group)
        action_layout.setSpacing(12)
        
        # 选项
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
        self.stats_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 12px;")
        action_layout.addWidget(self.stats_label)
        
        # 按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_compression)
        btn_row.addWidget(self.cancel_btn)
        
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setDefault(True)
        self.start_btn.setMinimumWidth(120)
        self.start_btn.clicked.connect(self._start_compression)
        btn_row.addWidget(self.start_btn, 1)
        
        action_layout.addLayout(btn_row)
        
        self.export_btn = QPushButton("导出统计")
        self.export_btn.setObjectName("secondaryBtn")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_stats)
        action_layout.addWidget(self.export_btn)
        
        right_layout.addWidget(action_group)
        right_layout.addStretch()
        
        # 底部面板（日志区）
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(220)
        bottom_panel.setStyleSheet(f"background-color: {self.BG_PRIMARY}; border-top: 1px solid {self.BORDER};")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # 输出标签页
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("等待开始...")
        self.tab_widget.addTab(self.log_text, "输出")
        
        # 统计标签页
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(7)
        self.stats_table.setHorizontalHeaderLabels([
            "序号", "文件名", "状态", "原始大小", "压缩后", "节省", "尺寸变化"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stats_table.setAlternatingRowColors(False)
        self.tab_widget.addTab(self.stats_table, "统计")
        
        bottom_layout.addWidget(self.tab_widget)
        
        # 组装右侧面板
        right_container = QWidget()
        right_container_layout = QVBoxLayout(right_container)
        right_container_layout.setContentsMargins(0, 0, 0, 0)
        right_container_layout.setSpacing(16)
        
        # 可滚动的主内容区
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        right_content = QWidget()
        right_content_layout = QVBoxLayout(right_content)
        right_content_layout.setContentsMargins(0, 0, 0, 0)
        right_content_layout.setSpacing(16)
        right_content_layout.addWidget(top_bar)
        right_content_layout.addWidget(preview_group)
        right_content_layout.addWidget(action_group)
        right_content_layout.addStretch()
        
        right_scroll.setWidget(right_content)
        right_container_layout.addWidget(right_scroll, 1)
        right_container_layout.addWidget(bottom_panel)
        
        main_layout.addWidget(right_container, 2)
    
    def _create_vscode_group(self, title):
        """创建 VS Code 风格的分组"""
        group = QGroupBox(title)
        return group
    
    def _connect_signals(self):
        """连接信号与槽"""
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
        
        desc = preset.get("description", "")
        self.preset_desc_label.setText(f"({desc})")
        
        self.log_text.append(f"[预设] 已加载: {preset.get('name')}")
    
    def _save_preset(self):
        """保存当前设置为预设"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        
        name, ok = QInputDialog.getText(self, "保存预设", "预设名称:", QLineEdit.Normal, "")
        if not ok or not name:
            return
        
        settings = {
            "quality": self.quality_spin.value(),
            "output_format": ["original", "jpg", "png", "webp"][self.format_combo.currentIndex()],
            "max_width": self.max_width_spin.value() if self.resize_cb.isChecked() else 0,
            "max_height": self.max_height_spin.value() if self.resize_cb.isChecked() else 0,
            "keep_ratio": self.keep_ratio_cb.isChecked(),
            "smart_mode": self.smart_cb.isChecked(),
            "target_size_kb": self.target_size_spin.value(),
            "min_size_mb": self.min_size_spin.value()
        }
        
        try:
            config_manager.save_custom_preset(name, settings, f"质量{settings['quality']}%")
            self._load_presets()
            self.preset_combo.setCurrentText(name)
            self.log_text.append(f"[预设] 已保存: {name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存预设失败: {e}")
    
    def _select_input(self):
        """选择输入文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_edit.setText(folder)
    
    def _select_output(self):
        """选择输出文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_edit.setText(folder)
    
    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def _show_exif(self):
        """显示 EXIF 对话框"""
        input_path = self.input_edit.text()
        if not input_path or not Path(input_path).exists():
            QMessageBox.warning(self, "警告", "请先选择有效的输入文件夹")
            return
        
        files = list(Path(input_path).glob("*"))
        image_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']]
        
        if not image_files:
            QMessageBox.warning(self, "警告", "未找到图片文件")
            return
        
        exif_data, image_info = get_exif_info(image_files[0])
        dialog = ExifDialog(exif_data, image_info, self)
        dialog.exec_()
    
    def _preview_compression(self):
        """预览压缩效果"""
        input_path = self.input_edit.text()
        if not input_path or not Path(input_path).exists():
            QMessageBox.warning(self, "警告", "请先选择有效的输入文件夹")
            return
        
        files = list(Path(input_path).glob("*"))
        image_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']]
        
        if not image_files:
            QMessageBox.warning(self, "警告", "未找到图片文件")
            return
        
        self.log_text.append("[预览] 正在处理第一张图片...")
        
        try:
            result = compress_image(
                src_path=image_files[0],
                input_root=Path(input_path),
                output_root=Path(input_path),
                quality=self.quality_spin.value(),
                min_size_bytes=self.min_size_spin.value() * 1024 * 1024,
                overwrite=False,
                max_width=self.max_width_spin.value() if self.resize_cb.isChecked() else 0,
                max_height=self.max_height_spin.value() if self.resize_cb.isChecked() else 0,
                keep_ratio=self.keep_ratio_cb.isChecked(),
                output_format=["original", "jpg", "png", "webp"][self.format_combo.currentIndex()],
                smart_mode=self.smart_cb.isChecked(),
                target_size_kb=self.target_size_spin.value(),
                keep_exif=self.keep_exif_cb.isChecked(),
                auto_rotate=self.auto_rotate_cb.isChecked()
            )
            
            path, status, orig_size, new_size, details = result
            
            self.preview_original_label.setText(f"原图: {format_bytes(orig_size)}")
            self.preview_compressed_label.setText(f"压缩后: {format_bytes(new_size)}")
            
            savings_percent = ((orig_size - new_size) / orig_size * 100) if orig_size > 0 else 0
            self.preview_savings_label.setText(f"节省: {savings_percent:.1f}%")
            
            self.log_text.append(f"[预览] 完成: {path.name} - {status}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {e}")
    
    def _start_compression(self):
        """开始压缩"""
        input_path = self.input_edit.text()
        if not input_path:
            QMessageBox.warning(self, "警告", "请选择输入文件夹")
            return
        
        if not Path(input_path).exists():
            QMessageBox.warning(self, "警告", "输入文件夹不存在")
            return
        
        self._is_running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.stats_label.setText("准备中...")
        self.log_text.clear()
        self.log_text.append("[开始] 图片压缩任务")
        
        self.thread = QThread()
        self.worker = CompressWorker(
            input_path=input_path,
            output_path=self.output_edit.text() or None,
            quality=self.quality_spin.value(),
            min_size_bytes=self.min_size_spin.value() * 1024 * 1024,
            max_width=self.max_width_spin.value() if self.resize_cb.isChecked() else 0,
            max_height=self.max_height_spin.value() if self.resize_cb.isChecked() else 0,
            keep_ratio=self.keep_ratio_cb.isChecked(),
            output_format=["original", "jpg", "png", "webp"][self.format_combo.currentIndex()],
            smart_mode=self.smart_cb.isChecked(),
            target_size_kb=self.target_size_spin.value(),
            include_subfolders=self.subfolder_cb.isChecked(),
            incremental=self.incremental_cb.isChecked()
        )
        
        self.worker.moveToThread(self.thread)
        
        self.worker.progress.connect(self._on_progress)
        self.worker.file_completed.connect(self._on_file_completed)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()
    
    def _cancel_compression(self):
        """取消压缩"""
        if self.worker:
            self.worker.cancel()
            self.log_text.append("[取消] 正在停止...")
    
    def _on_progress(self, current, total):
        """进度更新"""
        percent = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.stats_label.setText(f"处理中... {current}/{total}")
    
    def _on_file_completed(self, filename, status):
        """文件完成"""
        self.log_text.append(f"[处理] {filename} - {status}")
    
    def _on_result(self, results):
        """处理结果"""
        self.current_detailed_stats = results
        self._update_stats_table(results)
    
    def _update_stats_table(self, results):
        """更新统计表格"""
        self.stats_table.setRowCount(len(results))
        
        for i, (path, status, orig_size, new_size, details) in enumerate(results):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(path.name))
            self.stats_table.setItem(i, 2, QTableWidgetItem(status))
            self.stats_table.setItem(i, 3, QTableWidgetItem(format_bytes(orig_size)))
            self.stats_table.setItem(i, 4, QTableWidgetItem(format_bytes(new_size)))
            
            savings = orig_size - new_size
            savings_pct = (savings / orig_size * 100) if orig_size > 0 else 0
            self.stats_table.setItem(i, 5, QTableWidgetItem(f"{format_bytes(savings)} ({savings_pct:.1f}%)"))
            
            dim_change = details.get('dimensions', '-')
            self.stats_table.setItem(i, 6, QTableWidgetItem(dim_change))
    
    def _on_finished(self, success_count, skip_count, error_count, total_saved):
        """任务完成"""
        self._is_running = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.stats_label.setText(f"完成: 成功 {success_count} | 跳过 {skip_count} | 失败 {error_count}")
        
        self.log_text.append(f"[完成] 任务结束")
        self.log_text.append(f"[统计] 成功: {success_count}, 跳过: {skip_count}, 失败: {error_count}")
        self.log_text.append(f"[节省] 共节省: {format_bytes(total_saved)}")
        
        if self.input_edit.text():
            config_manager.save_history(self.input_edit.text(), self.output_edit.text())
            self._load_history()
        
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()
        self.worker = None
        self.thread = None
    
    def _export_stats(self):
        """导出统计"""
        if not self.current_detailed_stats:
            QMessageBox.warning(self, "警告", "没有可导出的统计数据")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "导出统计", f"压缩统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not path:
            return
        
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "文件名", "状态", "原始大小", "压缩后", "节省", "尺寸变化"])
                
                for i, (p, status, orig, new, details) in enumerate(self.current_detailed_stats, 1):
                    savings = orig - new
                    savings_pct = (savings / orig * 100) if orig > 0 else 0
                    writer.writerow([
                        i, p.name, status, format_bytes(orig), format_bytes(new),
                        f"{format_bytes(savings)} ({savings_pct:.1f}%)",
                        details.get('dimensions', '-')
                    ])
            
            self.log_text.append(f"[导出] 统计已保存: {path}")
            QMessageBox.information(self, "成功", "统计已导出")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
