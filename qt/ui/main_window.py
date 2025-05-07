# ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Slot
from core_code_generator import CoreCodeGenerator
from dialogs.custom_dialog import CustomDialog
from dialogs.code_dialog import CodeDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное окно (PySide6)")
        self.resize(500,500)
        # Центральный виджет и компоновка
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Экземпляр генератора
        self.core = CoreCodeGenerator()




        # Кнопки
        btn_custom = QPushButton("Открыть простое окно")
        btn_code   = QPushButton("Показать сгенерированный код")
        btn_gen    = QPushButton("Сгенерировать запись")
        btn_exit   = QPushButton("Выход")

        layout.addWidget(btn_custom)
        layout.addWidget(btn_code)
        layout.addWidget(btn_gen)
        layout.addWidget(btn_exit)

        # Подключение сигналов
        btn_custom.clicked.connect(self.on_show_custom)
        btn_custom.setMinimumSize(50,60)
        btn_custom.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                color: black;
                border: 1px solid gray;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: red;
                color: white;
                border: 1px solid black;
                
            }
        """)
        btn_code.clicked.connect(self.on_show_code)
        btn_gen.clicked.connect(self.on_generate)

        btn_exit.clicked.connect(self.close)

    @Slot()
    def on_show_custom(self):
        dlg = CustomDialog("Окно PySide6", "Это простое всплывающее окно.")
        dlg.exec()

    @Slot()
    def on_show_code(self):
        dlg = CodeDialog(self.core)
        dlg.exec()

    @Slot()
    def on_generate(self):
        name = f"Obj{len(self.core.generated_code) + 1}"
        code_str = f"print('Hello from {name}')"
        self.core.generate_code(name, code_str)