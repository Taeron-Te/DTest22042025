# graph_editor/utils.py

from PySide6.QtCore import QPointF

def center_of_item(item) -> QPointF:
    """Возвращает центр элемента относительно сцены."""
    rect = item.sceneBoundingRect()
    return QPointF(rect.x() + rect.width() / 2, rect.y() + rect.height() / 2)

def distance(p1: QPointF, p2: QPointF) -> float:
    """Евклидово расстояние между двумя точками."""
    return ((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2) ** 0.5

def align_to_grid(pos: QPointF, grid_size: int = 20) -> QPointF:
    """Привязывает позицию к сетке."""
    x = round(pos.x() / grid_size) * grid_size
    y = round(pos.y() / grid_size) * grid_size
    return QPointF(x, y)