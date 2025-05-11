# core_code_generator.py
from PySide6.QtCore import QObject, Signal

class CoreCodeGenerator(QObject):
    # Сигнал, передающий весь текущий список записей
    generated_code_changed = Signal(list)

    def __init__(self):
        super().__init__()
        # хранит кортежи (id: int, name: str, code: str)
        self.generated_code = []

    def generate_code(self, name: str, code_str: str):
        new_id = len(self.generated_code) + 1
        record = (new_id, name, code_str)
        self.generated_code.append(record)
        # уведомление об изменении
        self.generated_code_changed.emit(self.generated_code)

    def update_code(self, record_id: int, new_value: str, field: str):
        for index, (id_, name, code) in enumerate(self.generated_code):
            if id_ == record_id:
                if field == "name":
                    self.generated_code[index] = (id_, new_value, code)
                elif field == "code":
                    self.generated_code[index] = (id_, name, new_value)
                self.generated_code_changed.emit(self.generated_code)
                break