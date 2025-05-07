# graph_editor/main.py

import sys
from PySide6.QtWidgets import QApplication
from view import GraphView
from scene import GraphScene
from node import GraphNode
from edge import GraphEdge

def main():
    app = QApplication(sys.argv)

    # Создание сцены и представления
    scene = GraphScene()
    view = GraphView(scene)
    view.setWindowTitle("Редактор граф-схемы")
    view.resize(800, 600)
    view.show()

    # Добавление узлов
    node1 = GraphNode("Узел 1")
    node2 = GraphNode("Узел 2")
    node3 = GraphNode("Узел 3")

    scene.addItem(node1)
    scene.addItem(node2)
    scene.addItem(node3)

    node1.setPos(100, 100)
    node2.setPos(300, 200)
    node3.setPos(500, 100)

    # Добавление связей
    edge1 = GraphEdge(node1, node2)
    edge2 = GraphEdge(node2, node3)

    scene.addItem(edge1)
    scene.addItem(edge2)

    # Сохранение связей в узлах для автообновления при движении
    node1.add_edge(edge1)
    node2.add_edge(edge1)
    node2.add_edge(edge2)
    node3.add_edge(edge2)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
