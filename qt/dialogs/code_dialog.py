from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout
from PySide6.QtCore import Slot
from core_code_generator import CoreCodeGenerator
from PySide6.QtCore import Qt, Slot

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
        self.table.blockSignals(True)
        self.table.setRowCount(len(data))

        for row_index, (id_, name, code) in enumerate(self.core.generated_code):
            self.table.insertRow(row_index)

            item_id = QTableWidgetItem(str(id_))
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)  # ID не редактируется

            item_name = QTableWidgetItem(name)
            item_name.setFlags(item_name.flags() | Qt.ItemIsEditable)

            item_code = QTableWidgetItem(code)
            item_code.setFlags(item_code.flags() | Qt.ItemIsEditable)

            self.table.setItem(row_index, 0, item_id)
            self.table.setItem(row_index, 1, item_name)
            self.table.setItem(row_index, 2, item_code)
        self.table.blockSignals(False)

    @Slot(int, int)
    def on_cell_changed(self, row: int, column: int):
        if column not in (1, 2):
            return  # Только имя и код подлежат изменению

        try:
            record_id = int(self.table.item(row, 0).text())
            new_value = self.table.item(row, column).text()

            if column == 1:
                self.core.update_code(record_id, new_value=new_value, field="name")
            elif column == 2:
                self.core.update_code(record_id, new_value=new_value, field="code")
        except Exception as e:
            print(f"Ошибка при обновлении записи: {e}")

