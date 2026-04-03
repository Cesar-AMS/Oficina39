from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.infrastructure.asset_paths import default_logo_path
from desktop.services.settings_service import (
    create_professional,
    default_export_filename,
    export_data_to_file,
    get_backup_status,
    import_data_from_file,
    list_audit_history,
    list_professionals,
    list_report_history,
    load_settings,
    remove_professional,
    run_database_backup,
    save_settings,
    store_branding_asset,
)
from desktop.ui.components.logo_card import LogoCard


def _text(value) -> str:
    cleaned = "" if value is None else str(value).strip()
    return cleaned


def _digits(value: str) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def _format_phone(value: str) -> str:
    digits = _digits(value)
    if len(digits) <= 10:
        if len(digits) <= 2:
            return digits
        if len(digits) <= 6:
            return f"({digits[:2]}) {digits[2:]}"
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:10]}"
    if len(digits) <= 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:11]}"
    return digits


def _format_whatsapp(value: str) -> str:
    digits = _digits(value)
    if not digits:
        return ""
    if len(digits) <= 2:
        return f"+{digits}"
    if len(digits) <= 4:
        return f"+{digits[:2]} ({digits[2:]}"
    if len(digits) <= 9:
        return f"+{digits[:2]} ({digits[2:4]}) {digits[4:]}"
    return f"+{digits[:2]} ({digits[2:4]}) {digits[4:9]}-{digits[9:13]}"


class SettingsScreen(QWidget):
    settings_saved = pyqtSignal()
    navigate_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fields: dict[str, QWidget] = {}
        self._pending_branding: dict[str, str | None] = {"logo": None, "qrcode1": None, "qrcode2": None}
        self._current_settings: dict = {}

        self._logo_card = LogoCard()
        self._logo_scale_label = QLabel("100%")
        self._qr1_preview = QLabel()
        self._qr2_preview = QLabel()
        self._professionals_table = QTableWidget(0, 3)
        self._backup_status_label = QLabel("Carregando status de backup...")
        self._export_type_combo = QComboBox()
        self._export_format_combo = QComboBox()
        self._import_type_combo = QComboBox()
        self._history_table = QTableWidget(0, 6)
        self._audit_table = QTableWidget(0, 6)

        self._build_ui()
        self.reload_settings()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "Geral")
        tabs.addTab(self._build_branding_tab(), "Branding")
        tabs.addTab(self._build_integrations_tab(), "Integracoes")
        tabs.addTab(self._build_professionals_tab(), "Profissionais")
        tabs.addTab(self._build_data_tab(), "Dados")
        tabs.addTab(self._build_history_tab(), "Historico")
        content_layout.addWidget(tabs)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        reload_button = QPushButton("Recarregar")
        reload_button.clicked.connect(self.reload_settings)
        save_button = QPushButton("Salvar configuracoes")
        save_button.clicked.connect(self._save_settings)
        buttons.addWidget(reload_button)
        buttons.addWidget(save_button)
        root.addLayout(buttons)

    def _build_header(self) -> QWidget:
        card = QFrame()
        card.setObjectName("screenCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        texts = QVBoxLayout()
        title = QLabel("Configuracoes")
        title.setObjectName("screenTitle")
        subtitle = QLabel(
            "Painel nativo para branding, dados da empresa, integracoes e preferencias operacionais do sistema."
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

    def _build_general_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        company_box = QGroupBox("Empresa e sistema")
        company_form = QFormLayout(company_box)
        company_form.setHorizontalSpacing(16)
        company_form.setVerticalSpacing(10)
        for label, key in [
            ("Nome de exibicao do sistema", "empresa_nome"),
            ("Nome da empresa", "nome_exibicao_sistema"),
            ("E-mail da empresa", "empresa_email"),
            ("Telefone da empresa", "empresa_telefone"),
            ("Endereco da empresa", "empresa_endereco"),
            ("WhatsApp para orcamentos", "whatsapp_orcamento"),
        ]:
            field = QLineEdit()
            if key == "empresa_telefone":
                field.editingFinished.connect(lambda key=key: self._format_line_edit(key, _format_phone))
            if key == "whatsapp_orcamento":
                field.editingFinished.connect(lambda key=key: self._format_line_edit(key, _format_whatsapp))
            self._fields[key] = field
            company_form.addRow(f"{label}:", field)
        theme_combo = QComboBox()
        theme_combo.addItem("Tema escuro", "escuro")
        theme_combo.addItem("Tema claro", "claro")
        self._fields["tema_visual"] = theme_combo
        company_form.addRow("Tema da interface:", theme_combo)
        layout.addWidget(company_box)

        mail_box = QGroupBox("Envio automatico")
        mail_form = QFormLayout(mail_box)
        mail_form.setHorizontalSpacing(16)
        mail_form.setVerticalSpacing(10)
        self._fields["email_cliente"] = QLineEdit()
        self._fields["senha_app"] = QLineEdit()
        self._fields["senha_app"].setEchoMode(QLineEdit.Password)
        self._fields["email_contador"] = QLineEdit()
        professional_combo = QComboBox()
        self._fields["profissional_envio_auto"] = professional_combo
        frequency_combo = QComboBox()
        frequency_combo.addItem("Diario", "diario")
        frequency_combo.addItem("Semanal", "semanal")
        frequency_combo.addItem("Mensal", "mensal")
        self._fields["frequencia"] = frequency_combo
        day_spin = QSpinBox()
        day_spin.setRange(1, 28)
        self._fields["dia_envio"] = day_spin
        active_checkbox = QCheckBox("Ativar envio automatico de relatorios")
        self._fields["ativo"] = active_checkbox

        mail_form.addRow("E-mail remetente:", self._fields["email_cliente"])
        mail_form.addRow("Senha de app:", self._fields["senha_app"])
        mail_form.addRow("E-mail do contador:", self._fields["email_contador"])
        mail_form.addRow("Profissional para envio auto:", professional_combo)
        mail_form.addRow("Frequencia:", frequency_combo)
        mail_form.addRow("Dia do mes:", day_spin)
        mail_form.addRow("", active_checkbox)
        layout.addWidget(mail_box)
        layout.addStretch(1)
        return page

    def _build_branding_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        preview_card = QFrame()
        preview_card.setObjectName("screenCard")
        preview_layout = QGridLayout(preview_card)
        preview_layout.setContentsMargins(18, 18, 18, 18)
        preview_layout.setHorizontalSpacing(18)
        preview_layout.setVerticalSpacing(12)

        self._fields["logo_index_formato"] = QComboBox()
        self._fields["logo_index_formato"].addItem("Circulo", "circulo")
        self._fields["logo_index_formato"].addItem("Quadrado", "quadrado")
        self._fields["logo_index_formato"].currentIndexChanged.connect(self._update_branding_preview)

        self._fields["logo_index_escala"] = QSlider(Qt.Horizontal)
        self._fields["logo_index_escala"].setRange(70, 300)
        self._fields["logo_index_escala"].valueChanged.connect(self._update_branding_preview)
        self._fields["logo_index_offset_x"] = QSlider(Qt.Horizontal)
        self._fields["logo_index_offset_x"].setRange(-30, 30)
        self._fields["logo_index_offset_x"].valueChanged.connect(self._update_branding_preview)
        self._fields["logo_index_offset_y"] = QSlider(Qt.Horizontal)
        self._fields["logo_index_offset_y"].setRange(-30, 30)
        self._fields["logo_index_offset_y"].valueChanged.connect(self._update_branding_preview)

        choose_logo = QPushButton("Selecionar logo")
        choose_logo.clicked.connect(lambda: self._choose_branding_asset("logo"))
        reset_logo = QPushButton("Resetar ajuste")
        reset_logo.clicked.connect(self._reset_logo_adjustment)

        preview_layout.addWidget(self._logo_card, 0, 0, 6, 1)
        preview_layout.addWidget(QLabel("Formato:"), 0, 1)
        preview_layout.addWidget(self._fields["logo_index_formato"], 0, 2)
        preview_layout.addWidget(QLabel("Escala:"), 1, 1)
        preview_layout.addWidget(self._fields["logo_index_escala"], 1, 2)
        preview_layout.addWidget(self._logo_scale_label, 1, 3)
        preview_layout.addWidget(QLabel("Horizontal:"), 2, 1)
        preview_layout.addWidget(self._fields["logo_index_offset_x"], 2, 2, 1, 2)
        preview_layout.addWidget(QLabel("Vertical:"), 3, 1)
        preview_layout.addWidget(self._fields["logo_index_offset_y"], 3, 2, 1, 2)
        preview_layout.addWidget(choose_logo, 4, 1)
        preview_layout.addWidget(reset_logo, 4, 2)
        preview_layout.addWidget(QLabel("Ajuste visual usado na Home e no PDF."), 5, 1, 1, 3)
        layout.addWidget(preview_card)

        qr_box = QGroupBox("QR Codes")
        qr_layout = QHBoxLayout(qr_box)
        qr_layout.setSpacing(18)
        qr_layout.addWidget(self._build_qr_panel("QR Code 1", self._qr1_preview, "qrcode1"), 1)
        qr_layout.addWidget(self._build_qr_panel("QR Code 2", self._qr2_preview, "qrcode2"), 1)
        layout.addWidget(qr_box)
        layout.addStretch(1)
        return page

    def _build_qr_panel(self, title: str, preview_label: QLabel, slot: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setObjectName("screenText")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setMinimumSize(180, 180)
        preview_label.setObjectName("imagePreview")
        preview_label.setFrameShape(QFrame.Box)

        button = QPushButton(f"Selecionar {title}")
        button.clicked.connect(lambda: self._choose_branding_asset(slot))

        layout.addWidget(label)
        layout.addWidget(preview_label)
        layout.addWidget(button)
        return wrapper

    def _build_integrations_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        cep_box = QGroupBox("Integracao de CEP")
        cep_form = QFormLayout(cep_box)
        for label, key in [
            ("Provedor ativo", "cep_provider_ativo"),
            ("Primario", "cep_provider_primario"),
            ("API key primaria", "cep_api_key_primaria"),
            ("Secundario", "cep_provider_secundario"),
            ("API key secundaria", "cep_api_key_secundaria"),
        ]:
            field = QLineEdit()
            self._fields[key] = field
            cep_form.addRow(f"{label}:", field)
        layout.addWidget(cep_box)

        plate_box = QGroupBox("Integracao de placa")
        plate_form = QFormLayout(plate_box)
        for label, key in [
            ("Provedor ativo", "placa_provider_ativo"),
            ("Primario", "placa_provider_primario"),
            ("API key primaria", "placa_api_key_primaria"),
            ("Secundario", "placa_provider_secundario"),
            ("API key secundaria", "placa_api_key_secundaria"),
        ]:
            field = QLineEdit()
            self._fields[key] = field
            plate_form.addRow(f"{label}:", field)
        layout.addWidget(plate_box)
        layout.addStretch(1)
        return page

    def _build_professionals_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        form_box = QGroupBox("Cadastro de profissionais")
        form_layout = QGridLayout(form_box)
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(10)

        self._fields["profissional_nome"] = QLineEdit()
        self._fields["profissional_cnpj"] = QLineEdit()
        add_button = QPushButton("Cadastrar profissional")
        add_button.clicked.connect(self._create_professional)

        form_layout.addWidget(QLabel("Nome:"), 0, 0)
        form_layout.addWidget(self._fields["profissional_nome"], 0, 1)
        form_layout.addWidget(QLabel("CNPJ:"), 0, 2)
        form_layout.addWidget(self._fields["profissional_cnpj"], 0, 3)
        form_layout.addWidget(add_button, 0, 4)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)
        layout.addWidget(form_box)

        table_box = QFrame()
        table_box.setObjectName("screenCard")
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(12)

        self._professionals_table.setHorizontalHeaderLabels(["ID", "Nome", "CNPJ"])
        self._professionals_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._professionals_table.setSelectionMode(QTableWidget.SingleSelection)
        self._professionals_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._professionals_table.verticalHeader().setVisible(False)
        header = self._professionals_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeToContents)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, header.ResizeToContents)

        remove_button = QPushButton("Remover profissional selecionado")
        remove_button.clicked.connect(self._delete_selected_professional)
        table_layout.addWidget(self._professionals_table)
        table_layout.addWidget(remove_button, 0, Qt.AlignRight)
        layout.addWidget(table_box, 1)
        return page

    def _build_data_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        backup_box = QGroupBox("Backup do banco")
        backup_layout = QVBoxLayout(backup_box)
        backup_layout.setSpacing(10)
        self._backup_status_label.setWordWrap(True)
        backup_button = QPushButton("Executar backup agora")
        backup_button.clicked.connect(self._run_backup)
        backup_layout.addWidget(self._backup_status_label)
        backup_layout.addWidget(backup_button, 0, Qt.AlignLeft)
        layout.addWidget(backup_box)

        export_box = QGroupBox("Exportacao")
        export_layout = QFormLayout(export_box)
        self._export_type_combo.addItem("Banco completo", "completo")
        self._export_type_combo.addItem("Clientes", "clientes")
        self._export_type_combo.addItem("Ordens", "ordens")
        self._export_type_combo.addItem("Financeiro", "financeiro")
        self._export_format_combo.addItem("SQLite (.db)", "db")
        self._export_format_combo.addItem("CSV", "csv")
        self._export_format_combo.addItem("Excel (.xlsx)", "xlsx")
        self._export_format_combo.addItem("JSON", "json")
        export_button = QPushButton("Exportar dados")
        export_button.clicked.connect(self._export_data)
        export_layout.addRow("Tipo:", self._export_type_combo)
        export_layout.addRow("Formato:", self._export_format_combo)
        export_layout.addRow("", export_button)
        layout.addWidget(export_box)

        import_box = QGroupBox("Importacao")
        import_layout = QFormLayout(import_box)
        self._import_type_combo.addItem("Clientes", "clientes")
        self._import_type_combo.addItem("Ordens", "ordens")
        self._import_type_combo.addItem("Financeiro", "financeiro")
        import_button = QPushButton("Importar arquivo")
        import_button.clicked.connect(self._import_data)
        import_layout.addRow("Tipo:", self._import_type_combo)
        import_layout.addRow("", import_button)
        layout.addWidget(import_box)

        layout.addStretch(1)
        return page

    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        reports_box = QGroupBox("Ultimos relatorios enviados")
        reports_layout = QVBoxLayout(reports_box)
        self._history_table.setHorizontalHeaderLabels(
            ["Data/Hora", "Periodo", "Formato", "Remetente", "Destinatario", "Status"]
        )
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.verticalHeader().setVisible(False)
        report_header = self._history_table.horizontalHeader()
        report_header.setSectionResizeMode(0, report_header.ResizeToContents)
        report_header.setSectionResizeMode(1, report_header.ResizeToContents)
        report_header.setSectionResizeMode(2, report_header.ResizeToContents)
        report_header.setSectionResizeMode(3, report_header.Stretch)
        report_header.setSectionResizeMode(4, report_header.Stretch)
        report_header.setSectionResizeMode(5, report_header.ResizeToContents)
        reports_layout.addWidget(self._history_table)
        layout.addWidget(reports_box)

        audit_box = QGroupBox("Auditoria operacional")
        audit_layout = QVBoxLayout(audit_box)
        self._audit_table.setHorizontalHeaderLabels(
            ["Data/Hora", "Acao", "Entidade", "ID", "Operador", "Observacao"]
        )
        self._audit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._audit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._audit_table.verticalHeader().setVisible(False)
        audit_header = self._audit_table.horizontalHeader()
        audit_header.setSectionResizeMode(0, audit_header.ResizeToContents)
        audit_header.setSectionResizeMode(1, audit_header.ResizeToContents)
        audit_header.setSectionResizeMode(2, audit_header.ResizeToContents)
        audit_header.setSectionResizeMode(3, audit_header.ResizeToContents)
        audit_header.setSectionResizeMode(4, audit_header.ResizeToContents)
        audit_header.setSectionResizeMode(5, audit_header.Stretch)
        audit_layout.addWidget(self._audit_table)
        layout.addWidget(audit_box, 1)
        return page

    def _format_line_edit(self, key: str, formatter) -> None:
        field = self._fields.get(key)
        if not isinstance(field, QLineEdit):
            return
        field.setText(formatter(field.text()))

    def reload_settings(self) -> None:
        try:
            self._current_settings = load_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Nao foi possivel carregar as configuracoes.\n\n{exc}")
            return
        self._pending_branding = {"logo": None, "qrcode1": None, "qrcode2": None}
        self._apply_settings()
        self._reload_professionals()
        self._reload_backup_status()
        self._reload_history_tables()

    def _apply_settings(self) -> None:
        data = self._current_settings
        for key, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                widget.setText(_text(data.get(key)))
            elif isinstance(widget, QComboBox):
                if key == "profissional_envio_auto":
                    current_value = _text(data.get(key))
                    widget.blockSignals(True)
                    widget.clear()
                    widget.addItem("Todos os profissionais", "")
                    for professional in data.get("profissionais", []):
                        widget.addItem(professional, professional)
                    index = max(0, widget.findData(current_value))
                    widget.setCurrentIndex(index)
                    widget.blockSignals(False)
                else:
                    current_value = _text(data.get(key))
                    index = widget.findData(current_value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    elif widget.count():
                        widget.setCurrentIndex(0)
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(data.get(key) or 1))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(data.get(key)))

        self._format_line_edit("empresa_telefone", _format_phone)
        self._format_line_edit("whatsapp_orcamento", _format_whatsapp)
        self._update_branding_preview()
        self._set_qr_preview(self._qr1_preview, data.get("qrcode_1_local_path"))
        self._set_qr_preview(self._qr2_preview, data.get("qrcode_2_local_path"))

    def _choose_branding_asset(self, slot: str) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.gif *.bmp)",
        )
        if not filename:
            return
        self._pending_branding[slot] = filename
        if slot == "logo":
            self._update_branding_preview()
        elif slot == "qrcode1":
            self._set_qr_preview(self._qr1_preview, filename)
        else:
            self._set_qr_preview(self._qr2_preview, filename)

    def _reset_logo_adjustment(self) -> None:
        self._fields["logo_index_escala"].setValue(100)
        self._fields["logo_index_offset_x"].setValue(0)
        self._fields["logo_index_offset_y"].setValue(0)
        self._update_branding_preview()

    def _update_branding_preview(self) -> None:
        format_combo = self._fields["logo_index_formato"]
        shape = format_combo.currentData() if isinstance(format_combo, QComboBox) else "circulo"
        scale_slider = self._fields["logo_index_escala"]
        scale = (scale_slider.value() if isinstance(scale_slider, QSlider) else 100) / 100.0
        offset_x = self._fields["logo_index_offset_x"].value() if isinstance(self._fields["logo_index_offset_x"], QSlider) else 0
        offset_y = self._fields["logo_index_offset_y"].value() if isinstance(self._fields["logo_index_offset_y"], QSlider) else 0
        image_path = (
            self._pending_branding.get("logo")
            or self._current_settings.get("logo_local_path")
            or default_logo_path()
        )
        self._logo_card.update_logo(
            image_path=image_path,
            shape=shape or "circulo",
            scale=scale,
            offset_x=float(offset_x),
            offset_y=float(offset_y),
        )
        self._logo_scale_label.setText(f"{int(scale * 100)}%")

    def _set_qr_preview(self, target: QLabel, path: str | None) -> None:
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                target.setPixmap(
                    pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                target.setText("")
                return
        target.setPixmap(QPixmap())
        target.setText("Sem imagem")

    def _collect_payload(self) -> dict:
        payload = {}
        for key, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                payload[key] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                payload[key] = widget.currentData() if key != "profissional_envio_auto" else widget.currentData() or ""
            elif isinstance(widget, QSpinBox):
                payload[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                payload[key] = widget.isChecked()

        payload["whatsapp_orcamento"] = _digits(payload.get("whatsapp_orcamento", ""))
        payload["logo_index_escala"] = self._fields["logo_index_escala"].value() / 100.0
        payload["logo_index_offset_x"] = self._fields["logo_index_offset_x"].value()
        payload["logo_index_offset_y"] = self._fields["logo_index_offset_y"].value()
        payload["logo_index_formato"] = self._fields["logo_index_formato"].currentData() or "circulo"

        payload["logo_index_path"] = _text(self._current_settings.get("logo_index_path"))
        payload["qrcode_1_path"] = _text(self._current_settings.get("qrcode_1_path"))
        payload["qrcode_2_path"] = _text(self._current_settings.get("qrcode_2_path"))

        if self._pending_branding.get("logo"):
            payload["logo_index_path"] = store_branding_asset(self._pending_branding["logo"], "logo")
        if self._pending_branding.get("qrcode1"):
            payload["qrcode_1_path"] = store_branding_asset(self._pending_branding["qrcode1"], "qrcode1")
        if self._pending_branding.get("qrcode2"):
            payload["qrcode_2_path"] = store_branding_asset(self._pending_branding["qrcode2"], "qrcode2")

        return payload

    def _save_settings(self) -> None:
        try:
            saved = save_settings(self._collect_payload())
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao salvar", str(exc))
            return

        self._current_settings = saved
        self._pending_branding = {"logo": None, "qrcode1": None, "qrcode2": None}
        self._apply_settings()
        self._reload_backup_status()
        self._reload_history_tables()
        self.settings_saved.emit()
        QMessageBox.information(self, "Sucesso", "Configuracoes salvas com sucesso.")

    def _reload_professionals(self) -> None:
        try:
            professionals = list_professionals()
        except Exception as exc:
            QMessageBox.warning(self, "Profissionais", f"Nao foi possivel carregar os profissionais.\n\n{exc}")
            professionals = []

        self._professionals_table.setRowCount(len(professionals))
        for row, professional in enumerate(professionals):
            values = [
                str(professional.get("id") or ""),
                _text(professional.get("nome")),
                _text(professional.get("cnpj")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setData(Qt.UserRole, professional.get("id"))
                    item.setTextAlignment(Qt.AlignCenter)
                self._professionals_table.setItem(row, col, item)

    def _create_professional(self) -> None:
        name = _text(self._fields["profissional_nome"].text() if isinstance(self._fields["profissional_nome"], QLineEdit) else "")
        cnpj = _text(self._fields["profissional_cnpj"].text() if isinstance(self._fields["profissional_cnpj"], QLineEdit) else "")
        try:
            create_professional(name, cnpj, True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao cadastrar", str(exc))
            return

        if isinstance(self._fields["profissional_nome"], QLineEdit):
            self._fields["profissional_nome"].clear()
        if isinstance(self._fields["profissional_cnpj"], QLineEdit):
            self._fields["profissional_cnpj"].clear()
        self.reload_settings()
        QMessageBox.information(self, "Sucesso", "Profissional cadastrado com sucesso.")

    def _delete_selected_professional(self) -> None:
        row = self._professionals_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Profissionais", "Selecione um profissional para remover.")
            return

        item = self._professionals_table.item(row, 0)
        professional_id = int(item.data(Qt.UserRole)) if item and item.data(Qt.UserRole) else None
        if professional_id is None:
            QMessageBox.warning(self, "Profissionais", "Nao foi possivel identificar o profissional selecionado.")
            return

        answer = QMessageBox.question(
            self,
            "Remover profissional",
            "Deseja realmente remover o profissional selecionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            remove_professional(professional_id)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao remover", str(exc))
            return

        self.reload_settings()
        QMessageBox.information(self, "Sucesso", "Profissional removido com sucesso.")

    def _reload_backup_status(self) -> None:
        try:
            status = get_backup_status()
        except Exception as exc:
            self._backup_status_label.setText(f"Nao foi possivel carregar o status do backup: {exc}")
            return

        text = (
            f"Quantidade de backups: {status.get('quantidade', 0)}\n"
            f"Ultimo arquivo: {_text(status.get('ultimo_arquivo')) or '---'}\n"
            f"Ultima execucao: {_text(status.get('ultimo_em')) or '---'}\n"
            f"Pasta: {_text(status.get('backup_dir')) or '---'}"
        )
        self._backup_status_label.setText(text)

    def _run_backup(self) -> None:
        try:
            result = run_database_backup()
        except Exception as exc:
            QMessageBox.critical(self, "Erro no backup", str(exc))
            return

        self._reload_backup_status()
        QMessageBox.information(
            self,
            "Backup concluido",
            f"Arquivo gerado: {_text(result.get('arquivo'))}\nTamanho: {result.get('tamanho_bytes', 0)} bytes",
        )

    def _export_data(self) -> None:
        export_type = self._export_type_combo.currentData() or "completo"
        export_format = self._export_format_combo.currentData() or "db"
        suggested = default_export_filename(export_type, export_format)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar exportacao",
            suggested,
            "Todos os arquivos (*.*)",
        )
        if not filename:
            return

        try:
            saved_path = export_data_to_file(export_type, export_format, filename)
        except Exception as exc:
            QMessageBox.critical(self, "Erro na exportacao", str(exc))
            return

        QMessageBox.information(self, "Exportacao concluida", f"Arquivo salvo em:\n{saved_path}")

    def _import_data(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo para importar",
            "",
            "Arquivos suportados (*.json *.csv *.xlsx)",
        )
        if not filename:
            return

        import_type = self._import_type_combo.currentData() or "clientes"
        try:
            result = import_data_from_file(import_type, filename)
        except Exception as exc:
            QMessageBox.critical(self, "Erro na importacao", str(exc))
            return

        QMessageBox.information(
            self,
            "Importacao concluida",
            (
                f"Clientes: {result.get('clientes', 0)}\n"
                f"Ordens: {result.get('ordens', 0)}\n"
                f"Saidas: {result.get('saidas', 0)}"
            ),
        )
        self._reload_history_tables()

    def _reload_history_tables(self) -> None:
        try:
            reports = list_report_history(20)
        except Exception:
            reports = []
        try:
            audit_rows = list_audit_history(50)
        except Exception:
            audit_rows = []

        self._history_table.setRowCount(len(reports))
        for row, report in enumerate(reports):
            values = [
                _text(report.get("data_envio")),
                _text(report.get("periodo")),
                _text(report.get("formato")).upper(),
                _text(report.get("remetente")),
                _text(report.get("destinatario")),
                _text(report.get("status")),
            ]
            for col, value in enumerate(values):
                self._history_table.setItem(row, col, QTableWidgetItem(value))

        self._audit_table.setRowCount(len(audit_rows))
        for row, event in enumerate(audit_rows):
            values = [
                _text(event.get("data_evento")),
                _text(event.get("acao")),
                _text(event.get("entidade")),
                _text(event.get("entidade_id")),
                _text(event.get("operador")),
                _text(event.get("observacao")),
            ]
            for col, value in enumerate(values):
                self._audit_table.setItem(row, col, QTableWidgetItem(value))
