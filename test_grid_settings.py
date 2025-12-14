import tkinter as tk

import pytest

from src.canvas_view import CanvasView
from src.config import load_theme_settings, save_theme_settings, THEMES


def _grid_states(canvas: tk.Canvas) -> set[str]:
    return {canvas.itemcget(item, "state") for item in canvas.find_withtag("grid")}


def test_grid_visibility_toggle(tk_root):
    canvas = tk.Canvas(tk_root, width=200, height=200)
    view = CanvasView(canvas, None, THEMES["light"])

    view.draw_grid(20, visible=True)
    assert canvas.find_withtag("grid")
    assert _grid_states(canvas) == {"normal"}

    view.set_grid_visibility(False)
    assert _grid_states(canvas) == {"hidden"}

    view.set_grid_visibility(True)
    assert _grid_states(canvas) == {"normal"}


def test_grid_persistence_in_config(tmp_path):
    config_path = tmp_path / "config.json"
    colors = {name: theme["text"] for name, theme in THEMES.items()}

    save_theme_settings("dark", colors, show_grid=False, filename=config_path)
    loaded_theme, loaded_colors, show_grid = load_theme_settings(filename=config_path)

    assert loaded_theme == "dark"
    assert loaded_colors == colors
    assert show_grid is False


def test_grid_uses_theme_color(tk_root):
    canvas = tk.Canvas(tk_root, width=200, height=200)
    dark_theme = THEMES["dark"]
    view = CanvasView(canvas, None, dark_theme)

    view.draw_grid(10, visible=True)
    grid_items = canvas.find_withtag("grid")
    assert grid_items
    assert canvas.itemcget(grid_items[0], "fill") == dark_theme["grid"]
