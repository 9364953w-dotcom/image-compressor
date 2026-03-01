"""
主窗口模块 - 稳定可靠的简洁界面
"""

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QCheckBox, QProgressBar,
    QSlider, QSpinBox, QTextEdit, QDoubleSpinBox, QMessageBox,
    QGroupBox, QFormLayout, QSplitter
)
from PyQt5.QtCore import Qt, QThread

from src.config import APP_NAME, DEFAULT_QUALITY, DEFAULT_MIN_SIZE_MB
from src.utils import format_bytes, setup_logging
from src.widgets.drag_drop import DragDropLineEdit
from src.core.worker import CompressWorker


class MainWindow(QWidget):
    """图片压缩工具主窗口 - 简洁稳定版"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = setup_logging()
        self._is_running = False
        self.worker = None
        self.thread = None
        
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置用户界面 - 使用系统默认风格"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # ========== 标题 ==========
        title_label = QLabel(APP_NAME)
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)
        
        # ========== 路径设置 ==========
        path_group = QGroupBox("路径设置")
        path_layout = QFormLayout(path_group)
        path_layout.setSpacing(10)
        path_layout.setLabelAlignment(Qt.AlignLeft)
        path_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
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
        
        # 输出路径
        output_layout = QHBoxLayout()
        self.output_edit = DragDropLineEdit()
        self.output_edit.setPlaceholderText("留空则覆盖原文件（谨慎）...")
        output_layout.addWidget(self.output_edit)
        
        btn_output = QPushButton("浏览...")
        btn_output.setFixedWidth(80)
        btn_output.clicked.connect(self._select_output)
        output_layout.addWidget(btn_output)
        
        path_layout.addRow("输出文件夹：", output_layout)
        
        main_layout.addWidget(path_group)
        
        # ========== 压缩选项 ==========
        options_group = QGroupBox("压缩选项")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)
        
        # 选项行1
        row1 = QHBoxLayout()
        
        self.subfolder_cb = QCheckBox("包含子文件夹")
        self.subfolder_cb.setChecked(True)
        row1.addWidget(self.subfolder_cb)
        
        row1.addStretch()
        
        row1.addWidget(QLabel("最小文件大小:"))
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 100)
        self.min_size_spin.setDecimals(1)
        self.min_size_spin.setSingleStep(0.1)
        self.min_size_spin.setValue(DEFAULT_MIN_SIZE_MB)
        self.min_size_spin.setSuffix(" MB")
        self.min_size_spin.setFixedWidth(100)
        row1.addWidget(self.min_size_spin)
        
        options_layout.addLayout(row1)
        
        # 压缩质量
        quality_layout = QHBoxLayout()
        
        quality_layout.addWidget(QLabel("压缩质量:"))
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(DEFAULT_QUALITY)
        quality_layout.addWidget(self.quality_slider, stretch=1)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(DEFAULT_QUALITY)
        self.quality_spin.setSuffix("%")
        self.quality_spin.setFixedWidth(70)
        quality_layout.addWidget(self.quality_spin)
        
        options_layout.addLayout(quality_layout)
        
        main_layout.addWidget(options_group)
        
        # ========== 操作按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setFixedWidth(100)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addSpacing(10)
        
        self.start_btn = QPushButton("开始压缩")
        self.start_btn.setDefault(True)
        self.start_btn.setFixedWidth(120)
        btn_layout.addWidget(self.start_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        # ========== 进度区域 ==========
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        
        self.stats_label = QLabel("准备就绪")
        self.stats_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.stats_label)
        
        main_layout.addWidget(progress_group)
        
        # ========== 日志区域 ==========
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("等待开始...")
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group, stretch=1)
    
    def _connect_signals(self):
        """连接信号与槽"""
        self.start_btn.clicked.connect(self._start_compression)
        self.cancel_btn.clicked.connect(self._cancel_compression)
        self.quality_slider.valueChanged.connect(self.quality_spin.setValue)
        self.quality_spin.valueChanged.connect(self.quality_slider.setValue)
    
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
        
        is_overwrite_mode = False
        if not output_dir:
            reply = QMessageBox.question(
                self, "确认覆盖",
                "未选择输出文件夹，是否直接覆盖原文件？\n\n"
                "警告：此操作将直接修改原始文件，无法撤销！",
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
        
        self._is_running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.stats_label.setText("正在初始化...")
        
        self.worker = CompressWorker()
        self.worker.signals.progress.connect(self._update_progress)
        self.worker.signals.result.connect(self._show_result)
        self.worker.signals.finished.connect(self._on_finished)
        
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(
            lambda: self.worker.run(
                input_dir, output_dir,
                self.quality_spin.value(),
                self.subfolder_cb.isChecked(),
                self.min_size_spin.value(),
                is_overwrite_mode,
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
    
    def _show_result(self, result):
        """显示结果"""
        if "canceled" in result:
            self.stats_label.setText("任务已被用户取消")
            return
        
        if "error" in result:
            self.stats_label.setText(f"错误: {result['error']}")
            return
        
        p, s, t, f = result["processed"], result["skipped"], result["too_small"], result["failed"]
        orig = format_bytes(result["total_orig"])
        comp = format_bytes(result["total_comp"])
        saved = format_bytes(result["saved"])
        
        msg = f"完成！已处理：{p}张, 跳过：{s}张, 太小：{t}张, 失败：{f}张 | 原始：{orig} → 压缩后：{comp} | 节省：{saved}"
        self.stats_label.setText(msg)
    
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
