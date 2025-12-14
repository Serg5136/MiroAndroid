from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MouseBinding:
    sequence: str
    handler: str


@dataclass(frozen=True)
class Hotkey:
    action: str
    sequences: Sequence[str]
    handler: str


MOUSE_BINDINGS: List[MouseBinding] = [
    MouseBinding("<Double-Button-1>", "on_canvas_double_click"),
    MouseBinding("<Button-1>", "on_canvas_click"),
    MouseBinding("<B1-Motion>", "on_mouse_drag"),
    MouseBinding("<ButtonRelease-1>", "on_mouse_release"),
    MouseBinding("<Motion>", "on_mouse_move"),
    MouseBinding("<ButtonPress-2>", "start_pan"),
    MouseBinding("<B2-Motion>", "do_pan"),
    MouseBinding("<Button-3>", "on_canvas_right_click"),
    MouseBinding("<Double-Button-3>", "on_canvas_right_double_click"),
    MouseBinding("<MouseWheel>", "on_mousewheel"),
    MouseBinding("<Button-4>", "on_mousewheel_linux"),
    MouseBinding("<Button-5>", "on_mousewheel_linux"),
]

HOTKEYS: List[Hotkey] = [
    Hotkey("delete_selection", ("<Delete>",), "delete_selected_cards"),
    Hotkey("undo", ("<Control-z>", "<Control-Z>"), "on_undo"),
    Hotkey("redo", ("<Control-y>", "<Control-Y>"), "on_redo"),
    Hotkey("copy", ("<Control-c>", "<Control-C>"), "on_copy"),
    Hotkey("paste", ("<Control-v>", "<Control-V>", "<<Paste>>"), "on_paste"),
    Hotkey("duplicate", ("<Control-d>", "<Control-D>"), "on_duplicate"),
    Hotkey(
        "toggle_connection_direction",
        ("<Control-Shift-d>", "<Control-Shift-D>"),
        "toggle_selected_connection_direction",
    ),
]


class EventBinder:
    """Registers keyboard and mouse bindings for the application."""

    def __init__(self, mouse_bindings: Iterable[MouseBinding] | None = None,
                 hotkeys: Iterable[Hotkey] | None = None) -> None:
        self.mouse_bindings = list(mouse_bindings or MOUSE_BINDINGS)
        self.hotkeys = list(hotkeys or HOTKEYS)

    def bind(self, app) -> None:
        canvas = app.canvas
        for binding in self.mouse_bindings:
            handler = getattr(app, binding.handler)
            canvas.bind(binding.sequence, handler)

        for hotkey in self.hotkeys:
            handler = getattr(app, hotkey.handler)
            for sequence in hotkey.sequences:
                app.root.bind_all(sequence, handler)

    def hotkey_table(self) -> List[Hotkey]:
        return list(self.hotkeys)
