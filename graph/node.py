# graph_editor/node.py

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtCore import QRectF, Qt, QPointF


class GraphNode(QGraphicsItem):
    def __init__(self, label: str):
        super().__init__()
        self.label = label
        self.width = 80
        self.height = 40
        self.edges = []  # Список связанных связей

        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        brush = QBrush(QColor(180, 220, 255))
        painter.setBrush(brush)
        painter.drawRect(self.boundingRect())
        painter.drawText(self.boundingRect(),
                         Qt.AlignCenter, self.label)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def get_input_anchor(self):
        """Точка входа - середина левой стороны"""
        rect = self.sceneBoundingRect()
        return QPointF(rect.left(), rect.top() + rect.height() / 2)

    def get_output_anchor(self):
        """Точка выхода - середина правой стороны"""
        rect = self.sceneBoundingRect()
        return QPointF(rect.right(), rect.top() + rect.height() / 2)