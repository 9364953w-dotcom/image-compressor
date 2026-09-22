"""菜单栏图标与投放架控制器。"""

import sys
from pathlib import Path

from PyQt5.QtCore import QObject, QRect, QTimer
from PyQt5.QtGui import QColor, QCursor, QIcon, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon

from src.config import APP_NAME
from src.utils import format_bytes
from src.widgets.drag_proximity import DragProximityWatcher
from src.widgets.drop_sensor import DropSensor
from src.widgets.drop_shelf import DropShelf
from src.widgets.theme import DEFAULT_THEME
from src.widgets.window_level import elevate_window


def _app_icon() -> QIcon:
    from src.widgets.splash_screen import _resource_dir

    for name in ("icon.icns", "icon.png"):
        path = _resource_dir() / name
        if path.exists():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(DEFAULT_THEME.accent))
    return QIcon(pixmap)


def _menu_bar_icon() -> QIcon:
    """黑色模板图。macOS 会在浅色菜单栏里显示为黑，在深色菜单栏里显示为白。"""
    from src.widgets.splash_screen import _resource_dir

    path = _resource_dir() / "menu_icon.png"
    if path.exists():
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            pixmap.setDevicePixelRatio(2.0)
            icon = QIcon(pixmap)
            if hasattr(icon, "setIsMask"):
                icon.setIsMask(True)
            return icon
    return _app_icon()


class TrayController(QObject):
    """托盘图标 +（macOS）顶部感应条 + 投放架。"""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.shelf = DropShelf()
        self.sensor = None

        self.shelf.start_requested.connect(self.window.start_compression)
        self.shelf.cancel_requested.connect(self._on_shelf_cancel)
        self.shelf.hover_changed.connect(self._on_shelf_hover)
        self.shelf.folder_dropped.connect(self._on_folder_dropped)

        if sys.platform == "darwin":
            self.sensor = DropSensor()
            self.sensor.folder_dropped.connect(self._on_folder_dropped)
            self.sensor.hide()

        self.tray = QSystemTrayIcon(_menu_bar_icon(), self)
        self.tray.setToolTip(APP_NAME)
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        self._proximity = DragProximityWatcher(self)
        self._proximity.drag_near_top.connect(self._on_drag_near)
        self._proximity.drag_left_top.connect(self._on_sensor_left)
        self._anchor_timer = QTimer(self)
        self._anchor_timer.setInterval(500)
        self._anchor_timer.timeout.connect(self._refresh_anchor)
        self._anchor_timer.start()
        QTimer.singleShot(300, self._refresh_anchor)

        self.window.job_progress.connect(self._on_progress)
        self.window.job_finished.connect(self._on_finished)
        self.window.job_state.connect(self._on_state)
        self.window.input_staged.connect(self._on_input_staged)
        self.window.file_count_ready.connect(self.shelf.set_file_count)

        self._hovering = False
        self._last_progress = (0, 0, 0)

    def _refresh_anchor(self) -> None:
        geo = self.tray.geometry()
        if geo.isValid() and geo.width() > 0:
            self._proximity.set_anchor(geo)
        else:
            self._proximity.set_anchor(QRect())

    def _anchor_rect(self) -> QRect:
        geo = self.tray.geometry()
        if geo.isValid() and geo.width() > 0:
            return geo
        return QRect()

    def _drop_origin(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return 80, 40
        avail = screen.availableGeometry()
        tray_geo = self._anchor_rect()
        if tray_geo.isValid():
            x = tray_geo.center().x()
            y = max(avail.y() + 4, tray_geo.y() + tray_geo.height() + 4)
        else:
            x = QCursor.pos().x()
            y = avail.y() + 4
        return x, y, avail

    def _position_popups(self) -> None:
        origin_x, origin_y, avail = self._drop_origin()
        if self.sensor is not None:
            sx = origin_x - self.sensor.width() // 2
            sx = max(avail.x() + 8, min(sx, avail.right() - self.sensor.width() - 8))
            self.sensor.reposition(sx, origin_y)
            elevate_window(self.sensor)
        self.shelf.adjustSize()
        y = origin_y
        if self.sensor is not None and self.sensor.isVisible():
            y = origin_y + self.sensor.height() + 6
        sx = origin_x - self.shelf.width() // 2
        sx = max(avail.x() + 8, min(sx, avail.right() - self.shelf.width() - 8))
        self.shelf.move(sx, y)

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        open_action = QAction("打开主窗口", menu)
        open_action.triggered.connect(self.window.show_from_tray)
        menu.addAction(open_action)

        self.auto_start_action = QAction("拖入后自动开始", menu)
        self.auto_start_action.setCheckable(True)
        self.auto_start_action.setChecked(self.window.drop_auto_start)
        self.auto_start_action.toggled.connect(self.window.set_drop_auto_start)
        menu.addAction(self.auto_start_action)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        return menu

    def _on_activated(self, reason) -> None:
        if reason not in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            return
        self._refresh_anchor()
        if self.window.is_running:
            current, total, percent = self._last_progress
            self.shelf.set_running(current, total, percent)
            self._position_popups()
            self.shelf.reveal()
            return
        if self.shelf.is_pinned():
            self._position_popups()
            self.shelf.show()
            self.shelf.raise_()
            return
        self.window.show_from_tray()

    def _on_drag_near(self) -> None:
        if self.sensor is None:
            return
        self._refresh_anchor()
        self.sensor.show()
        self._position_popups()
        elevate_window(self.sensor)
        self.sensor.raise_()

    def _on_sensor_left(self) -> None:
        QTimer.singleShot(180, self._hide_sensor_after_drag)

    def _hide_sensor_after_drag(self) -> None:
        if self._proximity.is_dragging:
            return
        if self.sensor is not None:
            self.sensor.hide()

    def _on_shelf_hover(self, hovering: bool) -> None:
        self._hovering = hovering
        if hovering:
            self.shelf.cancel_hide()
        else:
            self.shelf.schedule_hide()

    def _on_folder_dropped(self, path: str) -> None:
        self.window.stage_input(path)

    def _on_input_staged(self, path: str) -> None:
        folder = Path(path).name or path
        if self.sensor is not None:
            self.sensor.hide()
        self.shelf.set_staged(folder, self.window.settings_summary(), self.window.is_overwrite())
        self._position_popups()
        if self.window.drop_auto_start:
            self.window.start_compression()

    def _on_shelf_cancel(self) -> None:
        if self.window.is_running:
            self.window.cancel_compression()

    def _on_state(self, state: str, payload: dict) -> None:
        if state == "Running":
            if self.sensor is not None:
                self.sensor.hide()
            total = int(payload.get("total", 0))
            self._last_progress = (0, total, 0)
            self.shelf.hide()
            self.tray.setToolTip(f"{APP_NAME} · 处理中 0/{total}")

    def _on_progress(self, data: dict) -> None:
        current = int(data.get("current", 0))
        total = int(data.get("total", 0))
        percent = int(data.get("percent", 0))
        self._last_progress = (current, total, percent)
        if self.shelf.isVisible():
            self.shelf.set_running(current, total, percent)
        self.tray.setToolTip(f"{APP_NAME} · {current}/{total} · {percent}%")

    def _on_finished(self, payload: dict) -> None:
        if payload.get("canceled") or payload.get("state") == "Cancelled":
            self.shelf.reset_and_hide()
            self.tray.setToolTip(APP_NAME)
            return
        if payload.get("state") == "Error":
            self.shelf.reset_and_hide()
            self.tray.setToolTip(APP_NAME)
            return
        self.tray.setToolTip(APP_NAME)
        if self.window.isVisible():
            self.shelf.hide()
            return
        processed = int(payload.get("processed", 0))
        saved = format_bytes(int(payload.get("saved", 0)))
        self.shelf.set_done(processed, saved)
        self._position_popups()
        self.shelf.reveal()

    def cleanup(self) -> None:
        if self.sensor is not None:
            self.sensor.close()
        self.shelf.close()
        self.tray.hide()
