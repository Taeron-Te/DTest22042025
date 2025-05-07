from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout
from PySide6.QtCore import Slot
from core_code_generator import CoreCodeGenerator

class CodeDialog(QDialog):
    def __init__(self, core: CoreCodeGenerator):
        super().__init__()
        self.setWindowTitle("Сгенерированный код")
        self.resize(600, 400)

        # Таблица: 3 столбца — ID, Name, Code
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Code"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        # Ссылка на генератор и подписка на сигнал
        self.core = core
        self.core.generated_code_changed.connect(self.update_table)

        # Первичное заполнение
        self.update_table(self.core.generated_code)

    @Slot(list)
    def update_table(self, data: list):
        """
        Получает список кортежей и полностью перерисовывает таблицу.
        """
        self.table.setRowCount(len(data))
        for row, (rid, name, code_str) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(code_str))