"""
主窗口模块 - 功能增强版
"""

from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QCheckBox, QProgressBar,
    QSlider, QSpinBox, QTextEdit, QDoubleSpinBox, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QSplitter,
    QAbstractItemView, QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread

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
    """图片压缩工具主窗口 - 功能增强版"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = setup_logging()
        self._is_running = False
        self.worker = None
        self.thread = None
        self.current_detailed_stats = []
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 800)
        self.resize(1000, 900)
        
        # 设置界面（使用 qdarkstyle 主题）
        self._setup_ui()
        self._connect_signals()
        self._load_history()
    
    def _setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # ========== 菜单栏 ==========
        menubar = QMenuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        main_layout.setMenuBar(menubar)
        
        # ========== 标题 ==========
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setSpacing(4)
        
        title_label = QLabel(f"{APP_NAME}")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(20)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #80cbc4;")
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"v{__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #78909c; font-size: 12px;")
        title_layout.addWidget(version_label)
        
        main_layout.addWidget(title_widget)
        
        # ========== 主分割器 ==========
        splitter = QSplitter(Qt.Vertical)
        
        # ========== 上半部分：设置区域 ==========
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # 路径设置
        path_group = QGroupBox("📁 路径设置")
        path_layout = QFormLayout(path_group)
        path_layout.setSpacing(10)
        
        # 输入路径
        input_layout = QHBoxLayout()
        self.input_edit = DragDropLineEdit()
        self.input_edit.setPlaceholderText("选择或拖拽输入文件夹...")
        input_layout.addWidget(self.input_edit)
        
        btn_input = QPushButton("浏览...")
        btn_input.setFixedWidth(80)
        btn_input.clicked.connect(self._select_input)
        input_layout.addWidget(btn_input)
        
        path_layout.addRow("输入文件夹：", input_layout)
        
        # 历史记录
        history_layout = QHBoxLayout()
        history_layout.addStretch()
        
        history_label = QLabel("📜 快速选择历史记录：")
        history_label.setStyleSheet("color: #78909c; font-size: 12px;")
        history_layout.addWidget(history_label)
        
        self.history_combo = QComboBox()
        self.history_combo.setFixedWidth(250)
        self.history_combo.setPlaceholderText("-- 选择之前使用过的文件夹 --")
        self.history_combo.setToolTip("选择历史记录会自动填充输入和输出路径")
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        history_layout.addWidget(self.history_combo)
        
        path_layout.addRow("", history_layout)
        
        # 输出路径
        output_layout = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("留空则覆盖原文件（谨慎使用）...")
        output_layout.addWidget(self.output_edit)
        
        btn_output = QPushButton("浏览...")
        btn_output.setFixedWidth(80)
        btn_output.clicked.connect(self._select_output)
        output_layout.addWidget(btn_output)
        
        path_layout.addRow("输出文件夹：", output_layout)
        
        top_layout.addWidget(path_group)
        
        # ========== 预设配置 ==========
        preset_group = QGroupBox("🎯 预设配置")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setSpacing(12)
        
        preset_layout.addWidget(QLabel("选择预设:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.setFixedWidth(180)
        self.preset_combo.setPlaceholderText("-- 选择预设 --")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)
        
        self.preset_desc_label = QLabel("")
        self.preset_desc_label.setStyleSheet("color: #78909c; font-size: 12px;")
        preset_layout.addWidget(self.preset_desc_label)
        
        preset_layout.addStretch()
        
        # 预设操作按钮
        self.save_preset_btn = QPushButton("💾 保存当前为预设")
        self.save_preset_btn.clicked.connect(self._save_preset)
        preset_layout.addWidget(self.save_preset_btn)
        
        self.manage_preset_btn = QPushButton("⚙️ 管理")
        self.manage_preset_btn.clicked.connect(self._manage_presets)
        preset_layout.addWidget(self.manage_preset_btn)
        
        top_layout.addWidget(preset_group)
        
        # 加载预设列表
        self._load_presets()
        
        # ========== 压缩预览 ==========
        preview_group = QGroupBox("👁️ 压缩预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(10)
        
        # 预览控制行
        preview_control = QHBoxLayout()
        
        self.preview_btn = QPushButton("🔍 预览第一张图片")
        self.preview_btn.clicked.connect(self._preview_compression)
        preview_control.addWidget(self.preview_btn)
        
        self.exif_btn = QPushButton("📋 查看EXIF")
        self.exif_btn.clicked.connect(self._show_exif)
        preview_control.addWidget(self.exif_btn)
        
        preview_control.addStretch()
        
        # EXIF 选项
        self.keep_exif_cb = QCheckBox("保留 EXIF 信息")
        self.keep_exif_cb.setChecked(True)
        preview_control.addWidget(self.keep_exif_cb)
        
        self.auto_rotate_cb = QCheckBox("自动旋转（根据EXIF方向）")
        self.auto_rotate_cb.setChecked(True)
        preview_control.addWidget(self.auto_rotate_cb)
        
        preview_layout.addLayout(preview_control)
        
        # 预览结果区域
        preview_result = QHBoxLayout()
        
        self.preview_original_label = QLabel("原图: -")
        self.preview_original_label.setStyleSheet("color: #b0bec5;")
        preview_result.addWidget(self.preview_original_label)
        
        preview_result.addWidget(QLabel("→"))
        
        self.preview_compressed_label = QLabel("压缩后: -")
        self.preview_compressed_label.setStyleSheet("color: #4caf50;")
        preview_result.addWidget(self.preview_compressed_label)
        
        preview_result.addWidget(QLabel("|"))
        
        self.preview_savings_label = QLabel("节省: -")
        self.preview_savings_label.setStyleSheet("color: #80cbc4;")
        preview_result.addWidget(self.preview_savings_label)
        
        preview_result.addStretch()
        
        preview_layout.addLayout(preview_result)
        
        top_layout.addWidget(preview_group)
        
        # 压缩选项
        options_group = QGroupBox("⚙️ 压缩选项")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)
        
        # 第一行：基本选项
        row1 = QHBoxLayout()
        
        self.subfolder_cb = QCheckBox("包含子文件夹")
        self.subfolder_cb.setChecked(True)
        row1.addWidget(self.subfolder_cb)
        
        self.incremental_cb = QCheckBox("跳过已处理文件（增量压缩）")
        self.incremental_cb.setChecked(True)
        row1.addWidget(self.incremental_cb)
        
        row1.addStretch()
        
        row1.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["保持原格式", "转换为 JPG", "转换为 PNG", "转换为 WebP"])
        self.format_combo.setFixedWidth(140)
        row1.addWidget(self.format_combo)
        
        row1.addSpacing(16)
        
        row1.addWidget(QLabel("最小大小:"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setSingleStep(0.1)
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedWidth(100)
        row1.addWidget(self.min_size_spin)
        
        options_layout.addLayout(row1)
        
        # 第二行：尺寸调整
        row2 = QHBoxLayout()
        
        self.resize_cb = QCheckBox("调整尺寸（限制最大宽高）")
        self.resize_cb.stateChanged.connect(self._on_resize_toggled)
        row2.addWidget(self.resize_cb)
        
        row2.addWidget(QLabel("最大宽度:"))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(0, 10000)
        self.max_width_spin.setSingleStep(100)
        self.max_width_spin.setValue(0)
        self.max_width_spin.setSuffix(" px")
        self.max_width_spin.setFixedWidth(90)
        self.max_width_spin.setEnabled(False)
        row2.addWidget(self.max_width_spin)
        
        row2.addWidget(QLabel("最大高度:"))
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 10000)
        self.max_height_spin.setSingleStep(100)
        self.max_height_spin.setValue(0)
        self.max_height_spin.setSuffix(" px")
        self.max_height_spin.setFixedWidth(90)
        self.max_height_spin.setEnabled(False)
        row2.addWidget(self.max_height_spin)
        
        self.keep_ratio_cb = QCheckBox("保持比例")
        self.keep_ratio_cb.setChecked(True)
        self.keep_ratio_cb.setEnabled(False)
        row2.addWidget(self.keep_ratio_cb)
        
        row2.addStretch()
        
        options_layout.addLayout(row2)
        
        # 第三行：压缩质量和智能压缩
        row3 = QHBoxLayout()
        
        row3.addWidget(QLabel("压缩质量:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        row3.addWidget(self.quality_slider, stretch=1)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(DEFAULT_QUALITY)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setFixedWidth(70)
        row3.addWidget(self.quality_spin)
        
        row3.addSpacing(20)
        
        self.smart_cb = QCheckBox("智能压缩（自动找最佳质量）")
        self.smart_cb.stateChanged.connect(self._on_smart_toggled)
        row3.addWidget(self.smart_cb)
        
        row3.addWidget(QLabel("目标:"))
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(10, 10000)
        self.target_size_spin.setValue(200)
        self.target_size_spin.setSuffix(" KB")
        self.target_size_spin.setFixedWidth(80)
        self.target_size_spin.setEnabled(False)
        row3.addWidget(self.target_size_spin)
        
        options_layout.addLayout(row3)
        
        # 第四行：重命名
        row4 = QHBoxLayout()
        
        self.rename_cb = QCheckBox("重命名文件")
        self.rename_cb.stateChanged.connect(self._on_rename_toggled)
        row4.addWidget(self.rename_cb)
        
        row4.addWidget(QLabel("命名模式:"))
        self.rename_combo = QComboBox()
        self.rename_combo.addItems([
            "保持原文件名",
            "原文件名_序号",
            "纯序号",
            "自定义前缀_序号",
            "日期_序号",
        ])
        self.rename_combo.setFixedWidth(160)
        self.rename_combo.setEnabled(False)
        self.rename_combo.currentIndexChanged.connect(self._on_rename_pattern_changed)
        row4.addWidget(self.rename_combo)
        
        self.rename_prefix_edit = QLineEdit()
        self.rename_prefix_edit.setPlaceholderText("输入前缀...")
        self.rename_prefix_edit.setFixedWidth(120)
        self.rename_prefix_edit.setEnabled(False)
        row4.addWidget(self.rename_prefix_edit)
        
        self.rename_preview = QLabel("")
        self.rename_preview.setStyleSheet("color: #78909c; font-style: italic;")
        row4.addWidget(self.rename_preview)
        
        row4.addStretch()
        
        options_layout.addLayout(row4)
        
        top_layout.addWidget(options_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.export_btn = QPushButton("📊 导出统计")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_stats)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addSpacing(20)
        
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setFixedWidth(90)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addSpacing(10)
        
        self.start_btn = QPushButton("🚀 开始压缩")
        self.start_btn.setDefault(True)
        self.start_btn.setFixedWidth(120)
        btn_layout.addWidget(self.start_btn)
        
        btn_layout.addStretch()
        top_layout.addLayout(btn_layout)
        
        # 进度区域
        progress_group = QGroupBox("📈 进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.stats_label = QLabel("准备就绪 - 请选择输入文件夹后开始")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #80cbc4; font-size: 13px; padding: 4px;")
        progress_layout.addWidget(self.stats_label)
        
        top_layout.addWidget(progress_group)
        
        splitter.addWidget(top_widget)
        
        # ========== 下半部分：标签页 ==========
        self.tab_widget = QTabWidget()
        # Fusion 风格下使用简洁模式
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
        
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([550, 350])
        
        main_layout.addWidget(splitter)
    
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
        if not self.rename_cb.isChecked():
            self.rename_prefix_edit.setEnabled(False)
            self.rename_preview.setText("")
            return
        
        pattern_idx = self.rename_combo.currentIndex()
        # 自定义前缀模式
        if pattern_idx == 3:
            self.rename_prefix_edit.setEnabled(True)
        else:
            self.rename_prefix_edit.setEnabled(False)
        
        # 更新预览
        patterns = ["{name}", "{name}_{index:03d}", "{index:03d}", "{prefix}{index:03d}", "{date}_{index:03d}"]
        pattern = patterns[pattern_idx]
        prefix = self.rename_prefix_edit.text() if pattern_idx == 3 else ""
        preview = pattern.format(name="image", index=1, prefix=prefix, date=datetime.now().strftime("%Y%m%d"))
        self.rename_preview.setText(f"示例: {preview}.jpg")
    
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
    
    def _get_rename_pattern(self):
        """获取重命名模式"""
        if not self.rename_cb.isChecked():
            return None
        
        patterns = ["{name}", "{name}_{index:03d}", "{index:03d}", "{prefix}{index:03d}", "{date}_{index:03d}"]
        pattern = patterns[self.rename_combo.currentIndex()]
        
        if self.rename_combo.currentIndex() == 3:
            prefix = self.rename_prefix_edit.text() or "img"
            pattern = pattern.replace("{prefix}", prefix)
        
        return pattern
    
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
        rename_pattern = self._get_rename_pattern()
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
                rename_pattern,
                keep_exif, auto_rotate,
            )
        )
        
        self.thread.start()
    
    def _cancel_compression(self):
        """取消压缩任务"""
        if self.worker and self._is_running:
            self.worker.cancel()
            self.stats_label.setText("正在取消...")
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
        
        # 状态带颜色
        status_item = QTableWidgetItem(stat_record["status"])
        if stat_record["status"] == "processed":
            status_item.setForeground(Qt.green)
        elif stat_record["status"] == "failed":
            status_item.setForeground(Qt.red)
        elif stat_record["status"] == "skipped":
            status_item.setForeground(Qt.yellow)
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
            return
        
        if "error" in result:
            self.stats_label.setText(f"❌ 错误: {result['error']}")
            return
        
        p, s, t, f, c = result["processed"], result["skipped"], result["too_small"], result["failed"], result["cached"]
        orig = format_bytes(result["total_orig"])
        comp = format_bytes(result["total_comp"])
        saved = format_bytes(result["saved"])
        threads = result.get("thread_count", 0)
        
        msg = f"✅ 完成！处理:{p} 跳过:{s} 太小:{t} 失败:{f} 缓存:{c} | 原始:{orig} → 压缩后:{comp} | 节省:{saved} | 线程:{threads}"
        self.stats_label.setText(msg)
        self.stats_label.setStyleSheet("color: #4caf50; font-size: 13px; padding: 4px;")
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
                    "节省(B)", "节省(%)", "原尺寸", "新尺寸", "是否重命名", "新文件名"
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
                        "是" if stat.get("renamed") else "否",
                        stat.get("new_name", ""),
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
    
    def _show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def _load_presets(self):
        """加载预设列表"""
        try:
            self.preset_combo.clear()
            self.preset_combo.addItem("-- 自定义 --", None)
            
            presets = config_manager.load_presets()
            for preset in presets:
                name = preset.get("name", "未命名")
                desc = preset.get("description", "")
                self.preset_combo.addItem(name, preset)
        except Exception as e:
            print(f"加载预设失败: {e}")
    
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
    
    def _manage_presets(self):
        """管理预设"""
        from PyQt5.QtWidgets import QListWidget, QDialog, QVBoxLayout, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("管理预设")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        presets = config_manager.load_presets()
        default_names = {"网页用", "手机分享", "高质量存档", "缩略图"}
        
        for preset in presets:
            name = preset.get("name", "未命名")
            if name not in default_names:
                list_widget.addItem(name)
        
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self._delete_selected_preset(list_widget, dialog))
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec_()
    
    def _delete_selected_preset(self, list_widget, dialog):
        """删除选中的预设"""
        item = list_widget.currentItem()
        if not item:
            QMessageBox.information(dialog, "提示", "请先选择要删除的预设")
            return
        
        name = item.text()
        reply = QMessageBox.question(dialog, "确认删除", f"确定删除预设 '{name}' 吗？")
        
        if reply == QMessageBox.Yes:
            if config_manager.delete_preset(name):
                list_widget.takeItem(list_widget.currentRow())
                self._load_presets()
                QMessageBox.information(dialog, "删除成功", f"预设 '{name}' 已删除")
            else:
                QMessageBox.warning(dialog, "删除失败", "无法删除该预设")
    
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
