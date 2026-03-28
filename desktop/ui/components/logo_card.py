from __future__ import annotations

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QWidget


class LogoCard(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._shape = "circulo"
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self.setMinimumSize(280, 280)

    def update_logo(
        self,
        image_path: str | None,
        shape: str = "circulo",
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        self._shape = shape
        self._scale = scale
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._pixmap = QPixmap(image_path) if image_path else None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), self.palette().window())
        window_color = self.palette().window().color()
        text_color = self.palette().text().color()
        border_fill = QColor(15, 19, 25) if window_color.lightness() < 128 else QColor(217, 225, 233)

        outer_rect = self.rect().adjusted(8, 8, -8, -8)
        radius = 32 if self._shape == "quadrado" else outer_rect.width() / 2

        border_path = QPainterPath()
        if self._shape == "quadrado":
            border_path.addRoundedRect(QRectF(outer_rect), radius, radius)
        else:
            border_path.addEllipse(QRectF(outer_rect))

        painter.fillPath(border_path, border_fill)
        painter.setPen(Qt.NoPen)

        clip_rect = outer_rect.adjusted(20, 20, -20, -20)
        clip_path = QPainterPath()
        if self._shape == "quadrado":
            clip_path.addRoundedRect(QRectF(clip_rect), max(18.0, radius - 12), max(18.0, radius - 12))
        else:
            clip_path.addEllipse(QRectF(clip_rect))

        painter.fillPath(clip_path, Qt.transparent)
        painter.setClipPath(clip_path)

        if self._pixmap and not self._pixmap.isNull():
            target_width = clip_rect.width() * self._scale
            target_height = clip_rect.height() * self._scale
            scaled = self._pixmap.scaled(
                int(target_width),
                int(target_height),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            x = clip_rect.center().x() - (scaled.width() / 2) + (clip_rect.width() * (self._offset_x / 100.0))
            y = clip_rect.center().y() - (scaled.height() / 2) + (clip_rect.height() * (self._offset_y / 100.0))
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            painter.setClipping(False)
            painter.setPen(QPen(text_color))
            painter.drawText(self.rect(), Qt.AlignCenter, "Sem logo")

        painter.end()
