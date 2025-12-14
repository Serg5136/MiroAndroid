from __future__ import annotations

from typing import TYPE_CHECKING
from tkinter import messagebox

if TYPE_CHECKING:
    from .main import BoardApp


class ConnectController:
    def __init__(self, app: "BoardApp") -> None:
        self.app = app

    def update_connect_mode_indicator(self) -> None:
        app = self.app
        if not hasattr(app, "btn_connect_mode"):
            return
        if app.connect_mode:
            active_bg = app.theme.get("frame_collapsed_bg", app.btn_connect_mode_default_bg)
            app.btn_connect_mode.config(
                relief="sunken",
                bg=active_bg,
                fg=app.theme.get("text", "black"),
                text=f"{app.btn_connect_mode_default_text} ✓",
            )
        else:
            app.btn_connect_mode.config(
                relief="raised",
                bg=app.btn_connect_mode_default_bg,
                text=app.btn_connect_mode_default_text,
            )

    def set_connect_mode(self, enabled: bool) -> None:
        app = self.app
        app.connect_mode = enabled
        if not enabled:
            app.connect_from_card_id = None
        self.update_connect_mode_indicator()

    def toggle_connect_mode(self) -> None:
        app = self.app
        if not app.connect_mode:
            self.set_connect_mode(True)
            messagebox.showinfo(
                "Режим соединения",
                "Кликните по первой карточке, затем по второй, чтобы соединить их.",
            )
        else:
            self.set_connect_mode(False)
