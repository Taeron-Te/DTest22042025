# graph_editor/view.py

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt

class GraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(self.renderHints() |
                            self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Перемещение сцены мышью
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        """Масштабирование колесом мыши."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)
