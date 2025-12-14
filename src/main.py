import tkinter as tk
import base64
import binascii
import math
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import copy
import io
from pathlib import Path
from typing import Dict, List
from .autosave import AutoSaveService
from .board_model import (
    Attachment,
    BoardData,
    Card as ModelCard,
    Connection as ModelConnection,
    DEFAULT_CONNECTION_RADIUS,
    DEFAULT_CONNECTION_CURVATURE,
    DEFAULT_CONNECTION_STYLE,
    DEFAULT_CONNECTION_DIRECTION,
    Frame as ModelFrame,
    bulk_update_card_colors,
)
from .canvas_view import CanvasView
from .config import THEMES, load_theme_settings, save_theme_settings
from .connect_controller import ConnectController
from .drag_controller import DragController
from . import files as file_io
from .history import History
from .layout import LayoutBuilder
from .selection_controller import SelectionController

class BoardApp:
    def __init__(self):
        self.max_attachment_bytes = 5 * 1024 * 1024
        self.root = tk.Tk()
        self.root.title("Mini Miro Board (Python)")
        self.root.geometry("1200x800")

        # Темы
        self.theme_name, self.text_colors, self.show_grid = load_theme_settings(THEMES)
        self.theme = self._build_theme()

        # Данные борда
        self.cards: Dict[int, ModelCard] = {}
        self.connections: List[ModelConnection] = []
        self.next_card_id = 1

        # Группы / рамки
        self.frames: Dict[int, ModelFrame] = {}
        self.next_frame_id = 1
        self.selected_frame_id = None
        self.min_frame_width = 150
        self.min_frame_height = 120

        # Выделение карточек
        self.selected_card_id = None
        self.selected_cards = set()
        self.selected_connection: ModelConnection | None = None

        # Прямоугольник выделения (lasso)
        self.selection_rect_id = None
        self.selection_start = None  # (x, y) в координатах canvas

        # Перетаскивание / перемещение / resize / connect-drag
        self.drag_data = {
            "dragging": False,
            "dragged_cards": set(),
            "last_x": 0,
            "last_y": 0,
            "moved": False,
            "mode": None,            # "cards", "frame", "resize_card", "resize_frame", "connect_drag", "connection_endpoint", "connection_radius", "connection_curvature"
            "frame_id": None,
            "resize_card_id": None,
            "resize_origin": None,   # (x1, y1) левый верх при ресайзе
            "resize_frame_id": None,
            "resize_frame_handle": None,
            "resize_frame_anchor": None,
            "resize_attachment": None,
            "connect_from_card": None,
            "connect_from_anchor": None,
            "connect_start": None,   # (sx, sy)
            "temp_line_id": None,
            "connection_edit": None,
        }

        # Hover
        self.hover_card_id = None
        self.hover_connection: ModelConnection | None = None
        self.connection_handle_map: Dict[int, ModelConnection] = {}

        # Режим соединения (кнопкой)
        self.connect_mode = False
        self.connect_from_card_id = None

        # Контроллеры поведения
        self.selection_controller = SelectionController(self)
        self.connect_controller = ConnectController(self)
        self.drag_controller = DragController(self)

        # Зум
        self.zoom_factor = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 2.5

        # Сетка
        self.grid_size = 20
        self.snap_to_grid = True
        self.var_show_grid = tk.BooleanVar(value=self.show_grid)
        # Привязка к сетке — переменные для UI
        self.var_snap_to_grid = tk.BooleanVar(value=self.snap_to_grid)
        self.var_grid_size = tk.IntVar(value=self.grid_size)
        self.var_card_width = tk.IntVar(value=180)
        self.var_card_height = tk.IntVar(value=100)
        self.var_connection_style = tk.StringVar(value=DEFAULT_CONNECTION_STYLE)
        self.var_connection_radius = tk.DoubleVar(value=DEFAULT_CONNECTION_RADIUS)

        # История (Undo/Redo) и автосохранение
        self.history = History()
        self.saved_history_index = -1
        self.unsaved_changes = False
        self.autosave_service = AutoSaveService()

        # Буфер обмена (копирование карточек)
        self.clipboard = None  # {"cards":[...], "connections":[...], "center":(x,y)}

        # Вложения
        self.attachments_dir = Path("attachments")
        self.attachment_items: Dict[tuple[int, int], int] = {}
        self.attachment_tk_images: Dict[tuple[int, int], tk.PhotoImage] = {}
        self.selected_attachment: tuple[int, int] | None = None
        self.attachment_selection_box_id: int | None = None
        self.attachment_resize_handles: Dict[str, int | None] = {}
        self.attachment_fit_mode: str = "contain"
        self.attachment_min_aspect_ratio = 0.5
        self.attachment_max_aspect_ratio = 2.0

        # Inline-редактор текста карточек
        self.inline_editor = None
        self.inline_editor_window_id = None
        self.inline_editor_card_id = None

        # Контекстные меню
        self.context_card_id = None
        self.context_frame_id = None
        self.context_connection = None
        self.context_click_x = 0
        self.context_click_y = 0

        # Мини-карта
        self.minimap = None

        # UI helpers
        self.ui_builder = LayoutBuilder()

        self._build_ui()
        self.canvas_view = CanvasView(self.canvas, self.minimap, self.theme)
        self._setup_dnd()
        self.init_board_state()
        self.update_controls_state()

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_theme(self):
        base_theme = THEMES.get(self.theme_name, THEMES["light"])
        text_color = self.text_colors.get(self.theme_name, base_theme.get("text", "#000000"))
        return {**base_theme, "text": text_color}

    def _apply_theme(self):
        self.theme = self._build_theme()
        if hasattr(self, "canvas_view"):
            self.canvas_view.set_theme(self.theme)
        if hasattr(self, "canvas"):
            self.canvas.config(bg=self.theme["bg"])
        if hasattr(self, "minimap") and self.minimap:
            self.minimap.config(bg=self.theme["minimap_bg"])

    def get_theme_button_text(self):
        return "Тёмная тема" if self.theme_name == "light" else "Светлая тема"

    def _redraw_with_current_theme(self):
        state = self.get_board_data()
        self.set_board_from_data(state)
        if hasattr(self, "btn_theme"):
            self.btn_theme.config(text=self.get_theme_button_text())
        self.update_minimap()
        self.update_connect_mode_indicator()

    def _build_ui(self):
        self.ui_builder.build(self)
        self._build_context_menus()

    def _build_context_menus(self):
        # Меню карточки
        self.card_menu = tk.Menu(self.root, tearoff=0)
        self.card_menu.add_command(
            label="Редактировать текст",
            command=self._context_edit_card_text,
        )
        self.card_menu.add_command(
            label="Изменить цвет...",
            command=self._context_change_card_color,
        )
        self.card_menu.add_separator()
        self.card_menu.add_command(
            label="Выровнять по левому краю",
            command=self.align_selected_cards_left,
        )
        self.card_menu.add_command(
            label="Выровнять по верхнему краю",
            command=self.align_selected_cards_top,
        )
        self.card_menu.add_command(
            label="Одинаковая ширина",
            command=self.equalize_selected_cards_width,
        )
        self.card_menu.add_command(
            label="Одинаковая высота",
            command=self.equalize_selected_cards_height,
        )
        self.card_menu.add_separator()
        self.card_menu.add_command(
            label="Удалить",
            command=self._context_delete_cards,
        )
    
        # Меню рамки
        self.frame_menu = tk.Menu(self.root, tearoff=0)
        self.frame_menu.add_command(
            label="Переименовать",
            command=self._context_rename_frame,
        )
        self.frame_menu.add_command(
            label="Свернуть/развернуть",
            command=self._context_toggle_frame,
        )
        self.frame_menu.add_separator()
        self.frame_menu.add_command(
            label="Удалить рамку",
            command=self._context_delete_frame,
        )
    
        # Меню связи
        self.connection_menu = tk.Menu(self.root, tearoff=0)
        connection_style_menu = tk.Menu(self.connection_menu, tearoff=0)
        connection_style_menu.add_radiobutton(
            label="Прямая",
            variable=self.var_connection_style,
            value="straight",
            command=lambda: self._context_set_connection_style("straight"),
        )
        connection_style_menu.add_radiobutton(
            label="Ломаная",
            variable=self.var_connection_style,
            value="elbow",
            command=lambda: self._context_set_connection_style("elbow"),
        )
        connection_style_menu.add_radiobutton(
            label="Закруглённая",
            variable=self.var_connection_style,
            value="rounded",
            command=lambda: self._context_set_connection_style("rounded"),
        )
        connection_style_menu.add_separator()
        connection_style_menu.add_command(
            label="Радиус закругления…",
            command=self._context_set_connection_radius,
        )
        connection_style_menu.add_command(
            label="Кривизна…",
            command=self._context_set_connection_curvature,
        )
        connection_style_menu.add_command(
            label="Сбросить радиус и кривизну",
            command=self._context_reset_connection_rounding,
        )
        self.connection_menu.add_cascade(
            label="Тип линии", menu=connection_style_menu
        )
        self.connection_menu.add_command(
            label="Редактировать подпись",
            command=self._context_edit_connection_label,
        )
        self.connection_menu.add_command(
            label="Поменять направление",
            command=self._context_toggle_connection_direction,
        )
        self.connection_menu.add_command(
            label="Удалить связь",
            command=self._context_delete_connection,
        )
    
        # Меню пустого места
        self.canvas_menu = tk.Menu(self.root, tearoff=0)
        self.canvas_menu.add_command(
            label="Новая карточка здесь",
            command=self._context_add_card_here,
        )
        self.canvas_menu.add_separator()
        self.canvas_menu.add_command(
            label="Вставить",
            command=self.on_paste,
        )

    def _setup_dnd(self) -> None:
        """Подключает обработчик drag-and-drop файлов, если поддерживается tkdnd."""

        drop_target_register = getattr(self.canvas, "drop_target_register", None)
        dnd_bind = getattr(self.canvas, "dnd_bind", None)
        if not drop_target_register or not dnd_bind:
            return
        try:
            drop_target_register("DND_Files")
            dnd_bind("<<Drop>>", self.on_drop_files)
        except tk.TclError:
            # tkdnd не установлен — тихо пропускаем
            return
    
    def on_canvas_right_click(self, event):
        """
        Показывает контекстное меню в зависимости от того, что под курсором.
        """
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        self.context_click_x = cx
        self.context_click_y = cy
    
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        # Сбрасываем контекст
        self.context_card_id = None
        self.context_frame_id = None
        self.context_connection = None
    
        if item_id:
            conn = self.get_connection_from_item(item_id)
            if conn is not None:
                self.context_connection = conn
                self.select_connection(conn)
                self.connection_menu.tk_popup(event.x_root, event.y_root)
                return
    
            card_id = self.get_card_id_from_item((item_id,))
            if card_id is not None:
                self.context_card_id = card_id
                if card_id not in self.selected_cards:
                    self.select_card(card_id, additive=False)
                self.card_menu.tk_popup(event.x_root, event.y_root)
                return
    
            frame_id = self.get_frame_id_from_item((item_id,))
            if frame_id is not None:
                self.context_frame_id = frame_id
                self.select_frame(frame_id)
                self.frame_menu.tk_popup(event.x_root, event.y_root)
                return
    
        # Пустое место
        self.canvas_menu.tk_popup(event.x_root, event.y_root)
    
    # --- Действия контекстного меню ---
    
    def on_canvas_right_double_click(self, event):
        """
        Двойной щелчок правой кнопкой мыши по карточке —
        создаёт её копию немного смещённой.
        """
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        card_id = self.get_card_id_from_item(item)
        if card_id is None:
            return
    
        card = self.cards.get(card_id)
        if not card:
            return
    
        # Смещаем копию относительно исходной карточки
        offset = 30
        new_x = card.x + offset
        new_y = card.y + offset
    
        new_card_id = self.create_card(new_x, new_y, card.text, color=card.color)
        # Выделим новую карточку
        self.select_card(new_card_id, additive=False)
        self.push_history()


    def _context_edit_card_text(self):
        if self.context_card_id is None:
            return
        self.start_inline_edit_card(self.context_card_id)
    
    def _context_change_card_color(self):
        if self.context_card_id is None:
            return
        if self.context_card_id not in self.selected_cards:
            self.select_card(self.context_card_id, additive=False)
        self.change_color()
    
    def _context_delete_cards(self):
        if self.context_card_id is not None:
            if self.context_card_id not in self.selected_cards:
                self.select_card(self.context_card_id, additive=False)
        self.delete_selected_cards()
    
    def _context_rename_frame(self):
        if self.context_frame_id is None or self.context_frame_id not in self.frames:
            return
        frame = self.frames[self.context_frame_id]
        new_title = simpledialog.askstring(
            "Название рамки",
            "Заголовок:",
            initialvalue=frame.title,
            parent=self.root,
        )
        if new_title is None:
            return
        frame.title = new_title
        self.canvas.itemconfig(frame.title_id, text=new_title)
        self.push_history()
    
    def _context_toggle_frame(self):
        if self.context_frame_id is None:
            return
        self.selected_frame_id = self.context_frame_id
        self.toggle_selected_frame_collapse()
    
    def _context_delete_frame(self):
        frame_id = self.context_frame_id
        if frame_id is None or frame_id not in self.frames:
            return
        self.hide_frame_handles(frame_id)
        frame = self.frames.pop(frame_id)
        self.canvas.delete(frame.rect_id)
        self.canvas.delete(frame.title_id)
        if self.selected_frame_id == frame_id:
            self.selected_frame_id = None
        self.push_history()
    
    def _context_edit_connection_label(self):
        conn = self.context_connection
        if not conn:
            return
        current_label = conn.label
        new_label = simpledialog.askstring(
            "Подпись связи",
            "Текст связи:",
            initialvalue=current_label,
            parent=self.root,
        )
        if new_label is None:
            return
        conn.label = new_label.strip()
        if conn.label_id:
            if conn.label:
                self.canvas.itemconfig(
                    conn.label_id,
                    text=conn.label,
                    state="normal",
                    fill=self.theme["connection_label"],
                )
            else:
                self.canvas.delete(conn.label_id)
                conn.label_id = None
        elif conn.label:
            coords = self.canvas.coords(conn.line_id)
            if len(coords) >= 4:
                x1, y1, x2, y2 = coords[:4]
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
            else:
                mx, my = self.context_click_x, self.context_click_y
            label_id = self.canvas.create_text(
                mx,
                my,
                text=conn.label,
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",),
            )
            conn.label_id = label_id

        self.push_history()

    def _context_set_connection_style(self, style: str) -> None:
        conn = self.context_connection
        if not conn:
            return
        conn.style = style
        self.var_connection_style.set(style)
        self.canvas_view.update_connection_positions([conn], self.cards)
        self.show_connection_handles(conn)
        self.push_history()

    def _context_set_connection_radius(self) -> None:
        conn = self.context_connection
        if not conn:
            return
        from_card = self.cards.get(conn.from_id)
        to_card = self.cards.get(conn.to_id)
        if not from_card or not to_card:
            return
        _, render_info = self.canvas_view.connection_geometry(conn, from_card, to_card)
        length = render_info.get(
            "length", math.hypot(to_card.x - from_card.x, to_card.y - from_card.y)
        )
        current = getattr(conn, "radius", DEFAULT_CONNECTION_RADIUS)
        new_radius = simpledialog.askfloat(
            "Радиус закругления",
            "Задайте радиус (в пикселях).",
            initialvalue=current,
            minvalue=0.0,
            parent=self.root,
        )
        if new_radius is None:
            return
        max_radius = max(0.0, (length or 1.0) * 0.6)
        conn.style = "rounded"
        conn.radius = max(0.0, min(float(new_radius), max_radius))
        self.var_connection_style.set(conn.style)
        self.var_connection_radius.set(conn.radius)
        self.canvas_view.update_connection_positions([conn], self.cards)
        self.show_connection_handles(conn)
        self.push_history()

    def _context_set_connection_curvature(self) -> None:
        conn = self.context_connection
        if not conn:
            return
        from_card = self.cards.get(conn.from_id)
        to_card = self.cards.get(conn.to_id)
        if not from_card or not to_card:
            return
        _, render_info = self.canvas_view.connection_geometry(conn, from_card, to_card)
        length = render_info.get(
            "length", math.hypot(to_card.x - from_card.x, to_card.y - from_card.y)
        )
        current = getattr(conn, "curvature", DEFAULT_CONNECTION_CURVATURE)
        new_curvature = simpledialog.askfloat(
            "Кривизна",
            "Смещение дуги (может быть отрицательным, px):",
            initialvalue=current,
            parent=self.root,
        )
        if new_curvature is None:
            return
        limit = max(1.0, length) / 2
        conn.style = "rounded"
        conn.curvature = max(-limit, min(float(new_curvature), limit))
        self.var_connection_style.set(conn.style)
        self.canvas_view.update_connection_positions([conn], self.cards)
        self.show_connection_handles(conn)
        self.push_history()

    def _context_reset_connection_rounding(self) -> None:
        conn = self.context_connection
        if not conn:
            return
        conn.style = "rounded"
        conn.radius = DEFAULT_CONNECTION_RADIUS
        conn.curvature = DEFAULT_CONNECTION_CURVATURE
        self.var_connection_style.set(conn.style)
        self.var_connection_radius.set(conn.radius)
        self.canvas_view.update_connection_positions([conn], self.cards)
        self.show_connection_handles(conn)
        self.push_history()

    def _context_delete_connection(self):
        conn = self.context_connection
        if not conn:
            return
        self._delete_connection(conn)
        self.push_history()

    def _delete_connection(self, connection: ModelConnection) -> None:
        self.hide_connection_handles(connection)
        self.canvas.delete(connection.line_id)
        if connection.label_id:
            self.canvas.delete(connection.label_id)
        try:
            self.connections.remove(connection)
        except ValueError:
            pass
        if connection is self.selected_connection:
            self.selected_connection = None
        if connection is self.context_connection:
            self.context_connection = None
        if connection is self.hover_connection:
            self.hover_connection = None
        self.render_selection()
        self.update_controls_state()
    
    def _context_add_card_here(self):
        text_value = simpledialog.askstring(
            "Новая карточка",
            "Введите текст карточки:",
            parent=self.root,
        )
        if text_value is None or text_value.strip() == "":
            return
        self.create_card(self.context_click_x, self.context_click_y, text_value.strip(), color=None)
        self.push_history()

    # ---------- Инициализация борда, история, автосейв ----------

    def init_board_state(self):
        """Запускается один раз при старте приложения."""
        restored = False

        # Попытка восстановиться из автосейва
        if self.autosave_service.exists():
            res = messagebox.askyesnocancel(
                "Автовосстановление",
                "Найден файл автосохранения.\n"
                "Восстановить последний сеанс?",
            )
            if res:  # Да
                try:
                    data = self.autosave_service.load()
                    self.set_board_from_data(data)
                    self.history.clear_and_init(self.get_board_data())
                    self.saved_history_index = -1
                    self.push_history()
                    restored = True
                except Exception as e:
                    messagebox.showerror("Ошибка автозагрузки", str(e))
                    restored = False
            elif res is None:
                restored = False
            else:
                restored = False

        if not restored:
            self.canvas.delete("all")
            self.cards.clear()
            self.connections.clear()
            self.frames.clear()
            self.selected_card_id = None
            self.selected_cards.clear()
            self.selected_frame_id = None
            self.selected_connection = None
            self.set_connect_mode(False)
            self.zoom_factor = 1.0
            self.canvas.config(scrollregion=(0, 0, 4000, 4000),
                               bg=self.theme["bg"])
            self.next_card_id = 1
            self.next_frame_id = 1

            self.history.clear_and_init(self.get_board_data())
            self.draw_grid()
            self.push_history()
            self.saved_history_index = self.history.index

        self.update_unsaved_flag()
        self.update_minimap()

    def get_board_data(self):
        """
        Собирает текущее состояние доски в BoardData
        и возвращает примитивный dict (готовый к JSON-сериализации).
        """
        cards: Dict[int, ModelCard] = {}
        for card_id, card in self.cards.items():
            cards[card_id] = ModelCard(
                id=card_id,
                x=card.x,
                y=card.y,
                width=card.width,
                height=card.height,
                text=card.text,
                color=card.color,
                attachments=[self._prepare_attachment_for_save(a) for a in card.attachments],
            )

        connections: List[ModelConnection] = []
        for conn in self.connections:
            connections.append(
                ModelConnection(
                    from_id=conn.from_id,
                    to_id=conn.to_id,
                    label=conn.label,
                    direction=conn.direction,
                    from_anchor=conn.from_anchor,
                    to_anchor=conn.to_anchor,
                )
            )

        frames: Dict[int, ModelFrame] = {}
        for frame_id, frame in self.frames.items():
            x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
            frames[frame_id] = ModelFrame(
                id=frame_id,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                title=frame.title,
                collapsed=frame.collapsed,
            )

        board = BoardData(cards=cards, connections=connections, frames=frames)
        return board.to_primitive()

    def set_board_from_data(self, data):
        """
        Принимает dict (как из JSON), конвертирует в BoardData
        и пересоздаёт объекты на холсте.
        """
        self.canvas.delete("all")
        self.cards.clear()
        self.connections.clear()
        self.frames.clear()
        self._clear_all_attachment_previews()
        self.selected_card_id = None
        self.selected_cards.clear()
        self.selected_frame_id = None
        self.selected_connection = None
        self.set_connect_mode(False)
        self.zoom_factor = 1.0
        self.canvas.config(scrollregion=(0, 0, 4000, 4000), bg=self.theme["bg"])

        # --- новая часть: используем модель BoardData ---
        board = BoardData.from_primitive(data)
        self._restore_attachment_files(board)
        self.cards = board.cards
        self.connections = board.connections
        self.frames = board.frames

        self.next_card_id = max(self.cards.keys(), default=0) + 1
        self.next_frame_id = max(self.frames.keys(), default=0) + 1

        self.render_board()
        self.update_controls_state()


    def push_history(self):
        state = self.get_board_data()
        self.history.push(state)
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def on_undo(self, event=None):
        state = self.history.undo(self)
        if state is None:
            return
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def on_redo(self, event=None):
        state = self.history.redo(self)
        if state is None:
            return
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()
        self.update_controls_state()

    def update_unsaved_flag(self):
        self.unsaved_changes = (self.history.index != self.saved_history_index)
        title = "Mini Miro Board (Python)"
        if self.unsaved_changes:
            title += " *"
        self.root.title(title)

    def write_autosave(self, state=None):
        try:
            data = state if state is not None else self.get_board_data()
            self.autosave_service.save(data)
        except Exception:
            pass

    # ---------- Сетка ----------

    def draw_grid(self):
        self.canvas_view.draw_grid(self.grid_size, visible=self.show_grid)

    def render_board(self):
        self.canvas_view.render_board(
            self.cards, self.frames, self.connections, self.grid_size, self.show_grid
        )
        self._clear_all_attachment_previews()
        self.render_all_attachments()

    def render_selection(self):
        self.canvas_view.render_selection(
            self.cards,
            self.frames,
            self.selected_cards,
            self.selected_frame_id,
            self.connections,
            self.selected_connection,
        )
        if self.selected_connection:
            self.show_connection_handles(self.selected_connection)
        else:
            self.hide_connection_handles()

    def clear_connection_selection(self) -> None:
        if self.selected_connection is None:
            return
        self.hide_connection_handles(self.selected_connection)
        self.selected_connection = None
        self.context_connection = None
        self.render_selection()
        self.update_controls_state()

    def select_connection(self, connection: ModelConnection | None) -> None:
        if connection is None:
            self.clear_connection_selection()
            return

        self.selection_controller.select_frame(None)
        self.selection_controller.select_card(None, additive=False)
        self.selected_connection = connection
        self.context_connection = connection
        self.render_selection()
        self._sync_connection_controls_with_selection()
        self.update_controls_state()

    def _register_connection_handle(self, connection: ModelConnection, handle_id: int) -> None:
        self.connection_handle_map[handle_id] = connection

    def hide_connection_handles(self, connection: ModelConnection | None = None) -> None:
        targets = [connection] if connection else list(self.connections)
        for conn in targets:
            for hid_attr in ("start_handle_id", "end_handle_id", "radius_handle_id", "curvature_handle_id"):
                hid = getattr(conn, hid_attr, None)
                if hid:
                    self.canvas.delete(hid)
                    self.connection_handle_map.pop(hid, None)
                setattr(conn, hid_attr, None)

    def show_connection_handles(self, connection: ModelConnection) -> None:
        from_card = self.cards.get(connection.from_id)
        to_card = self.cards.get(connection.to_id)
        if from_card is None or to_card is None:
            return

        self.hide_connection_handles()

        positions = self.canvas_view.connection_handle_positions(connection, from_card, to_card)
        r = 6
        start_id = self.canvas.create_oval(
            positions["start"][0] - r,
            positions["start"][1] - r,
            positions["start"][0] + r,
            positions["start"][1] + r,
            fill=self.theme["connection"],
            outline=self.theme.get("bg", "white"),
            width=2,
            tags=("connection_handle", "connection_handle_start"),
        )
        end_id = self.canvas.create_oval(
            positions["end"][0] - r,
            positions["end"][1] - r,
            positions["end"][0] + r,
            positions["end"][1] + r,
            fill=self.theme["connection"],
            outline=self.theme.get("bg", "white"),
            width=2,
            tags=("connection_handle", "connection_handle_end"),
        )

        ctrl_size = 6
        radius_id = self.canvas.create_rectangle(
            positions["radius"][0] - ctrl_size,
            positions["radius"][1] - ctrl_size,
            positions["radius"][0] + ctrl_size,
            positions["radius"][1] + ctrl_size,
            fill=self.theme["connection"],
            outline=self.theme.get("connection_label", "#333"),
            width=1,
            tags=("connection_handle", "connection_handle_radius"),
        )
        curvature_id = self.canvas.create_rectangle(
            positions["curvature"][0] - ctrl_size,
            positions["curvature"][1] - ctrl_size,
            positions["curvature"][0] + ctrl_size,
            positions["curvature"][1] + ctrl_size,
            fill=self.theme.get("frame_outline", self.theme["connection"]),
            outline=self.theme.get("connection_label", "#333"),
            width=1,
            tags=("connection_handle", "connection_handle_curvature"),
        )

        connection.start_handle_id = start_id
        connection.end_handle_id = end_id
        connection.radius_handle_id = radius_id
        connection.curvature_handle_id = curvature_id

        for hid in (start_id, end_id, radius_id, curvature_id):
            self._register_connection_handle(connection, hid)

        self.canvas.tag_raise(start_id)
        self.canvas.tag_raise(end_id)
        self.canvas.tag_raise(radius_id)
        self.canvas.tag_raise(curvature_id)

    def clear_attachment_selection(self) -> None:
        if self.attachment_selection_box_id:
            self.canvas.delete(self.attachment_selection_box_id)
        self.attachment_selection_box_id = None
        for hid in self.attachment_resize_handles.values():
            if hid:
                self.canvas.delete(hid)
        self.attachment_resize_handles.clear()
        self.selected_attachment = None

    def update_controls_state(self):
        has_card_selection = bool(self.selected_cards)
        has_frame_selection = self.selected_frame_id is not None
        has_connection_selection = self.selected_connection is not None

        if hasattr(self, "btn_change_color"):
            self.btn_change_color.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_edit_text"):
            self.btn_edit_text.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_delete_cards"):
            self.btn_delete_cards.config(state="normal" if has_card_selection else "disabled")
        if hasattr(self, "btn_toggle_frame"):
            self.btn_toggle_frame.config(state="normal" if has_frame_selection else "disabled")

        if hasattr(self, "connection_style_controls"):
            state = "normal" if has_connection_selection else "disabled"
            for control in self.connection_style_controls:
                control.config(state=state)
        if hasattr(self, "connection_radius_scale"):
            state = "normal" if has_connection_selection else "disabled"
            self.connection_radius_scale.config(state=state)

        if hasattr(self, "btn_undo_toolbar"):
            self.btn_undo_toolbar.config(
                state="normal" if self.history and self.history.can_undo() else "disabled"
            )
        if hasattr(self, "btn_redo_toolbar"):
            self.btn_redo_toolbar.config(
                state="normal" if self.history and self.history.can_redo() else "disabled"
            )

        self._sync_size_controls_with_selection()
        self._sync_connection_controls_with_selection()

    def _sync_size_controls_with_selection(self) -> None:
        if not hasattr(self, "var_card_width") or not hasattr(self, "var_card_height"):
            return
        card_id = self.selected_card_id if self.selected_card_id in self.cards else next(
            (cid for cid in self.selected_cards if cid in self.cards),
            None,
        )
        if card_id is None:
            return

        card = self.cards.get(card_id)
        if not card:
            return

        self.var_card_width.set(int(card.width))
        self.var_card_height.set(int(card.height))

    def _sync_connection_controls_with_selection(self) -> None:
        if not hasattr(self, "var_connection_style"):
            return
        if self.selected_connection is None:
            self.var_connection_style.set(DEFAULT_CONNECTION_STYLE)
            self.var_connection_radius.set(DEFAULT_CONNECTION_RADIUS)
            return

        self.var_connection_style.set(getattr(self.selected_connection, "style", DEFAULT_CONNECTION_STYLE))
        self.var_connection_radius.set(getattr(self.selected_connection, "radius", DEFAULT_CONNECTION_RADIUS))

    def update_connect_mode_indicator(self):
        self.connect_controller.update_connect_mode_indicator()

    def set_connect_mode(self, enabled: bool):
        self.connect_controller.set_connect_mode(enabled)

    def on_connection_style_change(self, *_):
        if not self.selected_connection:
            return

        new_style = self.var_connection_style.get()
        self.selected_connection.style = new_style
        self.canvas_view.update_connection_positions([self.selected_connection], self.cards)
        self.show_connection_handles(self.selected_connection)
        self.push_history()

    def on_connection_radius_change(self, value: str):
        if not self.selected_connection:
            return

        try:
            new_radius = float(value)
        except (TypeError, ValueError):
            return

        self.selected_connection.radius = max(0.0, new_radius)
        self.canvas_view.update_connection_positions([self.selected_connection], self.cards)
        self.show_connection_handles(self.selected_connection)
        self.push_history()

    # ---------- Вложения ----------

    def _ensure_attachments_dir(self) -> None:
        try:
            self.attachments_dir.mkdir(exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Вложения", f"Не удалось создать папку вложений:\n{exc}")
            raise

    def _clear_all_attachment_previews(self) -> None:
        for item_id in self.attachment_items.values():
            self.canvas.delete(item_id)
        self.attachment_items.clear()
        self.attachment_tk_images.clear()
        self.clear_attachment_selection()

    def _resolve_attachment_path(self, storage_path: str | None) -> Path | None:
        if not storage_path:
            return None
        path = Path(storage_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    def _clear_attachment_previews_for_card(self, card_id: int) -> None:
        card = self.cards.get(card_id)
        if card and card.image_id:
            self.canvas.delete(card.image_id)
            card.image_id = None
        to_delete = [key for key in self.attachment_items if key[0] == card_id]
        for key in to_delete:
            item_id = self.attachment_items.pop(key, None)
            if item_id:
                self.canvas.delete(item_id)
            self.attachment_tk_images.pop(key, None)
        if self.selected_attachment and self.selected_attachment[0] == card_id:
            self.clear_attachment_selection()

    def _load_attachment_image(self, attachment: Attachment):
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                "Вложения",
                "Для работы с изображениями нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return None

        path = self._resolve_attachment_path(attachment.storage_path)
        if path and path.exists():
            try:
                return Image.open(path)
            except OSError:
                return None

        if attachment.data_base64:
            try:
                raw = base64.b64decode(attachment.data_base64)
            except (binascii.Error, ValueError):
                return None
            try:
                return Image.open(io.BytesIO(raw))
            except OSError:
                return None

        return None

    def _read_attachment_base64(self, attachment: Attachment) -> str | None:
        path = self._resolve_attachment_path(attachment.storage_path)
        if not path or not path.exists():
            return None
        try:
            payload = path.read_bytes()
        except OSError:
            return None
        return base64.b64encode(payload).decode("ascii")

    def _attach_image_to_card(
        self,
        card: ModelCard,
        image,
        *,
        name: str,
        mime_type: str,
        source_type: str,
        storage_ext: str,
        embed_base64: bool,
    ) -> bool:
        attachment = self._store_attachment_image(
            card,
            image,
            name=name,
            mime_type=mime_type,
            source_type=source_type,
            storage_ext=storage_ext,
            embed_base64=embed_base64,
        )
        if attachment is None:
            messagebox.showerror(
                "Вложения",
                "Не удалось сохранить изображение или его размер превышает допустимый предел (5 МБ)",
            )
            return False

        layout = self.canvas_view.compute_card_layout(card)
        self._auto_position_attachment(card, attachment, layout)
        card.attachments.append(attachment)
        self.render_card_attachments(card.id)
        self.push_history()
        return True

    def _open_image_from_path(self, source_path: Path, *, dialog_title: str):
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                dialog_title,
                "Для добавления изображений нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return None

        try:
            if source_path.stat().st_size > self.max_attachment_bytes:
                messagebox.showerror(
                    dialog_title,
                    "Размер вложения превышает допустимый предел (5 МБ).",
                )
                return None
        except OSError:
            return None

        try:
            image = Image.open(source_path)
            image.load()
        except OSError as exc:
            messagebox.showerror(
                dialog_title,
                f"Не удалось открыть изображение:\n{exc}",
            )
            return None

        mime_type = Image.MIME.get(image.format, "image/png")
        if not mime_type.startswith("image/"):
            messagebox.showerror(
                dialog_title,
                "Формат изображения не поддерживается. Попробуйте PNG, JPEG, GIF или WebP.",
            )
            return None

        storage_ext = source_path.suffix or ".png"
        return image, mime_type, storage_ext

    def _store_attachment_image(
        self,
        card: ModelCard,
        image,
        *,
        name: str,
        mime_type: str,
        source_type: str,
        storage_ext: str,
        embed_base64: bool,
    ) -> Attachment | None:
        try:
            self._ensure_attachments_dir()
        except OSError:
            return None

        attachment_id = max((a.id for a in card.attachments), default=0) + 1
        if not storage_ext:
            storage_ext = self._extension_from_mime(mime_type)
        storage_ext = storage_ext if storage_ext.startswith(".") else f".{storage_ext}"
        target_path = self.attachments_dir / f"{card.id}-{attachment_id}{storage_ext}"

        target_format = (
            image.format
            or {
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".png": "PNG",
                ".gif": "GIF",
                ".webp": "WEBP",
            }.get(storage_ext.lower(), "PNG")
        )

        try:
            save_image = image.convert("RGBA") if target_format.upper() == "PNG" else image.convert("RGB")
            buffer = io.BytesIO()
            save_image.save(buffer, format=target_format)
            payload = buffer.getvalue()
        except OSError:
            return None

        if len(payload) > self.max_attachment_bytes:
            return None

        try:
            target_path.write_bytes(payload)
        except OSError:
            return None

        data_base64 = base64.b64encode(payload).decode("ascii") if embed_base64 else None

        storage_str = (
            str(target_path.relative_to(Path.cwd()))
            if target_path.is_relative_to(Path.cwd())
            else str(target_path)
        )

        return Attachment(
            id=attachment_id,
            name=name,
            source_type=source_type,
            mime_type=mime_type,
            width=image.width,
            height=image.height,
            offset_x=0.0,
            offset_y=0.0,
            preview_scale=1.0,
            storage_path=storage_str,
            data_base64=data_base64,
        )

    def _prepare_attachment_for_save(self, attachment: Attachment) -> Attachment:
        if not hasattr(attachment, "preview_scale"):
            attachment.preview_scale = 1.0
        prepared = copy.copy(attachment)
        if not prepared.data_base64:
            data_base64 = self._read_attachment_base64(attachment)
            if data_base64:
                prepared.data_base64 = data_base64
                attachment.data_base64 = data_base64
        return prepared

    def _create_card_with_image(
        self,
        image,
        *,
        name: str,
        mime_type: str,
        source_type: str,
        storage_ext: str,
        event=None,
        position: tuple[float, float] | None = None,
        embed_base64: bool = False,
    ) -> bool:
        width, height = self._compute_image_card_size(image)
        if position is None:
            cx, cy = self._get_canvas_point_from_event(event)
        else:
            cx, cy = position
        card_id = self.create_card(cx, cy, name or "Изображение", width=width, height=height)
        card = self.cards.get(card_id)
        if not card:
            return False

        attachment = self._store_attachment_image(
            card,
            image,
            name=name or "image.png",
            mime_type=mime_type,
            source_type=source_type,
            storage_ext=storage_ext,
            embed_base64=embed_base64,
        )
        if attachment is None:
            messagebox.showerror(
                "Изображение",
                "Не удалось сохранить изображение или его размер превышает допустимый предел (5 МБ)",
            )
            self._delete_card_by_id(card_id)
            return True

        card.attachments.append(attachment)
        self.render_card_attachments(card_id)
        self.select_card(card_id, additive=False)
        self.push_history()
        self.update_minimap()
        return True

    @staticmethod
    def _extension_from_mime(mime_type: str) -> str:
        if mime_type.endswith("/jpeg") or mime_type.endswith("/jpg"):
            return ".jpg"
        if mime_type.endswith("/png"):
            return ".png"
        if mime_type.endswith("/gif"):
            return ".gif"
        return ".bin"

    def _materialize_attachment(self, card_id: int, attachment: Attachment) -> bool:
        if not hasattr(attachment, "preview_scale"):
            attachment.preview_scale = 1.0
        path = self._resolve_attachment_path(attachment.storage_path)
        if path and path.exists():
            try:
                attachment.storage_path = str(path.relative_to(Path.cwd()))
            except ValueError:
                attachment.storage_path = str(path)
            return True

        if not attachment.data_base64:
            return False

        try:
            self._ensure_attachments_dir()
        except OSError:
            return False

        extension = Path(attachment.name).suffix or self._extension_from_mime(
            attachment.mime_type
        )
        target_path = self.attachments_dir / f"{card_id}-{attachment.id}{extension}"

        try:
            payload = base64.b64decode(attachment.data_base64)
        except (binascii.Error, ValueError):
            return False

        if len(payload) > self.max_attachment_bytes:
            return False

        try:
            target_path.write_bytes(payload)
        except OSError:
            return False

        attachment.storage_path = str(target_path.relative_to(Path.cwd()))
        return True

    def _restore_attachment_files(self, board: BoardData) -> None:
        failed: list[str] = []
        for card in board.cards.values():
            for attachment in card.attachments:
                restored = self._materialize_attachment(card.id, attachment)
                if not restored:
                    failed.append(attachment.name)

        if failed:
            unique = sorted(set(failed))
            names = "\n".join(unique)
            messagebox.showwarning(
                "Вложения",
                "Не удалось восстановить некоторые вложения (файлы отсутствуют и нет"
                f" встроенных данных):\n{names}",
            )

    def _prepare_preview_image(self, image, *, max_size=(200, 200), crop_to_square: bool = False):
        copy_image = image.copy()
        if crop_to_square:
            try:
                from PIL import Image, ImageOps
            except ImportError:
                return None
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            copy_image = ImageOps.fit(copy_image, max_size, method=resample)
        else:
            copy_image.thumbnail(max_size)
        return copy_image.convert("RGBA")

    def _resize_image(self, image, size: tuple[int, int], *, fit_mode: str = "contain"):
        try:
            from PIL import Image, ImageOps
        except ImportError:
            return None
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        copied = image.copy()
        if fit_mode == "cover":
            fitted = ImageOps.fit(copied, size, method=resample)
        else:
            fitted = ImageOps.contain(copied, size, method=resample)
        return fitted.convert("RGBA")

    def _prepare_icon_image(self, image, preview_scale: float = 1.0):
        base = max(image.width, image.height)
        target = max(1, int(base * preview_scale))
        return self._prepare_preview_image(image, max_size=(target, target), crop_to_square=True)

    def _calculate_attachment_preview_size(
        self, card: ModelCard, attachment: Attachment, layout: dict[str, float] | None = None
    ) -> tuple[int, int]:
        layout = layout or self.canvas_view.compute_card_layout(card)
        max_width = int(layout["image_width"])
        max_height = int(layout["image_height"])
        if max_width <= 0 or max_height <= 0:
            return 0, 0

        target_width = max(1, int(attachment.width * attachment.preview_scale))
        target_height = max(1, int(attachment.height * attachment.preview_scale))
        scale_limit = min(max_width / target_width, max_height / target_height, 1)
        if scale_limit <= 0:
            return 0, 0
        final_width = max(1, int(target_width * scale_limit))
        final_height = max(1, int(target_height * scale_limit))
        aspect = final_width / final_height if final_height else 0
        if self.attachment_max_aspect_ratio and aspect > self.attachment_max_aspect_ratio:
            final_width = int(final_height * self.attachment_max_aspect_ratio)
        elif self.attachment_min_aspect_ratio and aspect < self.attachment_min_aspect_ratio:
            final_height = int(final_width / self.attachment_min_aspect_ratio)

        final_width = min(final_width, max_width)
        final_height = min(final_height, max_height)
        if final_width <= 0 or final_height <= 0:
            return 0, 0
        return final_width, final_height

    def _clamp_attachment_offset(
        self,
        attachment: Attachment,
        preview_size: tuple[int, int],
        layout: dict[str, float],
    ) -> None:
        if not preview_size[0] or not preview_size[1]:
            return

        max_dx = max(layout["image_width"] / 2 - preview_size[0] / 2, 0)
        max_dy = max(layout["image_height"] / 2 - preview_size[1] / 2, 0)
        attachment.offset_x = min(max(attachment.offset_x, -max_dx), max_dx)
        attachment.offset_y = min(max(attachment.offset_y, -max_dy), max_dy)

    def _auto_position_attachment(
        self, card: ModelCard, attachment: Attachment, layout: dict[str, float]
    ) -> None:
        if not card.attachments:
            attachment.offset_x = 0.0
            attachment.offset_y = 0.0
            return

        previews = [
            self._calculate_attachment_preview_size(card, a, layout)
            for a in [*card.attachments, attachment]
        ]
        max_w = max((w for w, _ in previews), default=0)
        max_h = max((h for _, h in previews), default=0)
        thumb_size = (max_w or 1, max_h or 1)
        idx = len(card.attachments)
        offset_x, offset_y = self._compute_attachment_offset(card, thumb_size, idx, layout=layout)
        attachment.offset_x = offset_x
        attachment.offset_y = offset_y
        self._clamp_attachment_offset(attachment, previews[-1], layout)

    def _compute_attachment_offset(
        self,
        card: ModelCard,
        thumb_size: tuple[int, int],
        idx: int,
        *,
        layout: dict[str, float] | None = None,
    ) -> tuple[float, float]:
        layout = layout or self.canvas_view.compute_card_layout(card)
        gutter = layout.get("padding", 10) * 0.6
        padding = max(4.0, min(gutter, 12.0))
        per_row = max(int((layout["image_width"] - padding) // (thumb_size[0] + padding)), 1)
        col = idx % per_row
        row = idx // per_row
        offset_x = -layout["image_width"] / 2 + padding + thumb_size[0] / 2 + col * (thumb_size[0] + padding)
        offset_y = -layout["image_height"] / 2 + padding + thumb_size[1] / 2 + row * (thumb_size[1] + padding)
        return offset_x, offset_y

    def _compute_attachments_min_size(
        self, card: ModelCard, layout: dict[str, float]
    ) -> tuple[float, float]:
        if not card.attachments:
            return 0.0, 0.0

        padding = layout.get("padding", self.canvas_view.text_padding_min)
        required_width = 0.0
        required_image_height = 0.0
        for attachment in card.attachments:
            preview_w, preview_h = self._calculate_attachment_preview_size(card, attachment, layout)
            required_width = max(required_width, 2 * (abs(attachment.offset_x) + preview_w / 2))
            required_image_height = max(
                required_image_height, 2 * (abs(attachment.offset_y) + preview_h / 2)
            )

        min_width = required_width + 2 * padding
        non_image_height = card.height - layout["image_height"]
        min_height = non_image_height + required_image_height
        return min_width, min_height

    def select_attachment(self, card_id: int | None, attachment_id: int | None) -> None:
        if card_id is None or attachment_id is None:
            self.clear_attachment_selection()
            self.update_controls_state()
            return

        card, attachment = self._get_attachment(card_id, attachment_id)
        if not card or not attachment:
            self.clear_attachment_selection()
            self.update_controls_state()
            return

        self.selection_controller.select_card(card_id, additive=False)
        self.selected_attachment = (card_id, attachment_id)
        self._show_attachment_selection(card_id, attachment)
        self.update_controls_state()

    def _show_attachment_selection(self, card_id: int, attachment: Attachment) -> None:
        if not attachment:
            return
        key = (card_id, attachment.id)
        item_id = self.attachment_items.get(key)
        if not item_id:
            return
        bbox = self.canvas.bbox(item_id)
        if not bbox:
            return
        padding = 6
        x1, y1, x2, y2 = bbox
        x1 -= padding
        y1 -= padding
        x2 += padding
        y2 += padding

        if self.attachment_selection_box_id:
            self.canvas.coords(self.attachment_selection_box_id, x1, y1, x2, y2)
        else:
            self.attachment_selection_box_id = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline=self.theme["connection"],
                dash=(3, 2),
                width=2,
                tags=("attachment_selection", f"attachment_{card_id}_{attachment.id}"),
            )

        handle_size = 8
        corners = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "sw": (x1, y2),
            "se": (x2, y2),
        }
        for anchor, (cx, cy) in corners.items():
            existing = self.attachment_resize_handles.get(anchor)
            hx1 = cx - handle_size / 2
            hy1 = cy - handle_size / 2
            hx2 = cx + handle_size / 2
            hy2 = cy + handle_size / 2
            if existing:
                self.canvas.coords(existing, hx1, hy1, hx2, hy2)
                self.canvas.tag_raise(existing)
            else:
                hid = self.canvas.create_rectangle(
                    hx1,
                    hy1,
                    hx2,
                    hy2,
                    fill=self.theme["connection"],
                    outline="white",
                    width=1,
                    tags=(
                        "attachment_resize_handle",
                        f"attachment_handle_{anchor}",
                        f"attachment_{card_id}_{attachment.id}",
                    ),
                )
                self.attachment_resize_handles[anchor] = hid

        if self.attachment_selection_box_id:
            self.canvas.tag_raise(self.attachment_selection_box_id)
        for hid in self.attachment_resize_handles.values():
            if hid:
                self.canvas.tag_raise(hid)

    def _compute_image_card_size(self, image) -> tuple[float, float]:
        padding = 40
        max_dim = 320
        width = max(180, min(image.width + padding, max_dim))
        height = max(120, min(image.height + padding, max_dim))
        return float(width), float(height)

    def _get_canvas_point_from_event(self, event) -> tuple[float, float]:
        if event is None:
            cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
            cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
            return cx, cy

        if hasattr(event, "x") and hasattr(event, "y"):
            try:
                return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            except Exception:
                pass

        if hasattr(event, "x_root") and hasattr(event, "y_root"):
            local_x = event.x_root - self.canvas.winfo_rootx()
            local_y = event.y_root - self.canvas.winfo_rooty()
            return self.canvas.canvasx(local_x), self.canvas.canvasy(local_y)

        cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        return cx, cy

    def _get_attachment(self, card_id: int, attachment_id: int) -> tuple[ModelCard | None, Attachment | None]:
        card = self.cards.get(card_id)
        if not card:
            return None, None
        for attachment in card.attachments:
            if attachment.id == attachment_id:
                return card, attachment
        return card, None

    def open_attachment_viewer(self, card_id: int, attachment_id: int) -> None:
        card, attachment = self._get_attachment(card_id, attachment_id)
        if not card or not attachment:
            return
        image = self._load_attachment_image(attachment)
        if image is None:
            messagebox.showwarning("Вложения", "Не удалось загрузить вложение для просмотра.")
            return
        try:
            from PIL import ImageTk
        except ImportError:
            messagebox.showerror(
                "Вложения",
                "Для показа изображений нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return

        max_width = max(self.root.winfo_screenwidth() - 200, 300)
        max_height = max(self.root.winfo_screenheight() - 200, 300)
        preview = image.copy()
        preview.thumbnail((max_width, max_height))
        photo = ImageTk.PhotoImage(preview)

        viewer = tk.Toplevel(self.root)
        viewer.title(attachment.name or "Вложение")
        viewer.geometry(f"{photo.width()}x{photo.height()}")
        label = tk.Label(viewer, image=photo, bg="black")
        label.image = photo
        label.pack(fill="both", expand=True)

    def on_attachment_click(self, event):
        item = event.widget.find_withtag("current")
        item_id = item[0] if item else None
        if not item_id:
            return "break"
        tags = event.widget.gettags(item_id)
        for tag in tags:
            if tag.startswith("attachment_"):
                try:
                    _prefix, card_raw, attachment_raw = tag.split("_", 2)
                    card_id = int(card_raw)
                    attachment_id = int(attachment_raw)
                except (ValueError, IndexError):
                    return "break"
                self.select_attachment(card_id, attachment_id)
                return "break"
        return "break"

    def on_attachment_double_click(self, event):
        item = event.widget.find_withtag("current")
        item_id = item[0] if item else None
        if not item_id:
            return "break"
        tags = event.widget.gettags(item_id)
        for tag in tags:
            if tag.startswith("attachment_"):
                try:
                    _prefix, card_raw, attachment_raw = tag.split("_", 2)
                    card_id = int(card_raw)
                    attachment_id = int(attachment_raw)
                except (ValueError, IndexError):
                    return "break"
                self.open_attachment_viewer(card_id, attachment_id)
                return "break"
        return "break"

    def render_card_attachments(self, card_id: int) -> None:
        card = self.cards.get(card_id)
        if not card or not card.attachments:
            self._clear_attachment_previews_for_card(card_id)
            return

        try:
            from PIL import ImageTk
        except ImportError:
            messagebox.showerror(
                "Вложения",
                "Для показа изображений нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return

        self._clear_attachment_previews_for_card(card_id)

        layout = self.canvas_view.compute_card_layout(card)
        center_y = layout["image_top"] + layout["image_height"] / 2

        for attachment in card.attachments:
            image = self._load_attachment_image(attachment)
            if image is None:
                continue

            final_width, final_height = self._calculate_attachment_preview_size(card, attachment, layout)
            if final_width <= 0 or final_height <= 0:
                continue

            self._clamp_attachment_offset(attachment, (final_width, final_height), layout)
            fit_mode = self.attachment_fit_mode if self.attachment_fit_mode in {"contain", "cover"} else "contain"
            preview = self._resize_image(image, (final_width, final_height), fit_mode=fit_mode)
            if preview is None:
                continue
            photo = ImageTk.PhotoImage(preview)

            item_id = self.canvas.create_image(
                card.x + attachment.offset_x,
                center_y + attachment.offset_y,
                image=photo,
                anchor="center",
                tags=("attachment_preview", f"attachment_{card_id}_{attachment.id}"),
            )
            if card.text_bg_id:
                self.canvas.tag_lower(item_id, card.text_bg_id)
            self.canvas.tag_bind(
                f"attachment_{card_id}_{attachment.id}",
                "<Button-1>",
                self.on_attachment_click,
            )
            self.canvas.tag_bind(
                f"attachment_{card_id}_{attachment.id}",
                "<Double-Button-1>",
                self.on_attachment_double_click,
            )
            self.attachment_items[(card_id, attachment.id)] = item_id
            self.attachment_tk_images[(card_id, attachment.id)] = photo
            card.image_id = item_id
            if self.selected_attachment == (card_id, attachment.id):
                self._show_attachment_selection(card_id, attachment)

        if card.text_bg_id:
            self.canvas.tag_raise(card.text_bg_id)
        if card.text_id:
            self.canvas.tag_raise(card.text_id)

    def render_all_attachments(self) -> None:
        for card_id in list(self.cards.keys()):
            self.render_card_attachments(card_id)

    def update_attachment_positions(self, card_id: int, *, scale: float | None = None) -> None:
        card = self.cards.get(card_id)
        if not card or not card.attachments:
            return
        layout = self.canvas_view.compute_card_layout(card)
        if isinstance(scale, tuple):
            width_scale, height_scale = scale
        else:
            width_scale = height_scale = scale if scale is not None else 1.0

        center_y = layout["image_top"] + layout["image_height"] / 2
        for attachment in card.attachments:
            preview_size = self._calculate_attachment_preview_size(card, attachment, layout)
            if scale is not None:
                attachment.offset_x *= width_scale
                attachment.offset_y *= height_scale
            self._clamp_attachment_offset(attachment, preview_size, layout)
            item_id = self.attachment_items.get((card_id, attachment.id))
            if item_id:
                self.canvas.coords(
                    item_id,
                    card.x + attachment.offset_x,
                    center_y + attachment.offset_y,
                )
                if card.text_bg_id:
                    self.canvas.tag_lower(item_id, card.text_bg_id)
        self.render_card_attachments(card_id)

    def _read_clipboard_image(self):
        try:
            from PIL import ImageGrab, Image
        except ImportError:
            messagebox.showerror(
                "Вставка изображения",
                "Для вставки изображения нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return None

        try:
            grabbed = ImageGrab.grabclipboard()
        except FileNotFoundError:
            messagebox.showerror(
                "Вставка изображения",
                "Не удалось прочитать буфер обмена. Установите утилиту xclip (X11)"
                " или wl-clipboard (Wayland) и попробуйте снова.",
            )
            return None
        except Exception:
            return None

        if grabbed is None:
            return None

        if isinstance(grabbed, Image.Image):
            mime = Image.MIME.get(grabbed.format, "image/png")
            return grabbed, grabbed.format or "PNG", mime, "clipboard.png"

        if isinstance(grabbed, (list, tuple)) and grabbed:
            first = grabbed[0]
            path = Path(first)
            if path.is_file():
                try:
                    image = Image.open(path)
                except OSError:
                    return None
                mime = Image.MIME.get(image.format, "image/png")
                return image, image.format or "PNG", mime, path.name
        return None

    def _paste_clipboard_image_as_card(self, event=None) -> bool:
        result = self._read_clipboard_image()
        if result is None:
            return False

        image, _fmt, mime_type, name = result
        if not mime_type.startswith("image/"):
            messagebox.showerror(
                "Вставка изображения",
                "Формат изображения не поддерживается. Попробуйте PNG, JPEG, GIF или WebP.",
            )
            return True

        if self.selected_cards:
            card_id = self.selected_card_id or next(iter(self.selected_cards))
            card = self.cards.get(card_id)
            if card is None:
                return True

            self._attach_image_to_card(
                card,
                image,
                name=name,
                mime_type=mime_type,
                source_type="clipboard",
                storage_ext=self._extension_from_mime(mime_type),
                embed_base64=True,
            )
            return True

        return self._create_card_with_image(
            image,
            name=name,
            mime_type=mime_type,
            source_type="clipboard",
            storage_ext=".png",
            event=event,
            embed_base64=True,
        )

    def _create_card_from_path(
        self,
        source_path: Path,
        *,
        base_position: tuple[float, float],
        offset: tuple[float, float] = (0.0, 0.0),
    ) -> bool:
        opened = self._open_image_from_path(source_path, dialog_title="Изображение")
        if opened is None:
            return False

        image, mime_type, storage_ext = opened
        position = (base_position[0] + offset[0], base_position[1] + offset[1])
        return self._create_card_with_image(
            image,
            name=source_path.name,
            mime_type=mime_type,
            source_type="file",
            storage_ext=storage_ext,
            position=position,
        )

    def on_drop_files(self, event):
        data = getattr(event, "data", None)
        if not data:
            return
        paths = [Path(p) for p in self.root.splitlist(data)]
        if not paths:
            return

        if self.selected_cards:
            card_id = self.selected_card_id or next(iter(self.selected_cards))
            card = self.cards.get(card_id)
            if card is None:
                return
            attached_any = False
            for path in paths:
                if not path.is_file():
                    continue
                opened = self._open_image_from_path(path, dialog_title="Изображение")
                if opened is None:
                    continue
                image, mime_type, storage_ext = opened
                attached = self._attach_image_to_card(
                    card,
                    image,
                    name=path.name,
                    mime_type=mime_type,
                    source_type="file",
                    storage_ext=storage_ext,
                    embed_base64=False,
                )
                attached_any = attached_any or attached
            if attached_any:
                self.select_card(card.id, additive=False)
            return

        base_position = self._get_canvas_point_from_event(event)
        spacing = 60
        created_any = False
        for idx, path in enumerate(paths):
            if not path.is_file():
                continue
            offset = (spacing * (idx % 3), spacing * (idx // 3))
            created = self._create_card_from_path(
                path,
                base_position=base_position,
                offset=offset,
            )
            created_any = created_any or created

        if created_any:
            self.update_minimap()

    def _attach_image_from_file(self) -> bool:
        opened_exts = None
        try:
            from PIL import Image
        except ImportError:
            messagebox.showerror(
                "Прикрепить изображение",
                "Для добавления изображений нужен пакет Pillow.\n"
                "Установите его командой:\n\npip install pillow",
            )
            return True
        else:
            opened_exts = Image.registered_extensions()

        if not self.selected_cards:
            messagebox.showwarning(
                "Прикрепить изображение",
                "Выберите карточку, чтобы добавить вложение.",
            )
            return True

        ext_map = {
            ext: fmt
            for ext, fmt in opened_exts.items()
            if Image.MIME.get(fmt, "").startswith("image/")
        }
        patterns = " ".join(f"*{ext}" for ext in sorted(ext_map))
        filetypes = [
            ("Изображения", patterns or "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
            ("Все файлы", "*.*"),
        ]

        filename = filedialog.askopenfilename(
            defaultextension=".png",
            filetypes=filetypes,
        )
        if not filename:
            return False

        source_path = Path(filename)
        opened = self._open_image_from_path(source_path, dialog_title="Прикрепить изображение")
        if opened is None:
            return True
        image, mime_type, storage_ext = opened

        card_id = self.selected_card_id or next(iter(self.selected_cards))
        card = self.cards.get(card_id)
        if card is None:
            return True

        self._attach_image_to_card(
            card,
            image,
            name=source_path.name,
            mime_type=mime_type,
            source_type="file",
            storage_ext=storage_ext,
            embed_base64=False,
        )
        return True

    def _attach_clipboard_image_to_card(self) -> bool:
        if not self.selected_cards:
            messagebox.showwarning(
                "Прикрепить изображение", "Выберите карточку, чтобы добавить вложение."
            )
            return True

        result = self._read_clipboard_image()
        if result is None:
            messagebox.showerror(
                "Вставка изображения", "Буфер обмена не содержит поддерживаемое изображение."
            )
            return True

        image, _fmt, mime_type, name = result
        if not mime_type.startswith("image/"):
            messagebox.showerror(
                "Вставка изображения", "Формат изображения не поддерживается."
            )
            return True

        card_id = self.selected_card_id or next(iter(self.selected_cards))
        card = self.cards.get(card_id)
        if card is None:
            return True

        self._attach_image_to_card(
            card,
            image,
            name=name or "clipboard.png",
            mime_type=mime_type,
            source_type="clipboard",
            storage_ext=self._extension_from_mime(mime_type),
            embed_base64=True,
        )
        return True

    def attach_image_from_file(self):
        self._attach_image_from_file()

    def snap_cards_to_grid(self, card_ids):
        if not self.snap_to_grid or not card_ids:
            return
        for card_id in card_ids:
            card = self.cards.get(card_id)
            if not card:
                continue
            gx = round(card.x / self.grid_size) * self.grid_size
            gy = round(card.y / self.grid_size) * self.grid_size
            dx = gx - card.x
            dy = gy - card.y
            if dx == 0 and dy == 0:
                continue
            card.x = gx
            card.y = gy
            x1 = gx - card.width / 2
            y1 = gy - card.height / 2
            x2 = gx + card.width / 2
            y2 = gy + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.update_card_layout(card_id, redraw_attachment=False)
            self.update_card_handles_positions(card_id)
            self.update_connections_for_card(card_id)

    # ---------- Карточки ----------

    def add_card_dialog(self):
        text = simpledialog.askstring("Новая карточка",
                                      "Введите текст карточки:",
                                      parent=self.root)
        if text is None or text.strip() == "":
            return
        x = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        y = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        self.create_card(x, y, text, color=None)
        self.push_history()

    def on_canvas_double_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        item = self.canvas.find_withtag("current")
        item_id = item[0] if item else None
    
        # Двойной клик по связи — редактируем подпись
        conn = self.get_connection_from_item(item_id)
        if conn is not None:
            self.select_connection(conn)
            current_label = conn.label
            new_label = simpledialog.askstring(
                "Подпись связи",
                "Текст связи:",
                initialvalue=current_label,
                parent=self.root,
            )
            if new_label is None:
                return
            conn.label = new_label.strip()
            if conn.label_id:
                if conn.label:
                    self.canvas.itemconfig(
                        conn.label_id,
                        text=conn.label,
                        state="normal",
                        fill=self.theme["connection_label"],
                    )
                else:
                    self.canvas.delete(conn.label_id)
                    conn.label_id = None
            elif conn.label:
                coords = self.canvas.coords(conn.line_id)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    mx = (x1 + x2) / 2
                    my = (y1 + y2) / 2
                else:
                    mx, my = cx, cy
                label_id = self.canvas.create_text(
                    mx,
                    my,
                    text=conn.label,
                    font=("Arial", 9, "italic"),
                    fill=self.theme["connection_label"],
                    tags=("connection_label",),
                )
                conn.label_id = label_id
            self.push_history()
            return
    
        # Двойной клик по карточке — inline-редактирование
        card_id = self.get_card_id_from_item(item)
        if card_id is not None:
            self.start_inline_edit_card(card_id)
            return
    
        # Двойной клик по пустому месту — новая карточка
        text = simpledialog.askstring(
            "Новая карточка",
            "Введите текст карточки:",
            parent=self.root,
        )
        if text is None or text.strip() == "":
            return
        self.create_card(cx, cy, text.strip(), color=None)
        self.push_history()
    def create_card(self, x, y, text, color=None, card_id=None,
                    width=None, height=None):
        if width is None:
            width = 180
        if height is None:
            height = 100
        if color is None:
            color = self.theme["card_default"]
        if card_id is None:
            card_id = self.next_card_id
            self.next_card_id += 1
        else:
            self.next_card_id = max(self.next_card_id, card_id + 1)

        card = ModelCard(
            id=card_id,
            x=x,
            y=y,
            width=width,
            height=height,
            text=text,
            color=color,
        )
        self.canvas_view.draw_card(card)
        self.cards[card_id] = card
        return card_id

    def _delete_card_by_id(self, card_id: int) -> None:
        card = self.cards.pop(card_id, None)
        if not card:
            return
        for item_id in (
            card.rect_id,
            card.text_id,
            card.text_bg_id,
            card.image_id,
            card.resize_handle_id,
            *card.connect_handles.values(),
        ):
            if item_id:
                self.canvas.delete(item_id)
        self._clear_attachment_previews_for_card(card_id)
        self.connections = [
            conn for conn in self.connections if conn.from_id != card_id and conn.to_id != card_id
        ]

    def get_card_id_from_item(self, item_ids):
        if not item_ids:
            return None
        item_id = item_ids[0]
        tags = self.canvas.gettags(item_id)
        for tag in tags:
            if tag.startswith("card_"):
                try:
                    return int(tag.split("_")[1])
                except ValueError:
                    continue
        return None

    # ---------- Рамки / группы ----------

    def add_frame_dialog(self):
        title = simpledialog.askstring(
            "Новая рамка",
            "Заголовок группы:",
            parent=self.root
        )
        if title is None:
            return

        cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        width = 400
        height = 250
        x1 = cx - width / 2
        y1 = cy - height / 2
        x2 = cx + width / 2
        y2 = cy + height / 2

        self.create_frame(x1, y1, x2, y2, title=title)
        self.push_history()

    def create_frame(self, x1, y1, x2, y2, title="Группа",
                     frame_id=None, collapsed=False):
        if frame_id is None:
            frame_id = self.next_frame_id
            self.next_frame_id += 1
        else:
            self.next_frame_id = max(self.next_frame_id, frame_id + 1)

        frame = ModelFrame(
            id=frame_id,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            title=title,
            collapsed=collapsed,
        )
        self.canvas_view.draw_frame(frame)
        self.frames[frame_id] = frame

        if collapsed:
            self.apply_frame_collapse_state(frame_id)

    def get_frame_id_from_item(self, item_ids):
        if not item_ids:
            return None
        item_id = item_ids[0]
        tags = self.canvas.gettags(item_id)
        for tag in tags:
            if tag.startswith("frame_handle_"):
                parts = tag.split("_")
                try:
                    return int(parts[-1])
                except ValueError:
                    continue
        for tag in tags:
            if tag.startswith("frame_"):
                try:
                    return int(tag.split("_")[1])
                except ValueError:
                    continue
        for tag in tags:
            if tag.startswith("frame_title"):
                try:
                    return int(tag.split("_")[2])
                except Exception:
                    continue
        return None

    def select_frame(self, frame_id):
        self.selection_controller.select_frame(frame_id)

    def toggle_selected_frame_collapse(self):
        frame_id = self.selected_frame_id
        if frame_id is None or frame_id not in self.frames:
            messagebox.showwarning("Нет выбора", "Сначала выберите рамку.")
            return
        frame = self.frames[frame_id]
        frame.collapsed = not frame.collapsed

        rect_id = frame.rect_id
        if frame.collapsed:
            self.canvas.itemconfig(
                rect_id,
                dash=(3, 3),
                fill=self.theme["frame_collapsed_bg"],
                outline=self.theme["frame_collapsed_outline"]
            )
        else:
            self.canvas.itemconfig(
                rect_id,
                dash=(),
                fill=self.theme["frame_bg"],
                outline=self.theme["frame_outline"]
            )

        self.apply_frame_collapse_state(frame_id)
        self.push_history()

    def apply_frame_collapse_state(self, frame_id):
        frame = self.frames.get(frame_id)
        if not frame:
            return
        collapsed = frame.collapsed
        state = "hidden" if collapsed else "normal"

        x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
        cards_in_frame = [
            cid for cid, card in self.cards.items()
            if x1 <= card.x <= x2 and y1 <= card.y <= y2
        ]

        for cid in cards_in_frame:
            card = self.cards[cid]
            self.canvas.itemconfig(card.rect_id, state=state)
            self.canvas.itemconfig(card.text_id, state=state)
            if card.resize_handle_id:
                self.canvas.itemconfig(card.resize_handle_id, state=state)
            for hid in card.connect_handles.values():
                if hid:
                    self.canvas.itemconfig(hid, state=state)

        for conn in self.connections:
            if conn.from_id in cards_in_frame or conn.to_id in cards_in_frame:
                self.canvas.itemconfig(conn.line_id, state=state)
                if conn.label_id:
                    self.canvas.itemconfig(conn.label_id, state=state)

    # ---------- Хэндлы рамок ----------

    def show_frame_handles(self, frame_id: int):
        frame = self.frames.get(frame_id)
        if not frame or not frame.rect_id:
            return

        self.hide_frame_handles(frame_id)
        x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
        size = 10
        handles: dict[str, int | None] = {}
        positions = {
            "nw": (x1, y1),
            "ne": (x2, y1),
            "sw": (x1, y2),
            "se": (x2, y2),
        }
        cursors = {
            "nw": "top_left_corner",
            "ne": "top_right_corner",
            "sw": "bottom_left_corner",
            "se": "bottom_right_corner",
        }

        for key, (cx, cy) in positions.items():
            hx1 = cx - size
            hy1 = cy - size
            hx2 = cx
            hy2 = cy
            hid = self.canvas.create_rectangle(
                hx1,
                hy1,
                hx2,
                hy2,
                fill=self.theme["frame_outline"],
                outline="",
                tags=("frame_handle", f"frame_handle_{key}", f"frame_handle_{frame_id}"),
            )
            cursor = cursors.get(key, "sizing")
            self.canvas.tag_bind(hid, "<Enter>", lambda _event, cur=cursor: self.canvas.config(cursor=cur))
            self.canvas.tag_bind(hid, "<Leave>", lambda _event: self.canvas.config(cursor=""))
            handles[key] = hid
            self.canvas.tag_raise(hid)

        frame.resize_handles = handles

    def hide_frame_handles(self, frame_id: int | None):
        if frame_id is None:
            return
        frame = self.frames.get(frame_id)
        if not frame:
            return
        for hid in frame.resize_handles.values():
            if hid:
                self.canvas.delete(hid)
        self.canvas.config(cursor="")
        frame.resize_handles.clear()

    def hide_all_frame_handles(self):
        for fid in list(self.frames.keys()):
            self.hide_frame_handles(fid)

    def update_frame_handles_positions(self, frame_id: int):
        frame = self.frames.get(frame_id)
        if not frame or not frame.rect_id or not frame.resize_handles:
            return
        x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
        size = 10
        coords = {
            "nw": (x1 - size, y1 - size, x1, y1),
            "ne": (x2 - size, y1 - size, x2, y1),
            "sw": (x1 - size, y2 - size, x1, y2),
            "se": (x2 - size, y2 - size, x2, y2),
        }
        for key, hid in frame.resize_handles.items():
            if hid and key in coords:
                self.canvas.coords(hid, *coords[key])
                self.canvas.tag_raise(hid)

    # ---------- Хэндлы карточек (resize / connect) ----------

    def _card_handle_positions(self, card: ModelCard) -> Dict[str, tuple[float, float]]:
        return self.canvas_view.card_handle_positions(card)

    def _closest_card_anchor(self, card: ModelCard, x: float, y: float) -> str:
        positions = self._card_handle_positions(card)
        anchor, _ = min(
            positions.items(),
            key=lambda item: (item[1][0] - x) ** 2 + (item[1][1] - y) ** 2,
        )
        return anchor

    def show_card_handles(self, card_id: int, *, include_resize: bool = True):
        card = self.cards.get(card_id)
        if not card:
            return
        x = card.x
        y = card.y
        w = card.width
        h = card.height
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        if include_resize and not card.resize_handle_id:
            size = 10
            rx1 = x2 - size
            ry1 = y2 - size
            rx2 = x2
            ry2 = y2
            rid = self.canvas.create_rectangle(
                rx1,
                ry1,
                rx2,
                ry2,
                fill=self.theme["connection"],
                outline="",
                tags=("resize_handle", f"card_{card_id}"),
            )
            card.resize_handle_id = rid

        positions = self._card_handle_positions(card)
        r = 5
        for anchor, (cx, cy) in positions.items():
            existing_id = card.connect_handles.get(anchor)
            if existing_id is None:
                hid = self.canvas.create_oval(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    fill=self.theme["connection"],
                    outline="",
                    tags=("connect_handle", f"connect_handle_{anchor}", f"card_{card_id}"),
                )
                card.connect_handles[anchor] = hid
            else:
                hid = existing_id
            self.canvas.tag_raise(hid)

        if card.resize_handle_id:
            self.canvas.tag_raise(card.resize_handle_id)

    def hide_card_handles(self, card_id: int, *, include_resize: bool = True):
        card = self.cards.get(card_id)
        if not card:
            return
        if include_resize and card.resize_handle_id:
            self.canvas.delete(card.resize_handle_id)
            card.resize_handle_id = None
        for anchor, hid in list(card.connect_handles.items()):
            if hid:
                self.canvas.delete(hid)
            card.connect_handles.pop(anchor, None)

    def update_card_layout(
        self,
        card_id: int,
        *,
        redraw_attachment: bool = True,
        attachment_scale: float | tuple[float, float] | None = None,
    ) -> None:
        card = self.cards.get(card_id)
        if not card:
            return
        layout = self.canvas_view.compute_card_layout(card)
        self.canvas_view.apply_card_layout(card, layout)
        if card.attachments:
            if redraw_attachment or not card.image_id:
                self.render_card_attachments(card_id)
            else:
                self.update_attachment_positions(card_id, scale=attachment_scale)

    def update_card_handles_positions(self, card_id):
        card = self.cards.get(card_id)
        if not card:
            return
        w = card.width
        h = card.height
        x2 = card.x + w / 2
        y2 = card.y + h / 2

        if card.resize_handle_id:
            size = 10
            rx1 = x2 - size
            ry1 = y2 - size
            rx2 = x2
            ry2 = y2
            self.canvas.coords(card.resize_handle_id, rx1, ry1, rx2, ry2)

        positions = self._card_handle_positions(card)
        r = 5
        for anchor, (cx, cy) in positions.items():
            hid = card.connect_handles.get(anchor)
            if hid:
                self.canvas.coords(hid, cx - r, cy - r, cx + r, cy + r)
                self.canvas.tag_raise(hid)

    # ---------- Выделение карточек ----------

    def _clear_card_selection(self):
        self.selection_controller.clear_card_selection()

    def select_card(self, card_id, additive=False):
        self.selection_controller.select_card(card_id, additive)

    # ---------- Мышь: выбор/перетаскивание/resize/connect-drag ----------

    def on_canvas_click(self, event):
        return self.drag_controller.on_canvas_click(event)

    def on_mouse_drag(self, event):
        return self.drag_controller.on_mouse_drag(event)

    def on_mouse_release(self, event):
        return self.drag_controller.on_mouse_release(event)

    def on_mouse_move(self, event):
        if self.drag_data["dragging"]:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(cx, cy, cx, cy)
        card_id = None
        connection_hover = None
        for it in items:
            cid = self.get_card_id_from_item((it,))
            if cid is not None:
                card_id = cid
                break
            connection_hover = self.connection_handle_map.get(it)
            if connection_hover:
                break
            connection_hover = self.get_connection_from_item(it)
            if connection_hover:
                break

        if card_id == self.hover_card_id and connection_hover == self.hover_connection:
            return

        if self.hover_card_id is not None and self.hover_card_id not in self.selected_cards:
            self.hide_card_handles(self.hover_card_id, include_resize=False)

        self.hover_card_id = card_id
        if card_id is not None and card_id not in self.selected_cards:
            self.show_card_handles(card_id, include_resize=False)

        if connection_hover != self.hover_connection:
            if self.hover_connection and self.hover_connection is not self.selected_connection:
                self.canvas_view.set_connection_hover(self.hover_connection, False)
            self.hover_connection = connection_hover
            if connection_hover and connection_hover is not self.selected_connection:
                self.canvas_view.set_connection_hover(connection_hover, True)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.update_minimap()

    # ---------- Зум ----------

    def on_mousewheel(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.apply_zoom(scale, event)

    def on_mousewheel_linux(self, event):
        scale = 1.1 if event.num == 4 else 0.9
        self.apply_zoom(scale, event)

    def apply_zoom(self, scale, event):
        new_zoom = self.zoom_factor * scale
        if new_zoom < self.min_zoom or new_zoom > self.max_zoom:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        self.canvas.scale("all", cx, cy, scale, scale)
        self.zoom_factor = new_zoom

        for card in self.cards.values():
            x1, y1, x2, y2 = self.canvas.coords(card.rect_id)
            card.x = (x1 + x2) / 2
            card.y = (y1 + y2) / 2
            card.width = x2 - x1
            card.height = y2 - y1
            self.update_card_handles_positions(card.id)
            self.update_card_layout(card.id)

        for frame in self.frames.values():
            if frame.rect_id:
                x1, y1, x2, y2 = self.canvas.coords(frame.rect_id)
                frame.x1, frame.y1, frame.x2, frame.y2 = x1, y1, x2, y2
                self.update_frame_handles_positions(frame.id)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.update_minimap()

    # ---------- Связи ----------

    def get_connection_from_item(self, item_id):
        if not item_id:
            return None
        for conn in self.connections:
            if conn.line_id == item_id or conn.label_id == item_id:
                return conn
        return None

    def _connection_anchors(self, from_card, to_card, connection=None):
        return self.canvas_view._connection_anchors(from_card, to_card, connection)

    def create_connection(
        self,
        from_id,
        to_id,
        label: str = "",
        *,
        from_anchor: str | None = None,
        to_anchor: str | None = None,
        direction: str = DEFAULT_CONNECTION_DIRECTION,
    ):
        if from_id not in self.cards or to_id not in self.cards:
            return
        card_from = self.cards[from_id]
        card_to = self.cards[to_id]

        normalized_direction = (
            direction if direction in {"start", "end"} else DEFAULT_CONNECTION_DIRECTION
        )

        connection = ModelConnection(
            from_id=from_id,
            to_id=to_id,
            label=label,
            direction=normalized_direction,
            from_anchor=from_anchor,
            to_anchor=to_anchor,
        )
        self.canvas_view.draw_connection(connection, card_from, card_to)
        self.connections.append(connection)

    def update_connections_for_card(self, card_id):
        self.canvas_view.update_connection_positions(self.connections, self.cards, card_id)
        if self.selected_connection and (
            self.selected_connection.from_id == card_id
            or self.selected_connection.to_id == card_id
        ):
            self.show_connection_handles(self.selected_connection)

    def toggle_connect_mode(self):
        self.connect_controller.toggle_connect_mode()

    # ---------- Цвет и текст карточки ----------

    def change_color(self):
        card_ids = [cid for cid in self.selected_cards if cid in self.cards]
        if not card_ids:
            messagebox.showwarning("Нет выбора", "Сначала выберите карточку.")
            return

        initial_card_id = self.selected_card_id if self.selected_card_id in self.cards else card_ids[0]
        initial = self.cards[initial_card_id].color
        color = colorchooser.askcolor(initialcolor=initial, parent=self.root)[1]
        if not color:
            return

        changed = bulk_update_card_colors(self.cards, card_ids, color)
        if not changed:
            return

        for cid in changed:
            card = self.cards[cid]
            self.canvas_view.update_card_color(card)
            self.update_card_layout(cid, redraw_attachment=False)
        self.render_selection()
        self.push_history()

    def change_text_color(self):
        initial = self.theme.get("text")
        color = colorchooser.askcolor(initialcolor=initial, parent=self.root)[1]
        if not color:
            return
        self.text_colors[self.theme_name] = color
        self._apply_theme()
        self._redraw_with_current_theme()
        save_theme_settings(self.theme_name, self.text_colors, self.show_grid)

    def edit_card_text_dialog(self):
        if self.selected_card_id is None or self.selected_card_id not in self.cards:
            messagebox.showwarning("Нет выбора", "Сначала выберите карточку.")
            return
        self.edit_card_text(self.selected_card_id)
        self.push_history()

    def edit_card_text(self, card_id):
        card = self.cards[card_id]
        new_text = simpledialog.askstring("Редактировать текст",
                                          "Текст карточки:",
                                          initialvalue=card.text,
                                          parent=self.root)
        if new_text is None:
            return
        card.text = new_text
        self.canvas.itemconfig(card.text_id, text=new_text)
        self.update_card_layout(card_id)

    # ---------- Inline-редактирование карточек и выравнивание ----------
    
    def start_inline_edit_card(self, card_id: int):
        """
        Запускает inline-редактирование текста карточки через Text,
        встроенный в canvas.
        """
        card = self.cards.get(card_id)
        if not card:
            return
    
        # Если уже есть редактор — сначала завершим его с сохранением
        if self.inline_editor is not None:
            self.finish_inline_edit(commit=True)
    
        self.inline_editor_card_id = card_id
    
        # Берём bbox текста карточки
        try:
            x1, y1, x2, y2 = self.canvas.bbox(card.text_id)
        except Exception:
            x = card.x
            y = card.y
            w = card.width
            h = card.height
            x1 = x - w / 2 + 4
            y1 = y - h / 2 + 4
            x2 = x + w / 2 - 4
            y2 = y + h / 2 - 4
    
        pad_x = 2
        pad_y = 2
        width = max(40, x2 - x1 + pad_x * 2)
        height = max(20, y2 - y1 + pad_y * 2)
    
        self.inline_editor = tk.Text(
            self.canvas,
            font=("Arial", 10),
            wrap="word",
            undo=True,
            borderwidth=1,
            relief="solid",
        )
        self.inline_editor.insert("1.0", card.text)
        self.inline_editor.focus_set()
    
        self.inline_editor_window_id = self.canvas.create_window(
            x1 - pad_x,
            y1 - pad_y,
            anchor="nw",
            window=self.inline_editor,
            width=width,
            height=height,
        )
    
        self.inline_editor.bind("<Control-Return>", self._inline_edit_commit_event)
        self.inline_editor.bind("<Escape>", self._inline_edit_cancel_event)
        self.inline_editor.bind("<FocusOut>", self._inline_edit_commit_event)
    
    def _inline_edit_commit_event(self, event=None):
        self.finish_inline_edit(commit=True)
        return "break"
    
    def _inline_edit_cancel_event(self, event=None):
        self.finish_inline_edit(commit=False)
        return "break"
    
    def finish_inline_edit(self, commit: bool = True):
        """
        Завершает inline-редактирование.
        commit=True — сохранить изменения,
        commit=False — отменить.
        """
        if self.inline_editor is None:
            return
    
        editor = self.inline_editor
        window_id = self.inline_editor_window_id
        card_id = self.inline_editor_card_id
    
        self.inline_editor = None
        self.inline_editor_window_id = None
        self.inline_editor_card_id = None
    
        if window_id is not None:
            self.canvas.delete(window_id)
    
        try:
            editor_text = editor.get("1.0", "end-1c")
        except Exception:
            editor_text = None
    
        editor.destroy()
    
        if not commit or card_id is None or editor_text is None:
            return
    
        card = self.cards.get(card_id)
        if not card:
            return
    
        new_text = editor_text.strip()
        card.text = new_text
        self.canvas.itemconfig(card.text_id, text=new_text)
        self.update_card_layout(card_id)

        self.push_history()

    def _context_toggle_connection_direction(self):
        conn = self.context_connection
        if not conn:
            return
        conn.toggle_direction()
        self.canvas_view.apply_connection_direction(conn)
        self.push_history()

    def toggle_selected_connection_direction(self, event=None):
        if not self.selected_connection:
            return
        self.selected_connection.toggle_direction()
        self.canvas_view.apply_connection_direction(self.selected_connection)
        self.push_history()
    
    def _require_multiple_selected_cards(self):
        cards = [cid for cid in self.selected_cards if cid in self.cards]
        if len(cards) < 2:
            messagebox.showwarning(
                "Недостаточно карточек",
                "Для этой операции нужно выбрать минимум две карточки.",
            )
            return None
        return cards
    
    def align_selected_cards_left(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        left_min = min(
            self.cards[cid].x - self.cards[cid].width / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_x = left_min + card.width / 2
            card.x = new_x
            x1 = card.x - card.width / 2
            y1 = card.y - card.height / 2
            x2 = card.x + card.width / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.update_card_layout(cid, redraw_attachment=False)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)

        self.push_history()
    
    def align_selected_cards_top(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        top_min = min(
            self.cards[cid].y - self.cards[cid].height / 2 for cid in cards
        )
    
        for cid in cards:
            card = self.cards[cid]
            new_y = top_min + card.height / 2
            card.y = new_y
            x1 = card.x - card.width / 2
            y1 = card.y - card.height / 2
            x2 = card.x + card.width / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.update_card_layout(cid, redraw_attachment=False)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
    
        self.push_history()
    
    def equalize_selected_cards_width(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_w = ref.width
    
        for cid in cards:
            card = self.cards[cid]
            card.width = ref_w
            x1 = card.x - ref_w / 2
            y1 = card.y - card.height / 2
            x2 = card.x + ref_w / 2
            y2 = card.y + card.height / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.update_card_layout(cid)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)

        self.push_history()
    
    def equalize_selected_cards_height(self):
        cards = self._require_multiple_selected_cards()
        if not cards:
            return
    
        ref = self.cards[cards[0]]
        ref_h = ref.height
    
        for cid in cards:
            card = self.cards[cid]
            card.height = ref_h
            x1 = card.x - card.width / 2
            y1 = card.y - ref_h / 2
            x2 = card.x + card.width / 2
            y2 = card.y + ref_h / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            self.update_card_layout(cid)
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)

        self.push_history()

    def apply_card_size_from_controls(self):
        try:
            target_width = int(self.var_card_width.get())
            target_height = int(self.var_card_height.get())
        except (tk.TclError, ValueError):
            messagebox.showwarning(
                "Некорректный размер",
                "Введите целые числа для ширины и высоты карточки.",
            )
            return

        if target_width <= 0 or target_height <= 0:
            messagebox.showwarning(
                "Некорректный размер",
                "Ширина и высота должны быть положительными числами.",
            )
            return

        card_ids = [cid for cid in self.selected_cards if cid in self.cards]
        if not card_ids:
            messagebox.showinfo("Нет выбора", "Сначала выберите карточку для изменения размера.")
            return

        changed = False
        for cid in card_ids:
            card = self.cards.get(cid)
            if not card:
                continue

            original_w, original_h = card.width, card.height
            card.width = target_width
            card.height = target_height
            layout = self.canvas_view.compute_card_layout(card)
            attach_min_w, attach_min_h = self._compute_attachments_min_size(card, layout)
            min_w = max(60, attach_min_w)
            min_h = max(40, attach_min_h)
            new_w = max(target_width, min_w)
            new_h = max(target_height, min_h)
            card.width = new_w
            card.height = new_h

            x1 = card.x - new_w / 2
            y1 = card.y - new_h / 2
            x2 = card.x + new_w / 2
            y2 = card.y + new_h / 2
            self.canvas.coords(card.rect_id, x1, y1, x2, y2)
            width_scale = new_w / original_w if original_w else 1.0
            height_scale = new_h / original_h if original_h else 1.0
            self.update_card_layout(cid, attachment_scale=(width_scale, height_scale))
            self.update_card_handles_positions(cid)
            self.update_connections_for_card(cid)
            changed = True

        if changed:
            self.update_minimap()
            self.push_history()
        self.update_controls_state()
    
    # ---------- Настройки сетки (UI-обработчики) ----------
    
    def on_toggle_show_grid(self):
        """Отобразить или скрыть сетку и сохранить выбор пользователя."""
        self.show_grid = bool(self.var_show_grid.get())
        self.canvas_view.set_grid_visibility(self.show_grid)
        save_theme_settings(self.theme_name, self.text_colors, self.show_grid)

    def on_toggle_snap_to_grid(self):
        """
        Включаем / выключаем привязку к сетке.
        """
        self.snap_to_grid = bool(self.var_snap_to_grid.get())
    
    def on_grid_size_change(self, event=None):
        """
        Меняет шаг сетки и перерисовывает её.
        """
        try:
            value = int(self.var_grid_size.get())
        except Exception:
            value = self.grid_size
    
        if value < 5:
            value = 5
        if value > 200:
            value = 200
    
        self.grid_size = value
        self.var_grid_size.set(value)
    
        self.draw_grid()

    # ---------- Удаление карточек ----------

    def delete_selected_cards(self, event=None):
        deleted_anything = False
        if self.selected_connection:
            self._delete_connection(self.selected_connection)
            self.selected_connection = None
            deleted_anything = True

        if not self.selected_cards:
            if deleted_anything:
                self.push_history()
            return
        to_delete = list(self.selected_cards)

        for conn in list(self.connections):
            if conn.from_id in to_delete or conn.to_id in to_delete:
                self._delete_connection(conn)
                deleted_anything = True

        for card_id in to_delete:
            card = self.cards.get(card_id)
            if not card:
                continue
            for attachment in card.attachments:
                try:
                    path = Path(attachment.storage_path)
                    if not path.is_absolute():
                        path = Path.cwd() / path
                    if path.exists():
                        path.unlink()
                except Exception:
                    pass
            self._clear_attachment_previews_for_card(card_id)
            if card.resize_handle_id:
                self.canvas.delete(card.resize_handle_id)
            for hid in card.connect_handles.values():
                if hid:
                    self.canvas.delete(hid)
            self.canvas.delete(card.rect_id)
            self.canvas.delete(card.text_id)
            del self.cards[card_id]

        self.selected_cards.clear()
        self.selected_card_id = None
        self.push_history()

    # ---------- Копирование / вставка / дубликат ----------

    def on_copy(self, event=None):
        if not self.selected_cards:
            return
        ids = set(self.selected_cards)
        cards_data = []
        connections_data = []
        sx = sy = 0
        for cid in ids:
            c = self.cards[cid]
            cards_data.append({
                "id": cid,
                "x": c.x,
                "y": c.y,
                "width": c.width,
                "height": c.height,
                "text": c.text,
                "color": c.color,
            })
            sx += c.x
            sy += c.y
        center = (sx / len(ids), sy / len(ids))
        for conn in self.connections:
            if conn.from_id in ids and conn.to_id in ids:
                connections_data.append({
                    "from": conn.from_id,
                    "to": conn.to_id,
                    "label": conn.label,
                    "direction": conn.direction,
                    "from_anchor": conn.from_anchor,
                    "to_anchor": conn.to_anchor,
                })
        self.clipboard = {
            "cards": cards_data,
            "connections": connections_data,
            "center": center,
        }

    def on_paste(self, event=None):
        if self._paste_clipboard_image_as_card(event):
            return
        if not self.clipboard:
            return
        data = self.clipboard
        cards_data = data["cards"]
        connections_data = data["connections"]
        src_cx, src_cy = data["center"]

        dst_cx = self.canvas.canvasx(self.canvas.winfo_width() // 2)
        dst_cy = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        dx = dst_cx - src_cx + 30
        dy = dst_cy - src_cy + 30

        id_map = {}
        for c in cards_data:
            new_x = c["x"] + dx
            new_y = c["y"] + dy
            new_id = self.create_card(
                new_x, new_y,
                c["text"],
                color=c["color"],
                card_id=None,
                width=c["width"],
                height=c["height"],
            )
            id_map[c["id"]] = new_id

        for conn in connections_data:
            from_new = id_map.get(conn["from"])
            to_new = id_map.get(conn["to"])
            if from_new and to_new:
                self.create_connection(
                    from_new,
                    to_new,
                    label=conn.get("label", ""),
                    direction=conn.get("direction", DEFAULT_CONNECTION_DIRECTION),
                    from_anchor=conn.get("from_anchor"),
                    to_anchor=conn.get("to_anchor"),
                )

        self.select_card(None)
        for nid in id_map.values():
            self.select_card(nid, additive=True)

        self.update_minimap()
        self.push_history()

    def on_duplicate(self, event=None):
        self.on_copy()
        self.on_paste()

    # ---------- Сохранение/загрузка ----------

    def save_board(self):
        data = self.get_board_data()
        if file_io.save_board(data):
            self.saved_history_index = self.history.index
            self.update_unsaved_flag()

    def load_board(self):
        data = file_io.load_board()
        if data is None:
            return

        self.set_board_from_data(data)
        state = self.get_board_data()
        self.history.clear_and_init(state)
        self.push_history()
        self.saved_history_index = self.history.index
        self.update_unsaved_flag()
        self.write_autosave(state)
        self.update_minimap()

    # ---------- Экспорт в PNG (как было раньше) ----------

    def export_png(self):
        file_io.export_png(
            canvas=self.canvas,
            cards=self.cards,
            frames=self.frames,
            connections=self.connections,
            theme=self.theme,
            connection_anchor_fn=self._connection_anchors,
        )

    # ---------- Мини-карта ----------

    def update_minimap(self):
        self.canvas_view.render_minimap(self.cards.values(), self.frames.values())

    def on_minimap_click(self, event):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        if x2 == x1 or y2 == y1:
            return

        width = int(self.minimap.cget("width"))
        height = int(self.minimap.cget("height"))
        scale_x = width / (x2 - x1)
        scale_y = height / (y2 - y1)
        scale = min(scale_x, scale_y)

        board_x = x1 + event.x / scale
        board_y = y1 + event.y / scale

        vx0, vx1 = self.canvas.xview()
        vy0, vy1 = self.canvas.yview()
        view_frac_w = vx1 - vx0
        view_frac_h = vy1 - vy0

        view_width = (x2 - x1) * view_frac_w
        view_height = (y2 - y1) * view_frac_h

        new_view_x1 = board_x - view_width / 2
        new_view_y1 = board_y - view_height / 2

        new_xview = (new_view_x1 - x1) / (x2 - x1)
        new_yview = (new_view_y1 - y1) / (y2 - y1)

        new_xview = max(0.0, min(new_xview, 1.0 - view_frac_w))
        new_yview = max(0.0, min(new_yview, 1.0 - view_frac_h))

        self.canvas.xview_moveto(new_xview)
        self.canvas.yview_moveto(new_yview)
        self.update_minimap()

    # ---------- Переключение темы ----------

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self._apply_theme()
        self._redraw_with_current_theme()
        save_theme_settings(self.theme_name, self.text_colors, self.show_grid)

    # ---------- Закрытие ----------

    def on_close(self):
        if self.unsaved_changes:
            res = messagebox.askyesnocancel(
                "Выход",
                "Есть несохранённые изменения.\n"
                "Сохранить перед выходом?"
            )
            if res is None:
                return
            if res:
                self.save_board()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BoardApp()
    app.run()
