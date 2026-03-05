"""
主窗口模块 - OpenShot 风格设计
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
    QSizePolicy, QSpacerItem, QScrollArea, QToolButton,
    QDockWidget, QListWidget, QListWidgetItem, QMainWindow,
    QStatusBar, QToolBar
)
from PyQt5.QtCore import Qt, QThread, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

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
    """图片压缩工具主窗口 - OpenShot 风格"""
    
    # OpenShot 风格配色
    BG_DARK = "#1a1a1a"           # 主背景（接近黑色）
    BG_PANEL = "#232323"          # 面板背景
    BG_INPUT = "#2d2d2d"          # 输入框背景
    BG_HOVER = "#3a3a3a"          # 悬停背景
    BORDER = "#404040"            # 边框
    BORDER_LIGHT = "#555555"      # 亮边框
    TEXT_PRIMARY = "#e0e0e0"      # 主文字
    TEXT_SECONDARY = "#909090"    # 次要文字
    ACCENT = "#e67e22"            # 强调色（OpenShot 橙色）
    ACCENT_HOVER = "#ff9933"      # 悬停橙色
    BUTTON_PRIMARY = "#2980b9"    # 主按钮蓝色
    BUTTON_HOVER = "#3498db"      # 按钮悬停
    SUCCESS = "#27ae60"           # 成功绿色
    
    def __init__(self):
        super().__init__()
        
        self.logger = setup_logging()
        self._is_running = False
        self.worker = None
        self.thread = None
        self.current_detailed_stats = []
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 800)
        self.resize(1440, 900)
        
        self._setup_openshot_style()
        self._setup_ui()
        self._connect_signals()
        self._load_history()
        self._load_presets()
    
    def _setup_openshot_style(self):
        """设置 OpenShot 风格样式"""
        self.setStyleSheet(f"""
            /* 全局样式 */
            QWidget {{
                background-color: {self.BG_DARK};
                color: {self.TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
                font-size: 13px;
                border: none;
            }}
            
            /* 工具栏 */
            QToolBar {{
                background-color: {self.BG_PANEL};
                border-bottom: 1px solid {self.BORDER};
                padding: 4px;
                spacing: 4px;
            }}
            
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 6px 12px;
                color: {self.TEXT_PRIMARY};
                font-size: 12px;
            }}
            
            QToolButton:hover {{
                background-color: {self.BG_HOVER};
                border-color: {self.BORDER};
            }}
            
            QToolButton:pressed {{
                background-color: {self.BORDER_LIGHT};
            }}
            
            /* 面板样式 */
            QGroupBox {{
                background-color: {self.BG_PANEL};
                border: 1px solid {self.BORDER};
                border-radius: 3px;
                margin: 2px;
                padding: 10px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                color: {self.TEXT_SECONDARY};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-size: 11px;
            }}
            
            /* 输入框 */
            QLineEdit {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 2px;
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
            
            /* 按钮 - OpenShot 风格 */
            QPushButton {{
                background-color: {self.BG_HOVER};
                border: 1px solid {self.BORDER};
                border-radius: 3px;
                padding: 6px 16px;
                color: {self.TEXT_PRIMARY};
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {self.BORDER_LIGHT};
                border-color: {self.BORDER_LIGHT};
            }}
            
            QPushButton:pressed {{
                background-color: {self.BORDER};
            }}
            
            QPushButton:disabled {{
                background-color: {self.BG_PANEL};
                color: {self.TEXT_SECONDARY};
            }}
            
            /* 主按钮 - 橙色 */
            QPushButton#primaryBtn {{
                background-color: {self.ACCENT};
                border-color: {self.ACCENT};
                color: white;
                font-weight: bold;
            }}
            
            QPushButton#primaryBtn:hover {{
                background-color: {self.ACCENT_HOVER};
                border-color: {self.ACCENT_HOVER};
            }}
            
            /* 蓝色按钮 */
            QPushButton#blueBtn {{
                background-color: {self.BUTTON_PRIMARY};
                border-color: {self.BUTTON_PRIMARY};
                color: white;
            }}
            
            QPushButton#blueBtn:hover {{
                background-color: {self.BUTTON_HOVER};
                border-color: {self.BUTTON_HOVER};
            }}
            
            /* 复选框 */
            QCheckBox {{
                color: {self.TEXT_PRIMARY};
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 2px;
                border: 1px solid {self.BORDER};
                background-color: {self.BG_INPUT};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.ACCENT};
                border-color: {self.ACCENT};
            }}
            
            QCheckBox::indicator:hover {{
                border-color: {self.BORDER_LIGHT};
            }}
            
            /* 下拉框 */
            QComboBox {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 2px;
                padding: 6px 10px;
                color: {self.TEXT_PRIMARY};
                min-width: 100px;
            }}
            
            QComboBox:hover {{
                border-color: {self.BORDER_LIGHT};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.BG_PANEL};
                border: 1px solid {self.BORDER};
                selection-background-color: {self.ACCENT};
                outline: none;
            }}
            
            /* 滑块 - OpenShot 风格 */
            QSlider::groove:horizontal {{
                height: 6px;
                background-color: {self.BG_INPUT};
                border-radius: 3px;
            }}
            
            QSlider::sub-page:horizontal {{
                background-color: {self.ACCENT};
                border-radius: 3px;
            }}
            
            QSlider::add-page:horizontal {{
                background-color: {self.BORDER};
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                width: 16px;
                height: 16px;
                margin: -5px 0;
                background-color: {self.TEXT_PRIMARY};
                border: 2px solid {self.BG_PANEL};
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {self.ACCENT_HOVER};
            }}
            
            /* 数值框 */
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 2px;
                padding: 4px 8px;
                padding-right: 16px;
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
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
                background-color: {self.BG_HOVER};
            }}
            
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {self.BG_HOVER};
            }}
            
            /* 进度条 */
            QProgressBar {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 2px;
                text-align: center;
                height: 20px;
                color: {self.TEXT_PRIMARY};
                font-size: 11px;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.ACCENT};
                border-radius: 1px;
            }}
            
            /* 标签页 */
            QTabWidget::pane {{
                border: 1px solid {self.BORDER};
                background-color: {self.BG_PANEL};
            }}
            
            QTabBar::tab {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-bottom: none;
                color: {self.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 2px 2px 0 0;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.BG_PANEL};
                border-top: 2px solid {self.ACCENT};
                color: {self.TEXT_PRIMARY};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {self.BG_HOVER};
                color: {self.TEXT_PRIMARY};
            }}
            
            /* 列表 */
            QListWidget {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                color: {self.TEXT_PRIMARY};
            }}
            
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {self.BORDER};
            }}
            
            QListWidget::item:selected {{
                background-color: {self.ACCENT};
            }}
            
            /* 文本框 */
            QTextEdit {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                border-radius: 2px;
                padding: 8px;
                color: {self.TEXT_PRIMARY};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
            
            /* 表格 */
            QTableWidget {{
                background-color: {self.BG_INPUT};
                border: 1px solid {self.BORDER};
                gridline-color: {self.BORDER};
            }}
            
            QTableWidget::item {{
                padding: 6px;
                color: {self.TEXT_PRIMARY};
                border-bottom: 1px solid {self.BORDER};
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.ACCENT};
                color: white;
            }}
            
            QHeaderView::section {{
                background-color: {self.BG_PANEL};
                color: {self.TEXT_SECONDARY};
                padding: 8px;
                border: none;
                border-right: 1px solid {self.BORDER};
                border-bottom: 1px solid {self.BORDER};
                font-size: 11px;
                font-weight: bold;
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
            
            /* 状态栏 */
            QStatusBar {{
                background-color: {self.BG_PANEL};
                border-top: 1px solid {self.BORDER};
                color: {self.TEXT_SECONDARY};
            }}
            
            /* 菜单栏 */
            QMenuBar {{
                background-color: {self.BG_PANEL};
                border-bottom: 1px solid {self.BORDER};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.ACCENT};
                color: white;
            }}
            
            QMenu {{
                background-color: {self.BG_PANEL};
                border: 1px solid {self.BORDER};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 16px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QMenu::item:selected {{
                background-color: {self.ACCENT};
                color: white;
            }}
            
            /* 滚动条 */
            QScrollBar:vertical {{
                background-color: {self.BG_PANEL};
                width: 12px;
                border-left: 1px solid {self.BORDER};
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.BORDER};
                min-height: 30px;
                border-radius: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.BORDER_LIGHT};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
    
    def _setup_ui(self):
        """设置用户界面 - OpenShot 风格"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== 顶部工具栏 ==========
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"background-color: {self.BG_PANEL}; border-bottom: 1px solid {self.BORDER};")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 6, 12, 6)
        toolbar_layout.setSpacing(10)
        
        # Logo / 标题
        title_label = QLabel(f"🖼️ {APP_NAME}")
        title_label.setStyleSheet(f"color: {self.ACCENT}; font-size: 16px; font-weight: bold;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addSpacing(20)
        
        # 工具栏按钮
        open_btn = QPushButton("📁 打开")
        open_btn.setObjectName("blueBtn")
        open_btn.clicked.connect(self._select_input)
        toolbar_layout.addWidget(open_btn)
        
        save_btn = QPushButton("💾 保存预设")
        save_btn.clicked.connect(self._save_preset)
        toolbar_layout.addWidget(save_btn)
        
        toolbar_layout.addStretch()
        
        # 主操作按钮
        self.start_btn = QPushButton("▶ 开始压缩")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.clicked.connect(self._start_compression)
        toolbar_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("⏹ 取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_compression)
        toolbar_layout.addWidget(self.cancel_btn)
        
        toolbar_layout.addSpacing(10)
        
        about_btn = QPushButton("?")
        about_btn.setFixedWidth(30)
        about_btn.setToolTip("关于")
        about_btn.clicked.connect(self._show_about)
        toolbar_layout.addWidget(about_btn)
        
        main_layout.addWidget(toolbar)
        
        # ========== 中央区域 ==========
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(8, 8, 8, 8)
        center_layout.setSpacing(8)
        
        # ===== 左侧面板（项目文件）=====
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # 输入设置组
        input_group = QGroupBox("📂 输入设置")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(8)
        
        # 输入路径
        input_label = QLabel("输入文件夹:")
        input_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        input_layout.addWidget(input_label)
        
        input_row = QHBoxLayout()
        self.input_edit = DragDropLineEdit()
        self.input_edit.setPlaceholderText("选择文件夹...")
        input_row.addWidget(self.input_edit)
        
        browse_input = QPushButton("...")
        browse_input.setFixedWidth(32)
        browse_input.clicked.connect(self._select_input)
        input_row.addWidget(browse_input)
        input_layout.addLayout(input_row)
        
        # 输出路径
        output_label = QLabel("输出文件夹:")
        output_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        input_layout.addWidget(output_label)
        
        output_row = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("留空覆盖原文件")
        output_row.addWidget(self.output_edit)
        
        browse_output = QPushButton("...")
        browse_output.setFixedWidth(32)
        browse_output.clicked.connect(self._select_output)
        output_row.addWidget(browse_output)
        input_layout.addLayout(output_row)
        
        # 历史记录
        history_label = QLabel("历史记录:")
        history_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        input_layout.addWidget(history_label)
        
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("选择...")
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        input_layout.addWidget(self.history_combo)
        
        left_layout.addWidget(input_group)
        
        # 文件列表
        files_group = QGroupBox("📋 文件列表")
        files_layout = QVBoxLayout(files_group)
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(False)
        files_layout.addWidget(self.file_list)
        
        file_info = QLabel("0 个文件")
        file_info.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        file_info.setAlignment(Qt.AlignCenter)
        files_layout.addWidget(file_info)
        self.file_info_label = file_info
        
        left_layout.addWidget(files_group, 1)
        
        # 预设配置
        preset_group = QGroupBox("🎯 预设")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(6)
        
        preset_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setPlaceholderText("选择预设...")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.preset_combo)
        
        save_preset_btn = QPushButton("+")
        save_preset_btn.setFixedWidth(28)
        save_preset_btn.setToolTip("保存当前设置")
        save_preset_btn.clicked.connect(self._save_preset)
        preset_row.addWidget(save_preset_btn)
        preset_layout.addLayout(preset_row)
        
        self.preset_desc_label = QLabel("")
        self.preset_desc_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 10px;")
        preset_layout.addWidget(self.preset_desc_label)
        
        left_layout.addWidget(preset_group)
        
        center_layout.addWidget(left_panel)
        
        # ===== 中间面板（预览和设置）=====
        mid_panel = QWidget()
        mid_layout = QVBoxLayout(mid_panel)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(8)
        
        # 预览区域
        preview_group = QGroupBox("👁️ 预览")
        preview_layout = QVBoxLayout(preview_group)
        
        # 预览按钮行
        preview_btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("🔍 预览压缩效果")
        self.preview_btn.setObjectName("blueBtn")
        self.preview_btn.clicked.connect(self._preview_compression)
        preview_btn_row.addWidget(self.preview_btn)
        
        exif_btn = QPushButton("📋 EXIF")
        exif_btn.clicked.connect(self._show_exif)
        preview_btn_row.addWidget(exif_btn)
        preview_btn_row.addStretch()
        preview_layout.addLayout(preview_btn_row)
        
        # 预览信息
        preview_info = QHBoxLayout()
        self.preview_original_label = QLabel("原始: -")
        self.preview_original_label.setStyleSheet(f"color: {self.TEXT_SECONDARY};")
        preview_info.addWidget(self.preview_original_label)
        
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {self.ACCENT}; font-weight: bold; padding: 0 10px;")
        preview_info.addWidget(arrow)
        
        self.preview_compressed_label = QLabel("压缩后: -")
        self.preview_compressed_label.setStyleSheet(f"color: {self.TEXT_PRIMARY}; font-weight: bold;")
        preview_info.addWidget(self.preview_compressed_label)
        
        preview_info.addSpacing(20)
        
        self.preview_savings_label = QLabel("节省: -")
        self.preview_savings_label.setStyleSheet(f"color: {self.SUCCESS}; font-weight: bold;")
        preview_info.addWidget(self.preview_savings_label)
        preview_info.addStretch()
        
        preview_layout.addLayout(preview_info)
        mid_layout.addWidget(preview_group)
        
        # 输出设置组
        settings_group = QGroupBox("⚙️ 输出设置")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(12)
        
        # 格式和大小
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["保持原格式", "JPG", "PNG", "WebP"])
        self.format_combo.setFixedWidth(110)
        row1.addWidget(self.format_combo)
        
        row1.addSpacing(20)
        
        row1.addWidget(QLabel("最小:"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedWidth(90)
        row1.addWidget(self.min_size_spin)
        row1.addStretch()
        
        settings_layout.addLayout(row1)
        
        # 质量滑块
        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("质量:"))
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        quality_row.addWidget(self.quality_slider, 1)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(DEFAULT_QUALITY)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setFixedWidth(55)
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
        self.max_width_spin.setSuffix("px")
        self.max_width_spin.setFixedWidth(70)
        self.max_width_spin.setEnabled(False)
        resize_row.addWidget(self.max_width_spin)
        
        resize_row.addWidget(QLabel("高:"))
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 10000)
        self.max_height_spin.setValue(0)
        self.max_height_spin.setSuffix("px")
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
        self.target_size_spin.setSuffix("KB")
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
        
        mid_layout.addWidget(settings_group)
        
        # 操作选项
        options_group = QGroupBox("🔧 选项")
        options_layout = QHBoxLayout(options_group)
        
        self.subfolder_cb = QCheckBox("包含子文件夹")
        self.subfolder_cb.setChecked(True)
        options_layout.addWidget(self.subfolder_cb)
        
        self.incremental_cb = QCheckBox("跳过已处理")
        self.incremental_cb.setChecked(True)
        options_layout.addWidget(self.incremental_cb)
        
        options_layout.addStretch()
        
        mid_layout.addWidget(options_group)
        mid_layout.addStretch()
        
        center_layout.addWidget(mid_panel, 1)
        
        # ===== 右侧面板（统计信息）=====
        right_panel = QWidget()
        right_panel.setFixedWidth(280)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # 统计信息组
        stats_group = QGroupBox("📊 统计")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        stats_layout.addWidget(self.progress_bar)
        
        self.stats_label = QLabel("准备就绪")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; padding: 4px;")
        stats_layout.addWidget(self.stats_label)
        
        # 统计数字
        stats_grid = QHBoxLayout()
        
        success_box = QVBoxLayout()
        success_label = QLabel("成功")
        success_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 10px;")
        success_label.setAlignment(Qt.AlignCenter)
        success_box.addWidget(success_label)
        self.success_count_label = QLabel("0")
        self.success_count_label.setStyleSheet(f"color: {self.SUCCESS}; font-size: 18px; font-weight: bold;")
        self.success_count_label.setAlignment(Qt.AlignCenter)
        success_box.addWidget(self.success_count_label)
        stats_grid.addLayout(success_box)
        
        skip_box = QVBoxLayout()
        skip_label = QLabel("跳过")
        skip_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 10px;")
        skip_label.setAlignment(Qt.AlignCenter)
        skip_box.addWidget(skip_label)
        self.skip_count_label = QLabel("0")
        self.skip_count_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 18px; font-weight: bold;")
        self.skip_count_label.setAlignment(Qt.AlignCenter)
        skip_box.addWidget(self.skip_count_label)
        stats_grid.addLayout(skip_box)
        
        error_box = QVBoxLayout()
        error_label = QLabel("失败")
        error_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 10px;")
        error_label.setAlignment(Qt.AlignCenter)
        error_box.addWidget(error_label)
        self.error_count_label = QLabel("0")
        self.error_count_label.setStyleSheet(f"color: #e74c3c; font-size: 18px; font-weight: bold;")
        self.error_count_label.setAlignment(Qt.AlignCenter)
        error_box.addWidget(self.error_count_label)
        stats_grid.addLayout(error_box)
        
        stats_layout.addLayout(stats_grid)
        
        # 节省空间
        savings_box = QVBoxLayout()
        savings_title = QLabel("共节省空间")
        savings_title.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        savings_title.setAlignment(Qt.AlignCenter)
        savings_box.addWidget(savings_title)
        self.total_savings_label = QLabel("0 B")
        self.total_savings_label.setStyleSheet(f"color: {self.SUCCESS}; font-size: 16px; font-weight: bold;")
        self.total_savings_label.setAlignment(Qt.AlignCenter)
        savings_box.addWidget(self.total_savings_label)
        stats_layout.addLayout(savings_box)
        
        # 导出按钮
        self.export_btn = QPushButton("📤 导出统计")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_stats)
        stats_layout.addWidget(self.export_btn)
        
        right_layout.addWidget(stats_group)
        
        # 详细信息表格
        detail_group = QGroupBox("📝 详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["文件", "状态", "原始", "压缩后"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stats_table.setAlternatingRowColors(False)
        detail_layout.addWidget(self.stats_table)
        
        right_layout.addWidget(detail_group, 1)
        
        center_layout.addWidget(right_panel)
        
        main_layout.addWidget(center_widget, 1)
        
        # ========== 底部日志区域 ==========
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(180)
        bottom_panel.setStyleSheet(f"background-color: {self.BG_PANEL}; border-top: 1px solid {self.BORDER};")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(4)
        
        # 日志标题
        log_header = QWidget()
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(0, 0, 0, 0)
        
        log_title = QLabel("📋 输出日志")
        log_title.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()
        
        clear_btn = QPushButton("清除")
        clear_btn.setFixedWidth(50)
        clear_btn.setStyleSheet(f"font-size: 10px; padding: 2px 6px;")
        clear_btn.clicked.connect(self._clear_log)
        log_header_layout.addWidget(clear_btn)
        
        bottom_layout.addWidget(log_header)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("等待开始...")
        bottom_layout.addWidget(self.log_text)
        
        main_layout.addWidget(bottom_panel)
        
        # ========== 状态栏 ==========
        status_bar = QWidget()
        status_bar.setFixedHeight(26)
        status_bar.setStyleSheet(f"background-color: {self.BG_PANEL}; border-top: 1px solid {self.BORDER};")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        
        self.status_label = QLabel(f"就绪 | {APP_NAME} v{__version__}")
        self.status_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        main_layout.addWidget(status_bar)
    
    def _create_openshot_group(self, title):
        """创建 OpenShot 风格的分组"""
        group = QGroupBox(title)
        return group
    
    def _connect_signals(self):
        """连接信号与槽"""
        self.quality_slider.valueChanged.connect(self.quality_spin.setValue)
        self.quality_spin.valueChanged.connect(self.quality_slider.setValue)
        self.input_edit.textChanged.connect(self._update_file_list)
    
    def _update_file_list(self):
        """更新文件列表"""
        input_path = self.input_edit.text()
        self.file_list.clear()
        
        if not input_path or not Path(input_path).exists():
            self.file_info_label.setText("0 个文件")
            return
        
        try:
            path = Path(input_path)
            if path.is_dir():
                files = list(path.glob("*"))
                image_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']]
                
                for f in image_files[:100]:  # 限制显示100个文件
                    item = QListWidgetItem(f"🖼️ {f.name}")
                    item.setToolTip(str(f))
                    self.file_list.addItem(item)
                
                count = len(image_files)
                self.file_info_label.setText(f"{count} 个文件" if count <= 100 else f"{count}+ 个文件")
        except Exception:
            self.file_info_label.setText("0 个文件")
    
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
    
    def _clear_log(self):
        """清除日志"""
        self.log_text.clear()
    
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
            
            self.preview_original_label.setText(f"原始: {format_bytes(orig_size)}")
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
        
        # 重置统计
        self.progress_bar.setValue(0)
        self.stats_label.setText("准备中...")
        self.success_count_label.setText("0")
        self.skip_count_label.setText("0")
        self.error_count_label.setText("0")
        self.total_savings_label.setText("0 B")
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
        
        # 更新统计数字
        success = sum(1 for _, s, _, _, _ in results if s == "成功")
        skip = sum(1 for _, s, _, _, _ in results if s == "跳过")
        error = sum(1 for _, s, _, _, _ in results if s == "失败")
        total_saved = sum(max(0, o - n) for _, s, o, n, _ in results)
        
        self.success_count_label.setText(str(success))
        self.skip_count_label.setText(str(skip))
        self.error_count_label.setText(str(error))
        self.total_savings_label.setText(format_bytes(total_saved))
    
    def _update_stats_table(self, results):
        """更新统计表格"""
        self.stats_table.setRowCount(len(results))
        
        for i, (path, status, orig_size, new_size, details) in enumerate(results):
            self.stats_table.setItem(i, 0, QTableWidgetItem(path.name))
            
            status_item = QTableWidgetItem(status)
            if status == "成功":
                status_item.setForeground(QColor(self.SUCCESS))
            elif status == "失败":
                status_item.setForeground(QColor("#e74c3c"))
            self.stats_table.setItem(i, 1, status_item)
            
            self.stats_table.setItem(i, 2, QTableWidgetItem(format_bytes(orig_size)))
            self.stats_table.setItem(i, 3, QTableWidgetItem(format_bytes(new_size)))
    
    def _on_finished(self, success_count, skip_count, error_count, total_saved):
        """任务完成"""
        self._is_running = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        
        self.progress_bar.setValue(100)
        self.stats_label.setText(f"完成!")
        
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
