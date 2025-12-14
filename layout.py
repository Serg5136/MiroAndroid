import tkinter as tk
from typing import Optional

from .sidebar import SidebarFactory
from .tooltips import add_canvas_tooltip, add_tooltip
from .events import EventBinder


class ToolbarFactory:
    def create(self, app) -> tk.Frame:
        toolbar = tk.Frame(app.root, bg="#e0e0e0", height=32)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="new")

        btn_undo_toolbar = tk.Button(
            toolbar,
            text="⟲ Отменить",
            command=app.on_undo,
        )
        btn_undo_toolbar.pack(side="left", padx=(8, 2), pady=4)
        app.btn_undo_toolbar = btn_undo_toolbar
        add_tooltip(btn_undo_toolbar, "Отменить последнее действие")

        btn_redo_toolbar = tk.Button(
            toolbar,
            text="⟳ Повторить",
            command=app.on_redo,
        )
        btn_redo_toolbar.pack(side="left", padx=2, pady=4)
        app.btn_redo_toolbar = btn_redo_toolbar
        add_tooltip(btn_redo_toolbar, "Повторить отменённое действие")

        btn_attach_image = tk.Button(
            toolbar,
            text="📎 Прикрепить к карточке",
            command=app.attach_image_from_file,
        )
        btn_attach_image.pack(side="left", padx=(10, 2), pady=4)
        add_tooltip(
            btn_attach_image,
            "Прикрепить файл-изображение к выделенной карточке без создания новой",
        )

        btn_text_color = tk.Button(
            toolbar,
            text="🎨 Цвет текста",
            command=app.change_text_color,
        )
        btn_text_color.pack(side="left", padx=2, pady=4)
        add_tooltip(btn_text_color, "Изменить цвет текста карточек для текущей темы")

        size_frame = tk.Frame(toolbar, bg="#e0e0e0")
        size_frame.pack(side="left", padx=(12, 2), pady=4)

        tk.Label(size_frame, text="Ширина:", bg="#e0e0e0").grid(row=0, column=0, padx=(0, 4))
        spn_width = tk.Spinbox(
            size_frame,
            from_=60,
            to=1200,
            width=6,
            textvariable=app.var_card_width,
        )
        spn_width.grid(row=0, column=1, padx=(0, 8))
        add_tooltip(spn_width, "Задайте ширину карточки в пикселях")

        tk.Label(size_frame, text="Высота:", bg="#e0e0e0").grid(row=0, column=2, padx=(0, 4))
        spn_height = tk.Spinbox(
            size_frame,
            from_=40,
            to=1200,
            width=6,
            textvariable=app.var_card_height,
        )
        spn_height.grid(row=0, column=3, padx=(0, 8))
        add_tooltip(spn_height, "Задайте высоту карточки в пикселях")

        btn_apply_size = tk.Button(
            size_frame,
            text="Применить",
            command=app.apply_card_size_from_controls,
        )
        btn_apply_size.grid(row=0, column=4)
        add_tooltip(btn_apply_size, "Применить указанные ширину и высоту к выбранным карточкам")
        return toolbar


class CanvasFactory:
    def create_canvas(self, app) -> tk.Canvas:
        canvas = tk.Canvas(app.root, bg=app.theme["bg"])
        canvas.grid(row=1, column=0, sticky="nsew")
        canvas.config(scrollregion=(0, 0, 4000, 4000))
        return canvas


class MinimapFactory:
    def create(self, app) -> tk.Frame:
        container = tk.Frame(app.canvas, bg="#f8f8f8", highlightthickness=1, highlightbackground="#cccccc")
        container.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

        minimap_label = tk.Label(
            container, text="Мини карта", bg="#f8f8f8", font=("Arial", 12, "bold")
        )
        minimap_label.pack(fill="x", padx=8, pady=(8, 4))

        app.minimap = tk.Canvas(
            container,
            width=240,
            height=160,
            bg=app.theme["minimap_bg"],
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        app.minimap.pack(padx=8, pady=(0, 10))
        app.minimap.bind("<Button-1>", app.on_minimap_click)
        add_tooltip(app.minimap, "Нажмите, чтобы переместить вид по доске")
        add_canvas_tooltip(app.minimap, "minimap_card", "Карточка на доске")
        add_canvas_tooltip(app.minimap, "minimap_frame", "Рамка на доске")
        add_canvas_tooltip(app.minimap, "minimap_viewport", "Текущая область просмотра")

        add_tooltip(
            minimap_label,
            text=(
                "Подсказки:\n"
                "— Двойной клик по пустому месту: новая карточка\n"
                "— Двойной клик по карточке: редактировать текст\n"
                "— Двойной клик по связи: текст связи\n"
                "— ЛКМ по карточке: выбрать, перетаскивать\n"
                "— ЛКМ по пустому месту + движение: прямоугольное выделение\n"
                "— ЛКМ по связи: выбрать (Delete — удалить, Ctrl+Shift+D — направление)\n"
                "— Колёсико мыши: зум\n"
                "— Средняя кнопка: панорамирование\n"
                "— Правая кнопка: контекстное меню\n"
                "— Ctrl+Z / Ctrl+Y: отмена / повтор\n"
                "— Ctrl+C / Ctrl+V: копирование / вставка\n"
                "— Ctrl+D: дубликат\n"
                "— Delete: удалить выбранные карточки\n"
                "— Рамка: перетаскивание двигает и карточки внутри\n"
                "— Из карточки: кружок справа — перетягиваем на другую\n"
                "   карточку, чтобы соединить\n"
                "— Квадрат внизу справа — изменение размера карточки"
            ),
        )

        return container


class LayoutBuilder:
    def __init__(
        self,
        toolbar_factory: Optional[ToolbarFactory] = None,
        sidebar_factory: Optional[SidebarFactory] = None,
        canvas_factory: Optional[CanvasFactory] = None,
        minimap_factory: Optional[MinimapFactory] = None,
        events_binder: Optional[EventBinder] = None,
    ):
        self.toolbar_factory = toolbar_factory or ToolbarFactory()
        self.sidebar_factory = sidebar_factory or SidebarFactory()
        self.canvas_factory = canvas_factory or CanvasFactory()
        self.minimap_factory = minimap_factory or MinimapFactory()
        self.events_binder = events_binder or EventBinder()

    def configure_root_grid(self, root: tk.Tk) -> None:
        root.rowconfigure(0, weight=0)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)

    def build(self, app) -> None:
        self.configure_root_grid(app.root)
        self.toolbar_factory.create(app)
        app.canvas = self.canvas_factory.create_canvas(app)
        self.minimap_factory.create(app)
        self.sidebar_factory.create(app)
        self.events_binder.bind(app)
