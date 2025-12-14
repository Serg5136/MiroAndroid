import json
import os
from typing import Dict

CONFIG_FILENAME = "_mini_miro_config.json"

THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "bg": "#ffffff",
        "grid": "#f0f0f0",
        "card_default": "#fff9b1",
        "card_outline": "#444444",
        "frame_bg": "#f5f5f5",
        "frame_outline": "#888888",
        "frame_collapsed_bg": "#e0e0ff",
        "frame_collapsed_outline": "#aaaaaa",
        "text": "#000000",
        "connection": "#555555",
        "connection_label": "#333333",
        "minimap_bg": "#ffffff",
        "minimap_card_outline": "#888888",
        "minimap_frame_outline": "#aaaaaa",
        "minimap_viewport": "#ff0000",
    },
    "dark": {
        "bg": "#222222",
        "grid": "#333333",
        "card_default": "#444444",
        "card_outline": "#dddddd",
        "frame_bg": "#333333",
        "frame_outline": "#aaaaaa",
        "frame_collapsed_bg": "#444466",
        "frame_collapsed_outline": "#cccccc",
        "text": "#ffffff",
        "connection": "#dddddd",
        "connection_label": "#eeeeee",
        "minimap_bg": "#222222",
        "minimap_card_outline": "#aaaaaa",
        "minimap_frame_outline": "#888888",
        "minimap_viewport": "#ff6666",
    },
}


def load_theme_settings(
    themes: Dict[str, Dict[str, str]] = THEMES, filename: str = CONFIG_FILENAME
) -> tuple[str, Dict[str, str], bool]:
    """Load theme name, text colors and grid visibility flag from config file."""

    theme_name = "light"
    text_colors = {name: data.get("text", "#000000") for name, data in themes.items()}
    show_grid = True

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            saved_theme = cfg.get("theme")
            if saved_theme in themes:
                theme_name = saved_theme

            saved_colors = cfg.get("text_colors", {})
            if isinstance(saved_colors, dict):
                for name, color in saved_colors.items():
                    if name in text_colors and isinstance(color, str):
                        text_colors[name] = color
            saved_show_grid = cfg.get("show_grid")
            if isinstance(saved_show_grid, bool):
                show_grid = saved_show_grid
        except Exception:
            pass
    return theme_name, text_colors, show_grid


def save_theme_settings(
    theme_name: str,
    text_colors: Dict[str, str],
    show_grid: bool = True,
    filename: str = CONFIG_FILENAME,
) -> None:
    """Persist the selected theme name and text colors to config file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {"theme": theme_name, "text_colors": text_colors, "show_grid": show_grid},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        pass
