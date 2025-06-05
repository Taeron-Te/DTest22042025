import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, QGraphicsScene,
    QToolButton,
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QFormLayout, QScrollArea, QGroupBox, QFrame,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsItem, QGraphicsPathItem, QRadioButton, QGraphicsProxyWidget, QGridLayout,
    QSizePolicy, QComboBox
)
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QPainterPath, QFontMetricsF, QFont, QDoubleValidator, \
    QTextOption
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QLocale, QSizeF
import sys
from functools import partial
import json
import uuid
import copy
import functools
import os

# from parser import reader
BLOCK_TYPES = [
    ("Starter", "Стартовый блок"),
    ("Binares", "Бинарный блок"),
    ("Match", "Блок выбора"),
    ("Fuzzy", "Блок нечеткой логики"),
    ("Ender", "Финальный блок")
]

PORT_RADIUS = 14
PORT_OFFSET = 5


class BlockCreateDialog(QDialog):
    def __init__(self, parent=None, starter_exists=False, ender_exists=False):
        super().__init__(parent)
        self.setWindowTitle("Добавить блок")
        self.setMinimumWidth(400)
        self.selected_type = None
        self.fields = {}
        self.starter_exists = starter_exists
        self.ender_exists = ender_exists
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.type_group = QGroupBox("Тип блока")
        type_layout = QVBoxLayout()
        self.type_radiobuttons = {}
        for t, label in BLOCK_TYPES:
            rb = QRadioButton(label)
            rb.t = t
            rb.toggled.connect(self.on_type_changed)
            self.type_radiobuttons[t] = rb
            type_layout.addWidget(rb)
        if self.starter_exists:
            self.type_radiobuttons["Starter"].setEnabled(False)
        self.type_group.setLayout(type_layout)
        layout.addWidget(self.type_group)

        self.form_group = QGroupBox("Параметры блока")
        self.form_layout = QFormLayout()
        self.form_group.setLayout(self.form_layout)
        layout.addWidget(self.form_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    @staticmethod
    def _simple_filter_text(line_edit):
        current_text = line_edit.text()
        filtered_text = current_text.replace('{', '').replace('}', '')
        if current_text != filtered_text:
            cursor_pos = line_edit.cursorPosition()
            removed_chars_before_cursor = sum(
                1 for char_idx in range(min(cursor_pos, len(current_text))) if current_text[char_idx] in ('{', '}'))
            line_edit.setText(filtered_text)
            line_edit.setCursorPosition(max(0, cursor_pos - removed_chars_before_cursor))

    def on_type_changed(self):
        for t, rb in self.type_radiobuttons.items():
            if rb.isChecked():
                self.selected_type = rb.t
                self.update_fields()
                break
        else:
            self.selected_type = None
            self.clear_fields()

    def clear_fields(self):
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.fields = {}

    def update_fields(self):
        self.clear_fields()
        t = self.selected_type

        # Common field for all types that have a name
        if t in ["Starter", "Binares", "Match", "Fuzzy", "Ender"]:
            name_edit = QLineEdit()
            self.form_layout.addRow("Название блока:", name_edit)
            self.fields["name"] = name_edit
            name_edit.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(name_edit))

        if t == "Binares":
            cond = QLineEdit()
            self.form_layout.addRow("Условие:", cond)
            self.fields["condition"] = cond
            cond.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(cond))
        elif t == "Match":
            q = QLineEdit()
            self.form_layout.addRow("Вопрос (Match):", q)
            self.fields["question"] = q
            q.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(q))
            self.choices = []
            self.add_choice_btn = QPushButton("Добавить вариант")
            self.add_choice_btn.clicked.connect(self.add_choice_field)
            self.form_layout.addRow("Варианты:", self.add_choice_btn)
        elif t == "Fuzzy":
            q = QLineEdit()
            self.form_layout.addRow("Вопрос (Fuzzy):", q)
            self.fields["question"] = q
            q.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(q))
        elif t == "Ender":
            verdict_edit = QLineEdit()
            self.form_layout.addRow("Вердикт:", verdict_edit)
            self.fields["verdict"] = verdict_edit
            verdict_edit.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(verdict_edit))

    def add_choice_field(self):
        choice = QLineEdit()
        self.choices.append(choice)
        self.form_layout.addRow(f"Вариант {len(self.choices)}:", choice)
        choice.textChanged.connect(lambda: BlockCreateDialog._simple_filter_text(choice))

    def get_block_data(self):
        data = {"type": self.selected_type}
        if "name" in self.fields:  # All types with name will have this
            data["name"] = self.fields["name"].text()

        if self.selected_type == "Binares":
            if "condition" in self.fields: data["condition"] = self.fields["condition"].text()
        elif self.selected_type == "Match":
            if "question" in self.fields: data["question"] = self.fields["question"].text()
            data["choices"] = [c.text() for c in getattr(self, "choices", [])]
        elif self.selected_type == "Fuzzy":
            if "question" in self.fields: data["question"] = self.fields["question"].text()
        elif self.selected_type == "Ender":
            if "verdict" in self.fields: data["verdict"] = self.fields["verdict"].text()
        return data


class PortItem(QGraphicsEllipseItem):
    def __init__(self, port_type, parent_block, idx=0, label=None, label_side='right', label_text_width=100):
        super().__init__(0, 0, PORT_RADIUS, PORT_RADIUS, parent_block)
        self.setBrush(QColor('#ffffff'))
        self.setPen(QPen(Qt.black, 2))
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)
        self.port_type = port_type
        self.parent_block = parent_block
        self.idx = idx
        self.connections = []
        self.label = None
        self.label_side = label_side
        if label:
            self.label = QGraphicsTextItem(self)
            self.label.setZValue(11)

            doc = self.label.document()
            option = doc.defaultTextOption()
            option.setWrapMode(QTextOption.WrapAnywhere)
            doc.setDefaultTextOption(option)

            self.label.setTextWidth(label_text_width)

            self.label.setHtml(f"<center>{label}</center>")

            self.update_label_pos()

    def setPos(self, x, y):
        super().setPos(x, y)
        self.update_label_pos()

    def update_label_pos(self):
        if self.label:
            label_rect = self.label.boundingRect()
            if self.label_side == 'right':
                # For input ports - position label right of the port
                lx = PORT_RADIUS + 5
                ly = (PORT_RADIUS / 2) - (label_rect.height() / 2)
            elif self.label_side == 'left':
                # For output ports - position label left of the port
                # Increase spacing between label and port to prevent overlap
                lx = -label_rect.width() - 8  # Increased from PORT_OFFSET
                ly = (PORT_RADIUS / 2) - (label_rect.height() / 2)
            else:
                lx, ly = 0, 0

            label_check_rect = QRectF(lx, ly, label_rect.width(), label_rect.height())
            port_circle_rect = QRectF(0, 0, PORT_RADIUS, PORT_RADIUS)
            print('lx: ', lx, 'ly: ', ly, 'label_rect.width: ', label_rect.width(), 'label_rect.height: ', label_rect.height())
            if label_check_rect.intersects(port_circle_rect):
                ly = PORT_RADIUS + 2

            self.label.setPos(lx, ly)

    def hoverEnterEvent(self, event):
        self.setBrush(QColor('#a0ffa0') if self.port_type == 'in' else QColor('#a0c8ff'))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QColor('#ffffff'))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.port_type == 'out':
            scene = self.scene()
            if hasattr(scene, 'start_port_connection'):
                scene.start_port_connection(self)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)


class BlockItem(QGraphicsRectItem):
    def __init__(self, block_data, pos=QPointF(100, 100), width=160):
        super().__init__(0, 0, width, 80)
        self.config_btn = None
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setBrush(QColor('#8C8C8C'))
        self.setPen(QPen(Qt.black, 2))
        self._max_title_section_width = 0
        # Make a deep copy of the entire block_data to ensure full isolation
        # This is crucial for fuzzy_config to be correctly isolated when loaded from JSON
        self.block_data = copy.deepcopy(block_data)

        # Ensure Fuzzy blocks have an initial config if none provided
        if self.block_data.get("type") == "Fuzzy" and not self.block_data.get('fuzzy_config'):
            self.block_data['fuzzy_config'] = {
                'antecedents': {},
                'consequent': {
                    'Output': {'range': [0.0, 1.0, 0.1], 'terms': {'Default': ('trapmf', [0.0, 0.0, 1.0, 1.0])},
                               'term_order': ['Default']}},
                'rule_definitions': []
            }

        self.type_item = QGraphicsSimpleTextItem(f"[{self.block_data.get('type', '')}]")
        self.type_item.setParentItem(self)
        self.type_item.setPos(10, 0)
        self.type_item.setZValue(3)
        self.title_item = QGraphicsTextItem(self.get_title(), self)
        self.title_item.setParentItem(self)
        # Отключаем перенос строк — текст всегда занимает ровно одну строку
        self.title_item.setTextWidth(-1)
        self.title_item.setPos(25, 8)
        self.title_item.setDefaultTextColor(Qt.black)
        self.title_item.setZValue(3)
        self.ports_in = []
        self.ports_out = []
        self._updating_label = False
        self.create_ports()
        self.add_configure_button_if_needed()
        self.update_label()
        self.setPos(pos)


    def itemChange(self, change, value):
        # Обновляем связи
        if change in (
                QGraphicsItem.ItemPositionChange,
                QGraphicsItem.ItemPositionHasChanged,
                QGraphicsItem.ItemTransformChange,
                QGraphicsItem.ItemTransformHasChanged,
                QGraphicsItem.ItemScaleChange,
                QGraphicsItem.ItemScaleHasChanged
        ):
            for port in getattr(self, 'ports_in', []) + getattr(self, 'ports_out', []):
                for conn in getattr(port, 'connections', []):
                    conn.update_path()

            # Авто‑расширение сцены
            scene = self.scene()
            if isinstance(scene, SchemeScene):
                # Получаем прямоугольник блока в координатах сцены
                rect_in_scene = self.mapToScene(self.rect()).boundingRect()
                scene.ensureVisibleRect(rect_in_scene)

        return super().itemChange(change, value)

    def add_configure_button_if_needed(self):
        if self.block_data.get("type") == "Fuzzy":
            if not self.config_btn:
                self.config_btn_widget = QPushButton("⚙")
                self.config_btn_widget.setFixedSize(28, 28)
                self.config_btn_widget.setToolTip("Настроить блок нечеткой логики")
                self.config_btn_widget.clicked.connect(self.open_fuzzy_config)
                self.config_btn = QGraphicsProxyWidget(self)
                self.config_btn.setWidget(self.config_btn_widget)

                self.config_btn.setPos(self.rect().width() - 34, 2)
        else:
            if self.config_btn:
                self.scene().removeItem(self.config_btn)
                self.config_btn = None
                self.config_btn_widget = None

    def open_fuzzy_config(self):
        # DIAGNOSTIC: Print the fuzzy_config from self.block_data just before creating the dialog for this specific BlockItem instance
        current_fuzzy_config_in_block_item = self.block_data.get('fuzzy_config')
        print(
            f"DEBUG BlockItem.open_fuzzy_config (CALLED): For Block ID '{self.block_data.get('id')}', Name '{self.block_data.get('name')}'. "
            f"Current self.block_data.get('fuzzy_config') is: {current_fuzzy_config_in_block_item}")

        # Prepare data specifically for the dialog, using the already potentially deep-copied self.block_data
        initial_config_for_dialog = copy.deepcopy(
            current_fuzzy_config_in_block_item if current_fuzzy_config_in_block_item is not None else {})
        block_title_for_dialog = self.block_data.get("question") or self.block_data.get("name", "Fuzzy Block")

        dlg = FuzzyConfigDialog(
            initial_fuzzy_config_data=initial_config_for_dialog,
            block_display_title=block_title_for_dialog,
            parent=self.scene().views()[0] if self.scene() and self.scene().views() else None
        )
        if dlg.exec() == QDialog.Accepted:
            new_fuzzy_config = dlg.get_config_data()
            if self.block_data.get('fuzzy_config') != new_fuzzy_config:
                self.block_data['fuzzy_config'] = new_fuzzy_config
                print(
                    f"DEBUG BlockItem '{self.get_title()}': fuzzy_config UPDATED to: {self.block_data['fuzzy_config']}")
                self._rebuild_fuzzy_output_ports()
                self.reposition_ports()
                self.update_label()
            else:
                print(f"DEBUG BlockItem '{self.get_title()}': fuzzy_config unchanged. No UI rebuild needed.")
                self.update_label()

    def get_title(self):
        return self.block_data.get("name", "")

    def update_label(self):
        if getattr(self, '_updating_label', False):
            return
        self._updating_label = True
        try:
            margin = 20
            min_width = 180  # Increased minimum width for better division
            min_height = 80
            default_starter_width = 200  # Increased default width
            current_rect = self.rect()
            title_x_pos = margin // 2

            # Calculate required width for the block
            font_metrics = QFontMetricsF(self.title_item.font())
            title_text = self.get_title()
            natural_title_width = 0
            if title_text:
                lines = title_text.split('\n')
                for line in lines:
                    natural_title_width = max(natural_title_width, font_metrics.horizontalAdvance(line))


            # Ensure block is wide enough for both title and ports
            required = max(min_width / 2, natural_title_width + margin)
            self._max_title_section_width = max(self._max_title_section_width, required)
            title_section_width = self._max_title_section_width

            # Calculate max label width for ports
            max_port_label_width = 0
            for port in getattr(self, 'ports_in', []) + getattr(self, 'ports_out', []):
                if hasattr(port, 'label') and port.label:
                    label_rect = port.label.boundingRect()
                    max_port_label_width = max(max_port_label_width, label_rect.width())

            ports_section_width = max(min_width / 2, max_port_label_width + PORT_RADIUS + PORT_OFFSET + margin)

            # Set final block width based on both sections
            block_width = title_section_width + ports_section_width
            block_width = max(block_width, min_width, default_starter_width)

            # Set title width to ensure it stays in left half


            self.title_item.setPlainText(title_text)
            self.title_item.setPos(title_x_pos, 8)

            # Position type label under title
            type_text = f"[{self.block_data.get('type', '')}]"
            self.type_item.setText(type_text)
            self.type_item.setPos(title_x_pos, self.title_item.pos().y() + self.title_item.boundingRect().height() + 2)

            # Set midpoint for visual division
            midpoint = title_section_width

            # Calculate height
            title_bottom = self.title_item.pos().y() + self.title_item.boundingRect().height()
            type_bottom = self.type_item.pos().y() + self.type_item.boundingRect().height()

            header_bottom = min(title_bottom, type_bottom)


            # Add config button if needed
            self.add_configure_button_if_needed()
            if self.config_btn:
                self.config_btn.setPos(midpoint - self.config_btn.widget().width() - 5, 2)

            # Reposition ports based on new layout
            t = self.block_data.get("type")

            if t == "Match":
                self.update_match_ports()
                # Calculate height based on ports
                max_port_bottom = 0
                for port in self.ports_out:
                    port_bottom = port.pos().y() + PORT_RADIUS
                    if hasattr(port, 'label') and port.label:
                        label_bottom = port.pos().y() + port.label.pos().y() + port.label.boundingRect().height()
                        port_bottom = max(port_bottom, label_bottom)
                    max_port_bottom = max(max_port_bottom, port_bottom)

                block_height = max(header_bottom + margin / 2, max_port_bottom + margin / 2, min_height)
            else:


                # Calculate height
                max_port_bottom = 0
                print('port.pos().y()', port.pos().y())
                for port in self.ports_out:
                    port_bottom = port.pos().y() + PORT_RADIUS
                    if hasattr(port, 'label') and port.label:
                        label_bottom = port.pos().y() + port.label.pos().y() + port.label.boundingRect().height()
                        port_bottom = max(port_bottom, label_bottom)
                        print('max_port_bottom', port_bottom)
                        print('max_port_bottom', label_bottom)
                    max_port_bottom = max(max_port_bottom, port_bottom)
                    print('max_port_bottom', max_port_bottom)

                block_height = max(header_bottom + margin / 2, (max_port_bottom + margin / 2), min_height)



            # Update block geometry if dimensions changed
            # Текущий размер
            current_rect = self.rect()
            current_w = current_rect.width()
            current_h = current_rect.height()

            # Новый, рассчитанный
            new_w = block_width
            new_h = block_height
            print(f"DEBUG sizing: current_h={current_h}, new_h={new_h}")
            # Если есть хоть какое-то отличие — увеличиваем или уменьшаем:
            if abs(current_rect.width() - block_width) > 1 or abs(current_rect.height() - block_height) > 1:
                self.prepareGeometryChange()
                self.setRect(QRectF(0, 0, new_w, new_h))

                # Reposition ports after size change
                if t == "Match":
                    self.update_match_ports()
                else:
                    self.reposition_ports(midpoint)

            # Update connections
            for port in self.ports_in + self.ports_out:
                for conn in getattr(port, 'connections', []):
                    conn.update_path()

        finally:
            self._updating_label = False

    def reposition_ports(self, midpoint=None):
        t = self.block_data.get("type")
        rect = self.rect()
        center_y = rect.height() / 2 - PORT_RADIUS / 2

        # If midpoint is not provided, use default block middle
        if midpoint is None:
            midpoint = rect.height() / 2

        # Calculate positions for input and output ports
        right_x = rect.width() - PORT_RADIUS - PORT_OFFSET
        left_x = PORT_OFFSET

        # Position for input ports - bottom left corner
        bottom_y = rect.height() - PORT_RADIUS - PORT_OFFSET

        # For non-Match blocks, position ports on their respective sides
        if t == "Starter":
            # Only output port on the right
            if self.ports_out:
                self.ports_out[0].setPos(right_x, center_y)
                if hasattr(self.ports_out[0], 'label') and self.ports_out[0].label:
                    self.ports_out[0].label_side = 'left'
        elif t == "Ender":
            # Input port on bottom-left
            if self.ports_in:
                self.ports_in[0].setPos(left_x, bottom_y)
                if hasattr(self.ports_in[0], 'label') and self.ports_in[0].label:
                    self.ports_in[0].label_side = 'right'
        elif t == "Binares":
            # Input port on bottom-left, output ports on right
            if self.ports_in:
                self.ports_in[0].setPos(left_x, bottom_y)
                if hasattr(self.ports_in[0], 'label') and self.ports_in[0].label:
                    self.ports_in[0].label_side = 'right'

            if len(self.ports_out) > 1:
                # Adjust spacing between Yes/No ports
                port_spacing = min(rect.height() / 3, PORT_RADIUS * 3)
                self.ports_out[0].setPos(right_x, center_y - port_spacing)
                self.ports_out[1].setPos(right_x, center_y + port_spacing)

                # Ensure labels are on the left side of output ports
                for port in self.ports_out:
                    if hasattr(port, 'label') and port.label:
                        port.label_side = 'left'
        elif t == "Fuzzy":
            # Input port on bottom-left
            if self.ports_in:
                self.ports_in[0].setPos(left_x, bottom_y)
                if hasattr(self.ports_in[0], 'label') and self.ports_in[0].label:
                    self.ports_in[0].label_side = 'right'

            # Output ports on right
            num_out_ports = len(self.ports_out)
            if num_out_ports == 1:
                if self.ports_out:
                    self.ports_out[0].setPos(right_x, center_y)
                    if hasattr(self.ports_out[0], 'label') and self.ports_out[0].label:
                        self.ports_out[0].label_side = 'left'
            elif num_out_ports > 1:
                margin_top_bottom = PORT_RADIUS
                port_area_height = rect.height() - 2 * margin_top_bottom

                # Calculate spacing between ports
                total_port_circle_height = num_out_ports * PORT_RADIUS
                total_spacing_height = (num_out_ports - 1) * (PORT_RADIUS * 0.8)

                actual_ports_render_height = total_port_circle_height + total_spacing_height

                current_y = (rect.height() - actual_ports_render_height) / 2.0
                current_y = max(current_y, margin_top_bottom)

                for port in self.ports_out:
                    port.setPos(right_x, current_y)
                    if hasattr(port, 'label') and port.label:
                        port.label_side = 'left'
                    current_y += PORT_RADIUS + (PORT_RADIUS * 0.8)

        # Update label positions for all ports
        for port in self.ports_in + self.ports_out:
            port.update_label_pos()

    def create_ports(self):
        t = self.block_data.get("type")
        if t == "Starter":
            port = PortItem('out', self)
            self.ports_out.append(port)
            self.reposition_ports()
        elif t == "Ender":
            port = PortItem('in', self, label=None, label_side='left')
            self.ports_in.append(port)
            self.reposition_ports()
        elif t == "Binares":
            port_in = PortItem('in', self, label=None, label_side='left')
            self.ports_in.append(port_in)
            port_out_yes = PortItem('out', self, 0, label="Да", label_side='left')
            port_out_no = PortItem('out', self, 1, label="Нет", label_side='left')
            self.ports_out.extend([port_out_yes, port_out_no])
            self.reposition_ports()
        elif t == "Match":
            # Create input port but don't position it yet
            port_in = PortItem('in', self, label=None, label_side='left')
            self.ports_in.append(port_in)
            # Position will be set in update_match_ports
            self.create_match_ports()
        elif t == "Fuzzy":
            # Create input port
            port_in = PortItem('in', self, label=None, label_side='left')
            self.ports_in.append(port_in)
            # Initialize fuzzy output ports
            self._rebuild_fuzzy_output_ports()
            self.reposition_ports()

    def _rebuild_fuzzy_output_ports(self):
        scene = self.scene()
        stored_connections_info = []
        if scene and hasattr(self, 'ports_out'):
            for out_port in self.ports_out:
                if hasattr(out_port, 'connections'):
                    for conn in list(out_port.connections):
                        if conn.out_port == out_port:
                            stored_connections_info.append({'out_idx': out_port.idx, 'in_port_obj': conn.in_port})

        if hasattr(self, 'ports_out'):
            for port in list(self.ports_out):
                if hasattr(port, 'connections'):
                    for conn in list(port.connections):
                        other_port = conn.in_port if conn.out_port == port else conn.out_port
                        if other_port and hasattr(other_port, 'connections') and conn in other_port.connections:
                            other_port.connections.remove(conn)
                        if scene:
                            if hasattr(scene, 'connections') and conn in scene.connections:
                                scene.connections.remove(conn)
                            scene.removeItem(conn)
                if scene:
                    scene.removeItem(port)
                else:
                    port.setParentItem(None)
        self.ports_out = []

        fuzzy_config = self.block_data.get('fuzzy_config', {})
        # Print diagnostic info about the config
        print(f"DEBUG: rebuild_fuzzy_output_ports - config: {fuzzy_config}")

        # 'consequent' is a dict where keys are consequent names. We assume one.
        consequent_dict_overall = fuzzy_config.get('consequent', {})

        actual_consequent_terms_map = {}
        if consequent_dict_overall:
            # Get the first (and assumed only) consequent's data dictionary
            first_consequent_name = next(iter(consequent_dict_overall), None)
            if first_consequent_name:
                actual_consequent_terms_map = consequent_dict_overall[first_consequent_name].get('terms', {})
                # Print diagnostic info about the terms
                print(f"DEBUG: rebuild_fuzzy_output_ports - consequent terms: {actual_consequent_terms_map}")

        # actual_consequent_terms_map is now like: {"term_A_name": ('type', [vals]), "term_B_name": ...}

        if actual_consequent_terms_map:  # Check if the terms map is not empty
            # Get term_order if available for ordered port creation
            term_order = []
            if first_consequent_name and 'term_order' in consequent_dict_overall[first_consequent_name]:
                term_order = consequent_dict_overall[first_consequent_name].get('term_order', [])
                print(f"DEBUG: rebuild_fuzzy_output_ports - term order: {term_order}")

            if term_order:
                # Create ports in the order specified by term_order
                idx_counter = 0
                for term_name in term_order:
                    if term_name and term_name in actual_consequent_terms_map:
                        print(f"DEBUG: Creating port for term: {term_name}")
                        port = PortItem('out', self, idx_counter, label=term_name, label_side='left')
                        self.ports_out.append(port)
                        idx_counter += 1
            else:
                # No term_order, fall back to dictionary iteration (no guaranteed order)
                idx_counter = 0
                for term_name_key in actual_consequent_terms_map.keys():  # Iterate over term names (which are the keys)
                    if term_name_key:  # Ensure term name is not empty
                        print(f"DEBUG: Creating port for term: {term_name_key}")
                        # The idx for PortItem should be unique for this block's output ports
                        port = PortItem('out', self, idx_counter, label=term_name_key, label_side='left')
                        self.ports_out.append(port)
                        idx_counter += 1

        if not self.ports_out:  # If no terms or all terms were empty/nameless, add one default output port
            print("DEBUG: No consequent terms found, creating default output port")
            default_port = PortItem('out', self, 0, label=None, label_side='left')
            self.ports_out.append(default_port)

        if scene:
            for conn_info in stored_connections_info:
                target_in_port_obj = conn_info['in_port_obj']
                old_out_idx = conn_info['out_idx']

                new_out_port_obj = None
                for p_out in self.ports_out:
                    if p_out.idx == old_out_idx:
                        new_out_port_obj = p_out
                        break

                if new_out_port_obj and target_in_port_obj:
                    # Check if target input port still exists in scene
                    if target_in_port_obj.scene() == scene:
                        new_conn_item = ConnectionItem(new_out_port_obj, target_in_port_obj)
                        scene.addItem(new_conn_item)
                    else:
                        print(
                            f"Warning: Target input port for Fuzzy out_idx {old_out_idx} is no longer in the scene. Connection not restored.")

    def create_match_ports(self):
        scene = self.scene()
        stored_connections_info = []

        if scene and hasattr(self, 'ports_out'):
            for out_port in self.ports_out:
                if hasattr(out_port, 'connections'):
                    for conn in list(out_port.connections):
                        if conn.out_port == out_port:
                            stored_connections_info.append({'out_idx': out_port.idx, 'in_port_obj': conn.in_port})

        if hasattr(self, 'ports_out'):
            for port in list(self.ports_out):
                if hasattr(port, 'connections'):
                    for conn in list(port.connections):
                        other_port = conn.in_port if conn.out_port == port else conn.out_port
                        if other_port and hasattr(other_port, 'connections') and conn in other_port.connections:
                            other_port.connections.remove(conn)

                        if scene:
                            if hasattr(scene, 'connections') and conn in scene.connections:
                                scene.connections.remove(conn)
                            scene.removeItem(conn)

                if scene:
                    scene.removeItem(port)
                else:
                    port.setParentItem(None)

        self.ports_out = []

        choices = self.block_data.get("choices", [])
        port_x = self.rect().width() - PORT_RADIUS - PORT_OFFSET

        # Calculate the midpoint for the block
        midpoint = self.rect().width() * 0.6  # Increase space for right portion (60/40 split)

        # Start positioning ports from below the type label
        type_bottom = self.type_item.pos().y() + self.type_item.boundingRect().height()
        current_y = type_bottom + 15
        margin_ports_vertical = 20  # Increased vertical spacing between ports

        for i, choice_text in enumerate(choices):
            # Increase label_text_width to allow more space for text
            port = PortItem('out', self, i, label=choice_text, label_side='left', label_text_width=midpoint * 0.7)
            port.setPos(port_x, current_y)
            self.ports_out.append(port)

            # Calculate combined height of port and its label
            port_circle_rect = QRectF(port_x, current_y, PORT_RADIUS, PORT_RADIUS)
            combined_item_rect = port_circle_rect
            if port.label:
                label_rect = port.label.boundingRect()
                label_pos = port.label.pos()
                label_visual_rect = QRectF(
                    port_x + label_pos.x(),
                    current_y + label_pos.y(),
                    label_rect.width(),
                    label_rect.height()
                )
                combined_item_rect = combined_item_rect.united(label_visual_rect)

            # Move to position for next port
            current_y = combined_item_rect.bottom() + margin_ports_vertical

        # Restore connections if possible
        if scene:
            for conn_info in stored_connections_info:
                target_in_port_obj = conn_info['in_port_obj']
                old_out_idx = conn_info['out_idx']

                new_out_port_obj = None
                for p_out in self.ports_out:
                    if p_out.idx == old_out_idx:
                        new_out_port_obj = p_out
                        break

                if new_out_port_obj and target_in_port_obj:
                    if target_in_port_obj.scene() == scene:
                        new_conn_item = ConnectionItem(new_out_port_obj, target_in_port_obj)
                        scene.addItem(new_conn_item)
                    else:
                        print(
                            f"Warning: Target input port for out_idx {old_out_idx} is no longer in the scene. Connection not restored.")

    def update_match_ports(self):
        self.create_match_ports()

        # Position the input port in the bottom-left corner
        if self.ports_in:
            left_x = PORT_OFFSET
            bottom_y = self.rect().height() - PORT_RADIUS - PORT_OFFSET
            self.ports_in[0].setPos(left_x, bottom_y)
            self.ports_in[0].update_label_pos()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene = self.scene()
        if hasattr(scene, 'block_selected'):
            scene.block_selected(self)


class SchemeScene(QGraphicsScene):
    EXPAND_MARGIN = 100
    EXPAND_STEP = 300
    def __init__(self, on_block_selected=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_block_selected = on_block_selected
        self.connection_start_port = None
        self.temp_connection = None
        self.connections = []  # Все ConnectionItem
        self.blocks = {}  # id -> BlockItem


    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, BlockItem):
            block_id = item.block_data.get('id')
            if not block_id:
                block_type = item.block_data.get('type')
                prefix = 'u'
                if block_type == "Starter":
                    prefix = 's'
                elif block_type == "Ender":
                    prefix = 'e'
                elif block_type == "Binares":
                    prefix = 'b'
                elif block_type == "Match":
                    prefix = 'm'
                elif block_type == "Fuzzy":
                    prefix = 'f'

                block_id = f"{prefix}_{uuid.uuid4().hex}"
                item.block_data['id'] = block_id
            self.blocks[block_id] = item
        elif isinstance(item, ConnectionItem):
            self.connections.append(item)

    def ensureVisibleRect(self, item_rect: QRectF):
        scene_rect = self.sceneRect()
        new_rect = QRectF(scene_rect)



        if (item_rect.left() - scene_rect.left()) < self.EXPAND_MARGIN:
            new_rect.setLeft(scene_rect.left() - self.EXPAND_STEP)
        if (scene_rect.right() - item_rect.right()) < self.EXPAND_MARGIN:
            new_rect.setRight(scene_rect.right() + self.EXPAND_STEP)
        if (item_rect.top() - scene_rect.top()) < self.EXPAND_MARGIN:
            new_rect.setTop(scene_rect.top() - self.EXPAND_STEP)
        if (scene_rect.bottom() - item_rect.bottom()) < self.EXPAND_MARGIN:
            new_rect.setBottom(scene_rect.bottom() + self.EXPAND_STEP)

        if new_rect != scene_rect:

            self.setSceneRect(new_rect)

    def removeItem(self, item):
        super().removeItem(item)
        if isinstance(item, BlockItem):
            block_id = item.block_data.get('id')
            if block_id in self.blocks:
                del self.blocks[block_id]
        elif isinstance(item, ConnectionItem):
            if item in self.connections:
                self.connections.remove(item)

    def get_blocks(self):
        return list(self.blocks.values())

    def get_connections(self):
        return list(self.connections)

    def block_selected(self, block_item):
        if self.on_block_selected:
            self.on_block_selected(block_item)

    def start_port_connection(self, port):
        # Только с выхода
        if port.port_type == 'out':
            self.connection_start_port = port
            self.temp_connection = QGraphicsPathItem()
            self.temp_connection.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
            self.addItem(self.temp_connection)

    def end_port_connection(self, port):
        # Только выход->вход, разные блоки
        if (
                self.connection_start_port and
                self.connection_start_port.port_type == 'out' and
                port.port_type == 'in' and
                port.parent_block != self.connection_start_port.parent_block
        ):
            # Удалить все существующие соединения с этого выхода
            to_remove = [conn for conn in list(self.connections) if conn.out_port == self.connection_start_port]
            for conn in to_remove:
                if conn in self.connections:
                    self.connections.remove(conn)
                if conn in conn.out_port.connections:
                    conn.out_port.connections.remove(conn)
                if conn in conn.in_port.connections:
                    conn.in_port.connections.remove(conn)
                self.removeItem(conn)
            # Проверяем, нет ли уже такого соединения
            for conn in self.connections:
                if conn.out_port == self.connection_start_port and conn.in_port == port:
                    break
            else:
                conn = ConnectionItem(self.connection_start_port, port)
                self.addItem(conn)
                self.connections.append(conn)
        if self.temp_connection:
            self.removeItem(self.temp_connection)
            self.temp_connection = None
        self.connection_start_port = None

    def mouseMoveEvent(self, event):
        if self.connection_start_port and self.temp_connection:
            start = self.connection_start_port.scenePos() + QPointF(PORT_RADIUS / 2, PORT_RADIUS / 2)
            end = event.scenePos()
            path = QPainterPath(start)
            mid_x = (start.x() + end.x()) / 2
            path.lineTo(mid_x, start.y())
            path.lineTo(mid_x, end.y())
            path.lineTo(end.x(), end.y())
            self.temp_connection.setPath(path)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.connection_start_port:
            items = self.items(event.scenePos())
            for item in items:
                if (isinstance(item, PortItem) and
                        item.port_type == 'in' and
                        item.parent_block != self.connection_start_port.parent_block):
                    self.end_port_connection(item)
                    break
            else:
                if self.temp_connection:
                    self.removeItem(self.temp_connection)
                    self.temp_connection = None
                self.connection_start_port = None
        else:
            super().mouseReleaseEvent(event)


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, out_port, in_port):
        super().__init__()
        self.out_port = out_port
        self.in_port = in_port
        self.setPen(QPen(Qt.blue, 3))
        self.setZValue(1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable)
        self.update_path()
        # Регистрируем соединение в портах
        out_port.connections.append(self)
        in_port.connections.append(self)

    def update_path(self):
        start = self.out_port.scenePos() + QPointF(PORT_RADIUS / 2, PORT_RADIUS / 2)
        end = self.in_port.scenePos() + QPointF(PORT_RADIUS / 2, PORT_RADIUS / 2)
        # Смещение для смешивания линий
        idx = 0
        if hasattr(self.out_port, 'connections'):
            try:
                idx = self.out_port.connections.index(self)
            except ValueError:
                idx = 0
        offset = (idx - len(self.out_port.connections) // 2) * 12  # 12px per line
        path = QPainterPath(start)
        mid_x = (start.x() + end.x()) / 2 + offset
        path.lineTo(mid_x, start.y())
        path.lineTo(mid_x, end.y())
        path.lineTo(end.x(), end.y())
        self.setPath(path)

    def mouseDoubleClickEvent(self, event):
        self.out_port.connections.remove(self)
        self.in_port.connections.remove(self)
        scene = self.scene()
        if scene:
            if hasattr(scene.parent(), 'parent') and hasattr(scene.parent().parent(), 'show_block_settings'):
                # Попытка обновить настройки блокировки, если это возможно
                main_window = scene.parent().parent()
                if hasattr(main_window, 'current_block') and main_window.current_block:
                    main_window.show_block_settings(main_window.current_block)
            scene.removeItem(self)
        super().mouseDoubleClickEvent(event)


class SchemeEditor(QGraphicsView):
    def __init__(self, parent=None, on_add_block=None, on_block_selected=None):
        super().__init__(parent)
        self.scene = SchemeScene(on_block_selected=on_block_selected)
        self.setScene(self.scene)
        # Инициализируем sceneRect **на сцене**, а не во вьюшке:
        self.scene.setSceneRect(QRectF(-1000, -1000, 2000, 2000))
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.on_add_block = on_add_block
        self.on_block_selected = on_block_selected
        self.add_block_btn = QToolButton(self)
        self.add_block_btn.setText("+")
        self.add_block_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_block_btn.setToolTip("Добавить блок")
        self.add_block_btn.setFixedSize(64, 64)
        self.add_block_btn.raise_()
        self.add_block_btn.clicked.connect(self.handle_add_block)
        self.selected_block = None
        self._scale = 1.0

    def itemChange(self, change, value):
        if change in (
                QGraphicsItem.ItemPositionChange,
                QGraphicsItem.ItemPositionHasChanged,

        ):
            # вычисляем rect_in_scene
            rect_in_scene = self.mapToScene(self.rect()).boundingRect()

            scene = self.scene()
            if isinstance(scene, SchemeScene):
                scene.ensureVisibleRect(rect_in_scene)
        return super().itemChange(change, value)


    def wheelEvent(self, event):
        # Увеличение/ уменьшение масштаба с помощью Ctrl+ колесико или просто колесико
        if event.modifiers() & Qt.ControlModifier or True:
            angle = event.angleDelta().y()
            factor = 1.15 if angle > 0 else 1 / 1.15
            self._scale *= factor
            self._scale = max(0.2, min(self._scale, 5.0))
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def handle_add_block(self):
        if self.on_add_block:
            self.on_add_block()

    def calculate_block_width(self, block_data):
        # Estimate required width for the block title and all port labels
        base_width = 180  # Increased from 160
        margin = 40
        font = QFont()
        fm = QFontMetricsF(font)
        title = block_data.get("name") or block_data.get("question") or block_data.get("condition") or block_data.get(
            "type", "")
        title_lines = title.split("\n")
        title_width = max([fm.horizontalAdvance(line) for line in title_lines]) if title_lines else 0
        max_label_width = 0
        t = block_data.get("type")

        # Calculate port label widths
        if t == "Binares":
            labels = ["Да", "Нет"]
        elif t == "Match":
            labels = block_data.get("choices", [])
            # Add extra width for Match blocks to prevent poor text wrapping
            base_width = 250  # Wider base width for Match blocks specifically
        else:
            labels = []

        for label in labels:
            for line in label.split("\n"):
                w = fm.horizontalAdvance(line)
                if w > max_label_width:
                    max_label_width = w

        # Ensure adequate width for port labels
        port_section_width = max_label_width + 80

        # For Match blocks, ensure even more space for choices
        if t == "Match" and labels:
            port_section_width += 40

        required_width = max(base_width, title_width + margin, port_section_width)
        return required_width

    def add_block_to_scene(self, block_data):
        width = self.calculate_block_width(block_data)
        block = BlockItem(block_data, width=width)
        self.scene.addItem(block)
        return block

    def resizeEvent(self, event):
        btn_margin = 10
        x = self.viewport().width() - self.add_block_btn.width() - btn_margin
        y = self.viewport().height() - self.add_block_btn.height() - btn_margin
        self.add_block_btn.move(x, y)
        super().resizeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор блок-схемы")
        self.resize(1300, 850)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая часть: редактор схемы и кнопки
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.load_btn = QPushButton("Загрузить")
        self.export_btn = QPushButton("Экспорт")
        self.add_block_btn = QPushButton("Добавить блок...")
        # self.generate_btn = QPushButton("Генерация") # Removed this line

        for btn in [self.save_btn, self.load_btn, self.export_btn,
                    self.add_block_btn]:  # Removed self.generate_btn from this list
            btn.setFixedHeight(80)
            btn.setFixedWidth(200)
            btn.setStyleSheet("font-size: 20px;")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.add_block_btn)
        # btn_layout.addWidget(self.generate_btn) # Removed this line
        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)
        self.scheme_editor = SchemeEditor(on_add_block=self.open_block_dialog,
                                          on_block_selected=self.show_block_settings)
        left_layout.addWidget(self.scheme_editor)
        main_layout.addWidget(left_widget, 3)

        # Правая часть: панель настроек блока
        self.settings_panel = QGroupBox("Настройки блока")
        self.settings_layout = QVBoxLayout(self.settings_panel)
        self.settings_form = QFormLayout()
        self.settings_layout.addLayout(self.settings_form)
        self.settings_layout.addStretch(1)
        self.delete_btn = QPushButton("Удалить блок")
        self.delete_btn.setStyleSheet("background-color: #943636; font-size: 18px;")
        self.delete_btn.setVisible(False)
        self.delete_btn.clicked.connect(self.delete_current_block)
        self.settings_layout.addSpacing(10)
        self.settings_layout.addWidget(self.delete_btn)
        main_layout.addWidget(self.settings_panel, 1)

        self.add_block_btn.clicked.connect(self.open_block_dialog)
        self.starter_exists = False
        self.ender_exists = False
        self.current_block = None
        self.match_choice_edits = []
        self._adding_match_choice = False
        self._last_edit_was_changed = False
        self.save_btn.clicked.connect(self.save_scheme)
        self.load_btn.clicked.connect(self.load_scheme)
        self.export_btn.clicked.connect(self.handle_export_click)

    def open_block_dialog(self):
        dialog = BlockCreateDialog(self, starter_exists=self.starter_exists, ender_exists=self.ender_exists)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_block_data()
            if data["type"] == "Starter":
                self.starter_exists = True
            if data["type"] == "Ender":
                self.ender_exists = True
            block = self.scheme_editor.add_block_to_scene(data)

    def show_block_settings(self, block_item):
        self.current_block = block_item
        while self.settings_form.rowCount():
            self.settings_form.removeRow(0)
        self.match_choice_edits = []
        t = block_item.block_data["type"]
        _filter_func = BlockCreateDialog._simple_filter_text

        if t in ["Starter", "Binares", "Match", "Fuzzy", "Ender"]:
            name_edit = QLineEdit(block_item.block_data.get("name", ""))
            name_edit.editingFinished.connect(lambda: self.update_block_data("name", name_edit.text()))
            name_edit.textChanged.connect(lambda: _filter_func(name_edit))
            self.settings_form.addRow("Название блока:", name_edit)

        if t == "Binares":
            cond = QLineEdit(block_item.block_data.get("condition", ""))
            cond.editingFinished.connect(lambda: self.update_block_data("condition", cond.text()))
            cond.textChanged.connect(lambda: _filter_func(cond))
            self.settings_form.addRow("Условие:", cond)
        elif t == "Match":
            q = QLineEdit(block_item.block_data.get("question", ""))
            q.editingFinished.connect(lambda: self.update_block_data("question", q.text()))
            q.textChanged.connect(lambda: _filter_func(q))
            self.settings_form.addRow("Вопрос (Match):", q)
            choices = block_item.block_data.get("choices", [])
            self._match_add_input = None
            if not choices:
                add_input = QLineEdit()
                add_input.setPlaceholderText("Введите вариант и нажмите Enter...")
                add_input.textChanged.connect(lambda: _filter_func(add_input))

                def add_first_option():
                    text = add_input.text().strip()
                    if text:
                        block_item.block_data.setdefault("choices", []).append(text)
                        block_item.update_label()
                        add_input.clear()
                        QTimer.singleShot(0, lambda: self.show_block_settings(block_item))

                add_input.editingFinished.connect(add_first_option)
                self.settings_form.addRow("Вариант:", add_input)
                self._match_add_input = add_input
            else:
                for i, val in enumerate(choices):
                    ch = QLineEdit(val)
                    ch.editingFinished.connect(partial(self.update_choice, i, ch))
                    ch.textChanged.connect(lambda: _filter_func(ch))
                    self.settings_form.addRow(f"Вариант {i + 1}:", ch)
                    self.match_choice_edits.append(ch)

                def show_add_input():
                    if self._match_add_input is not None:
                        return
                    add_input_field = QLineEdit()
                    add_input_field.setPlaceholderText("Введите новый вариант и нажмите Enter...")
                    add_input_field.textChanged.connect(lambda: _filter_func(add_input_field))

                    def add_new_option_delayed():
                        new_text = add_input_field.text().strip()
                        if new_text:
                            block_item.block_data.setdefault("choices", []).append(new_text)
                            block_item.update_label()
                            self.settings_form.removeRow(add_input_field)
                            self._match_add_input = None
                            QTimer.singleShot(0, lambda: self.show_block_settings(block_item))
                        else:
                            self.settings_form.removeRow(add_input_field)
                            self._match_add_input = None

                    add_input_field.editingFinished.connect(add_new_option_delayed)
                    self.settings_form.addRow("Новый вариант:", add_input_field)
                    add_input_field.setFocus()
                    self._match_add_input = add_input_field

                add_btn = QPushButton("Добавить вариант")
                add_btn.clicked.connect(show_add_input)
                self.settings_form.addRow("", add_btn)
                if choices:
                    del_btn = QPushButton("Удалить последний вариант")
                    del_btn.clicked.connect(self.remove_match_choice)
                    self.settings_form.addRow("", del_btn)
        elif t == "Fuzzy":
            q = QLineEdit(block_item.block_data.get("question", ""))
            q.editingFinished.connect(lambda: self.update_block_data("question", q.text()))
            q.textChanged.connect(lambda: _filter_func(q))
            self.settings_form.addRow("Вопрос (Fuzzy):", q)
        elif t == "Ender":
            verdict_edit = QLineEdit(block_item.block_data.get("verdict", ""))
            verdict_edit.editingFinished.connect(lambda: self.update_block_data("verdict", verdict_edit.text()))
            verdict_edit.textChanged.connect(lambda: _filter_func(verdict_edit))
            self.settings_form.addRow("Вердикт:", verdict_edit)

        # Показываем соединения
        self.settings_form.addRow(QLabel("<b>Связи блока:</b>"))
        # Получение текущей ширины панели настроек, чтобы ограничить ширину надписи
        settings_panel_width = self.settings_panel.width()
        # Рассчёт ширины 3/4, учитывая, что поля / отступы могут повлиять на полезную ширину
        max_label_width = int(settings_panel_width * 0.75) - 20

        for port in getattr(block_item, 'ports_in', []) + getattr(block_item, 'ports_out', []):
            for conn in getattr(port, 'connections', []):
                other_block = conn.out_port.parent_block if conn.in_port.parent_block == block_item else conn.in_port.parent_block
                desc_text = f"{conn.out_port.parent_block.get_title()} → {conn.in_port.parent_block.get_title()}"

                desc_label = QLabel(desc_text)
                desc_label.setWordWrap(True)
                desc_label.setMaximumWidth(max_label_width)

                del_btn = QPushButton("Удалить связь")

                def make_del(c):
                    return lambda: self.delete_connection(c)

                del_btn.clicked.connect(make_del(conn))
                self.settings_form.addRow(desc_label, del_btn)
        self.delete_btn.setVisible(True)

    def update_block_data(self, key, value):
        if self.current_block:
            # Only update if the value actually changed
            if self.current_block.block_data.get(key) != value:
                self.current_block.block_data[key] = value
                self.current_block.update_label()

    def update_choice(self, idx, ch):
        if self.current_block:
            if "choices" in self.current_block.block_data:
                # Check if the value has actually changed before updating
                current_value = self.current_block.block_data["choices"][idx]
                new_value = ch.text()

                if current_value != new_value:
                    self.current_block.block_data["choices"][idx] = new_value
                    self.current_block.update_label()

    def remove_match_choice(self):
        if self.current_block and self.current_block.block_data["type"] == "Match":
            if self.current_block.block_data.get("choices"):
                self.current_block.block_data["choices"].pop()
                self.current_block.update_label()
                self.show_block_settings(self.current_block)

    def delete_current_block(self):
        if self.current_block:
            # Удалить соединения
            for port in getattr(self.current_block, 'ports_in', []) + getattr(self.current_block, 'ports_out', []):
                for conn in getattr(port, 'connections', []):
                    self.scheme_editor.scene.removeItem(conn)
            self.scheme_editor.scene.removeItem(self.current_block)
            self.current_block = None
            self.delete_btn.setVisible(False)
            while self.settings_form.rowCount():
                self.settings_form.removeRow(0)

    def delete_connection(self, conn):
        # Удалить соединение из сцены и портов
        if conn in self.scheme_editor.scene.connections:
            self.scheme_editor.scene.connections.remove(conn)
        if conn in conn.out_port.connections:
            conn.out_port.connections.remove(conn)
        if conn in conn.in_port.connections:
            conn.in_port.connections.remove(conn)
        self.scheme_editor.scene.removeItem(conn)
        # Обновить настройки
        if self.current_block:
            self.show_block_settings(self.current_block)

    def save_scheme(self, f='') -> str:
        print(f"save_scheme === [{f}]")
        from PySide6.QtWidgets import QFileDialog
        filename = f
        if filename == False:
            filename, _ = QFileDialog.getSaveFileName(self, "Сохранить схему", "", "JSON Files (*.json)")
        if filename:
            self.export_scheme(filename)
        return filename

    def handle_export_click(self):
        r = self.save_scheme("default01" + str(self.__hash__()) + ".json")
        reader(r)
        os.remove(r)

    def export_scheme(self, filename):
        blocks = []
        block_id_map = {}
        for item in self.scheme_editor.scene.items():
            if isinstance(item, BlockItem):
                # Присваиваем уникальный id, если его нет
                block_id = item.block_data.get('id')
                if not block_id:
                    block_type = item.block_data.get('type')
                    prefix = 'u'
                    if block_type == "Starter":
                        prefix = 's'
                    elif block_type == "Ender":
                        prefix = 'e'
                    elif block_type == "Binares":
                        prefix = 'b'
                    elif block_type == "Match":
                        prefix = 'm'
                    elif block_type == "Fuzzy":
                        prefix = 'f'
                    block_id = f"{prefix}_{uuid.uuid4().hex}"

                item.block_data['id'] = block_id
                block_id_map[item] = block_id
                block_data = item.block_data.copy()
                pos = item.pos()
                block_data['pos'] = (pos.x(), pos.y())

                # DIAGNOSTIC for export
                if block_data.get('type') == 'Fuzzy':
                    print(f"DEBUG EXPORT: Fuzzy block '{block_data.get('name', block_data.get('id'))}' "
                          f"fuzzy_config to be saved: {block_data.get('fuzzy_config')}")

                blocks.append(block_data)
        connections = []
        for item in self.scheme_editor.scene.items():
            if isinstance(item, ConnectionItem):
                out_block = item.out_port.parent_block
                in_block = item.in_port.parent_block
                connections.append({
                    'from': block_id_map.get(out_block),
                    'to': block_id_map.get(in_block),
                    'out_idx': item.out_port.idx,
                    'in_idx': item.in_port.idx
                })
        scheme = {'blocks': blocks, 'connections': connections}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scheme, f, ensure_ascii=False, indent=2)

    def load_scheme(self):
        from PySide6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить схему", "", "JSON Files (*.json)")
        if filename:
            self.import_scheme(filename)

    def import_scheme(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            scheme = json.load(f)
        # Очистить сцену
        for item in list(self.scheme_editor.scene.items()):
            if isinstance(item, (BlockItem, ConnectionItem)):
                self.scheme_editor.scene.removeItem(item)
        self.starter_exists = False
        self.ender_exists = False
        block_objs = {}
        # Восстановить блоки
        for block_data in scheme.get('blocks', []):
            pos = block_data.pop('pos', (100, 100))
            block_id = block_data.get('id')

            # DIAGNOSTIC for import
            if block_data.get('type') == 'Fuzzy':
                print(f"DEBUG IMPORT: Fuzzy block '{block_data.get('name', block_id)}' "
                      f"fuzzy_config loaded from JSON: {block_data.get('fuzzy_config')}")

            block = self.scheme_editor.add_block_to_scene(block_data)
            block.setPos(*pos)
            block_objs[block_id] = block
            if block_data.get('type') == 'Starter':
                self.starter_exists = True
            if block_data.get('type') == 'Ender':
                self.ender_exists = True
        # Восстановить соединения
        for conn in scheme.get('connections', []):
            out_block = block_objs.get(conn['from'])
            in_block = block_objs.get(conn['to'])
            if out_block is None or in_block is None:
                continue
            out_port = out_block.ports_out[conn['out_idx']]
            in_port = in_block.ports_in[conn['in_idx']]
            connection = ConnectionItem(out_port, in_port)
            self.scheme_editor.scene.addItem(connection)
            self.scheme_editor.scene.connections.append(connection)


class FuzzyConfigDialog(QDialog):
    def __init__(self, initial_fuzzy_config_data=None, block_display_title="Блок нечеткой логики", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки блока нечеткой логики")
        self.setMinimumWidth(800);
        self.setMinimumHeight(700)
        self.config_data = initial_fuzzy_config_data if initial_fuzzy_config_data is not None else {}
        self._loading_config = False
        self.antecedent_group_widgets = [];
        self.consequent_widgets = {};
        self.rule_group_widgets = []
        main_layout = QVBoxLayout(self)
        self.title_display_box = QLineEdit();
        self.title_display_box.setText(block_display_title);
        self.title_display_box.setReadOnly(True)
        self.title_display_box.textChanged.connect(
            lambda: BlockCreateDialog._simple_filter_text(self.title_display_box))
        h_layout = QHBoxLayout();
        left_panel_layout = QVBoxLayout();
        h_layout.addLayout(left_panel_layout, 1)
        antecedents_main_group = QGroupBox("Antecedents");
        left_panel_layout.addWidget(antecedents_main_group)
        antecedents_main_group_layout = QVBoxLayout(antecedents_main_group)
        self.add_antecedent_button = QPushButton("Добавить антецедент");
        self.add_antecedent_button.clicked.connect(self._add_antecedent_ui_slot)
        antecedents_main_group_layout.addWidget(self.add_antecedent_button)
        self.antecedents_scroll_area = QScrollArea();
        antecedents_scroll_content_widget = QWidget()
        self.antecedents_container_layout = QVBoxLayout(antecedents_scroll_content_widget)
        self.antecedents_scroll_area.setWidget(antecedents_scroll_content_widget);
        self.antecedents_scroll_area.setWidgetResizable(True);
        self.antecedents_scroll_area.setMaximumHeight(350)
        antecedents_main_group_layout.addWidget(self.antecedents_scroll_area)
        consequents_main_group = QGroupBox("Consequents");
        left_panel_layout.addWidget(consequents_main_group)
        consequents_main_group_layout = QVBoxLayout(consequents_main_group)
        consequent_group_box, self.consequent_widgets = self._create_parameter_ui("Консеквент", is_checkable=False,
                                                                                  is_consequent=True)
        consequents_main_group_layout.addWidget(consequent_group_box)
        right_panel_layout = QVBoxLayout();
        h_layout.addLayout(right_panel_layout, 1)
        rules_main_group = QGroupBox("Rule Definitions");
        right_panel_layout.addWidget(rules_main_group)
        rules_main_group_layout = QVBoxLayout(rules_main_group)
        self.add_rule_button = QPushButton("Добавить правило");
        self.add_rule_button.clicked.connect(self._add_rule_ui_slot)
        rules_main_group_layout.addWidget(self.add_rule_button)
        self.rules_scroll_area = QScrollArea();
        rules_scroll_content_widget = QWidget()
        self.rules_container_layout = QVBoxLayout(rules_scroll_content_widget);
        self.rules_container_layout.addStretch(1)
        self.rules_scroll_area.setWidget(rules_scroll_content_widget);
        self.rules_scroll_area.setWidgetResizable(True);
        self.rules_scroll_area.setMaximumHeight(480)
        rules_main_group_layout.addWidget(self.rules_scroll_area)
        self._load_existing_config()
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok);
        btn_box.accepted.connect(self.accept)
        main_layout.addWidget(self.title_display_box);
        main_layout.addLayout(h_layout, 1);
        main_layout.addWidget(btn_box)
        self._update_add_antecedent_button_state();
        self._update_add_rule_button_state()
        QTimer.singleShot(0, self._delayed_initial_rule_update)

    def _handle_name_or_term_change(self, text_from_signal, field_type="unknown"):
        if not self._loading_config:
            self._update_all_rule_widgets_content()
            if field_type in ["antecedent_name", "antecedent_term_name"]:
                self._update_add_rule_button_state()

    def _delayed_initial_rule_update(self):
        QApplication.processEvents()
        self._update_all_rule_widgets_content()
        if self._check_conditions_for_rules() and not self.rule_group_widgets:
            self._add_rule_ui_slot()

    def _filter_text_input(self, line_edit):
        current_text = line_edit.text();
        filtered_text = current_text.replace('{', '').replace('}', '')
        if current_text != filtered_text:
            cursor_pos = line_edit.cursorPosition()
            removed_chars = sum(
                1 for char_idx in range(min(cursor_pos, len(current_text))) if current_text[char_idx] in ('{', '}'))
            line_edit.setText(filtered_text);
            line_edit.setCursorPosition(max(0, cursor_pos - removed_chars))

    def _create_parameter_ui(self, title, is_checkable=True, is_consequent=False):
        group_box = QGroupBox(title)
        if is_checkable: group_box.setCheckable(True); group_box.setChecked(True)
        sp = group_box.sizePolicy();
        sp.setVerticalPolicy(QSizePolicy.Preferred if is_consequent else QSizePolicy.Fixed);
        group_box.setSizePolicy(sp)
        group_layout = QVBoxLayout(group_box)
        name_edit = QLineEdit();
        name_edit.setPlaceholderText(f"Название ({title.lower()})");
        group_layout.addWidget(name_edit)

        name_edit.textChanged.connect(lambda: self._filter_text_input(name_edit))  # Filter input
        field_type = "antecedent_name" if not is_consequent else "consequent_name"
        handler = functools.partial(self._handle_name_or_term_change, field_type=field_type)
        name_edit.textChanged.connect(handler)  # Connect to central handler

        locale = QLocale(QLocale.C);
        double_validator = QDoubleValidator(-float('inf'), float('inf'), 4, self);
        double_validator.setLocale(locale)
        positive_double_validator = QDoubleValidator(0.0001, float('inf'), 4, self);
        positive_double_validator.setLocale(locale)
        params_grid = QGridLayout();
        group_layout.addLayout(params_grid)
        range_frame = QFrame();
        range_frame.setFrameShape(QFrame.Panel);
        range_frame.setFrameShadow(QFrame.Sunken);
        range_layout = QVBoxLayout(range_frame);
        range_label = QLabel("Range");
        range_label.setAlignment(Qt.AlignCenter);
        range_layout.addWidget(range_label);
        range_edits_layout = QHBoxLayout();
        range_min_edit = QLineEdit();
        range_min_edit.setPlaceholderText("Min");
        range_min_edit.setValidator(double_validator);
        range_edits_layout.addWidget(range_min_edit);
        range_max_edit = QLineEdit();
        range_max_edit.setPlaceholderText("Max");
        range_max_edit.setValidator(double_validator);
        range_edits_layout.addWidget(range_max_edit);
        range_layout.addLayout(range_edits_layout);
        params_grid.addWidget(range_frame, 0, 0);
        range_min_edit.textChanged.connect(lambda: self._filter_text_input(range_min_edit));
        range_max_edit.textChanged.connect(lambda: self._filter_text_input(range_max_edit));
        step_frame = QFrame();
        step_frame.setFrameShape(QFrame.Panel);
        step_frame.setFrameShadow(QFrame.Sunken);
        step_layout = QVBoxLayout(step_frame);
        step_label = QLabel("Step");
        step_label.setAlignment(Qt.AlignCenter);
        step_layout.addWidget(step_label);
        step_edit = QLineEdit();
        step_edit.setPlaceholderText("Значение");
        step_edit.setValidator(positive_double_validator);
        step_layout.addWidget(step_edit);
        params_grid.addWidget(step_frame, 0, 1);
        step_edit.textChanged.connect(lambda: self._filter_text_input(step_edit));
        terms_label = QLabel("Термы:");
        group_layout.addWidget(terms_label)
        terms_layout_container_widget = QWidget();
        terms_layout = QVBoxLayout(terms_layout_container_widget);
        terms_layout.setContentsMargins(0, 0, 0, 0)
        if is_consequent:
            terms_scroll_area = QScrollArea();
            terms_scroll_area.setWidgetResizable(True);
            terms_scroll_area.setMaximumHeight(110);
            terms_scroll_area.setWidget(terms_layout_container_widget);
            group_layout.addWidget(terms_scroll_area);
            terms_layout.addStretch(1)
        else:
            group_layout.addWidget(terms_layout_container_widget)
        term_buttons_layout = QHBoxLayout();
        add_term_button = QPushButton("Добавить терм");
        remove_term_button = QPushButton("Удалить терм");
        term_buttons_layout.addWidget(add_term_button);
        term_buttons_layout.addWidget(remove_term_button);
        group_layout.addLayout(term_buttons_layout)
        widgets = {"group_box": group_box, "name_edit": name_edit, "range_min_edit": range_min_edit,
                   "range_max_edit": range_max_edit, "step_edit": step_edit, "terms_layout": terms_layout,
                   "term_structures": [], "add_term_button": add_term_button, "remove_term_button": remove_term_button,
                   "is_consequent": is_consequent}
        add_term_button.clicked.connect(lambda: self._add_term_field(widgets));
        remove_term_button.clicked.connect(lambda: self._remove_last_term_field(widgets))
        self._update_term_buttons_state(widgets)
        if is_checkable: group_box.toggled.connect(
            lambda checked, gb=group_box, w=widgets: self._handle_antecedent_removal(checked, gb, w))
        return group_box, widgets

    def _add_term_field(self, owner_widgets_dict, term_data=None):
        if len(owner_widgets_dict["term_structures"]) < 3:
            term_container_widget = QWidget();
            term_layout = QHBoxLayout(term_container_widget);
            term_layout.setContentsMargins(0, 0, 0, 0)
            name_text = term_data.get("name", "") if term_data else ""
            name_edit = QLineEdit(name_text);
            name_edit.setPlaceholderText(f"Терм {len(owner_widgets_dict['term_structures']) + 1}")

            name_edit.textChanged.connect(lambda text, te=name_edit: self._filter_text_input(te))  # Filter input
            field_type = "consequent_term_name" if owner_widgets_dict.get("is_consequent") else "antecedent_term_name"
            handler = functools.partial(self._handle_name_or_term_change, field_type=field_type)
            name_edit.textChanged.connect(handler)  # Connect to central handler

            term_layout.addWidget(name_edit, 2)
            value_edits = []
            locale = QLocale(QLocale.C);
            validator = QDoubleValidator(-float('inf'), float('inf'), 4, self);
            validator.setLocale(locale);
            validator.setNotation(QDoubleValidator.StandardNotation)
            for i in range(4):
                val_text = "";
                if term_data and "values" in term_data and i < len(term_data["values"]): val_text = term_data["values"][
                    i]
                val_edit = QLineEdit(val_text);
                val_edit.setPlaceholderText(f"Значение {i + 1}");
                val_edit.setValidator(validator);
                term_layout.addWidget(val_edit, 1);
                value_edits.append(val_edit)
            target_layout = owner_widgets_dict["terms_layout"]
            if owner_widgets_dict.get("is_consequent", False):
                if target_layout.count() > 0 and target_layout.itemAt(target_layout.count() - 1).spacerItem():
                    target_layout.insertWidget(target_layout.count() - 1, term_container_widget)
                else:
                    target_layout.addWidget(term_container_widget);
                    target_layout.addStretch(1)
            else:
                target_layout.addWidget(term_container_widget)
            owner_widgets_dict["term_structures"].append({
                "name_edit": name_edit, "value_edits": value_edits, "container_widget": term_container_widget
            })
            self._update_term_buttons_state(owner_widgets_dict)
            # Direct calls to _update_all_rule_widgets_content or _update_add_rule_button_state are NOT made here,
            # as they are handled by _handle_name_or_term_change (if text changes) or by _delayed_initial_rule_update.
            self.adjustSize()

    def _remove_last_term_field(self, owner_widgets_dict):
        if owner_widgets_dict["term_structures"]:
            term_structure_to_remove = owner_widgets_dict["term_structures"].pop();
            container_widget = term_structure_to_remove["container_widget"]
            owner_widgets_dict["terms_layout"].removeWidget(container_widget);
            container_widget.deleteLater()
            self._update_term_buttons_state(owner_widgets_dict)
            if not self._loading_config:  # This method modifies structure, so an update is needed if not loading
                self._update_all_rule_widgets_content()
                if not owner_widgets_dict.get("is_consequent", False):
                    self._update_add_rule_button_state()
            self.adjustSize()

    def _add_antecedent_ui_slot(self, data=None):
        if len(self.antecedent_group_widgets) < 3:
            index = len(self.antecedent_group_widgets)
            new_antecedent_group_box = self._create_antecedent_group_ui(index, data)
            self.antecedents_container_layout.addWidget(new_antecedent_group_box)
            self._update_add_antecedent_button_state()
            if not self._loading_config:  # This method adds new UI elements, update if not loading
                self._update_all_rule_widgets_content()
                self._update_add_rule_button_state()  # New antecedent might enable rule adding
            self.adjustSize()
        else:
            print("Максимум 3 антецедента.")

    def _handle_antecedent_removal(self, checked, group_box, widgets_dict_ref):
        if not checked:  # Antecedent is being disabled/removed
            if widgets_dict_ref in self.antecedent_group_widgets:
                self.antecedent_group_widgets.remove(widgets_dict_ref);
                self.antecedents_container_layout.removeWidget(group_box);
                group_box.setParent(None)
                for i, ant_widgets_dict in enumerate(self.antecedent_group_widgets): ant_widgets_dict[
                    "group_box"].setTitle(f"Антецедент {i + 1}")
        self._update_add_antecedent_button_state()
        if not self._loading_config:  # UI structure changed, update if not loading
            self._update_all_rule_widgets_content()
            self._update_add_rule_button_state()
        self.adjustSize()

    def _add_rule_ui_slot(self, data=None):
        new_rule_group_box = self._create_rule_group_ui(len(self.rule_group_widgets), data)
        if self.rules_container_layout.count() > 0 and self.rules_container_layout.itemAt(
                self.rules_container_layout.count() - 1).spacerItem():
            self.rules_container_layout.insertWidget(self.rules_container_layout.count() - 1, new_rule_group_box)
        else:
            self.rules_container_layout.addWidget(new_rule_group_box)
            if not (self.rules_container_layout.count() > 0 and self.rules_container_layout.itemAt(
                    self.rules_container_layout.count() - 1).spacerItem()): self.rules_container_layout.addStretch(1)
        if not self._loading_config:  # New rule added, update if not loading
            self._update_all_rule_widgets_content()  # Update to populate its combo boxes
        self._update_add_rule_button_state()  # Check if more rules can be added / conditions for existing ones
        self.adjustSize()
        for i, rule_dict in enumerate(self.rule_group_widgets):
            if "group_box" in rule_dict and hasattr(rule_dict["group_box"], 'setTitle'): rule_dict[
                "group_box"].setTitle(f"Правило {i + 1}")

    def _handle_rule_removal(self, checked, group_box):
        if not checked:  # Rule is being disabled/removed
            widget_to_remove = None;
            for widgets_dict_item in self.rule_group_widgets:
                if widgets_dict_item["group_box"] == group_box: widget_to_remove = widgets_dict_item; break
            if widget_to_remove:
                self.rule_group_widgets.remove(widget_to_remove);
                self.rules_container_layout.removeWidget(group_box);
                group_box.setParent(None)
                for i, rule_widgets_dict_item in enumerate(self.rule_group_widgets): rule_widgets_dict_item[
                    "group_box"].setTitle(f"Правило {i + 1}")
        if not self._loading_config:  # UI structure changed
            self._update_all_rule_widgets_content()
        # Always update rule button state as conditions for adding might change
        self._update_add_rule_button_state()
        self.adjustSize()

    def _load_existing_config(self):  # Ensure this is correctly implemented as per previous fixes
        self._loading_config = True
        try:
            print("DEBUG: Loading existing config from:", self.config_data)
            existing_antecedents_map = self.config_data.get('antecedents', {})
            if existing_antecedents_map:
                processed_ants_count = 0
                for ant_name, saved_ant_data_dict in existing_antecedents_map.items():
                    if processed_ants_count >= 3: break
                    transformed_data_for_ui = {"name": ant_name, "is_active": True}
                    range_values = saved_ant_data_dict.get("range", [0.0, 0.0, 0.0])
                    if isinstance(range_values, list) and len(range_values) == 3:
                        transformed_data_for_ui["range_min"] = str(range_values[0])
                        transformed_data_for_ui["range_max"] = str(range_values[1])
                        transformed_data_for_ui["step"] = str(range_values[2])
                    else:
                        transformed_data_for_ui["range_min"] = "0"
                        transformed_data_for_ui["range_max"] = "0"
                        transformed_data_for_ui["step"] = "0"

                    ui_terms_list = []
                    # Use term_order if available, otherwise fall back to dictionary iteration
                    term_order = saved_ant_data_dict.get("term_order", [])
                    saved_terms_map = saved_ant_data_dict.get("terms", {})

                    print(f"DEBUG: Loading antecedent '{ant_name}' with terms:", saved_terms_map)

                    # If we have term_order, use it to process terms in order
                    if term_order and isinstance(term_order, list):
                        for term_name in term_order:
                            if term_name in saved_terms_map:
                                term_details = saved_terms_map[term_name]
                                # Handle both tuple and list formats
                                if (isinstance(term_details, tuple) or isinstance(term_details, list)) and len(
                                        term_details) == 2:
                                    term_float_values = term_details[1]
                                    if isinstance(term_float_values, list):
                                        ui_terms_list.append(
                                            {"name": term_name, "values": [str(v) for v in term_float_values]})
                    # Otherwise, iterate through the dictionary (no guaranteed order)
                    elif isinstance(saved_terms_map, dict):
                        for term_name, term_details in saved_terms_map.items():
                            # Handle both tuple and list formats
                            if (isinstance(term_details, tuple) or isinstance(term_details, list)) and len(
                                    term_details) == 2:
                                term_float_values = term_details[1]
                                if isinstance(term_float_values, list):
                                    ui_terms_list.append(
                                        {"name": term_name, "values": [str(v) for v in term_float_values]})

                    print(f"DEBUG: Created UI terms list for antecedent '{ant_name}':", ui_terms_list)
                    transformed_data_for_ui["terms"] = ui_terms_list
                    self._add_antecedent_ui_slot(transformed_data_for_ui)
                    processed_ants_count += 1
            elif not self.antecedent_group_widgets:
                self._add_antecedent_ui_slot()

            existing_consequent_map = self.config_data.get('consequent', {})
            if existing_consequent_map and self.consequent_widgets:
                cons_name, saved_cons_data_dict = next(iter(existing_consequent_map.items()), (None, None))
                if cons_name and saved_cons_data_dict:
                    self.consequent_widgets["name_edit"].setText(cons_name)
                    range_values = saved_cons_data_dict.get("range", [0.0, 0.0, 0.0])
                    if isinstance(range_values, list) and len(range_values) == 3:
                        self.consequent_widgets["range_min_edit"].setText(str(range_values[0]))
                        self.consequent_widgets["range_max_edit"].setText(str(range_values[1]))
                        self.consequent_widgets["step_edit"].setText(str(range_values[2]))
                    else:
                        self.consequent_widgets["range_min_edit"].setText("0")
                        self.consequent_widgets["range_max_edit"].setText("0")
                        self.consequent_widgets["step_edit"].setText("0")

                    print(f"DEBUG: Loading consequent '{cons_name}' with terms:", saved_cons_data_dict.get("terms", {}))

                    # Use term_order if available for consequent too
                    term_order = saved_cons_data_dict.get("term_order", [])
                    saved_terms_map = saved_cons_data_dict.get("terms", {})

                    # If we have term_order, use it
                    if term_order and isinstance(term_order, list):
                        for term_name in term_order:
                            if term_name in saved_terms_map:
                                term_details = saved_terms_map[term_name]
                                # Handle both tuple and list formats
                                if (isinstance(term_details, tuple) or isinstance(term_details, list)) and len(
                                        term_details) == 2:
                                    term_float_values = term_details[1]
                                    if isinstance(term_float_values, list):
                                        term_data_for_ui = {"name": term_name,
                                                            "values": [str(v) for v in term_float_values]}
                                        self._add_term_field(self.consequent_widgets, term_data_for_ui)
                    # Otherwise, iterate through the dictionary
                    elif isinstance(saved_terms_map, dict):
                        for term_name, term_details in saved_terms_map.items():
                            # Handle both tuple and list formats
                            if (isinstance(term_details, tuple) or isinstance(term_details, list)) and len(
                                    term_details) == 2:
                                term_float_values = term_details[1]
                                if isinstance(term_float_values, list):
                                    term_data_for_ui = {"name": term_name,
                                                        "values": [str(v) for v in term_float_values]}
                                    self._add_term_field(self.consequent_widgets, term_data_for_ui)

            # Save all rule data for later processing
            self.saved_rule_definitions = self.config_data.get('rule_definitions', [])
            existing_rules = self.saved_rule_definitions

            print(f"DEBUG: Loading {len(existing_rules)} rules:", existing_rules)
            if existing_rules:
                for rule_data in existing_rules:
                    self._add_rule_ui_slot(rule_data)  # Create rules with data

            # Explicitly update all rule widgets AFTER all UI components have been created
            self._update_all_rule_widgets_content()

            # Set selections in all rules with a longer delay for Qt to finish UI updates
            QTimer.singleShot(500, self._set_rule_selections)

        finally:
            self._loading_config = False

    def _set_rule_selections(self):
        """Set rule combo box selections directly, bypassing other mechanisms."""
        if not hasattr(self, 'saved_rule_definitions') or not self.saved_rule_definitions:
            print("DEBUG: No saved rule definitions to apply")
            return

        print(f"DEBUG: Setting selections for {len(self.saved_rule_definitions)} rules")

        # Process each rule
        for i, rule_data in enumerate(self.saved_rule_definitions):
            if i >= len(self.rule_group_widgets):
                print(f"DEBUG: Rule index {i} out of range for UI widgets")
                continue

            print(f"DEBUG: Setting selections for rule {i + 1}: {rule_data}")
            rule_widgets = self.rule_group_widgets[i]

            # Process each IF condition
            if_conditions = rule_data.get("if", [])
            for j, condition in enumerate(if_conditions):
                if j >= len(rule_widgets["antecedent_rows"]):
                    print(f'TAERON DEBUG: j = {j} >= than {len(rule_widgets["antecedent_rows"])} CONTINUE')
                    continue
                print(f'TAERON DEBUG: -1=2- CONTINUE NOT HAPPEN')
                print(f'TAERON DEBUG: condition == {condition} and {print(type(condition))}')

                if isinstance(condition, list) and len(condition) == 2:
                    print(f'TAERON DEBUG: INSTANCE SUCCESSFUL')
                    _, term_name = condition
                    combo = rule_widgets["antecedent_rows"][j]["combo"]

                    # Force a direct text setting by term name
                    combo.setCurrentText(term_name)
                    print(f"DEBUG: Direct setting rule {i + 1}, antecedent {j + 1} to '{term_name}'")

            # Process THEN condition
            then_condition = rule_data.get("then")
            if then_condition and isinstance(then_condition, tuple) and len(then_condition) == 2:
                _, term_name = then_condition

                # Force a direct text setting for consequent
                cons_combo = rule_widgets["consequent_combo"]
                cons_combo.setCurrentText(term_name)
                print(f"DEBUG: Direct setting rule {i + 1}, consequent to '{term_name}'")

            # Set logic
            logic_value = rule_data.get("logic")
            if logic_value == "OR":
                rule_widgets["logic_or_rb"].setChecked(True)
            else:
                rule_widgets["logic_and_rb"].setChecked(True)

    def _update_term_buttons_state(self, owner_widgets_dict):
        can_add = len(owner_widgets_dict["term_structures"]) < 3
        can_remove = len(owner_widgets_dict["term_structures"]) > 0
        owner_widgets_dict["add_term_button"].setEnabled(can_add)
        owner_widgets_dict["remove_term_button"].setEnabled(can_remove)

    def _create_antecedent_group_ui(self, index, data=None):
        antecedent_group, widgets = self._create_parameter_ui(f"Антецедент {index + 1}", is_checkable=True)
        self.antecedent_group_widgets.append(widgets)
        if data:
            widgets["name_edit"].setText(data.get("name", ""))
            widgets["range_min_edit"].setText(data.get("range_min", ""))
            widgets["range_max_edit"].setText(data.get("range_max", ""))
            widgets["step_edit"].setText(data.get("step", ""))
            for term_data_item in data.get("terms", []):
                self._add_term_field(widgets, term_data_item)
            widgets["group_box"].setChecked(data.get("is_active", True))
        else:
            widgets["group_box"].setChecked(True)
            if not widgets["term_structures"]: self._add_term_field(widgets)
        return antecedent_group

    def _update_add_antecedent_button_state(self):
        self.add_antecedent_button.setEnabled(len(self.antecedent_group_widgets) < 3)

    def _create_rule_group_ui(self, index, data=None):
        rule_group = QGroupBox(f"Правило {index + 1}")
        rule_group.setCheckable(True)
        rule_group.setChecked(True)

        sp = rule_group.sizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Fixed)
        rule_group.setSizePolicy(sp)

        layout = QGridLayout(rule_group)
        current_row = 0

        rule_widgets = {
            "group_box": rule_group,
            "antecedent_rows": [],
            "logic_or_rb": None, "logic_and_rb": None,
            "consequent_label": None, "consequent_combo": None,
            "logic_label": None,
            "selected_terms": []  # Store selected terms here
        }

        # Add new field for the selected consequent
        rule_widgets["selected_consequent"] = None

        # Store rule data for later reference
        if data:
            rule_widgets["rule_data"] = data

        for i in range(3):  # Max 3 antecedents
            ant_label = QLabel(f"IF Антецедент {i + 1} IS:")
            ant_combo = QComboBox()
            ant_combo.setMinimumWidth(100)

            # Использование метки в качестве виджета для отображения/скрытия строки
            # Управление видимостью ant_label и ant_combo
            layout.addWidget(ant_label, current_row, 0)
            layout.addWidget(ant_combo, current_row, 1, 1, 2)

            rule_widgets["antecedent_rows"].append({
                "label": ant_label, "combo": ant_combo,
                "visible_widgets": [ant_label, ant_combo]
            })
            current_row += 1

        logic_label_widget = QLabel("Логика:")
        layout.addWidget(logic_label_widget, current_row, 0)

        # Fix for overlapping radio buttons - increase spacing and width
        logic_layout = QHBoxLayout()
        logic_layout.setSpacing(15)  # Increase spacing between radio buttons

        rb_or = QRadioButton("OR")
        rb_and = QRadioButton("AND")
        rb_and.setChecked(True)

        # Set minimum width for radio buttons to prevent text truncation
        rb_or.setMinimumWidth(60)
        rb_and.setMinimumWidth(60)

        logic_layout.addWidget(rb_or)
        logic_layout.addWidget(rb_and)
        logic_layout.addStretch(1)  # Add stretch to push radio buttons to the left

        layout.addLayout(logic_layout, current_row, 1, 1, 2)
        rule_widgets["logic_or_rb"] = rb_or
        rule_widgets["logic_and_rb"] = rb_and
        rule_widgets["logic_label"] = logic_label_widget
        current_row += 1

        cons_label = QLabel("THEN Консеквент IS:")
        cons_combo = QComboBox()
        cons_combo.setMinimumWidth(100)
        layout.addWidget(cons_label, current_row, 0)
        layout.addWidget(cons_combo, current_row, 1, 1, 2)
        rule_widgets["consequent_label"] = cons_label
        rule_widgets["consequent_combo"] = cons_combo

        self.rule_group_widgets.append(rule_widgets)
        rule_group.toggled.connect(lambda checked, gb=rule_group: self._handle_rule_removal(checked, gb))

        if data:
            # Store the antecedent and consequent term selections directly in the widget dict
            # Antecedent terms for combo pre-selection
            if_conditions = data.get("if", [])
            rule_widgets["selected_terms"] = []
            for i, ant_condition in enumerate(if_conditions):
                if isinstance(ant_condition, tuple) and len(ant_condition) == 2:
                    rule_widgets["selected_terms"].append(ant_condition[1])
                else:
                    rule_widgets["selected_terms"].append(None)

            # Fill with None values for any missing antecedents
            while len(rule_widgets["selected_terms"]) < 3:
                rule_widgets["selected_terms"].append(None)

            # Logic
            logic_value = data.get("logic")
            if logic_value == "OR":
                rule_widgets["logic_or_rb"].setChecked(True)
            else:  # Default to AND if not "OR" or if logic is None (for single antecedent rule)
                rule_widgets["logic_and_rb"].setChecked(True)

            # Consequent term for combo pre-selection
            then_condition = data.get("then")  # tuple (cons_name, term_name) or None
            if then_condition and isinstance(then_condition, tuple) and len(then_condition) == 2:
                # Store the consequent term name directly
                rule_widgets["selected_consequent"] = then_condition[1]

            # Explicitly call update for this rule to set combos as soon as they're created
            QTimer.singleShot(10, lambda: self._update_rule_combos(rule_widgets))

        return rule_group

    def _update_rule_combos(self, rule_widgets):
        """Update a single rule's combo boxes with available terms and select the right ones."""
        print("DEBUG: Updating rule combos directly for widget:", rule_widgets.get("group_box").title())

        if not rule_widgets or not hasattr(rule_widgets, "get"):
            return

        # Get all active antecedents and their terms
        active_antecedents_info = []
        for ant_w_dict in self.antecedent_group_widgets:
            if ant_w_dict["group_box"].isChecked():
                name = ant_w_dict["name_edit"].text().strip()
                if name:
                    terms = [ts["name_edit"].text().strip() for ts in ant_w_dict["term_structures"] if
                             ts["name_edit"].text().strip()]
                    active_antecedents_info.append({"name": name, "terms": terms})

        # Get consequent terms
        consequent_name = self.consequent_widgets.get("name_edit", QLineEdit()).text().strip() or "Консеквент"
        consequent_terms = []
        if "term_structures" in self.consequent_widgets:
            consequent_terms = [ts["name_edit"].text().strip() for ts in self.consequent_widgets["term_structures"] if
                                ts["name_edit"].text().strip()]

        # Process rule data if available
        rule_data = rule_widgets.get("rule_data")
        if not rule_data:
            return

        # Get the selected terms
        selected_terms = rule_widgets.get("selected_terms", [])
        selected_consequent = rule_widgets.get("selected_consequent")

        # Map terms from rule data to active antecedents
        if_conditions = rule_data.get("if", [])
        for i, ant_condition in enumerate(if_conditions):
            if i >= len(rule_widgets["antecedent_rows"]):
                continue

            ant_row = rule_widgets["antecedent_rows"][i]
            combo = ant_row["combo"]
            label = ant_row["label"]

            # Clear and populate combo box
            combo.clear()

            if i < len(active_antecedents_info):
                ant_info = active_antecedents_info[i]
                label.setText(f"IF {ant_info['name']} IS:")

                if ant_info['terms']:
                    combo.addItems(ant_info['terms'])

                    # Try to select the term from rule data
                    if isinstance(ant_condition, tuple) and len(ant_condition) == 2:
                        term_to_select = ant_condition[1]

                        # First attempt direct match with findText
                        index = combo.findText(term_to_select)
                        if index >= 0:
                            print(f"DEBUG: Setting antecedent {i} to '{term_to_select}' (direct match)")
                            combo.setCurrentIndex(index)
                        # Then try to find in the terms list
                        elif term_to_select in ant_info['terms']:
                            index = ant_info['terms'].index(term_to_select)
                            print(f"DEBUG: Setting antecedent {i} to '{term_to_select}' (index {index})")
                            combo.setCurrentIndex(index)
                        # Default to first item if not found
                        elif combo.count() > 0:
                            combo.setCurrentIndex(0)
                combo.setEnabled(True)
            else:
                label.setText(f"IF Антецедент {i + 1} (не определен) IS:")
                combo.setEnabled(False)

            # Make sure these are visible
            for widget in ant_row["visible_widgets"]:
                widget.setVisible(True)

        # Set consequent selection
        cons_combo = rule_widgets["consequent_combo"]
        rule_widgets["consequent_label"].setText(f"THEN {consequent_name} IS:")

        cons_combo.clear()
        if consequent_terms:
            cons_combo.addItems(consequent_terms)

            # Try to select consequent from rule data
            then_condition = rule_data.get("then")
            if then_condition and isinstance(then_condition, tuple) and len(then_condition) == 2:
                cons_term_to_select = then_condition[1]

                # First attempt direct match
                index = cons_combo.findText(cons_term_to_select)
                if index >= 0:
                    print(f"DEBUG: Setting consequent to '{cons_term_to_select}' (direct match)")
                    cons_combo.setCurrentIndex(index)
                # Then try to find in the terms list
                elif cons_term_to_select in consequent_terms:
                    index = consequent_terms.index(cons_term_to_select)
                    print(f"DEBUG: Setting consequent to '{cons_term_to_select}' (index {index})")
                    cons_combo.setCurrentIndex(index)
                # Default to first item if not found
                elif cons_combo.count() > 0:
                    cons_combo.setCurrentIndex(0)

    def _update_all_rule_widgets_content(self):
        active_antecedents_info = []
        for ant_w_dict in self.antecedent_group_widgets:
            if ant_w_dict["group_box"].isChecked():
                name = ant_w_dict["name_edit"].text().strip()
                if name:
                    terms = [ts["name_edit"].text().strip() for ts in ant_w_dict["term_structures"] if
                             ts["name_edit"].text().strip()]
                    active_antecedents_info.append({"name": name, "terms": terms})
        consequent_name = self.consequent_widgets.get("name_edit", QLineEdit()).text().strip() or "Консеквент"
        consequent_terms = []
        if "term_structures" in self.consequent_widgets:
            consequent_terms = [ts["name_edit"].text().strip() for ts in self.consequent_widgets["term_structures"] if
                                ts["name_edit"].text().strip()]

        for rule_w_dict in self.rule_group_widgets:
            # Process antecedent rows and their combo boxes
            for i, ant_row_widgets in enumerate(rule_w_dict["antecedent_rows"]):
                combo = ant_row_widgets["combo"]
                label = ant_row_widgets["label"]

                # Get the selected term from our rule_w_dict structure
                selected_term = None
                if "selected_terms" in rule_w_dict and i < len(rule_w_dict["selected_terms"]):
                    selected_term = rule_w_dict["selected_terms"][i]

                combo.clear()
                if i < len(active_antecedents_info):
                    ant_info = active_antecedents_info[i]
                    label.setText(f"IF {ant_info['name']} IS:")

                    if ant_info['terms']:
                        combo.addItems(ant_info['terms'])

                        # Try to select the previously selected term
                        if selected_term is not None and selected_term in ant_info['terms']:
                            index = ant_info['terms'].index(selected_term)
                            combo.setCurrentIndex(index)
                        elif combo.count() > 0:
                            combo.setCurrentIndex(0)

                    combo.setEnabled(True)
                else:
                    label.setText(f"IF Антецедент {i + 1} (не определен) IS:")
                    combo.setEnabled(False)

                for w_to_show in ant_row_widgets["visible_widgets"]:
                    w_to_show.setVisible(True)

            # Logic radio buttons
            if "logic_label" in rule_w_dict and rule_w_dict["logic_label"]:
                rule_w_dict["logic_label"].setVisible(True)

            rule_w_dict["logic_or_rb"].setVisible(True)
            rule_w_dict["logic_and_rb"].setVisible(True)

            enable_logic_rbs = len(active_antecedents_info) > 1
            rule_w_dict["logic_or_rb"].setEnabled(enable_logic_rbs)
            rule_w_dict["logic_and_rb"].setEnabled(enable_logic_rbs)

            # Consequent combobox
            rule_w_dict["consequent_label"].setText(f"THEN {consequent_name} IS:")
            cons_combo = rule_w_dict["consequent_combo"]

            # Get the selected consequent term
            selected_consequent = rule_w_dict.get("selected_consequent")

            cons_combo.clear()
            if consequent_terms:
                cons_combo.addItems(consequent_terms)

                # Try to select the previously selected term
                if selected_consequent is not None and selected_consequent in consequent_terms:
                    index = consequent_terms.index(selected_consequent)
                    cons_combo.setCurrentIndex(index)
                elif cons_combo.count() > 0:
                    cons_combo.setCurrentIndex(0)

    def _update_add_rule_button_state(self):
        self.add_rule_button.setEnabled(self._check_conditions_for_rules())

    def _check_conditions_for_rules(self):
        for ant_widgets_dict in self.antecedent_group_widgets:
            if not ant_widgets_dict["group_box"].isChecked(): continue
            if not ant_widgets_dict["name_edit"].text().strip(): continue
            has_at_least_one_named_term = False
            for ts in ant_widgets_dict["term_structures"]:
                if ts["name_edit"].text().strip(): has_at_least_one_named_term = True; break
            if has_at_least_one_named_term: return True
        return False

    def _to_float_list(self, *args, expected_len=None):
        result = [];
        for s_val in args:
            try:
                result.append(float(s_val))
            except (ValueError, TypeError):
                return None
        if expected_len is not None and len(result) != expected_len: return None
        return result

    def get_config_data(self):
        config_to_save = {"antecedents": {}, "consequent": {}, "rule_definitions": []}
        active_antecedents_for_rules = []
        for widgets_dict in self.antecedent_group_widgets:
            if not widgets_dict["group_box"].isChecked(): active_antecedents_for_rules.append(None); continue
            ant_name = widgets_dict["name_edit"].text().strip()
            if not ant_name: active_antecedents_for_rules.append(None); continue
            current_ant_data_for_rules = {"name": ant_name, "terms": []}
            range_list = self._to_float_list(widgets_dict["range_min_edit"].text(),
                                             widgets_dict["range_max_edit"].text(), widgets_dict["step_edit"].text(),
                                             expected_len=3)
            if range_list is None: range_list = [0.0, 0.0, 0.0]
            terms_dict = {}
            # Save terms in order
            term_order = []
            for ts in widgets_dict["term_structures"]:
                term_name = ts["name_edit"].text().strip()
                if not term_name: continue
                term_values = self._to_float_list(*[ve.text() for ve in ts["value_edits"]], expected_len=4)
                if term_values is None: continue
                terms_dict[term_name] = ('trapmf', term_values)
                term_order.append(term_name)  # Track order of terms
                current_ant_data_for_rules["terms"].append(term_name)
            config_to_save["antecedents"][ant_name] = {"range": range_list, "terms": terms_dict,
                                                       "term_order": term_order}
            active_antecedents_for_rules.append(current_ant_data_for_rules)
        consequent_name_for_rules = None
        if self.consequent_widgets:
            cons_name = self.consequent_widgets["name_edit"].text().strip()
            if cons_name:
                consequent_name_for_rules = cons_name
                range_list = self._to_float_list(self.consequent_widgets["range_min_edit"].text(),
                                                 self.consequent_widgets["range_max_edit"].text(),
                                                 self.consequent_widgets["step_edit"].text(), expected_len=3)
                if range_list is None: range_list = [0.0, 0.0, 0.0]
                terms_dict = {}
                # Save terms in order
                term_order = []
                for ts in self.consequent_widgets["term_structures"]:
                    term_name = ts["name_edit"].text().strip()
                    if not term_name: continue
                    term_values = self._to_float_list(*[ve.text() for ve in ts["value_edits"]], expected_len=4)
                    if term_values is None: continue
                    terms_dict[term_name] = ('trapmf', term_values)
                    term_order.append(term_name)  # Track order of terms
                config_to_save["consequent"][cons_name] = {"range": range_list, "terms": terms_dict,
                                                           "term_order": term_order}
        rule_ui_antecedents_source = []
        for ant_widgets_dict_for_ui in self.antecedent_group_widgets:
            if ant_widgets_dict_for_ui["group_box"].isChecked():
                ant_name_for_ui = ant_widgets_dict_for_ui["name_edit"].text().strip()
                if ant_name_for_ui:
                    terms_for_ui = [ts["name_edit"].text().strip() for ts in ant_widgets_dict_for_ui["term_structures"]
                                    if ts["name_edit"].text().strip()]
                    rule_ui_antecedents_source.append({"name": ant_name_for_ui, "terms": terms_for_ui})
        for rule_widgets_dict in self.rule_group_widgets:
            if not rule_widgets_dict["group_box"].isChecked(): continue
            if_conditions = [];
            active_antecedent_count_in_rule = 0
            for i, ant_row_ui in enumerate(rule_widgets_dict["antecedent_rows"]):
                if i < len(rule_ui_antecedents_source):
                    actual_antecedent_data_for_this_row = rule_ui_antecedents_source[i]
                    actual_antecedent_name = actual_antecedent_data_for_this_row["name"]
                    valid_terms_for_this_antecedent = actual_antecedent_data_for_this_row["terms"]
                    selected_term_in_rule = ant_row_ui["combo"].currentText().strip()
                    if selected_term_in_rule and selected_term_in_rule in valid_terms_for_this_antecedent:
                        if_conditions.append((actual_antecedent_name, selected_term_in_rule));
                        active_antecedent_count_in_rule += 1
            if not if_conditions: continue
            logic = None
            if active_antecedent_count_in_rule > 1:
                logic = "OR" if rule_widgets_dict["logic_or_rb"].isChecked() else "AND"
            elif active_antecedent_count_in_rule == 1:
                logic = "AND"
            then_condition = None
            selected_consequent_term = rule_widgets_dict["consequent_combo"].currentText().strip()
            if consequent_name_for_rules and selected_consequent_term:
                if consequent_name_for_rules in config_to_save["consequent"] and selected_consequent_term in \
                        config_to_save["consequent"][consequent_name_for_rules]["terms"]:
                    then_condition = (consequent_name_for_rules, selected_consequent_term)
            if not then_condition: continue
            config_to_save["rule_definitions"].append({"if": if_conditions, "logic": logic, "then": then_condition})
        return config_to_save

    def reject(self):
        self.done(QDialog.Accepted)

    def rebuild_rule_widgets(self):
        """Completely rebuild rule widgets to ensure proper display of selections"""
        print("DEBUG: Completely rebuilding rule widgets")

        # Store the current rule data
        saved_rules = []
        for rule_widgets in self.rule_group_widgets:
            rule_data = {}

            # Store selected antecedent terms
            if_conditions = []
            for i, ant_row in enumerate(rule_widgets["antecedent_rows"]):
                if ant_row["combo"].isEnabled() and ant_row["combo"].count() > 0:
                    # Get the antecedent name from the label
                    label_text = ant_row["label"].text()
                    ant_name = label_text.replace("IF ", "").replace(" IS:", "").strip()
                    term_name = ant_row["combo"].currentText()
                    if ant_name and term_name:
                        if_conditions.append((ant_name, term_name))

            rule_data["if"] = if_conditions

            # Store logic setting
            rule_data["logic"] = "OR" if rule_widgets["logic_or_rb"].isChecked() else "AND"

            # Store consequent selection
            cons_label_text = rule_widgets["consequent_label"].text()
            cons_name = cons_label_text.replace("THEN ", "").replace(" IS:", "").strip()
            cons_term = rule_widgets["consequent_combo"].currentText()
            if cons_name and cons_term:
                rule_data["then"] = (cons_name, cons_term)

            saved_rules.append(rule_data)

        # Clear existing rule widgets
        for rule_group_box in [w["group_box"] for w in self.rule_group_widgets]:
            self.rules_container_layout.removeWidget(rule_group_box)
            rule_group_box.setParent(None)
            rule_group_box.deleteLater()

        self.rule_group_widgets = []

        # Rebuild with saved data
        for rule_data in saved_rules:
            self._add_rule_ui_slot(rule_data)

        # Update after rebuilding
        QTimer.singleShot(500, self._update_all_rule_widgets_content)
        QTimer.singleShot(1000, self._set_rule_selections)
        QTimer.singleShot(1500, self._update_add_rule_button_state)

    def accept(self):
        # On accept, rebuild rules first to ensure proper data before saving
        self.rebuild_rule_widgets()
        # Add a short delay before accepting to let UI update
        QTimer.singleShot(100, lambda s=self: QDialog.accept(s))


class Code_generator:
    __code_was_gendered = 0
    __generated_file_names = []

    # Добавление нового элемента в общий пул
    def __add(self, fn):
        Code_generator.__code_was_gendered += 1
        Code_generator.__generated_file_names.append(fn)

    # Получаем элементы из общего пула

    def get_generated_files(self):
        print(self.__generated_file_names)
        for j, i in enumerate(self.__generated_file_names):
            print(j, i)
        return self.__generated_file_names

    # Получаем все файлы содержащие t в названии
    def get_file_by_name(self, t):
        tmp = []
        for i in self.__generated_file_names:
            if i == t:
                print(i)
                tmp.append(i)
        return tmp

    # Бинарный блок
    def primitive_generate(self, txt, f='', linka='', linkb=''):
        filename = f
        if filename == 'LAST' and Code_generator.__generated_file_names != []:
            filename = Code_generator.__generated_file_names.pop()
        if filename == '':
            filename = 'b' + str(self.__hash__())
        generated = ''
        if linka == '':
            linka = "#"
            print("Пропущено значение linka")
        else:
            generated += f'''
from {linka} import {linka}
'''
        if linkb == '':
            linkb = "#"
            print("Пропущено значение linkb")
        else:
            generated += f'''
from {linkb} import {linkb}
'''

        generated += f'''
def {filename}():
    print("{txt}")
    b = input()
    if "Да" == b:
        {linka}()
        return True
    else:
        {linkb}() 
        return False       
'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename

    # Не бинарный блок выбора
    def match_generate(self, txt, q: list, lincs: list[str], f=''):
        # Генерация имени
        filename = f
        if filename == '':
            filename = 'm' + str(self.__hash__())
        generated = ''
        if len(lincs) > 0:
            for i in lincs:
                generated += f"""
from {i} import {i}
"""
        # Тело функции
        generated += f'''
def {filename}():
    print("{txt}")
    b = input("{q}")
    match b.split():
'''
        # Генерация кейсов
        for i in q:
            generated += f'''               
        case ["{i}"]:
        '''
            try:
                generated += f'''
            {lincs[q.index(i)]}()
            '''
            except:
                generated += f'''
            #()'''
                print("Пропущено значение ссылки")
            generated += f'''
            print("{i}")
            '''
        generated += f'''
        case _:
            {filename}()
            print("default")'''
        # Запись файла
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(f'generated/{filename}.py')
        print(filename)
        return filename

    # Fuzzy Logic
    def fuzzy_generate(self,
                       f: str, question: str, antecedents: dict,
                       consequents: dict, rule_definitions: list, links: list
                       ):
        filename = f
        if filename == '':
            filename = 'fl' + str(self.__hash__())

        # Заголовок файла
        lines = [
            "import numpy as np",
            "import skfuzzy as fuzz",
            "from skfuzzy import control as ctrl",
            ""]
        for i in links:
            lines += [f"from {i} import {i}"]

        lines += [f"def {filename}():",
                  f"    print('{question}')",

                  ""
                  # Определение лингвистических переменных
                  ]
        for i in antecedents.keys():
            lines += [f"    {i} = float(input('Введите значение {i}'))"]

        # Создаём Antecedent
        for var, spec in antecedents.items():
            start, end, step = spec['range']
            lines.append(f"    {var}X = ctrl.Antecedent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}X['{term}'] = fuzz.{mf}({var}X.universe, {params})")
        # Создаём Consequent
        out_var = list(consequents.keys())[0]
        for var, spec in consequents.items():
            start, end, step = spec['range']
            lines.append(f"    {var}X = ctrl.Consequent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}X['{term}'] = fuzz.{mf}({var}X.universe, {params})")
        # Правила
        lines.append("    rules = []")
        for rd in rule_definitions:
            cond_terms = rd['if']
            logic = rd['logic']
            cond_expr = f" {'& ' if logic == 'AND' else ' | '}".join([
                f"{var}X['{term}']" for var, term in cond_terms
            ])
            out_t = rd['then'][1]
            lines.append(f"    rules.append(ctrl.Rule({cond_expr}, {out_var}X['{out_t}']))")
        # Сборка и инференс
        lines += ["    ",
                  "    system = ctrl.ControlSystem(rules)",
                  "    sim = ctrl.ControlSystemSimulation(system)",
                  ]
        # Вывод данных
        for var in antecedents.keys():
            lines.append(f"    sim.input['{var}'] = {var}")
        lines += [
            "    sim.compute()",
            "    # Получение результата",
            f"    # Дефаззификация для выходной переменной '{out_var}'",
            f"    {out_var}_index = float(sim.output['{out_var}'])",
            f"    memberships = {{",
            f"        label: float(fuzz.interp_membership(",
            f"            {out_var}X.universe, {out_var}X[label].mf, {out_var}_index",
            f"        ))",
            f"        for label in {out_var}X.terms.keys()",
            f"    }}",
            f"    {out_var}_category = max(memberships, key=memberships.get)"]
        tmpint = 0
        for _, spec in consequents.items():
            for i, _ in spec['terms'].items():

                try:
                    lines += [f"    ",
                              f"    if {out_var}_category == '{i}':",
                              f"        {links[tmpint]}()"]

                except Exception as e:
                    print(e)
                    break
                tmpint += 1
        lines += [

            "    return {",
            f"        '{out_var}_index': {out_var}_index,",
            f"        '{out_var}_category': {out_var}_category",
            "    }"
        ]
        # Запись в файл
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write("\n".join(lines))

        self.__add(f'generated/{filename}.py')
        print(filename)
        return filename

    def starter_generate(self, f: str, linka: str):
        filename = f
        if filename == '':
            filename = "s" + str(self.__hash__())
        generated = ''
        generated += f'''
from {linka} import {linka}
if __name__ == '__main__':
    print("Starting...")
    {linka}()'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename

    def ender_generate(self, f: str, output: str):
        filename = f
        if filename == '':
            filename = "e" + str(self.__hash__())
        generated = ''
        generated += f'''
def {filename}():
    print("{output}")
    return "Result" + "{output}"'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename


def reader(filename:str):
    block_from_file: dict
    connection_from_file: dict
    with open(f"{filename}", "r", encoding="utf-8") as file:
        tmp = json.load(file)
        block_from_file = tmp['blocks']
        connection_from_file = tmp['connections']

    block_connections={}
    for i in block_from_file:
        block_connections[i['id']] = []
        for j in connection_from_file:
            if i['id'] == j['from']:
                block_connections[i['id']].append(j['to'])

    creater(block_from_file, block_connections)


def creater(bff:dict, bc:dict):
    c = Code_generator()
    for i in bff:
        match i['type']:
            case 'Starter':
                c.starter_generate(i['id'], bc[i['id']][0] ) #i['question']
            case 'Ender':
                c.ender_generate(i['id'], i['verdict'])
            case 'Binares':
                c.primitive_generate(i['condition'],i['id'], bc[i['id']][1], bc[i['id']][0])
            case 'Match':
                c.match_generate(i['question'], i['choices'], bc[i['id']], i['id'])
            case 'Fuzzy':
                c.fuzzy_generate(i['id'], i['question'],
                                 i['fuzzy_config']['antecedents'],
                                 i['fuzzy_config']['consequent'],
                                 i['fuzzy_config']['rule_definitions'],
                                 bc[i['id']])
            case _:
                print("def")


directory = "generated"

if not os.path.exists(directory):
    os.makedirs(directory)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())