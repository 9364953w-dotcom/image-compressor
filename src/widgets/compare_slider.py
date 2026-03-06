"""
Before/After 滑块对比控件，支持缩放和平移。
"""

from PyQt5.QtCore import Qt, QRect, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QFont, QWheelEvent
from PyQt5.QtWidgets import QWidget


class CompareSlider(QWidget):
    """左右滑块对比原图与压缩图，支持缩放平移。"""

    HANDLE_WIDTH = 3
    HANDLE_HIT_WIDTH = 12
    MIN_ZOOM = 0.05
    MAX_ZOOM = 8.0
    ZOOM_STEP = 1.15

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original = None
        self._compressed = None
        self._split_ratio = 0.5
        self._dragging_split = False
        self._panning = False
        self._pan_start = QPointF()
        self._placeholder = "请选择输入目录后查看预览"

        self._zoom = 0.0  # 0 means fit-to-view
        self._offset = QPointF(0, 0)

        self.setMouseTracking(True)
        self.setMinimumSize(60, 60)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_images(self, original, compressed) -> None:
        self._original = original
        self._compressed = compressed
        if original and not original.isNull():
            self._split_ratio = 0.5
        self._zoom = 0.0
        self._offset = QPointF(0, 0)
        self.update()

    def clear(self, message: str = "") -> None:
        self._original = None
        self._compressed = None
        self._placeholder = message
        self._zoom = 0.0
        self._offset = QPointF(0, 0)
        self.update()

    def zoom_fit(self) -> None:
        self._zoom = 0.0
        self._offset = QPointF(0, 0)
        self.update()

    def zoom_100(self) -> None:
        if not self._compressed or self._compressed.isNull():
            return
        self._zoom = 1.0
        self._offset = QPointF(0, 0)
        self.update()

    def _fit_scale(self) -> float:
        if not self._compressed or self._compressed.isNull():
            return 1.0
        pw, ph = self._compressed.width(), self._compressed.height()
        vw, vh = self.width(), self.height()
        if pw == 0 or ph == 0:
            return 1.0
        return min(vw / pw, vh / ph)

    def _effective_zoom(self) -> float:
        if self._zoom <= 0:
            return self._fit_scale()
        return self._zoom

    def _image_rect(self) -> QRectF:
        """缩放+平移后图片在控件坐标系中的矩形。"""
        if not self._compressed or self._compressed.isNull():
            return QRectF()
        pw, ph = self._compressed.width(), self._compressed.height()
        z = self._effective_zoom()
        dw, dh = pw * z, ph * z
        cx = self.width() / 2 + self._offset.x()
        cy = self.height() / 2 + self._offset.y()
        return QRectF(cx - dw / 2, cy - dh / 2, dw, dh)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if not self._compressed or self._compressed.isNull():
            painter.setPen(QColor(160, 160, 160))
            painter.drawText(self.rect(), Qt.AlignCenter, self._placeholder)
            return

        ir = self._image_rect()
        dr = ir.toAlignedRect()
        split_x = int(ir.x() + ir.width() * self._split_ratio)

        if self._original and not self._original.isNull():
            left_clip = QRect(dr.x(), dr.y(), split_x - dr.x(), dr.height())
            painter.setClipRect(left_clip)
            painter.drawPixmap(dr, self._original)

        right_clip = QRect(split_x, dr.y(), dr.right() - split_x + 1, dr.height())
        painter.setClipRect(right_clip)
        painter.drawPixmap(dr, self._compressed)

        painter.setClipping(False)

        pen = QPen(QColor(255, 255, 255, 200), self.HANDLE_WIDTH)
        painter.setPen(pen)
        vis_top = max(dr.y(), 0)
        vis_bot = min(dr.bottom(), self.height())
        painter.drawLine(split_x, vis_top, split_x, vis_bot)

        handle_h = min(30, max(10, (vis_bot - vis_top) // 3))
        cy = (vis_top + vis_bot) // 2
        handle_rect = QRect(split_x - 8, cy - handle_h // 2, 16, handle_h)
        painter.setBrush(QColor(42, 130, 218, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(handle_rect, 4, 4)

        painter.setPen(QColor(255, 255, 255, 220))
        for dy in (-4, 0, 4):
            painter.drawLine(split_x - 3, cy + dy, split_x + 3, cy + dy)

        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 180))
        lx = max(dr.x() + 6, 4)
        ly = max(dr.y() + 16, 16)
        if self._original and not self._original.isNull():
            painter.drawText(lx, ly, "原图")
        rx = min(dr.right() - 36, self.width() - 40)
        painter.drawText(rx, ly, "压缩后")

        zoom_pct = int(self._effective_zoom() * 100)
        zoom_text = f"{zoom_pct}%"
        if self._zoom <= 0:
            zoom_text = f"适应 ({zoom_pct}%)"
        badge_font = QFont(font)
        badge_font.setPointSize(8)
        painter.setFont(badge_font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(zoom_text) + 10
        th = fm.height() + 4
        bx = self.width() - tw - 6
        by = self.height() - th - 6
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 140))
        painter.drawRoundedRect(bx, by, tw, th, 3, 3)
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(bx + 5, by + fm.ascent() + 2, zoom_text)

    def _is_on_split_handle(self, x, y) -> bool:
        ir = self._image_rect()
        if ir.isNull():
            return False
        split_x = ir.x() + ir.width() * self._split_ratio
        vis_top = max(ir.y(), 0)
        vis_bot = min(ir.bottom(), self.height())
        return abs(x - split_x) < self.HANDLE_HIT_WIDTH and vis_top <= y <= vis_bot

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._is_on_split_handle(event.x(), event.y()):
                self._dragging_split = True
            else:
                self._panning = True
                self._pan_start = QPointF(event.pos()) - self._offset
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        ir = self._image_rect()
        if ir.isNull() or ir.width() == 0:
            return

        if self._dragging_split:
            ratio = (event.x() - ir.x()) / ir.width()
            self._split_ratio = max(0.02, min(0.98, ratio))
            self.update()
        elif self._panning:
            self._offset = QPointF(event.pos()) - self._pan_start
            self.update()
        else:
            if self._is_on_split_handle(event.x(), event.y()):
                self.setCursor(Qt.SplitHCursor)
            else:
                self.setCursor(Qt.OpenHandCursor if self._zoom > 0 else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging_split = False
            if self._panning:
                self._panning = False
                self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self._zoom <= 0 or abs(self._zoom - 1.0) > 0.01:
                self._zoom = 1.0
                self._offset = QPointF(0, 0)
            else:
                self._zoom = 0.0
                self._offset = QPointF(0, 0)
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._compressed or self._compressed.isNull():
            return

        old_zoom = self._effective_zoom()
        delta = event.angleDelta().y()
        if delta > 0:
            new_zoom = old_zoom * self.ZOOM_STEP
        else:
            new_zoom = old_zoom / self.ZOOM_STEP

        fit = self._fit_scale()
        new_zoom = max(min(fit, self.MIN_ZOOM) * 0.5, min(self.MAX_ZOOM, new_zoom))

        mouse_pos = QPointF(event.pos())
        center = QPointF(self.width() / 2, self.height() / 2)
        img_point = mouse_pos - center - self._offset

        scale_ratio = new_zoom / old_zoom
        new_img_point = img_point * scale_ratio
        self._offset = mouse_pos - center - new_img_point

        self._zoom = new_zoom
        self.update()
