from __future__ import annotations

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.services.reports_service import (
    default_filename,
    export_accounting_excel,
    export_operational_excel,
    export_production_excel,
    get_accounting_summary,
    get_operational_summary,
    get_production_summary,
    list_active_professionals,
)
from desktop.ui.components.summary_card import SummaryCard


def _money(value: float) -> str:
    amount = float(value or 0)
    text = f"{amount:,.2f}"
    return f"R$ {text}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_date(value: str) -> str:
    if not value:
        return "-"
    if len(value) == 10 and value[4] == "-":
        year, month, day = value.split("-")
        return f"{day}/{month}/{year}"
    return value


class ReportsScreen(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._production_cards: dict[str, SummaryCard] = {}
        self._accounting_cards: dict[str, SummaryCard] = {}
        self._operational_cards: dict[str, SummaryCard] = {}

        self._production_professional = QComboBox()
        self._production_start = QDateEdit()
        self._production_end = QDateEdit()
        self._production_table = QTableWidget(0, 5)
        self._production_period_label = QLabel("-")
        self._production_selected_label = QLabel("-")

        self._accounting_month = QDateEdit()
        self._accounting_table = QTableWidget(0, 3)

        self._operational_start = QDateEdit()
        self._operational_end = QDateEdit()
        self._services_table = QTableWidget(0, 5)
        self._parts_table = QTableWidget(0, 5)
        self._outputs_table = QTableWidget(0, 4)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)
        root.addWidget(self._build_header())
        root.addWidget(self._build_tabs(), 1)

        self._setup_tables()
        self._setup_dates()
        self.reload_all()

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Relatórios")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Painel nativo de produção, contabilidade e visão operacional com dados reais e exportação Excel."
        )
        subtitle.setObjectName("screenText")
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)

        back_button = QPushButton("Voltar ao início")
        back_button.clicked.connect(lambda: self.navigate_requested.emit("home"))

        layout.addLayout(texts, 1)
        layout.addWidget(back_button)
        return card

    def _build_tabs(self) -> QWidget:
        tabs = QTabWidget()
        tabs.addTab(self._build_production_tab(), "Produção")
        tabs.addTab(self._build_accounting_tab(), "Contabilidade")
        tabs.addTab(self._build_operational_tab(), "Operacional")
        return tabs

    def _build_production_tab(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        filters = QFrame()
        filters.setObjectName("screenCard")
        layout = QGridLayout(filters)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        search_button = QPushButton("Pesquisar")
        search_button.clicked.connect(self._load_production)
        export_button = QPushButton("Exportar Excel")
        export_button.clicked.connect(self._export_production)

        layout.addWidget(QLabel("Profissional"), 0, 0)
        layout.addWidget(QLabel("Data início"), 0, 1)
        layout.addWidget(QLabel("Data fim"), 0, 2)
        layout.addWidget(self._production_professional, 1, 0)
        layout.addWidget(self._production_start, 1, 1)
        layout.addWidget(self._production_end, 1, 2)
        layout.addWidget(search_button, 1, 3)
        layout.addWidget(export_button, 1, 4)
        layout.setColumnStretch(0, 1)

        context_card = QFrame()
        context_card.setObjectName("screenCard")
        context_layout = QGridLayout(context_card)
        context_layout.setContentsMargins(18, 14, 18, 14)
        context_layout.addWidget(QLabel("Profissional selecionado:"), 0, 0)
        context_layout.addWidget(self._production_selected_label, 0, 1)
        context_layout.addWidget(QLabel("Período solicitado:"), 1, 0)
        context_layout.addWidget(self._production_period_label, 1, 1)
        context_layout.setColumnStretch(1, 1)

        summary_row = self._build_summary_row(
            self._production_cards,
            [
                ("qtd", "Serviços"),
                ("total", "Total"),
                ("media", "Média"),
                ("intervalo", "Intervalo"),
            ],
        )

        table_card = QFrame()
        table_card.setObjectName("screenCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.addWidget(self._production_table)

        root.addWidget(filters)
        root.addWidget(context_card)
        root.addWidget(summary_row)
        root.addWidget(table_card, 1)
        return panel

    def _build_accounting_tab(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        filters = QFrame()
        filters.setObjectName("screenCard")
        layout = QGridLayout(filters)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        load_button = QPushButton("Atualizar resumo")
        load_button.clicked.connect(self._load_accounting)
        export_button = QPushButton("Exportar Excel")
        export_button.clicked.connect(self._export_accounting)

        layout.addWidget(QLabel("Mês de referência"), 0, 0)
        layout.addWidget(self._accounting_month, 1, 0)
        layout.addWidget(load_button, 1, 1)
        layout.addWidget(export_button, 1, 2)
        layout.setColumnStretch(0, 1)

        summary_row_1 = self._build_summary_row(
            self._accounting_cards,
            [
                ("faturamento", "Faturamento bruto"),
                ("saidas", "Total saídas"),
                ("saldo", "Saldo operacional"),
                ("os", "OS concluídas"),
            ],
        )
        summary_row_2 = self._build_summary_row(
            self._accounting_cards,
            [("ticket", "Ticket médio"), ("periodo", "Período")],
        )
        self._accounting_cards["periodo"].set_value("-")

        table_card = QFrame()
        table_card.setObjectName("screenCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.addWidget(self._accounting_table)

        root.addWidget(filters)
        root.addWidget(summary_row_1)
        root.addWidget(summary_row_2)
        root.addWidget(table_card, 1)
        return panel

    def _build_operational_tab(self) -> QWidget:
        panel = QWidget()
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        filters = QFrame()
        filters.setObjectName("screenCard")
        layout = QGridLayout(filters)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)

        load_button = QPushButton("Atualizar")
        load_button.clicked.connect(self._load_operational)
        export_button = QPushButton("Exportar Excel")
        export_button.clicked.connect(self._export_operational)

        layout.addWidget(QLabel("Data início"), 0, 0)
        layout.addWidget(QLabel("Data fim"), 0, 1)
        layout.addWidget(self._operational_start, 1, 0)
        layout.addWidget(self._operational_end, 1, 1)
        layout.addWidget(load_button, 1, 2)
        layout.addWidget(export_button, 1, 3)

        summary_row_1 = self._build_summary_row(
            self._operational_cards,
            [
                ("qtd_servicos", "Qtd serviços"),
                ("total_servicos", "Total serviços"),
                ("qtd_pecas", "Qtd peças"),
                ("total_pecas", "Total peças"),
            ],
        )
        summary_row_2 = self._build_summary_row(
            self._operational_cards,
            [
                ("qtd_saidas", "Qtd saídas"),
                ("total_saidas", "Total saídas"),
                ("periodo", "Período"),
            ],
        )
        self._operational_cards["periodo"].set_value("-")

        tables_wrapper = QWidget()
        tables_layout = QVBoxLayout(tables_wrapper)
        tables_layout.setContentsMargins(0, 0, 0, 0)
        tables_layout.setSpacing(12)
        tables_layout.addWidget(self._build_table_group("Serviços", self._services_table), 1)
        tables_layout.addWidget(self._build_table_group("Peças", self._parts_table), 1)
        tables_layout.addWidget(self._build_table_group("Saídas", self._outputs_table), 1)

        root.addWidget(filters)
        root.addWidget(summary_row_1)
        root.addWidget(summary_row_2)
        root.addWidget(tables_wrapper, 1)
        return panel

    def _build_table_group(self, title: str, table: QTableWidget) -> QWidget:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(table)
        return group

    def _build_summary_row(self, target: dict[str, SummaryCard], items: list[tuple[str, str]]) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for key, title in items:
            card = SummaryCard(title)
            target[key] = card
            layout.addWidget(card, 1)
        return wrapper

    def _setup_dates(self) -> None:
        today = QDate.currentDate()
        for widget in [self._production_start, self._production_end, self._operational_start, self._operational_end]:
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.setDate(today)

        self._accounting_month.setCalendarPopup(True)
        self._accounting_month.setDisplayFormat("MM/yyyy")
        self._accounting_month.setDate(QDate(today.year(), today.month(), 1))

    def _setup_tables(self) -> None:
        self._production_table.setHorizontalHeaderLabels(["OS", "Data", "Cliente", "Serviço", "Valor"])
        self._accounting_table.setHorizontalHeaderLabels(["Forma de pagamento", "Quantidade", "Valor total"])
        self._services_table.setHorizontalHeaderLabels(["OS", "Data", "Profissional", "Serviço", "Valor"])
        self._parts_table.setHorizontalHeaderLabels(["OS", "Data", "Peça", "Qtd", "Total"])
        self._outputs_table.setHorizontalHeaderLabels(["Data", "Categoria", "Descrição", "Valor"])

        for table in [
            self._production_table,
            self._accounting_table,
            self._services_table,
            self._parts_table,
            self._outputs_table,
        ]:
            table.setAlternatingRowColors(True)
            table.setSelectionMode(QTableWidget.NoSelection)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            header = table.horizontalHeader()
            header.setStretchLastSection(False)
            for col in range(table.columnCount()):
                resize_mode = header.Stretch if col not in {0, table.columnCount() - 1} else header.ResizeToContents
                header.setSectionResizeMode(col, resize_mode)

    def reload_all(self) -> None:
        self._load_professionals()
        self._load_production()
        self._load_accounting()
        self._load_operational()

    def _load_professionals(self) -> None:
        try:
            names = list_active_professionals()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar profissionais.\n\n{exc}")
            names = []

        current = self._production_professional.currentText()
        self._production_professional.clear()
        self._production_professional.addItems(names)
        if current:
            index = self._production_professional.findText(current)
            if index >= 0:
                self._production_professional.setCurrentIndex(index)

    def _load_production(self) -> None:
        if self._production_professional.count() == 0:
            self._production_selected_label.setText("-")
            self._production_period_label.setText("-")
            self._populate_table(self._production_table, [], placeholder_columns=5)
            return
        try:
            report = get_production_summary(
                self._production_professional.currentText(),
                self._production_start.date().toPyDate(),
                self._production_end.date().toPyDate(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Relatórios", str(exc))
            return

        period_label = f"{_format_date(report['periodo']['inicio'])} até {_format_date(report['periodo']['fim'])}"
        self._production_selected_label.setText(report["profissional"])
        self._production_period_label.setText(period_label)
        summary = report["resumo"]
        self._production_cards["qtd"].set_value(summary.get("quantidade_servicos", 0))
        self._production_cards["total"].set_value(_money(summary.get("valor_total", 0)))
        self._production_cards["media"].set_value(_money(summary.get("media_por_servico", 0)))
        self._production_cards["intervalo"].set_value(period_label)

        rows = [
            [
                f"#{item.get('ordem_id')}",
                item.get("data_referencia", "-"),
                item.get("cliente", "-"),
                item.get("descricao_servico", "-"),
                _money(item.get("valor_servico", 0)),
            ]
            for item in report["servicos"]
        ]
        self._populate_table(self._production_table, rows, placeholder_columns=5)

    def _load_accounting(self) -> None:
        try:
            report = get_accounting_summary(self._accounting_month.date().toPyDate())
        except Exception as exc:
            QMessageBox.warning(self, "Relatórios", str(exc))
            return

        self._accounting_cards["faturamento"].set_value(_money(report["faturamento_bruto"]))
        self._accounting_cards["saidas"].set_value(_money(report["total_saidas"]))
        self._accounting_cards["saldo"].set_value(_money(report["saldo_operacional"]))
        self._accounting_cards["os"].set_value(report["quantidade_os"])
        self._accounting_cards["ticket"].set_value(_money(report["ticket_medio"]))
        self._accounting_cards["periodo"].set_value(
            f"{_format_date(report['periodo']['inicio'])} até {_format_date(report['periodo']['fim'])}"
        )

        rows = [
            [
                item.get("forma_pagamento", "Não informado"),
                str(item.get("quantidade", 0)),
                _money(item.get("valor_total", 0)),
            ]
            for item in report["pagamentos"]
        ]
        self._populate_table(self._accounting_table, rows, placeholder_columns=3)

    def _load_operational(self) -> None:
        try:
            report = get_operational_summary(
                self._operational_start.date().toPyDate(),
                self._operational_end.date().toPyDate(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Relatórios", str(exc))
            return

        summary = report["resumo"]
        self._operational_cards["qtd_servicos"].set_value(summary["quantidade_servicos"])
        self._operational_cards["total_servicos"].set_value(_money(summary["valor_servicos"]))
        self._operational_cards["qtd_pecas"].set_value(summary["quantidade_pecas"])
        self._operational_cards["total_pecas"].set_value(_money(summary["valor_pecas"]))
        self._operational_cards["qtd_saidas"].set_value(summary["quantidade_saidas"])
        self._operational_cards["total_saidas"].set_value(_money(summary["valor_saidas"]))
        self._operational_cards["periodo"].set_value(
            f"{_format_date(report['periodo']['inicio'])} até {_format_date(report['periodo']['fim'])}"
        )

        self._populate_table(
            self._services_table,
            [
                [
                    f"#{item.get('ordem_id')}",
                    item.get("data_referencia", "-"),
                    item.get("profissional", "-"),
                    item.get("descricao", "-"),
                    _money(item.get("valor", 0)),
                ]
                for item in report["servicos"]
            ],
            placeholder_columns=5,
        )
        self._populate_table(
            self._parts_table,
            [
                [
                    f"#{item.get('ordem_id')}",
                    item.get("data_referencia", "-"),
                    item.get("descricao", "-"),
                    str(item.get("quantidade", 0)),
                    _money(item.get("valor_total", 0)),
                ]
                for item in report["pecas"]
            ],
            placeholder_columns=5,
        )
        self._populate_table(
            self._outputs_table,
            [
                [
                    item.get("data_referencia", "-"),
                    item.get("categoria", "-"),
                    item.get("descricao", "-"),
                    _money(item.get("valor", 0)),
                ]
                for item in report["saidas"]
            ],
            placeholder_columns=4,
        )

    def _populate_table(self, table: QTableWidget, rows: list[list[str]], placeholder_columns: int) -> None:
        table.clearContents()
        table.clearSpans()
        if not rows:
            table.setRowCount(1)
            item = QTableWidgetItem("Sem dados.")
            item.setFlags(Qt.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, placeholder_columns)
            return

        table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if col_index in {0, len(row_values) - 1}:
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_index, col_index, item)

    def _pick_target(self, suggested_name: str) -> str | None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório",
            suggested_name,
            "Planilha Excel (*.xlsx)",
        )
        return file_path or None

    def _export_production(self) -> None:
        professional = self._production_professional.currentText()
        start_date = self._production_start.date().toPyDate()
        end_date = self._production_end.date().toPyDate()
        target = self._pick_target(default_filename("producao", professional=professional, end_date=end_date))
        if not target:
            return
        try:
            export_production_excel(professional, start_date, end_date, target)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório.\n\n{exc}")
            return
        QMessageBox.information(self, "Relatórios", "Excel de produção salvo com sucesso.")

    def _export_accounting(self) -> None:
        month_date = self._accounting_month.date().toPyDate()
        target = self._pick_target(default_filename("contabilidade", month=month_date))
        if not target:
            return
        try:
            export_accounting_excel(month_date, target)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório.\n\n{exc}")
            return
        QMessageBox.information(self, "Relatórios", "Excel contábil salvo com sucesso.")

    def _export_operational(self) -> None:
        start_date = self._operational_start.date().toPyDate()
        end_date = self._operational_end.date().toPyDate()
        target = self._pick_target(default_filename("operacional", start_date=start_date, end_date=end_date))
        if not target:
            return
        try:
            export_operational_excel(start_date, end_date, target)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório.\n\n{exc}")
            return
        QMessageBox.information(self, "Relatórios", "Excel operacional salvo com sucesso.")
