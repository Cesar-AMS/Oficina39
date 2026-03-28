"""Compat shim for legacy desktop entrypoints.

Historically the project launched a webview-hosted Flask UI from this file.
During the desktop migration the real native entrypoint moved to ``desktop.main``.
We keep this module only so old shortcuts/scripts continue to work.
"""

from desktop.main import main


if __name__ == "__main__":
    raise SystemExit(main())
