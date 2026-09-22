"""
主窗口模块 - Dock 化 OpenShot 风格。
"""

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PIL import Image
from PyQt5.QtCore import QThread, Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QShortcut,
    QStatusBar,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
)

from src.config import APP_NAME, IMAGE_EXTENSIONS, __version__, config_manager
from src.core.compressor import get_exif_info
from src.core.worker import CompressWorker
from src.utils import format_bytes, setup_logging
from src.widgets.about_dialog import AboutDialog
from src.widgets.exif_dialog import ExifDialog
from src.widgets.file_scanner import FileScanController
from src.widgets.history_dialog import HistoryDialog
from src.widgets.panels import InputPanel, LogPanel, SettingsPanel, StatsPanel
from src.widgets.theme import DEFAULT_THEME, build_stylesheet, build_palette_from_tokens


STATUS_TEXT = {
    "Idle": "就绪",
    "Validating": "校验参数中",
    "Scanning": "扫描文件中",
    "Running": "处理中",
    "Finalizing": "汇总结果中",
    "Done": "已完成",
    "Cancelled": "已取消",
    "Canceling": "取消中",
    "Paused": "已暂停",
    "Error": "错误",
}


class MainWindow(QMainWindow):
    """图片压缩工具主窗口。"""

    job_progress = pyqtSignal(dict)
    job_finished = pyqtSignal(dict)
    job_state = pyqtSignal(str, dict)
    input_staged = pyqtSignal(str)
    file_count_ready = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.logger = setup_logging()
        self._is_running = False
        self._is_paused = False
        self.worker = None
        self.thread = None
        self.current_detailed_stats: List[Dict] = []
        self.current_view_name = "Simple"
        self._image_files: List[Path] = []
        self._selected_image_path: Path = None
        self._task_queue: List[dict] = []
        self._last_worker_args = None
        self._scan_generation = 0
        self._file_scanner = FileScanController(self)
        self._file_scanner.finished.connect(self._on_scan_finished)

        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)

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
        self._apply_theme()

    def _setup_menu_and_toolbars(self) -> None:
        menu = self.menuBar()

        edit_menu = menu.addMenu("编辑")
        self.undo_action = QAction("撤销上次压缩", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self._undo_last_compression)
        edit_menu.addAction(self.undo_action)

        view_menu = menu.addMenu("视图")
        view_group = QActionGroup(self)
        view_group.setExclusive(True)
        self.simple_view_action = QAction("简洁视图", self)
        self.simple_view_action.setCheckable(True)
        self.simple_view_action.setChecked(True)
        self.simple_view_action.triggered.connect(lambda: self._apply_view("Simple"))
        self.advanced_view_action = QAction("高级视图", self)
        self.advanced_view_action.setCheckable(True)
        self.advanced_view_action.triggered.connect(lambda: self._apply_view("Advanced"))
        view_group.addAction(self.simple_view_action)
        view_group.addAction(self.advanced_view_action)
        view_menu.addAction(self.simple_view_action)
        view_menu.addAction(self.advanced_view_action)

        help_menu = menu.addMenu("帮助")
        history_action = QAction("历史任务", self)
        history_action.triggered.connect(self._show_task_history)
        help_menu.addAction(history_action)
        help_menu.addSeparator()
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        self.context_toolbar = QToolBar("上下文栏", self)
        self.context_toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.context_toolbar)

        self.badge_files = QLabel("  文件: 0  ")
        self.badge_files.setObjectName("badge")
        self.badge_threads = QLabel("  线程: -  ")
        self.badge_threads.setObjectName("badge")
        self.badge_eta = QLabel("  ETA: -  ")
        self.badge_eta.setObjectName("badge")
        self.context_toolbar.addWidget(self.badge_files)
        self.context_toolbar.addWidget(self.badge_threads)
        self.context_toolbar.addWidget(self.badge_eta)

        self._setup_shortcuts()

    def _setup_layout(self) -> None:
        self.input_panel = InputPanel(self)
        self.settings_panel = SettingsPanel(self)
        self.stats_panel = StatsPanel(self)
        self.log_panel = LogPanel(self)

        self.main_splitter = QSplitter(Qt.Horizontal, self)
        self.main_splitter.addWidget(self.input_panel)
        self.main_splitter.addWidget(self.settings_panel)
        self.main_splitter.addWidget(self.stats_panel)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(3)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 1)

        self.input_panel.setMinimumWidth(260)
        self.input_panel.setMaximumWidth(400)

        self.vertical_splitter = QSplitter(Qt.Vertical, self)
        self.vertical_splitter.addWidget(self.main_splitter)
        self.vertical_splitter.addWidget(self.log_panel)
        self.vertical_splitter.setChildrenCollapsible(False)
        self.vertical_splitter.setHandleWidth(3)
        self.vertical_splitter.setStretchFactor(0, 1)
        self.vertical_splitter.setStretchFactor(1, 0)

        container = QWidget(self)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(6)
        container_layout.addWidget(self.vertical_splitter)
        self.setCentralWidget(container)
        self.main_splitter.setSizes([280, 400, 420])
        self.vertical_splitter.setSizes([560, 120])

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"就绪 | v{__version__}")
        self.status_signature_label = QLabel("成都一禾视觉专用")
        self.status_signature_label.setObjectName("signatureLabel")
        self.status_bar.addPermanentWidget(self.status_signature_label)

    def _connect_signals(self) -> None:
        self.input_panel.browse_input_btn.clicked.connect(self._select_input)
        self.input_panel.browse_output_btn.clicked.connect(self._select_output)
        self.input_panel.input_edit.textChanged.connect(self._refresh_file_list)
        self.input_panel.history_combo.currentTextChanged.connect(self._on_history_selected)
        self.input_panel.file_list.currentItemChanged.connect(self._on_file_selected)
        self.input_panel.file_list.folder_dropped.connect(self.stage_input)
        self.input_panel.enqueue_btn.clicked.connect(self._enqueue_task)
        self.input_panel.clear_queue_btn.clicked.connect(self._clear_queue)

        self.input_panel.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.input_panel.file_list.customContextMenuRequested.connect(self._show_file_context_menu)

        self.settings_panel.include_subfolders_cb.toggled.connect(self._refresh_file_list)
        self.settings_panel.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        self.settings_panel.save_preset_btn.clicked.connect(self._save_preset)
        self.settings_panel.exif_btn.clicked.connect(self._show_exif)
        self.settings_panel.convert_only_btn.clicked.connect(self._start_convert_only)
        self.settings_panel.start_btn.clicked.connect(self._start_compression)
        self.settings_panel.pause_btn.clicked.connect(self._toggle_pause)
        self.settings_panel.cancel_btn.clicked.connect(self._cancel_compression)

        self.stats_panel.export_btn.clicked.connect(self._export_stats)

    # ========== Theme / View ==========

    def _apply_theme(self) -> None:
        tokens = DEFAULT_THEME
        app = QApplication.instance()
        if app is not None:
            app.setPalette(build_palette_from_tokens(tokens))
        self.setStyleSheet(build_stylesheet(tokens))

    def _apply_view(self, view_name: str) -> None:
        self.current_view_name = view_name
        self.simple_view_action.setChecked(view_name == "Simple")
        self.advanced_view_action.setChecked(view_name == "Advanced")
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
            "从 Finder 把文件夹拖到屏幕顶部菜单栏附近即可压缩。\n"
            "需要改参数时，再打开主窗口。",
        )
        settings["tutorial_seen"] = True
        config_manager.save_ui_settings(settings)

    def _load_ui_settings(self) -> None:
        settings = config_manager.load_ui_settings()
        view_name = settings.get("view", "Simple")
        self._apply_view(view_name)

    def _save_ui_settings(self) -> None:
        settings = config_manager.load_ui_settings()
        settings["view"] = self.current_view_name
        config_manager.save_ui_settings(settings)

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def drop_auto_start(self) -> bool:
        return bool(config_manager.load_ui_settings().get("drop_auto_start", False))

    def set_drop_auto_start(self, enabled: bool) -> None:
        settings = config_manager.load_ui_settings()
        settings["drop_auto_start"] = bool(enabled)
        config_manager.save_ui_settings(settings)

    def should_show_on_startup(self) -> bool:
        settings = config_manager.load_ui_settings()
        if not settings.get("tutorial_seen"):
            return True
        return bool(settings.get("show_main_on_startup", True))

    def show_from_tray(self) -> None:
        settings = config_manager.load_ui_settings()
        settings["show_main_on_startup"] = True
        config_manager.save_ui_settings(settings)
        self.show()
        self.raise_()
        self.activateWindow()

    def is_overwrite(self) -> bool:
        return not self.input_panel.output_edit.text().strip()

    def settings_summary(self) -> str:
        fmt = self.settings_panel.output_format_value()
        fmt_text = "原格式" if fmt == "original" else fmt.upper()
        mode = "覆盖" if self.is_overwrite() else "输出到指定目录"
        return f"质量 {self.settings_panel.quality_spin.value()}% · {fmt_text} · {mode}"

    def stage_input(self, path: str) -> None:
        target = Path(path)
        if target.is_file():
            target = target.parent
        if not target.exists():
            return
        text = str(target)
        if self.input_panel.input_edit.text().strip() == text:
            self._refresh_file_list()
        else:
            self.input_panel.input_edit.setText(text)
        self.input_staged.emit(text)

    def closeEvent(self, event) -> None:
        settings = config_manager.load_ui_settings()
        settings["show_main_on_startup"] = False
        config_manager.save_ui_settings(settings)
        self.hide()
        event.ignore()

    # ========== History / Presets ==========

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
        format_map = {"original": 0, "jpg": 1, "png": 2, "webp": 3, "avif": 4, "heif": 5}
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

    # ========== File List ==========

    def _refresh_file_list(self) -> None:
        self.input_panel.file_list.clear()
        self._image_files = []
        self._selected_image_path = None
        input_path = self.input_panel.input_edit.text().strip()
        if not input_path or not Path(input_path).exists():
            self.input_panel.file_info_label.setText("0 个文件")
            self.badge_files.setText("文件: 0")
            self.file_count_ready.emit(0)
            return

        self._scan_generation += 1
        self.input_panel.file_info_label.setText("扫描中…")
        self.badge_files.setText("文件: …")
        self._file_scanner.start(
            input_path,
            self.settings_panel.include_subfolders_cb.isChecked(),
            self._scan_generation,
        )

    def _on_scan_finished(self, generation: int, files) -> None:
        if generation != self._scan_generation:
            return
        self._image_files = list(files)
        input_path = self.input_panel.input_edit.text().strip()
        self._populate_file_list(Path(input_path) if input_path else None)
        self.file_count_ready.emit(len(self._image_files))

    def _populate_file_list(self, base_path=None) -> None:
        self.input_panel.file_list.clear()
        for file_path in self._image_files[:200]:
            if base_path and self.settings_panel.include_subfolders_cb.isChecked():
                try:
                    label = str(file_path.relative_to(base_path))
                except ValueError:
                    label = file_path.name
            else:
                label = file_path.name
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, str(file_path))
            self.input_panel.file_list.addItem(item)
        total = len(self._image_files)
        suffix = "（仅显示前200）" if total > 200 else ""
        self.input_panel.file_info_label.setText(f"{total} 个文件{suffix}")
        self.badge_files.setText(f"文件: {total}")
        if self.input_panel.file_list.count() > 0:
            self.input_panel.file_list.setCurrentRow(0)

    def _on_file_selected(self, current_item, _previous_item) -> None:
        self._selected_image_path = None
        if current_item:
            item_path = current_item.data(Qt.UserRole)
            if item_path:
                selected = Path(item_path)
                if selected.exists() and selected.is_file():
                    self._selected_image_path = selected

    # ========== Context Menu ==========

    def _show_file_context_menu(self, pos) -> None:
        item = self.input_panel.file_list.itemAt(pos)
        if not item:
            return
        file_path = Path(item.data(Qt.UserRole))

        menu = QMenu(self)
        exif_action = menu.addAction("查看 EXIF")
        menu.addSeparator()
        finder_action = menu.addAction("在 Finder 中显示")
        menu.addSeparator()
        remove_action = menu.addAction("从列表移除")

        chosen = menu.exec_(self.input_panel.file_list.viewport().mapToGlobal(pos))
        if chosen == exif_action:
            self._selected_image_path = file_path
            self._show_exif()
        elif chosen == finder_action:
            if sys.platform == "darwin":
                subprocess.run(["open", "-R", str(file_path)], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(file_path)], check=False)
        elif chosen == remove_action:
            row = self.input_panel.file_list.row(item)
            self.input_panel.file_list.takeItem(row)
            self._image_files = [f for f in self._image_files if str(f) != str(file_path)]
            total = len(self._image_files)
            self.input_panel.file_info_label.setText(f"{total} 个文件")
            self.badge_files.setText(f"文件: {total}")

    # ========== Task Queue ==========

    def _enqueue_task(self) -> None:
        try:
            args = self._collect_worker_args()
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return
        self._task_queue.append(args)
        label = f"{args['input_dir']} → {args.get('output_dir') or '覆盖'}"
        self.input_panel.queue_list.addItem(label)
        self.log_panel.append(f"任务已加入队列（共 {len(self._task_queue)} 个）")

    def _clear_queue(self) -> None:
        self._task_queue.clear()
        self.input_panel.queue_list.clear()

    def _process_next_queued(self) -> None:
        if not self._task_queue:
            return
        args = self._task_queue.pop(0)
        self.input_panel.queue_list.takeItem(0)
        self.input_panel.input_edit.setText(args["input_dir"])
        self.input_panel.output_edit.setText(args.get("output_dir") or "")
        self._run_worker(args, f"队列任务：{args['input_dir']}")

    # ========== Input / Output ==========

    def _select_input(self) -> None:
        folder = self._choose_directory("选择输入文件夹")
        if folder:
            self.input_panel.input_edit.setText(folder)

    def _select_output(self) -> None:
        folder = self._choose_directory("选择输出文件夹")
        if folder:
            self.input_panel.output_edit.setText(folder)

    def _choose_directory(self, title: str) -> str:
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        return QFileDialog.getExistingDirectory(self, title, "", options)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Return"), self, self._start_compression)
        QShortcut(QKeySequence("Ctrl+O"), self, self._select_input)
        QShortcut(QKeySequence("Ctrl+E"), self, self._export_stats)
        QShortcut(QKeySequence("Escape"), self, self._cancel_compression)

    # ========== Dialogs ==========

    def _show_about(self) -> None:
        AboutDialog(DEFAULT_THEME, self).exec_()

    def _show_task_history(self) -> None:
        dlg = HistoryDialog(DEFAULT_THEME, self)
        dlg.exec_()
        if dlg.selected_settings:
            self._apply_settings_dict(dlg.selected_settings)

    def _apply_settings_dict(self, settings: dict) -> None:
        self.settings_panel.quality_spin.setValue(int(settings.get("quality", 90)))
        format_map = {"original": 0, "jpg": 1, "png": 2, "webp": 3, "avif": 4, "heif": 5}
        self.settings_panel.format_combo.setCurrentIndex(
            format_map.get(settings.get("output_format", "original"), 0)
        )
        self.settings_panel.min_size_spin.setValue(float(settings.get("min_size_mb", 0.1)))
        max_w = int(settings.get("max_width", 0))
        max_h = int(settings.get("max_height", 0))
        self.settings_panel.resize_cb.setChecked(max_w > 0 or max_h > 0)
        self.settings_panel.max_width_spin.setValue(max_w)
        self.settings_panel.max_height_spin.setValue(max_h)
        self.settings_panel.keep_ratio_cb.setChecked(bool(settings.get("keep_ratio", True)))
        self.settings_panel.smart_cb.setChecked(bool(settings.get("smart_mode", False)))
        self.settings_panel.target_size_spin.setValue(int(settings.get("target_size_kb", 200)))
        self.log_panel.append("已从历史记录加载参数")

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
        include_subdirs = self.settings_panel.include_subfolders_cb.isChecked()
        path_obj = Path(input_path)
        files_iter = path_obj.rglob("*") if include_subdirs else path_obj.glob("*")
        files = [p for p in files_iter if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
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
            ExifDialog(exif_raw, image_info, DEFAULT_THEME, self).exec_()
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))

    # ========== Compression ==========

    def _collect_worker_args(self) -> dict:
        input_dir = self.input_panel.input_edit.text().strip()
        if not input_dir or not Path(input_dir).exists():
            raise ValueError("请选择有效输入目录")
        output_dir = self.input_panel.output_edit.text().strip() or None
        overwrite = output_dir is None

        rename_error = self.settings_panel.validate_rename()
        if rename_error:
            raise ValueError(rename_error)
        rename_pattern = self.settings_panel.rename_pattern_value()

        backup_set = None
        if overwrite:
            backup_set = config_manager.create_backup_set()

        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "quality": self.settings_panel.quality_spin.value(),
            "include_subdirs": self.settings_panel.include_subfolders_cb.isChecked(),
            "min_size_mb": self.settings_panel.min_size_spin.value(),
            "overwrite": overwrite,
            "max_width": self.settings_panel.max_width_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "max_height": self.settings_panel.max_height_spin.value() if self.settings_panel.resize_cb.isChecked() else 0,
            "keep_ratio": self.settings_panel.keep_ratio_cb.isChecked(),
            "output_format": self.settings_panel.output_format_value(),
            "smart_mode": self.settings_panel.smart_cb.isChecked(),
            "target_size_kb": self.settings_panel.target_size_spin.value(),
            "rename_pattern": rename_pattern,
            "keep_exif": self.settings_panel.keep_exif_cb.isChecked(),
            "auto_rotate": self.settings_panel.auto_rotate_cb.isChecked(),
            "incremental": self.settings_panel.incremental_cb.isChecked(),
            "max_retries": self.settings_panel.retry_spin.value(),
            "backup_set": backup_set,
        }

    def _start_convert_only(self) -> None:
        if self._is_running:
            return
        output_format = self.settings_panel.output_format_value()
        if output_format == "original":
            QMessageBox.warning(self, "提示", "请先选择要转换的目标格式（当前为「保持原格式」）")
            return
        try:
            worker_args = self._collect_worker_args()
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return

        worker_args["quality"] = 100
        worker_args["max_width"] = 0
        worker_args["max_height"] = 0
        worker_args["smart_mode"] = False
        worker_args["target_size_kb"] = 0
        worker_args["min_size_mb"] = 0
        worker_args["incremental"] = False

        self._run_worker(worker_args, "开始格式转换任务")

    def start_compression(self) -> None:
        QTimer.singleShot(0, self._start_compression)

    def _warn(self, message: str) -> None:
        parent = self if self.isVisible() else None
        QMessageBox.warning(parent, "提示", message)

    def _start_compression(self) -> None:
        if self._is_running:
            return
        try:
            worker_args = self._collect_worker_args()
            self._run_worker(worker_args, "开始压缩任务")
        except ValueError as exc:
            self._warn(str(exc))
        except Exception as exc:
            self.logger.exception("启动压缩失败")
            self._is_running = False
            self._warn(f"启动压缩失败：{exc}")

    def _run_worker(self, worker_args: dict, log_message: str) -> None:
        self._is_running = True
        self._is_paused = False
        self._last_worker_args = worker_args
        self.settings_panel.start_btn.setEnabled(False)
        self.settings_panel.convert_only_btn.setEnabled(False)
        self.settings_panel.pause_btn.setEnabled(True)
        self.settings_panel.pause_btn.setText("暂停")
        self.settings_panel.cancel_btn.setEnabled(True)
        self.stats_panel.export_btn.setEnabled(False)
        self.stats_panel.progress_bar.setValue(0)
        self.stats_panel.status_label.setText("准备中")
        self.stats_panel.metrics_label.setText("速度: - | ETA: -")
        self.stats_panel.set_records([])
        self.current_detailed_stats = []
        self.log_panel.log_text.clear()
        self.log_panel.append(log_message)

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

    def _toggle_pause(self) -> None:
        if not self.worker:
            return
        if self._is_paused:
            self.worker.resume()
            self._is_paused = False
            self.settings_panel.pause_btn.setText("暂停")
        else:
            self.worker.pause()
            self._is_paused = True
            self.settings_panel.pause_btn.setText("继续")

    def cancel_compression(self) -> None:
        self._cancel_compression()

    def _cancel_compression(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.log_panel.append("收到取消请求，正在停止...")

    def shutdown_jobs(self) -> None:
        """退出前停掉压缩线程，避免 QThread 在运行中被销毁导致进程 abort。"""
        self._task_queue.clear()
        if self.worker:
            self.worker.cancel()
        if self.thread:
            self.thread.quit()
            self.thread.wait(5000)

    def _on_worker_state(self, state: str, payload: dict) -> None:
        self.stats_panel.status_label.setText(STATUS_TEXT.get(state, state))
        self.status_bar.showMessage(f"{STATUS_TEXT.get(state, state)} | v{__version__}")
        if state == "Running":
            self.badge_threads.setText(f"线程: {payload.get('workers', '-')}")
            self.badge_files.setText(f"文件: {payload.get('total', 0)}")
        self.job_state.emit(state, payload)

    def _on_worker_progress(self, data: dict) -> None:
        percent = int(data.get("percent", 0))
        self.stats_panel.progress_bar.setValue(percent)
        self.stats_panel.status_label.setText(f"处理中 {data.get('current', 0)}/{data.get('total', 0)}")
        rate = data.get("rate", 0.0)
        eta = int(data.get("eta_seconds", 0.0))
        self.stats_panel.metrics_label.setText(f"速度: {rate:.2f} 张/秒 | ETA: {eta}s")
        self.badge_eta.setText(f"ETA: {eta}s")
        self.job_progress.emit(data)

    def _on_worker_file_completed(self, record: dict) -> None:
        retry = record.get("retry_count", 0)
        suffix = f" (重试{retry}次)" if retry > 0 else ""
        self.log_panel.append(f"{record.get('status')} - {record.get('filename')}{suffix}")

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
        self._is_paused = False
        self.settings_panel.start_btn.setEnabled(True)
        self.settings_panel.convert_only_btn.setEnabled(True)
        self.settings_panel.pause_btn.setEnabled(False)
        self.settings_panel.pause_btn.setText("暂停")
        self.settings_panel.cancel_btn.setEnabled(False)
        if payload.get("state") == "Done":
            self.stats_panel.progress_bar.setValue(100)
        self.log_panel.append(f"任务结束：{payload.get('state')}")

        self._save_task_record(payload)

        try:
            history = config_manager.load_history()
            history.append(
                {
                    "input_path": self.input_panel.input_edit.text().strip(),
                    "output_path": self.input_panel.output_edit.text().strip(),
                    "settings": self._last_worker_args or {},
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

        if payload.get("state") == "Done" and not payload.get("canceled"):
            self._show_completion_dialog(payload)

        if self._task_queue:
            self._process_next_queued()
        self.job_finished.emit(payload)

    def _save_task_record(self, payload: dict) -> None:
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_path": self.input_panel.input_edit.text().strip(),
            "output_path": self.input_panel.output_edit.text().strip(),
            "total_files": payload.get("total_files", 0),
            "processed": payload.get("processed", 0),
            "failed": payload.get("failed", 0),
            "skipped": payload.get("skipped", 0),
            "saved": payload.get("saved", 0),
            "elapsed_seconds": payload.get("elapsed_seconds", 0),
            "state": payload.get("state", ""),
            "settings": self._last_worker_args or {},
        }
        config_manager.save_task_record(record)

    def _show_completion_dialog(self, payload: dict) -> None:
        QApplication.beep()

        output_dir = self.input_panel.output_edit.text().strip()
        if not output_dir:
            output_dir = self.input_panel.input_edit.text().strip()

        processed = payload.get("processed", 0)
        saved = format_bytes(int(payload.get("saved", 0)))
        elapsed = payload.get("elapsed_seconds", 0)

        if not self.isVisible():
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("任务完成")
        msg.setText(f"成功处理 {processed} 个文件，节省 {saved}，耗时 {elapsed:.1f}s")
        msg.setIcon(QMessageBox.Information)
        open_btn = msg.addButton("打开输出文件夹", QMessageBox.ActionRole)
        msg.addButton("确定", QMessageBox.AcceptRole)
        msg.exec_()

        if msg.clickedButton() == open_btn and output_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))

    # ========== Undo ==========

    def _undo_last_compression(self) -> None:
        backup_set = config_manager.get_latest_backup()
        if not backup_set:
            QMessageBox.information(self, "提示", "没有可撤销的压缩操作")
            return

        reply = QMessageBox.question(
            self, "确认撤销",
            f"将从备份还原文件：\n{backup_set.name}\n\n确定撤销？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        restored = config_manager.restore_backup(backup_set)
        if restored:
            self.log_panel.append(f"已撤销 {len(restored)} 个文件")
            QMessageBox.information(self, "撤销完成", f"已还原 {len(restored)} 个文件")
            self._refresh_file_list()
        else:
            QMessageBox.warning(self, "撤销失败", "备份数据异常，未能还原")

    # ========== Export ==========

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
