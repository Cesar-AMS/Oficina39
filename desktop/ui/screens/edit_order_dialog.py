from __future__ import annotations

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.order_edit_service import load_order_edit, save_order_edit
from desktop.services.orders_query_service import get_professional_names


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


def _parse_pt_datetime_to_qdate(value: str | None) -> QDate | None:
    if not value:
        return None
    try:
        date_part = value.split(" ")[0]
        day, month, year = date_part.split("/")
        return QDate(int(year), int(month), int(day))
    except Exception:
        return None


class EditOrderDialog(QDialog):
    def __init__(self, order_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._order_id = order_id
        self._order_data = load_order_edit(order_id)

        self.setWindowTitle(f"Editar OS #{order_id}")
        self.resize(1100, 820)

        self._professional_combo = QComboBox()
        self._status_combo = QComboBox()
        self._diagnostic_edit = QPlainTextEdit()
        self._internal_notes_edit = QPlainTextEdit()
        self._signature_edit = QPlainTextEdit()
        self._pickup_date = QDateEdit()
        self._services_table = QTableWidget(0, 4)
        self._parts_table = QTableWidget(0, 8)
        self._blocked_label = QLabel("Ordem concluida/em garantia: reabra na consulta para editar.")
        self._add_service_button: QPushButton | None = None
        self._remove_service_button: QPushButton | None = None
        self._add_part_button: QPushButton | None = None
        self._remove_part_button: QPushButton | None = None
        self._save_button: QPushButton | None = None
        self.saved_data: dict | None = None

        self._build_ui()
        self._populate_data()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        content = QVBoxLayout(container)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)

        content.addWidget(self._build_header())
        content.addWidget(self._build_identity_section())
        content.addWidget(self._build_vehicle_section())
        content.addWidget(self._build_editable_section())
        content.addWidget(self._build_services_section())
        content.addWidget(self._build_parts_section())
        content.addWidget(self._build_totals_section())
        content.addStretch(1)

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self._save_button = buttons.button(QDialogButtonBox.Save)
        self._save_button.setText("Salvar alteracoes")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._configure_tables()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title = QLabel(f"Editar Ordem de Servico #{self._order_id}")
        title.setObjectName("screenTitle")

        self._blocked_label.setObjectName("screenText")
        self._blocked_label.setObjectName("screenText")
        self._blocked_label.hide()

        subtitle = QLabel("Edicao nativa da OS, reaproveitando as validacoes e regras atuais do dominio.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("screenText")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._blocked_label)
        return card

    def _build_identity_section(self) -> QWidget:
        client = self._order_data.get("cliente") or {}
        box = QGroupBox("Dados do cliente")
        form = QFormLayout(box)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(8)
        form.addRow("Cliente:", QLabel(_text(client.get("nome_cliente"))))
        form.addRow("CPF:", QLabel(_text(client.get("cpf"))))
        form.addRow("Telefone:", QLabel(_text(client.get("telefone"))))
        form.addRow("Endereco:", QLabel(_text(client.get("endereco"))))
        return box

    def _build_vehicle_section(self) -> QWidget:
        client = self._order_data.get("cliente") or {}
        box = QGroupBox("Dados do veiculo")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        fields = [
            ("Placa", _text(client.get("placa"))),
            ("Fabricante", _text(client.get("fabricante"))),
            ("Modelo", _text(client.get("modelo"))),
            ("Ano", _text(client.get("ano"))),
            ("Motor", _text(client.get("motor"))),
            ("Combustivel", _text(client.get("combustivel"))),
            ("Cor", _text(client.get("cor"))),
            ("Tanque", _text(client.get("tanque"))),
            ("KM", _text(client.get("km"))),
            ("Direcao", _text(client.get("direcao"))),
            ("Ar", _text(client.get("ar"))),
        ]
        for index, (label, value) in enumerate(fields):
            grid.addWidget(QLabel(f"{label}:"), index // 2, (index % 2) * 2)
            grid.addWidget(QLabel(value), index // 2, (index % 2) * 2 + 1)
        return box

    def _build_editable_section(self) -> QWidget:
        box = QGroupBox("Campos editaveis")
        layout = QFormLayout(box)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(10)

        self._professional_combo.addItem("Selecione")
        self._professional_combo.addItems(get_professional_names())

        for status in ["Aguardando", "Aguardando pecas", "Em andamento", "Concluido", "Garantia"]:
            self._status_combo.addItem(status)

        self._pickup_date.setCalendarPopup(True)
        self._pickup_date.setDisplayFormat("dd/MM/yyyy")
        self._pickup_date.setSpecialValueText("Sem data")
        self._pickup_date.setDate(QDate(2000, 1, 1))
        self._pickup_date.setMinimumDate(QDate(2000, 1, 1))

        self._diagnostic_edit.setPlaceholderText("Descreva o diagnostico")
        self._diagnostic_edit.setFixedHeight(90)
        self._internal_notes_edit.setPlaceholderText("Observacoes internas")
        self._internal_notes_edit.setFixedHeight(90)
        self._signature_edit.setPlaceholderText("Assinatura do consumidor")
        self._signature_edit.setFixedHeight(56)

        layout.addRow("Profissional responsavel:", self._professional_combo)
        layout.addRow("Status:", self._status_combo)
        layout.addRow("Data de retirada:", self._pickup_date)
        layout.addRow("Diagnostico:", self._diagnostic_edit)
        layout.addRow("Observacoes internas:", self._internal_notes_edit)
        layout.addRow("Assinatura do cliente:", self._signature_edit)
        return box

    def _build_services_section(self) -> QWidget:
        box = QGroupBox("Servicos")
        layout = QVBoxLayout(box)

        buttons = QHBoxLayout()
        self._add_service_button = QPushButton("Adicionar servico")
        self._add_service_button.clicked.connect(self._add_service_row)
        self._remove_service_button = QPushButton("Remover servico selecionado")
        self._remove_service_button.clicked.connect(self._remove_selected_service_row)
        buttons.addWidget(self._add_service_button)
        buttons.addWidget(self._remove_service_button)
        buttons.addStretch(1)

        layout.addLayout(buttons)
        layout.addWidget(self._services_table)
        return box

    def _build_parts_section(self) -> QWidget:
        box = QGroupBox("Pecas")
        layout = QVBoxLayout(box)

        buttons = QHBoxLayout()
        self._add_part_button = QPushButton("Adicionar peca")
        self._add_part_button.clicked.connect(self._add_part_row)
        self._remove_part_button = QPushButton("Remover peca selecionada")
        self._remove_part_button.clicked.connect(self._remove_selected_part_row)
        buttons.addWidget(self._add_part_button)
        buttons.addWidget(self._remove_part_button)
        buttons.addStretch(1)

        layout.addLayout(buttons)
        layout.addWidget(self._parts_table)
        return box

    def _build_totals_section(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QFormLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(8)

        self._total_services_label = QLabel("R$ 0,00")
        self._total_parts_label = QLabel("R$ 0,00")
        self._total_general_label = QLabel("R$ 0,00")

        layout.addRow("Total servicos:", self._total_services_label)
        layout.addRow("Total pecas:", self._total_parts_label)
        layout.addRow("Total geral:", self._total_general_label)
        return card

    def _configure_tables(self) -> None:
        self._services_table.setHorizontalHeaderLabels(["Codigo", "Descricao", "Valor", ""])
        self._services_table.verticalHeader().setVisible(False)
        self._services_table.horizontalHeader().setStretchLastSection(True)
        self._services_table.setColumnWidth(0, 90)
        self._services_table.setColumnWidth(2, 100)
        self._services_table.setColumnWidth(3, 40)
        self._services_table.itemChanged.connect(self._recalculate_totals)

        self._parts_table.setHorizontalHeaderLabels(
            ["Codigo", "Descricao", "Qtd", "Valor custo", "Lucro %", "Valor unit.", "Total", ""]
        )
        self._parts_table.verticalHeader().setVisible(False)
        self._parts_table.horizontalHeader().setStretchLastSection(False)
        self._parts_table.setColumnWidth(0, 90)
        self._parts_table.setColumnWidth(1, 260)
        self._parts_table.setColumnWidth(2, 70)
        self._parts_table.setColumnWidth(3, 100)
        self._parts_table.setColumnWidth(4, 80)
        self._parts_table.setColumnWidth(5, 100)
        self._parts_table.setColumnWidth(6, 100)
        self._parts_table.setColumnWidth(7, 40)
        self._parts_table.itemChanged.connect(self._recalculate_totals)

    def _populate_data(self) -> None:
        data = self._order_data
        blocked = data.get("status") in {"Concluido", "Garantia"}
        if blocked:
            self._blocked_label.show()
            if self._save_button:
                self._save_button.setEnabled(False)
            self._professional_combo.setEnabled(False)
            self._status_combo.setEnabled(False)
            self._pickup_date.setEnabled(False)
            self._diagnostic_edit.setReadOnly(True)
            self._internal_notes_edit.setReadOnly(True)
            self._signature_edit.setReadOnly(True)
            self._services_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self._parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
            if self._add_service_button:
                self._add_service_button.setEnabled(False)
            if self._remove_service_button:
                self._remove_service_button.setEnabled(False)
            if self._add_part_button:
                self._add_part_button.setEnabled(False)
            if self._remove_part_button:
                self._remove_part_button.setEnabled(False)

        professional = (data.get("profissional_responsavel") or "").strip()
        if professional and self._professional_combo.findText(professional) == -1:
            self._professional_combo.addItem(professional)
        if professional:
            self._professional_combo.setCurrentText(professional)

        status = data.get("status") or "Aguardando"
        if self._status_combo.findText(status) != -1:
            self._status_combo.setCurrentText(status)

        pickup_qdate = _parse_pt_datetime_to_qdate(data.get("data_retirada"))
        if pickup_qdate:
            self._pickup_date.setDate(pickup_qdate)

        self._diagnostic_edit.setPlainText(data.get("diagnostico") or "")
        self._internal_notes_edit.setPlainText(data.get("observacao_interna") or "")
        self._signature_edit.setPlainText(data.get("assinatura_cliente") or "")

        for service in data.get("servicos", []):
            self._add_service_row(service)
        if self._services_table.rowCount() == 0:
            self._add_service_row()

        for part in data.get("pecas", []):
            self._add_part_row(part)
        if self._parts_table.rowCount() == 0:
            self._add_part_row()

        self._recalculate_totals()

    def _add_service_row(self, service: dict | None = None) -> None:
        row = self._services_table.rowCount()
        self._services_table.insertRow(row)

        code_item = QTableWidgetItem((service or {}).get("codigo_servico") or "")
        desc_item = QTableWidgetItem((service or {}).get("descricao_servico") or "")
        value_item = QTableWidgetItem(str(float((service or {}).get("valor_servico") or 0)))
        value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

        remove_item = QTableWidgetItem("x")
        remove_item.setTextAlignment(Qt.AlignCenter)

        self._services_table.setItem(row, 0, code_item)
        self._services_table.setItem(row, 1, desc_item)
        self._services_table.setItem(row, 2, value_item)
        self._services_table.setItem(row, 3, remove_item)

    def _remove_selected_service_row(self) -> None:
        row = self._services_table.currentRow()
        if row >= 0:
            self._services_table.removeRow(row)
            self._recalculate_totals()

    def _add_part_row(self, part: dict | None = None) -> None:
        row = self._parts_table.rowCount()
        self._parts_table.insertRow(row)

        values = [
            (part or {}).get("codigo_peca") or "",
            (part or {}).get("descricao_peca") or "",
            str(float((part or {}).get("quantidade") or 1)),
            str(float((part or {}).get("valor_custo") or 0)),
            str(float((part or {}).get("percentual_lucro") or 0)),
            str(float((part or {}).get("valor_unitario") or 0)),
            _money(
                float((part or {}).get("total") or ((part or {}).get("quantidade") or 0) * ((part or {}).get("valor_unitario") or 0))
            ),
            "x",
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col in {2, 3, 4, 5, 6, 7}:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._parts_table.setItem(row, col, item)

    def _remove_selected_part_row(self) -> None:
        row = self._parts_table.currentRow()
        if row >= 0:
            self._parts_table.removeRow(row)
            self._recalculate_totals()

    def _parse_float(self, table: QTableWidget, row: int, col: int) -> float:
        item = table.item(row, col)
        raw = (item.text() if item else "").strip().replace("R$", "").replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return 0.0

    def _recalculate_totals(self, *args) -> None:
        total_services = 0.0
        for row in range(self._services_table.rowCount()):
            total_services += self._parse_float(self._services_table, row, 2)

        total_parts = 0.0
        for row in range(self._parts_table.rowCount()):
            quantity = self._parse_float(self._parts_table, row, 2)
            cost = self._parse_float(self._parts_table, row, 3)
            profit = self._parse_float(self._parts_table, row, 4)
            unit = cost * (1 + (profit / 100.0))
            total = quantity * unit
            self._parts_table.blockSignals(True)
            unit_item = QTableWidgetItem(f"{unit:.2f}")
            unit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._parts_table.setItem(row, 5, unit_item)
            total_item = QTableWidgetItem(_money(total))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._parts_table.setItem(row, 6, total_item)
            self._parts_table.blockSignals(False)
            total_parts += total

        self._total_services_label.setText(_money(total_services))
        self._total_parts_label.setText(_money(total_parts))
        self._total_general_label.setText(_money(total_services + total_parts))

    def _collect_services(self) -> list[dict]:
        services = []
        for row in range(self._services_table.rowCount()):
            description = (self._services_table.item(row, 1).text() if self._services_table.item(row, 1) else "").strip()
            if not description:
                continue
            services.append(
                {
                    "codigo_servico": (self._services_table.item(row, 0).text() if self._services_table.item(row, 0) else "").strip(),
                    "descricao_servico": description,
                    "valor_servico": self._parse_float(self._services_table, row, 2),
                }
            )
        return services

    def _collect_parts(self) -> list[dict]:
        parts = []
        for row in range(self._parts_table.rowCount()):
            description = (self._parts_table.item(row, 1).text() if self._parts_table.item(row, 1) else "").strip()
            if not description:
                continue
            parts.append(
                {
                    "codigo_peca": (self._parts_table.item(row, 0).text() if self._parts_table.item(row, 0) else "").strip(),
                    "descricao_peca": description,
                    "quantidade": self._parse_float(self._parts_table, row, 2),
                    "valor_custo": self._parse_float(self._parts_table, row, 3),
                    "percentual_lucro": self._parse_float(self._parts_table, row, 4),
                    "valor_unitario": self._parse_float(self._parts_table, row, 5),
                }
            )
        return parts

    def _build_payload(self) -> dict:
        pickup_date = self._pickup_date.date()
        pickup_value = None
        if pickup_date.isValid() and pickup_date != QDate(2000, 1, 1):
            pickup_value = pickup_date.toString("yyyy-MM-dd")

        return {
            "diagnostico": self._diagnostic_edit.toPlainText().strip(),
            "observacao_interna": self._internal_notes_edit.toPlainText().strip(),
            "profissional_responsavel": self._professional_combo.currentText().strip(),
            "assinatura_cliente": self._signature_edit.toPlainText().strip(),
            "data_retirada": pickup_value,
            "status": self._status_combo.currentText().strip(),
            "servicos": self._collect_services(),
            "pecas": self._collect_parts(),
        }

    def _save(self) -> None:
        payload = self._build_payload()

        if not payload["profissional_responsavel"] or payload["profissional_responsavel"] == "Selecione":
            QMessageBox.warning(self, "Validacao", "Informe o profissional responsavel.")
            return
        if not payload["servicos"] and not payload["pecas"]:
            QMessageBox.warning(self, "Validacao", "Adicione pelo menos um servico ou uma peca.")
            return

        try:
            self.saved_data = save_order_edit(self._order_id, payload)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))
            return

        QMessageBox.information(self, "Sucesso", "Ordem atualizada com sucesso.")
        self.accept()
