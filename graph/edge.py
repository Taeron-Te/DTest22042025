# edge.py

from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import Qt, QPointF
import math
from utils import center_of_item

class GraphEdge(QGraphicsPathItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setZValue(-1)
        self.pen = QPen(Qt.black, 2)
        self.arrow_size = 10  # Размер стрелки
        self.setPen(self.pen)
        self.update_position()

    def update_position(self):
        start_point = self.start_item.get_output_anchor()
        end_point = self.end_item.get_input_anchor()

        path = QPainterPath(start_point)

        dx = (end_point.x() - start_point.x()) * 0.5

        control_point1 = start_point + QPointF(dx, 0)
        control_point2 = end_point - QPointF(dx, 0)

        path.cubicTo(control_point1, control_point2, end_point)

        self.setPath(path)

    def paint(self, painter, option, widget=None):
        painter.setPen(self.pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

        middle_percent = 0.5
        center_point = self.path().pointAtPercent(middle_percent)
        angle = self.path().angleAtPercent(middle_percent)

        angle_rad_minus = math.radians(angle - 30)
        angle_rad_plus = math.radians(angle + 30)

        arrow_p1 = center_point + QPointF(
            self.arrow_size * 0.5 * math.cos(angle_rad_minus),
            -self.arrow_size * 0.5 * math.sin(angle_rad_minus)
        )
        arrow_p2 = center_point + QPointF(
            self.arrow_size * 0.5 * math.cos(angle_rad_plus),
            -self.arrow_size * 0.5 * math.sin(angle_rad_plus)
        )

        arrow_head = QPolygonF([arrow_p1, center_point, arrow_p2])

        painter.setBrush(QBrush(Qt.black))
        painter.drawPolygon(arrow_head)