"""アプリケーションのメインエントリポイント."""

import flet as ft

from .gui import main as gui_main


def app() -> None:
    """アプリケーションを起動する."""
    ft.app(target=gui_main)
