from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
from PySide6.QtCore import Slot

class CustomDialog(QDialog):
    def __init__(self, title: str, message: str):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Сообщение и кнопка закрытия
        layout.addWidget(QLabel(message))
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.on_close)
        layout.addWidget(btn_close)

    @Slot()
    def on_close(self):
        self.accept()