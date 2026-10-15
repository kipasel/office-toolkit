"""Dependency-free Metro icon factory.

Icons are drawn at runtime with QPainter as simple geometric glyphs on a
100x100 design canvas, so the app ships no external icon files and needs no new
dependency. Every glyph uses a single stroke colour, which keeps them legible
both on light surfaces and on saturated category tiles.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

from .tokens import CATEGORY_COLORS, Colors

_CANVAS = 100.0


def _poly(*points: tuple[float, float]) -> QPolygonF:
    return QPolygonF([QPointF(x, y) for x, y in points])


def _arrowhead(p: QPainter, tip: tuple[float, float], direction: str, length: float = 12, width: float = 11) -> None:
    x, y = tip
    half = width / 2
    if direction == "up":
        poly = _poly((x, y), (x - half, y + length), (x + half, y + length))
    elif direction == "down":
        poly = _poly((x, y), (x - half, y - length), (x + half, y - length))
    elif direction == "left":
        poly = _poly((x, y), (x + length, y - half), (x + length, y + half))
    else:  # right
        poly = _poly((x, y), (x - length, y - half), (x - length, y + half))
    p.save()
    p.setBrush(p.pen().color())
    p.drawPolygon(poly)
    p.restore()


# -- individual glyphs (drawn on the 100x100 canvas) ---------------------

def _home(p: QPainter) -> None:
    p.drawPolyline(_poly((14, 50), (50, 20), (86, 50)))
    p.drawPolyline(_poly((24, 44), (24, 82), (76, 82), (76, 44)))
    p.drawRect(QRectF(42, 60, 16, 22))


def _image(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(14, 20, 72, 60), 6, 6)
    p.drawEllipse(QPointF(35, 39), 7, 7)
    p.drawPolyline(_poly((18, 74), (40, 50), (56, 66), (68, 56), (82, 74)))


def _pdf(p: QPainter) -> None:
    p.drawPolyline(_poly((28, 14), (60, 14), (74, 30), (74, 86), (28, 86), (28, 14)))
    p.drawPolyline(_poly((60, 14), (60, 30), (74, 30)))
    p.drawLine(QPointF(38, 50), QPointF(64, 50))
    p.drawLine(QPointF(38, 62), QPointF(64, 62))
    p.drawLine(QPointF(38, 74), QPointF(54, 74))


def _qr(p: QPainter) -> None:
    for ox, oy in ((16, 16), (58, 16), (16, 58)):
        p.drawRect(QRectF(ox, oy, 26, 26))
        p.save()
        p.setBrush(p.pen().color())
        p.drawRect(QRectF(ox + 8, oy + 8, 10, 10))
        p.restore()
    p.save()
    p.setBrush(p.pen().color())
    p.drawRect(QRectF(58, 58, 10, 10))
    p.drawRect(QRectF(74, 58, 10, 10))
    p.drawRect(QRectF(58, 74, 10, 10))
    p.drawRect(QRectF(74, 74, 10, 10))
    p.restore()


def _files(p: QPainter) -> None:
    p.drawPolyline(_poly((12, 34), (38, 34), (45, 42), (88, 42), (88, 82), (12, 82), (12, 34)))


def _settings(p: QPainter) -> None:
    p.drawEllipse(QPointF(50, 50), 15, 15)
    import math

    for i in range(8):
        a = math.radians(i * 45)
        x1, y1 = 50 + 22 * math.cos(a), 50 + 22 * math.sin(a)
        x2, y2 = 50 + 32 * math.cos(a), 50 + 32 * math.sin(a)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _search(p: QPainter) -> None:
    p.drawEllipse(QPointF(44, 44), 24, 24)
    p.drawLine(QPointF(62, 62), QPointF(84, 84))


def _merge(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(14, 22, 28, 22), 4, 4)
    p.drawRoundedRect(QRectF(14, 56, 28, 22), 4, 4)
    p.drawPolyline(_poly((42, 33), (62, 33), (62, 50), (74, 50)))
    p.drawPolyline(_poly((42, 67), (62, 67), (62, 50)))
    _arrowhead(p, (84, 50), "right")


def _split(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(14, 40, 28, 22), 4, 4)
    p.drawPolyline(_poly((42, 51), (62, 51), (62, 30), (74, 30)))
    _arrowhead(p, (84, 30), "right")
    p.drawPolyline(_poly((62, 51), (62, 72), (74, 72)))
    _arrowhead(p, (84, 72), "right")


def _extract(p: QPainter) -> None:
    p.drawPolyline(_poly((22, 20), (22, 84), (70, 84)))
    p.drawLine(QPointF(46, 58), QPointF(80, 24))
    _arrowhead(p, (84, 20), "up")


def _reorder(p: QPainter) -> None:
    for y in (28, 50, 72):
        p.drawLine(QPointF(20, y), QPointF(66, y))
    p.drawLine(QPointF(80, 26), QPointF(80, 74))
    _arrowhead(p, (80, 84), "down")
    _arrowhead(p, (80, 16), "up")


def _rotate(p: QPainter) -> None:
    p.drawArc(QRectF(24, 24, 52, 52), 70 * 16, 280 * 16)
    _arrowhead(p, (76, 40), "right", length=14, width=13)


def _compress(p: QPainter) -> None:
    p.drawLine(QPointF(50, 14), QPointF(50, 42))
    _arrowhead(p, (50, 46), "down")
    p.drawLine(QPointF(50, 86), QPointF(50, 58))
    _arrowhead(p, (50, 54), "up")
    p.drawLine(QPointF(14, 50), QPointF(42, 50))
    _arrowhead(p, (46, 50), "right")
    p.drawLine(QPointF(86, 50), QPointF(58, 50))
    _arrowhead(p, (54, 50), "left")


def _to_image(p: QPainter) -> None:
    p.drawPolyline(_poly((18, 14), (44, 14), (56, 26), (56, 44)))
    p.drawPolyline(_poly((18, 14), (18, 86), (42, 86)))
    p.drawRoundedRect(QRectF(50, 48, 36, 32), 4, 4)
    p.drawPolyline(_poly((52, 76), (64, 62), (74, 70), (86, 60)))


def _from_image(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(14, 48, 36, 32), 4, 4)
    p.drawPolyline(_poly((16, 76), (28, 62), (38, 70), (50, 60)))
    p.drawPolyline(_poly((44, 14), (70, 14), (82, 26), (82, 44)))
    p.drawPolyline(_poly((44, 14), (44, 86), (68, 86)))


def _text(p: QPainter) -> None:
    p.drawLine(QPointF(22, 24), QPointF(78, 24))
    p.drawLine(QPointF(50, 24), QPointF(50, 80))
    p.drawLine(QPointF(38, 80), QPointF(62, 80))


def _image_add(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(12, 24, 62, 52), 6, 6)
    p.drawPolyline(_poly((16, 70), (36, 48), (50, 62), (60, 54), (74, 68)))
    p.drawLine(QPointF(80, 16), QPointF(80, 40))
    p.drawLine(QPointF(68, 28), QPointF(92, 28))


def _annotate(p: QPainter) -> None:
    p.save()
    pen = QPen(p.pen())
    pen.setWidthF(16)
    pen.setCapStyle(Qt.FlatCap)
    p.setPen(pen)
    p.drawLine(QPointF(26, 66), QPointF(70, 30))
    p.restore()
    p.drawLine(QPointF(20, 82), QPointF(80, 82))


def _signature(p: QPainter) -> None:
    path = QPainterPath(QPointF(16, 66))
    path.cubicTo(QPointF(34, 20), QPointF(44, 88), QPointF(58, 54))
    path.cubicTo(QPointF(68, 30), QPointF(74, 74), QPointF(86, 44))
    p.drawPath(path)
    p.drawLine(QPointF(16, 84), QPointF(86, 84))


def _lock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(28, 46, 44, 38), 6, 6)
    p.drawArc(QRectF(36, 22, 28, 44), 0, 180 * 16)


def _unlock(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(28, 46, 44, 38), 6, 6)
    p.drawArc(QRectF(50, 20, 30, 44), 0, 180 * 16)


def _info(p: QPainter) -> None:
    p.drawEllipse(QPointF(50, 50), 34, 34)
    p.save()
    p.setBrush(p.pen().color())
    p.drawEllipse(QPointF(50, 34), 4, 4)
    p.restore()
    p.drawLine(QPointF(50, 46), QPointF(50, 68))


def _convert(p: QPainter) -> None:
    p.drawArc(QRectF(24, 24, 52, 52), 40 * 16, 130 * 16)
    p.drawArc(QRectF(24, 24, 52, 52), 220 * 16, 130 * 16)
    _arrowhead(p, (74, 36), "right", length=13, width=12)
    _arrowhead(p, (26, 64), "left", length=13, width=12)


def _resize(p: QPainter) -> None:
    p.drawPolyline(_poly((20, 22), (20, 80), (78, 80)))
    p.drawLine(QPointF(34, 66), QPointF(74, 26))
    _arrowhead(p, (80, 20), "up", length=13)
    _arrowhead(p, (28, 72), "down", length=13)


def _crop(p: QPainter) -> None:
    p.drawPolyline(_poly((30, 16), (30, 70), (84, 70)))
    p.drawPolyline(_poly((16, 30), (70, 30), (70, 84)))


def _rename(p: QPainter) -> None:
    p.drawPolyline(_poly((20, 26), (68, 26), (68, 74), (20, 74), (20, 26)))
    p.drawLine(QPointF(30, 40), QPointF(58, 40))
    p.drawLine(QPointF(30, 52), QPointF(58, 52))
    p.drawLine(QPointF(30, 64), QPointF(48, 64))
    p.drawLine(QPointF(74, 60), QPointF(88, 74))
    p.drawPolyline(_poly((72, 76), (74, 60), (88, 74), (78, 78), (72, 76)))


def _duplicate(p: QPainter) -> None:
    p.drawRoundedRect(QRectF(18, 18, 46, 46), 5, 5)
    p.drawRoundedRect(QRectF(36, 36, 46, 46), 5, 5)


def _export(p: QPainter) -> None:
    p.drawPolyline(_poly((24, 52), (24, 84), (76, 84), (76, 52)))
    p.drawLine(QPointF(50, 20), QPointF(50, 62))
    _arrowhead(p, (50, 18), "up")


def _json(p: QPainter) -> None:
    p.drawPolyline(_poly((38, 18), (24, 18), (24, 82), (38, 82)))
    p.drawPolyline(_poly((62, 18), (76, 18), (76, 82), (62, 82)))
    p.drawLine(QPointF(54, 30), QPointF(46, 70))


def _csv(p: QPainter) -> None:
    p.drawRect(QRectF(18, 20, 64, 60))
    p.drawLine(QPointF(18, 40), QPointF(82, 40))
    p.drawLine(QPointF(18, 60), QPointF(82, 60))
    p.drawLine(QPointF(50, 20), QPointF(50, 80))


def _encoding(p: QPainter) -> None:
    p.drawPolyline(_poly((20, 78), (36, 24), (52, 78)))
    p.drawLine(QPointF(26, 60), QPointF(46, 60))
    p.drawLine(QPointF(60, 34), QPointF(84, 34))
    _arrowhead(p, (86, 34), "right", length=12)
    p.drawLine(QPointF(84, 66), QPointF(60, 66))
    _arrowhead(p, (58, 66), "left", length=12)


def _batch(p: QPainter) -> None:
    for i, y in enumerate((22, 44, 66)):
        p.drawRoundedRect(QRectF(18 + i * 6, y, 58, 16), 4, 4)


def _check(p: QPainter) -> None:
    p.drawPolyline(_poly((24, 52), (44, 72), (78, 30)))


def _offline(p: QPainter) -> None:
    p.drawEllipse(QPointF(50, 50), 32, 32)
    p.drawLine(QPointF(28, 28), QPointF(72, 72))


def _gear_doc(p: QPainter) -> None:
    _pdf(p)
    p.drawEllipse(QPointF(74, 74), 14, 14)


_GLYPHS = {
    "home": _home,
    "image": _image,
    "pdf": _pdf,
    "pdf_advanced": _gear_doc,
    "qr": _qr,
    "files": _files,
    "settings": _settings,
    "search": _search,
    "merge": _merge,
    "split": _split,
    "extract": _extract,
    "reorder": _reorder,
    "rotate": _rotate,
    "compress": _compress,
    "to_image": _to_image,
    "from_image": _from_image,
    "text": _text,
    "image_add": _image_add,
    "annotate": _annotate,
    "signature": _signature,
    "lock": _lock,
    "unlock": _unlock,
    "info": _info,
    "convert": _convert,
    "resize": _resize,
    "crop": _crop,
    "rename": _rename,
    "duplicate": _duplicate,
    "export": _export,
    "json": _json,
    "csv": _csv,
    "encoding": _encoding,
    "batch": _batch,
    "check": _check,
    "offline": _offline,
}


def pixmap(name: str, color: str, size: int = 24) -> QPixmap:
    """Render a named glyph into a QPixmap of ``size`` pixels."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    draw = _GLYPHS.get(name, _info)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.scale(size / _CANVAS, size / _CANVAS)
    pen = QPen(QColor(color))
    pen.setWidthF(8.0)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    draw(painter)
    painter.end()
    return pm


def icon(name: str, color: str, size: int = 24) -> QIcon:
    return QIcon(pixmap(name, color, size))


def app_logo(size: int = 34) -> QPixmap:
    """Four-square geometric logo using the category palette."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing, True)
    gap = max(1.0, size * 0.06)
    cell = (size - gap) / 2.0
    radius = size * 0.14
    squares = (
        (0, 0, CATEGORY_COLORS["pdf"]),
        (cell + gap, 0, CATEGORY_COLORS["qr"]),
        (0, cell + gap, CATEGORY_COLORS["gambar"]),
        (cell + gap, cell + gap, CATEGORY_COLORS["file"]),
    )
    for x, y, color in squares:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(x, y, cell, cell), radius, radius)
    painter.end()
    return pm


def app_icon(size: int = 34) -> QIcon:
    return QIcon(app_logo(size))


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, Colors.PRIMARY)
