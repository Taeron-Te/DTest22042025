# graph_editor/scene.py

from PySide6.QtWidgets import QGraphicsScene

class GraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 600)  # Размер сцены
