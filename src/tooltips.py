import tkinter as tk


class Tooltip:
    def __init__(self, widget: tk.Misc, text: str, delay: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None

    def _schedule(self, event: tk.Event) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay, lambda: self._show(event))

    def _cancel(self) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self, event: tk.Event) -> None:
        self._cancel()
        if self._window:
            return
        x = event.x_root + 10
        y = event.y_root + 10
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=4,
            pady=2,
        )
        label.pack()

    def _hide(self, event: tk.Event | None = None) -> None:
        self._cancel()
        if self._window:
            self._window.destroy()
            self._window = None

    def _move(self, event: tk.Event) -> None:
        if self._window:
            x = event.x_root + 10
            y = event.y_root + 10
            self._window.wm_geometry(f"+{x}+{y}")

    def bind_to_widget(self) -> None:
        self.widget.bind("<Enter>", self._schedule, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<Motion>", self._move, add="+")

    def bind_to_tag(self, tag: str) -> None:
        if not hasattr(self.widget, "tag_bind"):
            return
        self.widget.tag_bind(tag, "<Enter>", self._schedule, add="+")
        self.widget.tag_bind(tag, "<Leave>", self._hide, add="+")
        self.widget.tag_bind(tag, "<Motion>", self._move, add="+")


def add_tooltip(widget: tk.Misc, text: str, delay: int = 500) -> Tooltip:
    tooltip = Tooltip(widget, text, delay=delay)
    tooltip.bind_to_widget()
    if not hasattr(widget, "_tooltips"):
        widget._tooltips = []  # type: ignore[attr-defined]
    widget._tooltips.append(tooltip)  # type: ignore[attr-defined]
    return tooltip


def add_canvas_tooltip(canvas: tk.Canvas, tag: str, text: str, delay: int = 500) -> Tooltip:
    tooltip = Tooltip(canvas, text, delay=delay)
    tooltip.bind_to_tag(tag)
    if not hasattr(canvas, "_tooltips"):
        canvas._tooltips = []  # type: ignore[attr-defined]
    canvas._tooltips.append(tooltip)  # type: ignore[attr-defined]
    return tooltip
