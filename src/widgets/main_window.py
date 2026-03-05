"""
主窗口模块 - Dock 化 OpenShot 风格。
"""

import csv
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageOps
from PyQt5.QtCore import QThread, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
)

from src.config import APP_NAME, __version__, config_manager
from src.core.compressor import get_exif_info
from src.core.worker import CompressWorker
from src.utils import format_bytes, setup_logging
from src.widgets.about_dialog import AboutDialog
from src.widgets.exif_dialog import ExifDialog
from src.widgets.panels import InputPanel, LogPanel, SettingsPanel, StatsPanel
from src.widgets.theme import THEMES, build_stylesheet


STATUS_TEXT = {
    "Idle": "就绪",
    "Validating": "校验参数中",
    "Scanning": "扫描文件中",
    "Running": "处理中",
    "Finalizing": "汇总结果中",
    "Done": "已完成",
    "Cancelled": "已取消",
    "Canceling": "取消中",
    "Error": "错误",
}


class MainWindow(QMainWindow):
    """图片压缩工具主窗口。"""

    def __init__(self):
        super().__init__()

        self.logger = setup_logging()
        self._is_running = False
        self.worker = None
        self.thread = None
        self.current_detailed_stats: List[Dict] = []
        self.current_theme_name = "HumanityDark"
        self.current_view_name = "Simple"
        self._image_files: List[Path] = []
        self._selected_image_path: Path = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._refresh_live_preview)

        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.setMinimumSize(1280, 820)
        self.resize(1480, 920)

        self._setup_ui()
        self._connect_signals()
        self._load_history()
        self._load_presets()
        self._load_ui_settings()
        self._refresh_file_list()
        self._show_onboarding_if_needed()

    def _setup_ui(self) -> None:
        self._setup_menu_and_toolbars()
        self._setup_layout()
        self._setup_status_bar()
        self._apply_theme(self.current_theme_name)

    @staticmethod
    def _pil_to_qpixmap(image: Image.Image) -> QPixmap:
        """将 PIL Image 稳定转换为 QPixmap（不依赖 ImageQt）。"""
        rgba = image.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimage = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage.copy())

    def _setup_menu_and_toolbars(self) -> None:
        menu = self.menuBar()

        view_menu = menu.addMenu("视图")
        self.simple_view_action = QAction("简洁视图", self)
        self.simple_view_action.triggered.connect(lambda: self._apply_view("Simple"))
        self.advanced_view_action = QAction("高级视图", self)
        self.advanced_view_action.triggered.connect(lambda: self._apply_view("Advanced"))
        view_menu.addAction(self.simple_view_action)
        view_menu.addAction(self.advanced_view_action)

        theme_menu = menu.addMenu("主题")
        self.theme_actions = {}
        for theme_name in THEMES:
            action = QAction(theme_name, self)
            action.triggered.connect(lambda _, t=theme_name: self._apply_theme(t))
            self.theme_actions[theme_name] = action
            theme_menu.addAction(action)

        help_menu = menu.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        self.main_toolbar = QToolBar("主工具栏", self)
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        self.main_toolbar.hide()

        self.context_toolbar = QToolBar("上下文栏", self)
        self.context_toolbar.setMovable(False)
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.addToolBar(Qt.TopToolBarArea, self.context_toolbar)

        self.context_toolbar.addWidget(QLabel("主题配色:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self._apply_theme)
        self.context_toolbar.addWidget(self.theme_combo)
        self.context_toolbar.addSeparator()

        self.badge_files = QLabel("文件: 0")
        self.badge_threads = QLabel("线程: -")
        self.badge_eta = QLabel("ETA: -")
        self.context_toolbar.addWidget(self.badge_files)
        self.context_toolbar.addSeparator()
        self.context_toolbar.addWidget(self.badge_threads)
        self.context_toolbar.addSeparator()
        self.context_toolbar.addWidget(self.badge_eta)

    def _setup_layout(self) -> None:
        self.input_panel = InputPanel(self)
        self.settings_panel = SettingsPanel(self)
        self.stats_panel = StatsPanel(self)
        self.log_panel = LogPanel(self)

        # 三栏布局：左固定，中右等宽
        self.main_splitter = QSplitter(Qt.Horizontal, self)
        self.main_splitter.addWidget(self.input_panel)
        self.main_splitter.addWidget(self.settings_panel)
        self.main_splitter.addWidget(self.stats_panel)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(0)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 1)

        self.input_panel.setMinimumWidth(280)
        self.input_panel.setMaximumWidth(340)
        self.input_panel.setFixedWidth(300)

        # 顶部三栏 + 底部日志
        self.vertical_splitter = QSplitter(Qt.Vertical, self)
        self.vertical_splitter.addWidget(self.main_splitter)
        self.vertical_splitter.addWidget(self.log_panel)
        self.vertical_splitter.setChildrenCollapsible(False)
        self.vertical_splitter.setHandleWidth(0)
        self.vertical_splitter.setStretchFactor(0, 1)
        self.vertical_splitter.setStretchFactor(1, 0)

        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(6)
        container_layout.addWidget(self.vertical_splitter)
        self.setCentralWidget(container)
        self.main_splitter.setSizes([300, 590, 590])
        self.vertical_splitter.setSizes([760, 160])

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"就绪 | v{__version__}")
        self.status_signature_label = QLabel("成都一禾视觉专用")
        self.status_signature_label.setStyleSheet("color: #b5b5b5; padding-right: 8px;")
        self.status_bar.addPermanentWidget(self.status_signature_label)

    def _connect_signals(self) -> None:
        self.input_panel.browse_input_btn.clicked.connect(self._select_input)
        self.input_panel.browse_output_btn.clicked.connect(self._select_output)
        self.input_panel.input_edit.textChanged.connect(self._refresh_file_list)
        self.input_panel.history_combo.currentTextChanged.connect(self._on_history_selected)
        self.input_panel.file_list.currentItemChanged.connect(self._on_file_selected)

        self.settings_panel.include_subfolders_cb.toggled.connect(self._refresh_file_list)
        self.settings_panel.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        self.settings_panel.save_preset_btn.clicked.connect(self._save_preset)
        self.settings_panel.exif_btn.clicked.connect(self._show_exif)
        self.settings_panel.start_btn.clicked.connect(self._start_compression)
        self.settings_panel.cancel_btn.clicked.connect(self._cancel_compression)
        self.settings_panel.preview_100_cb.toggled.connect(lambda _checked: self.settings_panel.refresh_preview_widget())

        self.stats_panel.export_btn.clicked.connect(self._export_stats)

        for signal in (
            self.settings_panel.format_combo.currentIndexChanged,
            self.settings_panel.min_size_spin.valueChanged,
            self.settings_panel.quality_spin.valueChanged,
            self.settings_panel.resize_cb.toggled,
            self.settings_panel.keep_ratio_cb.toggled,
            self.settings_panel.max_width_spin.valueChanged,
            self.settings_panel.max_height_spin.valueChanged,
            self.settings_panel.smart_cb.toggled,
            self.settings_panel.target_size_spin.valueChanged,
            self.settings_panel.keep_exif_cb.toggled,
            self.settings_panel.auto_rotate_cb.toggled,
        ):
            signal.connect(self._schedule_live_preview)

        self.settings_panel.live_preview_cb.toggled.connect(self._schedule_live_preview)

    def _apply_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            return
        self.current_theme_name = theme_name
        self.setStyleSheet(build_stylesheet(THEMES[theme_name]))
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_name)
        self.theme_combo.blockSignals(False)
        self._save_ui_settings()

    def _apply_view(self, view_name: str) -> None:
        self.current_view_name = view_name
        if view_name == "Simple":
            self.log_panel.hide()
        else:
            self.log_panel.show()
        self._save_ui_settings()

    def _show_onboarding_if_needed(self) -> None:
        settings = config_manager.load_ui_settings()
        if settings.get("tutorial_seen"):
            return
        QMessageBox.information(
            self,
            "快速开始",
            "欢迎使用图片压缩工具。\n\n"
            "1. 先选择输入文件夹\n"
            "2. 选择一个预设（可选）\n"
            "3. 点击“开始压缩”\n\n"
            "提示：可以切换简洁/高级视图与主题。",
        )
        settings["tutorial_seen"] = True
        config_manager.save_ui_settings(settings)

    def _load_ui_settings(self) -> None:
        settings = config_manager.load_ui_settings()
        theme_name = settings.get("theme", "HumanityDark")
        view_name = settings.get("view", "Simple")
        self._apply_theme(theme_name)
        self._apply_view(view_name)

    def _save_ui_settings(self) -> None:
        settings = config_manager.load_ui_settings()
        settings["theme"] = self.current_theme_name
        settings["view"] = self.current_view_name
        config_manager.save_ui_settings(settings)

    def _load_history(self) -> None:
        history = config_manager.load_history()
        self.input_panel.history_combo.clear()
        for item in history:
            self.input_panel.history_combo.addItem(item.get("input_path", ""))

    def _on_history_selected(self, text: str) -> None:
        if not text:
            return
        history = config_manager.load_history()
        for item in history:
            if item.get("input_path") == text:
                self.input_panel.input_edit.setText(item.get("input_path", ""))
                self.input_panel.output_edit.setText(item.get("output_path", ""))
                break

    def _refresh_file_list(self) -> None:
        self.input_panel.file_list.clear()
        self._image_files = []
        self._selected_image_path = None
        input_path = self.input_panel.input_edit.text().strip()
        if not input_path or not Path(input_path).exists():
            self.input_panel.file_info_label.setText("0 个文件")
            self.badge_files.setText("文件: 0")
            self.settings_panel.clear_preview("请选择输入目录后查看预览")
            return

        path = Path(input_path)
        files = path.rglob("*") if self.settings_panel.include_subfolders_cb.isChecked() else path.glob("*")
        image_files = [f for f in files if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}]
        self._image_files = sorted(image_files)
        for file_path in self._image_files[:100]:
            label = str(file_path.relative_to(path)) if self.settings_panel.include_subfolders_cb.isChecked() else file_path.name
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, str(file_path))
            self.input_panel.file_list.addItem(item)
        total = len(self._image_files)
        suffix = "（仅显示前100）" if total > 100 else ""
        self.input_panel.file_info_label.setText(f"{total} 个文件{suffix}")
        self.badge_files.setText(f"文件: {total}")
        if self.input_panel.file_list.count() > 0:
            self.input_panel.file_list.setCurrentRow(0)
        self._schedule_live_preview()

    def _on_file_selected(self, current_item, _previous_item) -> None:
        self._selected_image_path = None
        if current_item:
            item_path = current_item.data(Qt.UserRole)
            if item_path:
                selected = Path(item_path)
                if selected.exists() and selected.is_file():
                    self._selected_image_path = selected
        self._schedule_live_preview()

    def _load_presets(self) -> None:
        presets = config_manager.load_presets()
        self.settings_panel.preset_combo.clear()
        self.settings_panel.preset_combo.addItem("选择预设...")
        for preset in presets:
            self.settings_panel.preset_combo.addItem(preset["name"])

    def _on_preset_selected(self, index: int) -> None:
        if index <= 0:
            self.settings_panel.preset_desc_label.setText("")
            return

        presets = config_manager.load_presets()
        if index - 1 >= len(presets):
            return
        preset = presets[index - 1]
        settings = preset.get("settings", {})

        self.settings_panel.quality_spin.setValue(int(settings.get("quality", 90)))
        format_map = {"original": 0, "jpg": 1, "png": 2, "webp": 3}
        self.settings_panel.format_combo.setCurrentIndex(format_map.get(settings.get("output_format", "original"), 0))
        self.settings_panel.min_size_spin.setValue(float(settings.get("min_size_mb", 0.1)))

        max_width = int(settings.get("max_width", 0))
        max_height = int(settings.get("max_height", 0))
        self.settings_panel.resize_cb.setChecked(max_width > 0 or max_height > 0)
        self.settings_panel.max_width_spin.setValue(max_width)
        self.settings_panel.max_height_spin.setValue(max_height)
        self.settings_panel.keep_ratio_cb.setChecked(bool(settings.get("keep_ratio", True)))

        self.settings_panel.smart_cb.setChecked(bool(settings.get("smart_mode", False)))
        self.settings_panel.target_size_spin.setValue(int(settings.get("target_size_kb", 200)))
        self.settings_panel.preset_desc_label.setText(preset.get("description", ""))

    def _save_preset(self) -> None:
        from PyQt5.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "保存预设", "预设名称")
        if not ok or not name.strip():
            return
        description, _ = QInputDialog.getText(self, "保存预设", "预设说明")

        settings = {
            "quality": self.settings_panel.quality_spin.value(),
            "output_format": self.settings_panel.output_format_value(),
            "max_width": self.settings_panel.max_width_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "max_height": self.settings_panel.max_height_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "keep_ratio": self.settings_panel.keep_ratio_cb.isChecked(),
            "smart_mode": self.settings_panel.smart_cb.isChecked(),
            "target_size_kb": self.settings_panel.target_size_spin.value(),
            "min_size_mb": self.settings_panel.min_size_spin.value(),
        }
        config_manager.save_custom_preset(name.strip(), description, settings)
        self._load_presets()
        self.settings_panel.preset_combo.setCurrentText(name.strip())
        self.log_panel.append(f"已保存预设：{name.strip()}")

    def _select_input(self) -> None:
        folder = self._choose_directory("选择输入文件夹")
        if folder:
            self.input_panel.input_edit.setText(folder)

    def _select_output(self) -> None:
        folder = self._choose_directory("选择输出文件夹")
        if folder:
            self.input_panel.output_edit.setText(folder)

    def _choose_directory(self, title: str) -> str:
        """使用系统原生目录选择器。"""
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        return QFileDialog.getExistingDirectory(self, title, "", options)

    def _show_about(self) -> None:
        AboutDialog(self).exec_()

    def _collect_sample_image(self) -> Path:
        current_item = self.input_panel.file_list.currentItem()
        if current_item:
            item_path = current_item.data(Qt.UserRole)
            if item_path:
                selected = Path(item_path)
                if selected.exists() and selected.is_file():
                    return selected

        if self._image_files:
            return self._image_files[0]

        input_path = self.input_panel.input_edit.text().strip()
        if not input_path or not Path(input_path).exists():
            raise ValueError("请先选择有效的输入文件夹")
        files = [p for p in Path(input_path).rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}]
        if not files:
            raise ValueError("输入目录中未找到图片文件")
        return files[0]

    def _show_exif(self) -> None:
        try:
            sample = self._collect_sample_image()
            exif_info = get_exif_info(sample)
            exif_raw = exif_info.get("raw", {}) if isinstance(exif_info, dict) else {}
            if isinstance(exif_info, dict):
                if exif_info.get("orientation"):
                    exif_raw.setdefault("Orientation", exif_info["orientation"])
                if exif_info.get("camera"):
                    exif_raw.setdefault("Camera", exif_info["camera"])
                if exif_info.get("date"):
                    exif_raw.setdefault("DateTimeOriginal", exif_info["date"])
                if exif_info.get("gps"):
                    exif_raw.setdefault("GPSInfo", exif_info["gps"])

            with Image.open(sample) as img:
                dimensions = img.size
                mode = img.mode
                fmt = img.format or sample.suffix.lstrip(".").upper()
            image_info = {
                "filename": sample.name,
                "format": fmt,
                "file_size": sample.stat().st_size,
                "dimensions": dimensions,
                "mode": mode,
            }
            ExifDialog(exif_raw, image_info, self).exec_()
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))

    def _schedule_live_preview(self, *_args) -> None:
        if not self.settings_panel.live_preview_cb.isChecked():
            return
        self._preview_timer.start(120)

    def _refresh_live_preview(self, show_errors: bool = False) -> None:
        try:
            sample = self._collect_sample_image()
        except ValueError as exc:
            self.settings_panel.clear_preview(str(exc))
            if show_errors:
                QMessageBox.warning(self, "提示", str(exc))
            return

        try:
            with Image.open(sample) as img:
                if self.settings_panel.auto_rotate_cb.isChecked():
                    img = ImageOps.exif_transpose(img)

                original_img = img.copy()
                original_bytes = sample.stat().st_size

                work_img = img.copy()
                if self.settings_panel.resize_cb.isChecked():
                    max_w = self.settings_panel.max_width_spin.value()
                    max_h = self.settings_panel.max_height_spin.value()
                    ow, oh = work_img.size
                    ratio = 1.0
                    if max_w > 0 and ow > max_w:
                        ratio = min(ratio, max_w / ow)
                    if max_h > 0 and oh > max_h:
                        ratio = min(ratio, max_h / oh)
                    if ratio < 1.0:
                        nw, nh = max(1, int(ow * ratio)), max(1, int(oh * ratio))
                        work_img = work_img.resize((nw, nh), Image.Resampling.LANCZOS)

                output_fmt = self.settings_panel.output_format_value()
                if output_fmt == "original":
                    output_fmt = sample.suffix.lstrip(".").lower()
                if output_fmt == "jpg":
                    output_fmt = "jpeg"

                save_img = work_img.copy()
                save_kwargs = {}
                if output_fmt in ("jpeg", "webp"):
                    save_kwargs["quality"] = self.settings_panel.quality_spin.value()
                if output_fmt == "jpeg":
                    if save_img.mode != "RGB":
                        save_img = save_img.convert("RGB")
                    fmt_name = "JPEG"
                elif output_fmt == "png":
                    fmt_name = "PNG"
                elif output_fmt == "webp":
                    fmt_name = "WEBP"
                    if save_img.mode not in ("RGB", "RGBA"):
                        save_img = save_img.convert("RGB")
                else:
                    fmt_name = "JPEG"
                    if save_img.mode != "RGB":
                        save_img = save_img.convert("RGB")

                buf = BytesIO()
                save_img.save(buf, format=fmt_name, **save_kwargs)
                comp_bytes_data = buf.getvalue()
                compressed_bytes = len(comp_bytes_data)
                compressed_img = Image.open(BytesIO(comp_bytes_data)).convert("RGBA")

                original_pix = self._pil_to_qpixmap(original_img)
                compressed_pix = self._pil_to_qpixmap(compressed_img)
                self.settings_panel.set_preview_images(original_pix, compressed_pix)

                ratio = (original_bytes - compressed_bytes) / original_bytes * 100 if original_bytes > 0 else 0
                self.settings_panel.preview_original_label.setText(f"原始: {format_bytes(original_bytes)}")
                self.settings_panel.preview_compressed_label.setText(f"压缩后: {format_bytes(compressed_bytes)}")
                self.settings_panel.preview_savings_label.setText(f"节省: {ratio:.1f}%")
                if show_errors:
                    self.log_panel.append(f"预览完成: {sample.name}")
        except Exception as exc:
            self.settings_panel.clear_preview("预览生成失败")
            if show_errors:
                QMessageBox.critical(self, "错误", f"预览失败: {exc}")

    def _collect_worker_args(self) -> dict:
        input_dir = self.input_panel.input_edit.text().strip()
        if not input_dir or not Path(input_dir).exists():
            raise ValueError("请选择有效输入目录")
        output_dir = self.input_panel.output_edit.text().strip() or None

        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "quality": self.settings_panel.quality_spin.value(),
            "include_subdirs": self.settings_panel.include_subfolders_cb.isChecked(),
            "min_size_mb": self.settings_panel.min_size_spin.value(),
            "overwrite": output_dir is None,
            "max_width": self.settings_panel.max_width_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "max_height": self.settings_panel.max_height_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "keep_ratio": self.settings_panel.keep_ratio_cb.isChecked(),
            "output_format": self.settings_panel.output_format_value(),
            "smart_mode": self.settings_panel.smart_cb.isChecked(),
            "target_size_kb": self.settings_panel.target_size_spin.value(),
            "rename_pattern": None,
            "keep_exif": self.settings_panel.keep_exif_cb.isChecked(),
            "auto_rotate": self.settings_panel.auto_rotate_cb.isChecked(),
            "incremental": self.settings_panel.incremental_cb.isChecked(),
        }

    def _start_compression(self) -> None:
        if self._is_running:
            return
        try:
            worker_args = self._collect_worker_args()
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return

        self._is_running = True
        self.settings_panel.start_btn.setEnabled(False)
        self.settings_panel.cancel_btn.setEnabled(True)
        self.stats_panel.export_btn.setEnabled(False)
        self.stats_panel.progress_bar.setValue(0)
        self.stats_panel.status_label.setText("准备中")
        self.stats_panel.metrics_label.setText("速度: - | ETA: -")
        self.stats_panel.set_records([])
        self.current_detailed_stats = []
        self.log_panel.log_text.clear()
        self.log_panel.append("开始压缩任务")

        self.thread = QThread(self)
        self.worker = CompressWorker(**worker_args)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.state_changed.connect(self._on_worker_state)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.file_completed.connect(self._on_worker_file_completed)
        self.worker.result.connect(self._on_worker_result)
        self.worker.finished.connect(self._on_worker_finished)
        self.thread.start()

    def _cancel_compression(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.log_panel.append("收到取消请求，正在停止...")

    def _on_worker_state(self, state: str, payload: dict) -> None:
        self.stats_panel.status_label.setText(STATUS_TEXT.get(state, state))
        self.status_bar.showMessage(f"{STATUS_TEXT.get(state, state)} | v{__version__}")
        if state == "Running":
            self.badge_threads.setText(f"线程: {payload.get('workers', '-')}")
            self.badge_files.setText(f"文件: {payload.get('total', 0)}")

    def _on_worker_progress(self, data: dict) -> None:
        percent = int(data.get("percent", 0))
        self.stats_panel.progress_bar.setValue(percent)
        self.stats_panel.status_label.setText(f"处理中 {data.get('current', 0)}/{data.get('total', 0)}")
        rate = data.get("rate", 0.0)
        eta = int(data.get("eta_seconds", 0.0))
        self.stats_panel.metrics_label.setText(f"速度: {rate:.2f} 张/秒 | ETA: {eta}s")
        self.badge_eta.setText(f"ETA: {eta}s")

    def _on_worker_file_completed(self, record: dict) -> None:
        self.log_panel.append(f"{record.get('status')} - {record.get('filename')}")

    def _on_worker_result(self, payload: dict) -> None:
        self.current_detailed_stats = payload.get("detailed_stats", [])
        self.stats_panel.set_records(self.current_detailed_stats)
        self.stats_panel.update_summary(payload)
        self.stats_panel.export_btn.setEnabled(bool(self.current_detailed_stats))
        self.log_panel.append(
            f"结果：成功 {payload.get('processed', 0)}，失败 {payload.get('failed', 0)}，"
            f"节省 {format_bytes(int(payload.get('saved', 0)))}"
        )

    def _on_worker_finished(self, payload: dict) -> None:
        self._is_running = False
        self.settings_panel.start_btn.setEnabled(True)
        self.settings_panel.cancel_btn.setEnabled(False)
        if payload.get("state") == "Done":
            self.stats_panel.progress_bar.setValue(100)
        self.log_panel.append(f"任务结束：{payload.get('state')}")

        try:
            history = config_manager.load_history()
            history.append(
                {
                    "input_path": self.input_panel.input_edit.text().strip(),
                    "output_path": self.input_panel.output_edit.text().strip(),
                    "settings": self._collect_worker_args(),
                }
            )
            config_manager.save_history(history)
            self._load_history()
        except ValueError:
            pass

        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def _export_stats(self) -> None:
        if not self.current_detailed_stats:
            QMessageBox.warning(self, "提示", "当前没有可导出的统计")
            return
        target, _ = QFileDialog.getSaveFileName(
            self,
            "导出压缩统计",
            f"压缩统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)",
        )
        if not target:
            return
        try:
            with open(target, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["序号", "文件名", "状态", "原始大小", "压缩后大小", "节省比例"])
                for rec in self.current_detailed_stats:
                    orig = int(rec.get("original_size", 0))
                    comp = int(rec.get("compressed_size", 0))
                    ratio = (orig - comp) / orig * 100 if orig > 0 else 0
                    writer.writerow(
                        [
                            rec.get("index", 0),
                            rec.get("filename", ""),
                            rec.get("status", ""),
                            format_bytes(orig),
                            format_bytes(comp),
                            f"{ratio:.1f}%",
                        ]
                    )
            self.log_panel.append(f"统计已导出: {target}")
            QMessageBox.information(self, "成功", "统计导出完成")
        except Exception as exc:
            QMessageBox.critical(self, "错误", f"导出失败: {exc}")
