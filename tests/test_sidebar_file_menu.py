import tkinter as tk

from src.sidebar import SidebarFactory


def _noop(*_, **__):
    return None


class DummyApp:
    def __init__(self, root: tk.Tk, collapsed: bool = False) -> None:
        self.root = root
        self.theme = {"minimap_bg": "#ffffff"}
        self.var_show_grid = tk.BooleanVar(value=True)
        self.var_snap_to_grid = tk.BooleanVar(value=True)
        self.var_grid_size = tk.IntVar(value=20)
        self.var_file_menu_collapsed = tk.BooleanVar(value=collapsed)

        # Callbacks used as command targets in SidebarFactory
        self.add_card_dialog = _noop
        self.change_color = _noop
        self.toggle_connect_mode = _noop
        self.edit_card_text_dialog = _noop
        self.delete_selected_cards = _noop
        self.add_frame_dialog = _noop
        self.toggle_selected_frame_collapse = _noop
        self.save_board = _noop
        self.load_board = _noop
        self.export_png = _noop
        self.attach_image_from_file = _noop
        self.toggle_theme = _noop
        self.on_toggle_show_grid = _noop
        self.on_toggle_snap_to_grid = _noop
        self.on_grid_size_change = _noop
        self.on_minimap_click = _noop

    def get_theme_button_text(self) -> str:
        return "Тёмная тема"


def _find_widget_by_text(root: tk.Misc, cls: type[tk.Misc], text: str):
    stack = [root]
    while stack:
        widget = stack.pop()
        if isinstance(widget, cls) and widget.cget("text") == text:
            return widget
        stack.extend(widget.winfo_children())
    raise LookupError(f"Widget with text '{text}' not found")


def test_file_menu_toggle_updates_visibility_and_state(tk_root):
    app = DummyApp(tk_root)
    SidebarFactory().create(app)

    collapse_button = _find_widget_by_text(app.root, tk.Button, "Свернуть «Файл» ▴")
    save_button = _find_widget_by_text(app.root, tk.Button, "Сохранить...")
    file_content = save_button.master

    assert collapse_button.aria_controls == "file_content"
    assert collapse_button.aria_expanded.get() is True
    assert app.var_file_menu_collapsed.get() is False
    assert file_content.winfo_ismapped() is True

    collapse_button.invoke()

    assert app.var_file_menu_collapsed.get() is True
    assert collapse_button.aria_expanded.get() is False
    assert collapse_button.cget("text") == "Показать «Файл» "
    assert file_content.winfo_ismapped() is False

    collapse_button.invoke()

    assert app.var_file_menu_collapsed.get() is False
    assert collapse_button.aria_expanded.get() is True
    assert collapse_button.cget("text") == "Свернуть «Файл» ▴"
    assert file_content.winfo_ismapped() is True


def test_file_menu_preserves_existing_collapse_var(tk_root):
    app = DummyApp(tk_root, collapsed=True)
    SidebarFactory().create(app)

    collapse_button = _find_widget_by_text(app.root, tk.Button, "Свернуть «Файл» ▴")

    assert app.var_file_menu_collapsed.get() is True

    collapse_button.invoke()

    assert app.var_file_menu_collapsed.get() is False
    assert collapse_button.cget("text") == "Свернуть «Файл» ▴"
    assert collapse_button.aria_expanded.get() is True
