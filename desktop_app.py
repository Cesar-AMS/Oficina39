import os
import socket
import sys
import threading
import webbrowser
from contextlib import closing

from werkzeug.serving import make_server

from app import create_app


def _porta_livre(porta_preferida=5000):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if s.connect_ex(("127.0.0.1", porta_preferida)) != 0:
            return porta_preferida

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _ServidorThread(threading.Thread):
    def __init__(self, app, host, port):
        super().__init__(daemon=True)
        self._server = make_server(host, port, app)

    def run(self):
        self._server.serve_forever()

    def stop(self):
        self._server.shutdown()


def _abrir_no_navegador(app, host, porta, motivo=None):
    url = f"http://{host}:{porta}"
    if motivo:
        print(f"Modo navegador ativado: {motivo}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=porta, debug=False, use_reloader=False)


def _usar_webview():
    if os.environ.get("OFICINA39_USE_WEBVIEW") == "1":
        return True
    if getattr(sys, "frozen", False):
        return False
    return True


def main():
    app = create_app()
    host = "127.0.0.1"
    porta = _porta_livre(5000)

    if not _usar_webview():
        _abrir_no_navegador(app, host, porta, "executavel configurado para abrir no navegador")
        return

    try:
        import webview
    except Exception as exc:
        _abrir_no_navegador(app, host, porta, f"pywebview indisponivel ({exc})")
        return

    url = f"http://{host}:{porta}"
    servidor = _ServidorThread(app, host, porta)
    servidor.start()

    try:
        webview.create_window(
            "Oficina 39",
            url=url,
            width=1400,
            height=900,
            min_size=(1024, 700),
        )
        webview.start()
    except Exception as exc:
        servidor.stop()
        _abrir_no_navegador(app, host, porta, f"falha ao iniciar janela desktop ({exc})")
        return

    servidor.stop()


if __name__ == "__main__":
    main()
