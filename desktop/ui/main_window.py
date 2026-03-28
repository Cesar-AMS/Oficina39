from __future__ import annotations

from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.services.settings_service import load_settings
from desktop.ui.components.navigation import NavigationRail
from desktop.ui.screens.consult_orders_screen import ConsultOrdersScreen
from desktop.ui.screens.cash_flow_screen import CashFlowScreen
from desktop.ui.screens.clients_screen import ClientsScreen
from desktop.ui.screens.debts_screen import DebtsScreen
from desktop.ui.screens.home_screen import HomeScreen
from desktop.ui.screens.new_order_screen import NewOrderScreen
from desktop.ui.screens.placeholder_screen import PlaceholderScreen
from desktop.ui.screens.reports_screen import ReportsScreen
from desktop.ui.screens.settings_screen import SettingsScreen


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Oficina 39")
        self.resize(1440, 920)

        self._screen_map: dict[str, int] = {}
        self._stack = QStackedWidget()
        self._theme_mode = "escuro"

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._nav = NavigationRail(
            [
                ("home", "Inicio"),
                ("nova_os", "Nova OS"),
                ("consultar_os", "Consultar OS"),
                ("fluxo_caixa", "Fluxo Caixa"),
                ("clientes", "Clientes"),
                ("debitos", "Debitos"),
                ("configuracoes", "Configuracoes"),
                ("relatorios", "Relatorios"),
            ]
        )
        self._nav.section_changed.connect(self._change_screen)

        content_shell = self._build_content_shell()

        layout.addWidget(self._nav)
        layout.addWidget(content_shell, 1)

        self.setCentralWidget(central)
        self._register_screens()
        self._reload_theme_from_settings()
        self._nav.set_current("home")

    def _build_content_shell(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("contentShell")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(28, 24, 28, 24)
        wrapper_layout.setSpacing(18)

        title = QLabel("Sistema Oficina 39")
        title.setObjectName("windowTitle")

        subtitle = QLabel(
            "Base nativa em PyQt5 pronta para migrar as telas sem depender da interface web."
        )
        subtitle.setObjectName("windowSubtitle")
        subtitle.setWordWrap(True)

        header = QFrame()
        header.setObjectName("headerCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 18)
        header_layout.setSpacing(4)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(self._stack, 1)
        return wrapper

    def _register_screens(self) -> None:
        home_screen = HomeScreen()
        home_screen.navigate_requested.connect(self._nav.set_current)

        consult_orders_screen = ConsultOrdersScreen()
        consult_orders_screen.navigate_requested.connect(self._nav.set_current)

        new_order_screen = NewOrderScreen()
        new_order_screen.navigate_requested.connect(self._nav.set_current)
        new_order_screen.order_created.connect(lambda order_id: consult_orders_screen.reload_orders())

        clients_screen = ClientsScreen()
        clients_screen.navigate_requested.connect(self._nav.set_current)
        cash_flow_screen = CashFlowScreen()
        cash_flow_screen.navigate_requested.connect(self._nav.set_current)
        debts_screen = DebtsScreen()
        debts_screen.navigate_requested.connect(self._nav.set_current)

        settings_screen = SettingsScreen()
        settings_screen.navigate_requested.connect(self._nav.set_current)
        settings_screen.settings_saved.connect(home_screen.reload_state)
        settings_screen.settings_saved.connect(self._reload_theme_from_settings)

        reports_screen = ReportsScreen()
        reports_screen.navigate_requested.connect(self._nav.set_current)

        screens = {
            "home": home_screen,
            "nova_os": new_order_screen,
            "consultar_os": consult_orders_screen,
            "fluxo_caixa": cash_flow_screen,
            "clientes": clients_screen,
            "debitos": debts_screen,
            "configuracoes": settings_screen,
            "relatorios": reports_screen,
        }

        for key, screen in screens.items():
            index = self._stack.addWidget(screen)
            self._screen_map[key] = index

    def _change_screen(self, key: str) -> None:
        index = self._screen_map.get(key)
        if index is not None:
            self._stack.setCurrentIndex(index)

    def _reload_theme_from_settings(self) -> None:
        try:
            settings = load_settings()
            theme_mode = (settings.get("tema_visual") or "escuro").strip().lower()
        except Exception:
            theme_mode = "escuro"
        self.apply_theme(theme_mode)

    def apply_theme(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode if theme_mode in {"escuro", "claro"} else "escuro"
        self.setStyleSheet(self._stylesheet_for_theme(self._theme_mode))
        self._nav.apply_theme(self._theme_mode)

    def _stylesheet_for_theme(self, theme_mode: str) -> str:
        if theme_mode == "claro":
            return """
                QMainWindow {
                    background: #f4f7fb;
                    color: #243847;
                }
                #contentShell {
                    background: #f4f7fb;
                }
                #headerCard {
                    background: #ffffff;
                    border: 1px solid #d7e0e8;
                    border-radius: 18px;
                }
                #windowTitle {
                    color: #16344c;
                    font-size: 28px;
                    font-weight: 700;
                }
                #homeHeroTitle {
                    color: #17384f;
                    font-size: 32px;
                    font-weight: 800;
                }
                #homeCompanyTitle {
                    color: #1e6cb6;
                    font-size: 18px;
                    font-weight: 700;
                }
                #windowSubtitle {
                    color: #61788f;
                    font-size: 14px;
                }
                #screenCard {
                    background: #ffffff;
                    border: 1px solid #d7e0e8;
                    border-radius: 18px;
                }
                #screenTitle {
                    color: #16344c;
                    font-size: 24px;
                    font-weight: 700;
                }
                #screenText {
                    color: #4b6278;
                    font-size: 14px;
                    line-height: 1.4em;
                }
                #badge {
                    background: #ddf7e8;
                    color: #0f7a44;
                    border-radius: 999px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                #summaryCard {
                    background: #ffffff;
                    border: 1px solid #d7e0e8;
                    border-radius: 14px;
                }
                #summaryValue {
                    color: #17384f;
                    font-size: 26px;
                    font-weight: 800;
                }
                #summaryTitle {
                    color: #678096;
                    font-size: 12px;
                    text-transform: uppercase;
                }
                QWidget {
                    color: #243847;
                }
                QFrame, QDialog, QGroupBox {
                    background: #ffffff;
                }
                QGroupBox {
                    border: 1px solid #d7e0e8;
                    border-radius: 14px;
                    margin-top: 12px;
                    font-weight: 700;
                    color: #17384f;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                    color: #1e6cb6;
                }
                QPushButton {
                    background: #2a6db0;
                    color: #ffffff;
                    border: 1px solid #347dca;
                    border-radius: 10px;
                    padding: 10px 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #347dca;
                }
                QPushButton:pressed {
                    background: #255d97;
                }
                QPushButton:disabled {
                    background: #e4ebf2;
                    color: #7b8ea0;
                    border: 1px solid #d0dbe6;
                }
                QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
                    background: #ffffff;
                    color: #17384f;
                    border: 1px solid #c7d4df;
                    border-radius: 10px;
                    padding: 8px 10px;
                    selection-background-color: #347dca;
                }
                QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
                    border: 1px solid #5aa8f2;
                }
                QComboBox::drop-down, QDateEdit::drop-down {
                    border: none;
                    width: 24px;
                }
                QTableWidget {
                    background: #ffffff;
                    alternate-background-color: #f6f9fc;
                    gridline-color: #d7e0e8;
                    border: 1px solid #d7e0e8;
                    border-radius: 12px;
                    selection-background-color: #2a6db0;
                    selection-color: #ffffff;
                }
                QHeaderView::section {
                    background: #edf3f8;
                    color: #21405a;
                    border: none;
                    border-right: 1px solid #d7e0e8;
                    border-bottom: 1px solid #d7e0e8;
                    padding: 8px;
                    font-weight: 700;
                }
                QTabWidget::pane {
                    border: 1px solid #d7e0e8;
                    background: #ffffff;
                    border-radius: 14px;
                    top: -1px;
                }
                QTabBar::tab {
                    background: #eaf0f6;
                    color: #5f778d;
                    border: 1px solid #d7e0e8;
                    padding: 10px 16px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    margin-right: 4px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    color: #17384f;
                    border-bottom-color: #ffffff;
                }
                QTabBar::tab:hover {
                    color: #17384f;
                }
                #imagePreview {
                    border: 1px solid #d7e0e8;
                    background: #f8fbfe;
                    color: #647b90;
                    border-radius: 12px;
                }
                QLabel {
                    background: transparent;
                }
            """
        return """
            QMainWindow {
                background: #10161d;
                color: #e7edf3;
            }
            #contentShell {
                background: #10161d;
            }
            #headerCard {
                background: #16202a;
                border: 1px solid #273442;
                border-radius: 18px;
            }
            #windowTitle {
                color: #f3f7fb;
                font-size: 28px;
                font-weight: 700;
            }
            #homeHeroTitle {
                color: #f3f7fb;
                font-size: 32px;
                font-weight: 800;
            }
            #homeCompanyTitle {
                color: #8cc8ff;
                font-size: 18px;
                font-weight: 700;
            }
            #windowSubtitle {
                color: #99a8b8;
                font-size: 14px;
            }
            #screenCard {
                background: #16202a;
                border: 1px solid #273442;
                border-radius: 18px;
            }
            #screenTitle {
                color: #f3f7fb;
                font-size: 24px;
                font-weight: 700;
            }
            #screenText {
                color: #9aa9b8;
                font-size: 14px;
                line-height: 1.4em;
            }
            #badge {
                background: #183127;
                color: #7ee2a8;
                border-radius: 999px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            #summaryCard {
                background: #16202a;
                border: 1px solid #273442;
                border-radius: 14px;
            }
            #summaryValue {
                color: #f4f8fc;
                font-size: 26px;
                font-weight: 800;
            }
            #summaryTitle {
                color: #8da0b3;
                font-size: 12px;
                text-transform: uppercase;
            }
            QWidget {
                color: #e7edf3;
            }
            QFrame, QDialog, QGroupBox {
                background: #16202a;
            }
            QGroupBox {
                border: 1px solid #273442;
                border-radius: 14px;
                margin-top: 12px;
                font-weight: 700;
                color: #f2f6fa;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #9ed2ff;
            }
            QPushButton {
                background: #2a6db0;
                color: #ffffff;
                border: 1px solid #347dca;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #347dca;
            }
            QPushButton:pressed {
                background: #255d97;
            }
            QPushButton:disabled {
                background: #273442;
                color: #6f8091;
                border: 1px solid #2d3c4b;
            }
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QPlainTextEdit, QSpinBox {
                background: #0f161d;
                color: #f3f7fb;
                border: 1px solid #314150;
                border-radius: 10px;
                padding: 8px 10px;
                selection-background-color: #347dca;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
                border: 1px solid #5aa8f2;
            }
            QComboBox::drop-down, QDateEdit::drop-down {
                border: none;
                width: 24px;
            }
            QTableWidget {
                background: #10171e;
                alternate-background-color: #16202a;
                gridline-color: #273442;
                border: 1px solid #273442;
                border-radius: 12px;
                selection-background-color: #2a6db0;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background: #1c2834;
                color: #dce7f1;
                border: none;
                border-right: 1px solid #273442;
                border-bottom: 1px solid #273442;
                padding: 8px;
                font-weight: 700;
            }
            QTabWidget::pane {
                border: 1px solid #273442;
                background: #16202a;
                border-radius: 14px;
                top: -1px;
            }
            QTabBar::tab {
                background: #111922;
                color: #91a5b8;
                border: 1px solid #273442;
                padding: 10px 16px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #16202a;
                color: #ffffff;
                border-bottom-color: #16202a;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
            #imagePreview {
                border: 1px solid #314150;
                background: #0f161d;
                color: #9aa9b8;
                border-radius: 12px;
            }
            QLabel {
                background: transparent;
            }
        """
