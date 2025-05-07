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

    def update_code(self, record_id: int, new_code: str):
        for idx, (rid, nm, _) in enumerate(self.generated_code):
            if rid == record_id:
                self.generated_code[idx] = (rid, nm, new_code)
                self.generated_code_changed.emit(self.generated_code)
                break