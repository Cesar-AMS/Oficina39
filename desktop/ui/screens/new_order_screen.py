from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
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

from desktop.services.new_order_service import create_order, get_new_order_metadata, load_client
from desktop.ui.screens.client_picker_dialog import ClientPickerDialog
from desktop.ui.screens.view_order_dialog import ViewOrderDialog


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or "---"


class NewOrderScreen(QWidget):
    navigate_requested = pyqtSignal(str)
    order_created = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._metadata = get_new_order_metadata()
        self._selected_client: dict | None = None

        self._client_search_label = QLabel("Nenhum cliente selecionado")
        self._client_fields: dict[str, QLabel] = {}
        self._vehicle_fields: dict[str, QLabel] = {}
        self._professional_combo = QComboBox()
        self._status_value = QLabel(self._metadata.get("status_inicial", "Aguardando"))
        self._diagnostic_edit = QPlainTextEdit()
        self._services_table = QTableWidget(0, 4)
        self._parts_table = QTableWidget(0, 8)
        self._total_services_label = QLabel("R$ 0,00")
        self._total_parts_label = QLabel("R$ 0,00")
        self._total_general_label = QLabel("R$ 0,00")
        self._save_button: QPushButton | None = None

        self._build_ui()
        self._populate_metadata()
        self._reset_form(keep_client=False)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content_wrapper = QWidget()
        content = QVBoxLayout(content_wrapper)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(14)

        content.addWidget(self._build_client_section())
        content.addWidget(self._build_vehicle_section())
        content.addWidget(self._build_editable_section())
        content.addWidget(self._build_services_section())
        content.addWidget(self._build_parts_section())
        content.addWidget(self._build_totals_section())
        content.addStretch(1)

        scroll.setWidget(content_wrapper)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(lambda: self._reset_form(keep_client=False))

        save_button = QPushButton("Salvar OS")
        save_button.clicked.connect(self._save_order)

        save_open_button = QPushButton("Salvar e abrir")
        save_open_button.clicked.connect(lambda: self._save_order(open_after_save=True))

        self._save_button = save_button
        buttons.addWidget(clear_button)
        buttons.addWidget(save_button)
        buttons.addWidget(save_open_button)
        root.addLayout(buttons)

        self._configure_tables()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Nova Ordem de Servico")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Criacao nativa da OS com selecao de cliente, profissional, servicos e pecas usando o dominio atual."
        )
        subtitle.setObjectName("screenText")
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)

        back_button = QPushButton("Voltar ao inicio")
        back_button.clicked.connect(lambda: self.navigate_requested.emit("home"))

        layout.addLayout(texts, 1)
        layout.addWidget(back_button)
        return card

    def _build_client_section(self) -> QWidget:
        box = QGroupBox("Cliente")
        outer = QVBoxLayout(box)
        outer.setSpacing(12)

        top_row = QHBoxLayout()
        self._client_search_label.setObjectName("screenText")
        choose_button = QPushButton("Selecionar cliente")
        choose_button.clicked.connect(self._choose_client)
        clear_button = QPushButton("Remover cliente")
        clear_button.clicked.connect(self._clear_client)
        top_row.addWidget(self._client_search_label, 1)
        top_row.addWidget(choose_button)
        top_row.addWidget(clear_button)
        outer.addLayout(top_row)

        form = QGridLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(8)
        fields = [
            ("Nome", "nome_cliente"),
            ("CPF", "cpf"),
            ("Telefone", "telefone"),
            ("E-mail", "email"),
            ("Endereco", "endereco"),
            ("Cidade", "cidade"),
            ("Estado", "estado"),
            ("CEP", "cep"),
        ]
        for index, (label, key) in enumerate(fields):
            value = QLabel("---")
            value.setWordWrap(True)
            self._client_fields[key] = value
            row = index // 2
            base_col = (index % 2) * 2
            form.addWidget(QLabel(f"{label}:"), row, base_col)
            form.addWidget(value, row, base_col + 1)
        outer.addLayout(form)
        return box

    def _build_vehicle_section(self) -> QWidget:
        box = QGroupBox("Veiculo")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        fields = [
            ("Placa", "placa"),
            ("Fabricante", "fabricante"),
            ("Modelo", "modelo"),
            ("Ano", "ano"),
            ("Motor", "motor"),
            ("Combustivel", "combustivel"),
            ("Cor", "cor"),
            ("Tanque", "tanque"),
            ("KM", "km"),
            ("Direcao", "direcao"),
            ("Ar", "ar"),
        ]
        for index, (label, key) in enumerate(fields):
            value = QLabel("---")
            value.setWordWrap(True)
            self._vehicle_fields[key] = value
            row = index // 2
            base_col = (index % 2) * 2
            grid.addWidget(QLabel(f"{label}:"), row, base_col)
            grid.addWidget(value, row, base_col + 1)
        return box

    def _build_editable_section(self) -> QWidget:
        box = QGroupBox("Dados da ordem")
        layout = QFormLayout(box)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(10)

        self._diagnostic_edit.setPlaceholderText("Descreva o diagnostico da ordem")
        self._diagnostic_edit.setFixedHeight(90)
        layout.addRow("Profissional responsavel:", self._professional_combo)
        layout.addRow("Status inicial:", self._status_value)
        layout.addRow("Diagnostico:", self._diagnostic_edit)
        return box

    def _build_services_section(self) -> QWidget:
        box = QGroupBox("Servicos")
        layout = QVBoxLayout(box)

        buttons = QHBoxLayout()
        add_button = QPushButton("Adicionar servico")
        add_button.clicked.connect(self._add_service_row)
        remove_button = QPushButton("Remover servico selecionado")
        remove_button.clicked.connect(self._remove_selected_service_row)
        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)
        buttons.addStretch(1)

        layout.addLayout(buttons)
        layout.addWidget(self._services_table)
        return box

    def _build_parts_section(self) -> QWidget:
        box = QGroupBox("Pecas")
        layout = QVBoxLayout(box)

        buttons = QHBoxLayout()
        add_button = QPushButton("Adicionar peca")
        add_button.clicked.connect(self._add_part_row)
        remove_button = QPushButton("Remover peca selecionada")
        remove_button.clicked.connect(self._remove_selected_part_row)
        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)
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
        layout.addRow("Total servicos:", self._total_services_label)
        layout.addRow("Total pecas:", self._total_parts_label)
        layout.addRow("Total geral:", self._total_general_label)
        return card

    def _populate_metadata(self) -> None:
        self._professional_combo.addItem("Selecione")
        for professional in self._metadata.get("profissionais", []):
            self._professional_combo.addItem(professional)

    def _configure_tables(self) -> None:
        self._services_table.setHorizontalHeaderLabels(["Codigo", "Descricao", "Valor", ""])
        self._services_table.verticalHeader().setVisible(False)
        self._services_table.horizontalHeader().setStretchLastSection(True)
        self._services_table.setColumnWidth(0, 90)
        self._services_table.setColumnWidth(2, 110)
        self._services_table.setColumnWidth(3, 40)
        self._services_table.itemChanged.connect(self._recalculate_totals)

        self._parts_table.setHorizontalHeaderLabels(
            ["Codigo", "Descricao", "Qtd", "Valor custo", "Lucro %", "Valor unit.", "Total", ""]
        )
        self._parts_table.verticalHeader().setVisible(False)
        self._parts_table.horizontalHeader().setStretchLastSection(False)
        self._parts_table.setColumnWidth(0, 90)
        self._parts_table.setColumnWidth(1, 250)
        self._parts_table.setColumnWidth(2, 70)
        self._parts_table.setColumnWidth(3, 100)
        self._parts_table.setColumnWidth(4, 80)
        self._parts_table.setColumnWidth(5, 100)
        self._parts_table.setColumnWidth(6, 100)
        self._parts_table.setColumnWidth(7, 40)
        self._parts_table.itemChanged.connect(self._recalculate_totals)

    def _choose_client(self) -> None:
        dialog = ClientPickerDialog(self)
        if dialog.exec_() and dialog.selected_client:
            client_id = dialog.selected_client.get("id")
            if client_id:
                self._selected_client = load_client(int(client_id))
                self._apply_client()

    def _apply_client(self) -> None:
        client = self._selected_client or {}
        if client:
            self._client_search_label.setText(f"Cliente selecionado: {_text(client.get('nome_cliente'))} (#{client.get('id')})")
        else:
            self._client_search_label.setText("Nenhum cliente selecionado")

        for key, label in self._client_fields.items():
            label.setText(_text(client.get(key)))
        for key, label in self._vehicle_fields.items():
            label.setText(_text(client.get(key)))

    def _clear_client(self) -> None:
        self._selected_client = None
        self._apply_client()

    def _reset_form(self, keep_client: bool = False) -> None:
        if not keep_client:
            self._selected_client = None
        self._apply_client()
        self._professional_combo.setCurrentIndex(0)
        self._diagnostic_edit.clear()
        self._services_table.setRowCount(0)
        self._parts_table.setRowCount(0)
        self._add_service_row()
        self._add_part_row()
        self._recalculate_totals()

    def _add_service_row(self, service: dict | None = None) -> None:
        row = self._services_table.rowCount()
        self._services_table.insertRow(row)
        items = [
            QTableWidgetItem((service or {}).get("codigo_servico") or ""),
            QTableWidgetItem((service or {}).get("descricao_servico") or ""),
            QTableWidgetItem(str(float((service or {}).get("valor_servico") or 0))),
            QTableWidgetItem("x"),
        ]
        items[2].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        items[3].setTextAlignment(Qt.AlignCenter)
        for col, item in enumerate(items):
            self._services_table.setItem(row, col, item)

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
            _money(float((part or {}).get("total") or 0)),
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

    def _build_payload(self) -> dict | None:
        if not self._selected_client:
            QMessageBox.warning(self, "Validacao", "Selecione um cliente antes de salvar a ordem.")
            return None

        professional = self._professional_combo.currentText().strip()
        if not professional or professional == "Selecione":
            QMessageBox.warning(self, "Validacao", "Selecione um profissional responsavel.")
            return None

        services = self._collect_services()
        parts = self._collect_parts()
        if not services and not parts:
            QMessageBox.warning(self, "Validacao", "Adicione pelo menos um servico ou uma peca.")
            return None

        return {
            "cliente_id": int(self._selected_client["id"]),
            "diagnostico": self._diagnostic_edit.toPlainText().strip(),
            "profissional_responsavel": professional,
            "servicos": services,
            "pecas": parts,
        }

    def _save_order(self, open_after_save: bool = False) -> None:
        payload = self._build_payload()
        if not payload:
            return

        if self._save_button:
            self._save_button.setEnabled(False)
        try:
            created = create_order(payload)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))
            return
        finally:
            if self._save_button:
                self._save_button.setEnabled(True)

        order_id = int(created["id"])
        self.order_created.emit(order_id)

        if open_after_save:
            QMessageBox.information(self, "Sucesso", f"OS #{order_id} criada com sucesso.")
            dialog = ViewOrderDialog(order_id, self)
            dialog.exec_()
            self._reset_form(keep_client=False)
            return

        QMessageBox.information(self, "Sucesso", f"OS #{order_id} criada com sucesso.")
        self._reset_form(keep_client=False)
