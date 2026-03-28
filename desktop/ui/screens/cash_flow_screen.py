from __future__ import annotations

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.cash_flow_service import (
    build_movements,
    get_cash_conference,
    load_daily_cash_flow,
    register_output,
    summarize_cash_flow,
)
from desktop.ui.components.summary_card import SummaryCard
from desktop.ui.screens.finalize_order_dialog import FinalizeOrderDialog


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


class OutputEntryDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar saída")
        self.resize(440, 260)
        self.output_data: dict | None = None

        self._description = QLineEdit()
        self._value = QLineEdit()
        self._date = QDateEdit()
        self._category = QComboBox()

        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("dd/MM/yyyy")
        self._date.setDate(QDate.currentDate())
        self._category.addItems(
            ["Peças", "Fornecedor", "Aluguel", "Salários", "Impostos", "Ferramentas", "Marketing", "Despesa casa", "Outros"]
        )

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Descrição *", self._description)
        form.addRow("Valor (R$) *", self._value)
        form.addRow("Data", self._date)
        form.addRow("Categoria", self._category)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Salvar saída")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        descricao = self._description.text().strip()
        raw = self._value.text().strip().replace(".", "").replace(",", ".")
        try:
            valor = float(raw)
        except ValueError:
            valor = 0.0
        if not descricao:
            QMessageBox.warning(self, "Saída", "Descrição é obrigatória.")
            return
        if valor <= 0:
            QMessageBox.warning(self, "Saída", "Informe um valor válido.")
            return
        self.output_data = {
            "descricao": descricao,
            "valor": valor,
            "data": self._date.date().toPyDate(),
            "categoria": self._category.currentText(),
        }
        self.accept()


class CashFlowScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._movements: list[dict] = []
        self._summary_cards: dict[str, SummaryCard] = {}
        self._movement_filter = "todas"
        self._conference_inputs: dict[str, QLineEdit] = {}

        self._movements_table = QTableWidget(0, 6)
        self._conference_table = QTableWidget(0, 4)
        self._order_id_input = QLineEdit()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)
        root.addWidget(self._build_header())
        root.addWidget(self._build_tabs(), 1)

        self._setup_tables()
        self.reload_cash_flow()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Fluxo de Caixa")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Acompanhe o caixa do dia, registre saídas, faça conferência por forma de pagamento e abra o recebimento de uma OS."
        )
        subtitle.setObjectName("screenText")
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)

        layout.addLayout(texts, 1)
        layout.addWidget(QPushButton("Voltar ao início", clicked=lambda: self.navigate_requested.emit("home")))
        return card

    def _build_tabs(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._build_day_cash_tab(), "Caixa do Dia")
        tabs.addTab(self._build_conference_tab(), "Conferência")
        return tabs

    def _build_day_cash_tab(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        summary_row = QWidget()
        summary_layout = QHBoxLayout(summary_row)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(12)
        for key, title in [
            ("entradas", "Recebimentos"),
            ("saidas", "Saídas"),
            ("saldo", "Saldo"),
        ]:
            card = SummaryCard(title)
            self._summary_cards[key] = card
            summary_layout.addWidget(card, 1)

        actions_card = QFrame()
        actions_card.setObjectName("screenCard")
        actions_layout = QGridLayout(actions_card)
        actions_layout.setContentsMargins(22, 18, 22, 18)
        actions_layout.setHorizontalSpacing(14)
        actions_layout.setVerticalSpacing(12)

        new_output_button = QPushButton("Nova saída")
        new_output_button.clicked.connect(self._open_output_dialog)
        refresh_button = QPushButton("Atualizar caixa")
        refresh_button.clicked.connect(self.reload_cash_flow)
        open_order_button = QPushButton("Abrir OS no caixa")
        open_order_button.clicked.connect(self._open_order_in_cashier)

        actions_layout.addWidget(QLabel("Número da OS"), 0, 0)
        actions_layout.addWidget(self._order_id_input, 1, 0)
        actions_layout.addWidget(open_order_button, 1, 1)
        actions_layout.addWidget(new_output_button, 1, 2)
        actions_layout.addWidget(refresh_button, 1, 3)
        actions_layout.setColumnStretch(0, 1)

        filters_card = QFrame()
        filters_card.setObjectName("screenCard")
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(22, 14, 22, 14)
        filters_layout.setSpacing(8)
        for label, key in [("Todas", "todas"), ("Entradas", "entradas"), ("Saídas", "saidas")]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, filter_key=key: self._set_filter(filter_key))
            filters_layout.addWidget(button)
        filters_layout.addStretch(1)

        table_card = QFrame()
        table_card.setObjectName("screenCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.addWidget(self._movements_table)

        root.addWidget(summary_row)
        root.addWidget(actions_card)
        root.addWidget(filters_card)
        root.addWidget(table_card, 1)
        return panel

    def _build_conference_tab(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        filters_card = QFrame()
        filters_card.setObjectName("screenCard")
        filters_layout = QGridLayout(filters_card)
        filters_layout.setContentsMargins(22, 18, 22, 18)
        filters_layout.setHorizontalSpacing(14)
        filters_layout.setVerticalSpacing(12)

        self._conference_date = QDateEdit()
        self._conference_date.setCalendarPopup(True)
        self._conference_date.setDisplayFormat("dd/MM/yyyy")
        self._conference_date.setDate(QDate.currentDate())
        compare_button = QPushButton("Conferir")
        compare_button.clicked.connect(self._run_conference)

        filters_layout.addWidget(QLabel("Data da conferência"), 0, 0)
        filters_layout.addWidget(self._conference_date, 1, 0)
        filters_layout.addWidget(compare_button, 1, 1)
        filters_layout.setColumnStretch(0, 1)

        forms_card = QFrame()
        forms_card.setObjectName("screenCard")
        forms_layout = QGridLayout(forms_card)
        forms_layout.setContentsMargins(22, 18, 22, 18)
        forms_layout.setHorizontalSpacing(14)
        forms_layout.setVerticalSpacing(12)

        formas = ["Pix", "Cartão", "Dinheiro", "Boleto", "Não informado"]
        for index, forma in enumerate(formas):
            field = QLineEdit()
            field.setPlaceholderText("0,00")
            self._conference_inputs[forma] = field
            forms_layout.addWidget(QLabel(forma), index // 2 * 2, index % 2 * 2)
            forms_layout.addWidget(field, index // 2 * 2 + 1, index % 2 * 2)

        table_card = QFrame()
        table_card.setObjectName("screenCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.addWidget(self._conference_table)

        root.addWidget(filters_card)
        root.addWidget(forms_card)
        root.addWidget(table_card, 1)
        return panel

    def _setup_tables(self) -> None:
        self._movements_table.setHorizontalHeaderLabels(["Horário", "Tipo", "Origem", "Forma", "Valor", "Observação"])
        self._conference_table.setHorizontalHeaderLabels(["Forma", "Esperado", "Contado", "Diferença"])
        for table in [self._movements_table, self._conference_table]:
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)
            table.verticalHeader().setVisible(False)
            header = table.horizontalHeader()
            header.setStretchLastSection(False)
            for col in range(table.columnCount()):
                mode = header.ResizeToContents if col in {0, 1, table.columnCount() - 1} else header.Stretch
                header.setSectionResizeMode(col, mode)

    def reload_cash_flow(self) -> None:
        try:
            data = load_daily_cash_flow()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar o caixa.\n\n{exc}")
            return
        summary = summarize_cash_flow(data)
        self._summary_cards["entradas"].set_value(_money(summary["total_entradas"]))
        self._summary_cards["saidas"].set_value(_money(summary["total_saidas"]))
        self._summary_cards["saldo"].set_value(_money(summary["saldo"]))
        self._movements = build_movements(data)
        self._render_movements()

    def _render_movements(self) -> None:
        rows = [
            item
            for item in self._movements
            if self._movement_filter == "todas"
            or (self._movement_filter == "entradas" and item["tipo"] == "Entrada")
            or (self._movement_filter == "saidas" and item["tipo"] == "Saída")
        ]
        self._movements_table.clearContents()
        self._movements_table.clearSpans()
        if not rows:
            self._movements_table.setRowCount(1)
            placeholder = QTableWidgetItem("Nenhuma movimentação no filtro selecionado.")
            placeholder.setFlags(Qt.ItemIsEnabled)
            placeholder.setTextAlignment(Qt.AlignCenter)
            self._movements_table.setItem(0, 0, placeholder)
            self._movements_table.setSpan(0, 0, 1, 6)
            return

        self._movements_table.setRowCount(len(rows))
        for row, item in enumerate(rows):
            values = [item["horario"], item["tipo"], item["origem"], item["forma"], _money(item["valor"]), item["observacao"]]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                if col in {0, 1, 4}:
                    table_item.setTextAlignment(Qt.AlignCenter)
                self._movements_table.setItem(row, col, table_item)

    def _set_filter(self, filter_key: str) -> None:
        self._movement_filter = filter_key
        self._render_movements()

    def _open_output_dialog(self) -> None:
        dialog = OutputEntryDialog(self)
        if not dialog.exec_() or not dialog.output_data:
            return
        try:
            register_output(
                dialog.output_data["descricao"],
                dialog.output_data["valor"],
                dialog.output_data["data"],
                dialog.output_data["categoria"],
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao registrar saída.\n\n{exc}")
            return
        QMessageBox.information(self, "Fluxo de Caixa", "Saída registrada com sucesso.")
        self.reload_cash_flow()

    def _open_order_in_cashier(self) -> None:
        raw = self._order_id_input.text().strip().replace("#", "")
        if not raw.isdigit():
            QMessageBox.warning(self, "Fluxo de Caixa", "Informe um número de OS válido.")
            return
        dialog = FinalizeOrderDialog(int(raw), self)
        if dialog.exec_():
            self.reload_cash_flow()

    def _run_conference(self) -> None:
        counted_values = {}
        for forma, field in self._conference_inputs.items():
            raw = field.text().strip().replace(".", "").replace(",", ".")
            try:
                counted_values[forma] = float(raw) if raw else 0.0
            except ValueError:
                QMessageBox.warning(self, "Conferência", f"Valor inválido para {forma}.")
                return
        try:
            result = get_cash_conference(self._conference_date.date().toPyDate(), counted_values)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar conferência.\n\n{exc}")
            return

        rows = result.get("comparativo") or []
        self._conference_table.clearContents()
        self._conference_table.clearSpans()
        if not rows:
            self._conference_table.setRowCount(1)
            placeholder = QTableWidgetItem("Sem dados para conferência.")
            placeholder.setFlags(Qt.ItemIsEnabled)
            placeholder.setTextAlignment(Qt.AlignCenter)
            self._conference_table.setItem(0, 0, placeholder)
            self._conference_table.setSpan(0, 0, 1, 4)
            return

        self._conference_table.setRowCount(len(rows) + 1)
        for row, item in enumerate(rows):
            values = [
                item["forma_pagamento"],
                _money(item["valor_esperado"]),
                _money(item["valor_contado"]),
                _money(item["diferenca"]),
            ]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                if col > 0:
                    table_item.setTextAlignment(Qt.AlignCenter)
                self._conference_table.setItem(row, col, table_item)

        footer_row = len(rows)
        footer = [
            "Saldo estimado",
            _money(result.get("total_esperado", 0)),
            _money(result.get("total_saidas", 0)),
            _money(result.get("saldo_estimado", 0)),
        ]
        for col, value in enumerate(footer):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter if col > 0 else Qt.AlignLeft | Qt.AlignVCenter)
            self._conference_table.setItem(footer_row, col, item)
