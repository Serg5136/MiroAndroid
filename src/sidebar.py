import tkinter as tk

from .tooltips import add_tooltip


class SidebarFactory:
    def create(self, app) -> tk.Frame:
        sidebar = tk.Frame(app.root, width=260, bg="#f0f0f0")
        sidebar.grid(row=1, column=1, sticky="ns")
        sidebar.grid_propagate(False)

        controls_frame = tk.Frame(sidebar, bg="#f0f0f0")

        collapse_button = tk.Button(
            sidebar,
            text="Свернуть управление ▴",
            takefocus=True,
            highlightthickness=1,
            highlightbackground="#999999",
            highlightcolor="#333333",
        )
        collapse_button.pack(fill="x", padx=10, pady=(10, 5))
        controls_frame.pack(fill="both", expand=True)

        collapse_button.aria_controls = "manage_section"
        collapse_button.aria_expanded = tk.BooleanVar(value=True)

        manage_section = tk.Frame(controls_frame, bg="#f0f0f0")
        manage_section.pack(fill="both", expand=False)
        other_sections = tk.Frame(controls_frame, bg="#f0f0f0")
        other_sections.pack(fill="both", expand=True)

        def toggle_sidebar():
            if manage_section.winfo_ismapped():
                manage_section.pack_forget()
                collapse_button.config(text="Показать управление ▾")
                collapse_button.aria_expanded.set(False)
            else:
                manage_section.pack(fill="both", expand=False, before=other_sections)
                collapse_button.config(text="Свернуть управление ▴")
                collapse_button.aria_expanded.set(True)

        collapse_button.configure(command=toggle_sidebar)
        collapse_button.bind("<Return>", lambda event: toggle_sidebar())
        collapse_button.bind("<space>", lambda event: toggle_sidebar())
        add_tooltip(
            collapse_button,
            "Свернуть или развернуть панель управления (доступно с клавиатуры)",
        )

        btn_add = tk.Button(manage_section, text="Добавить карточку",
                            command=app.add_card_dialog)
        btn_add.pack(fill="x", padx=10, pady=5)
        app.btn_add_card = btn_add
        add_tooltip(btn_add, "Создать новую карточку на холсте")

        btn_color = tk.Button(manage_section, text="Изменить цвет",
                              command=app.change_color)
        btn_color.pack(fill="x", padx=10, pady=5)
        app.btn_change_color = btn_color
        add_tooltip(btn_color, "Изменить цвет выделенной карточки")

        btn_connect = tk.Button(manage_section, text="Соединить карточки (режим)",
                                command=app.toggle_connect_mode)
        btn_connect.pack(fill="x", padx=10, pady=5)
        app.btn_connect_mode = btn_connect
        app.btn_connect_mode_default_bg = btn_connect.cget("bg")
        app.btn_connect_mode_default_text = btn_connect.cget("text")
        add_tooltip(btn_connect, "Включить режим соединения карточек")

        btn_edit = tk.Button(manage_section, text="Редактировать текст",
                             command=app.edit_card_text_dialog)
        btn_edit.pack(fill="x", padx=10, pady=5)
        app.btn_edit_text = btn_edit
        add_tooltip(btn_edit, "Изменить текст выделенной карточки")

        btn_delete = tk.Button(manage_section, text="Удалить карточку(и) (Del)",
                               command=app.delete_selected_cards)
        btn_delete.pack(fill="x", padx=10, pady=5)
        app.btn_delete_cards = btn_delete
        add_tooltip(btn_delete, "Удалить выбранные карточки")

        btn_add_frame = tk.Button(other_sections, text="Добавить рамку",
                                  command=app.add_frame_dialog)
        btn_add_frame.pack(fill="x", padx=10, pady=5)
        app.btn_add_frame = btn_add_frame
        add_tooltip(btn_add_frame, "Создать новую рамку для группировки")

        btn_toggle_frame = tk.Button(other_sections, text="Свернуть/развернуть рамку",
                                     command=app.toggle_selected_frame_collapse)
        btn_toggle_frame.pack(fill="x", padx=10, pady=5)
        app.btn_toggle_frame = btn_toggle_frame
        add_tooltip(btn_toggle_frame, "Свернуть или развернуть выделенную рамку")

        app.var_file_menu_collapsed = getattr(
            app, "var_file_menu_collapsed", tk.BooleanVar(value=False)
        )

        file_section = tk.Frame(other_sections, bg="#f0f0f0")
        file_section.pack(fill="both", expand=False)

        file_header = tk.Frame(file_section, bg="#f0f0f0")
        file_header.pack(fill="x", pady=(20, 5), padx=10)

        file_collapse_button = tk.Button(
            file_header,
            text="Свернуть «Файл» ▴",
            relief="flat",
            bg="#f0f0f0",
            activebackground="#e0e0e0",
            takefocus=True,
            highlightthickness=1,
            highlightbackground="#999999",
            highlightcolor="#333333",
        )
        file_collapse_button.pack(side="right")

        file_collapse_button.aria_controls = "file_content"
        file_collapse_button.aria_expanded = tk.BooleanVar(value=True)

        file_content = tk.Frame(file_section, bg="#f0f0f0")
        file_content.pack(fill="both", expand=False)

        def toggle_file_section():
            collapsed = not app.var_file_menu_collapsed.get()
            app.var_file_menu_collapsed.set(collapsed)
            if collapsed:
                file_content.pack_forget()
                file_collapse_button.config(text="Показать «Файл» ▾")
                file_collapse_button.aria_expanded.set(False)
            else:
                file_content.pack(fill="both", expand=False)
                file_collapse_button.config(text="Свернуть «Файл» ▴")
                file_collapse_button.aria_expanded.set(True)

        file_collapse_button.configure(command=toggle_file_section)
        file_collapse_button.bind("<Return>", lambda event: toggle_file_section())
        file_collapse_button.bind("<space>", lambda event: toggle_file_section())
        add_tooltip(
            file_collapse_button,
            "Свернуть или открыть раздел «Файл» (можно переключать клавишами)",
        )

        btn_save = tk.Button(file_content, text="Сохранить...",
                             command=app.save_board)
        btn_save.pack(fill="x", padx=10, pady=5)
        add_tooltip(btn_save, "Сохранить текущую доску в файл")

        btn_load = tk.Button(file_content, text="Загрузить...",
                             command=app.load_board)
        btn_load.pack(fill="x", padx=10, pady=5)
        add_tooltip(btn_load, "Загрузить доску из файла")

        btn_export = tk.Button(file_content, text="Экспорт в PNG",
                               command=app.export_png)
        btn_export.pack(fill="x", padx=10, pady=5)
        add_tooltip(btn_export, "Сохранить доску как изображение PNG")

        btn_attach_image = tk.Button(file_content, text="Прикрепить изображение",
                                     command=app.attach_image_from_file)
        btn_attach_image.pack(fill="x", padx=10, pady=5)
        add_tooltip(btn_attach_image, "Добавить изображение к выделенной карточке")

        app.btn_theme = tk.Button(other_sections, text=app.get_theme_button_text(),
                                   command=app.toggle_theme)
        app.btn_theme.pack(fill="x", padx=10, pady=5)
        add_tooltip(app.btn_theme, "Переключить светлую/тёмную тему")

        tk.Label(other_sections, text="Сетка", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(pady=(20, 5))

        chk_show_grid = tk.Checkbutton(
            other_sections,
            text="Показывать сетку",
            variable=app.var_show_grid,
            bg="#f0f0f0",
            command=app.on_toggle_show_grid,
        )
        chk_show_grid.pack(fill="x", padx=10, pady=2)
        add_tooltip(chk_show_grid, "Отобразить или скрыть сетку на холсте")

        chk_snap = tk.Checkbutton(
            other_sections,
            text="Привязка к сетке",
            variable=app.var_snap_to_grid,
            bg="#f0f0f0",
            command=app.on_toggle_snap_to_grid,
        )
        chk_snap.pack(fill="x", padx=10, pady=2)
        add_tooltip(chk_snap, "Включить или выключить привязку карточек к сетке")

        frame_grid = tk.Frame(other_sections, bg="#f0f0f0")
        frame_grid.pack(fill="x", padx=10, pady=2)

        tk.Label(frame_grid, text="Шаг:", bg="#f0f0f0").pack(side="left")

        spn_grid = tk.Spinbox(
            frame_grid,
            from_=5,
            to=200,
            increment=5,
            textvariable=app.var_grid_size,
            width=5,
            command=app.on_grid_size_change,
        )
        spn_grid.pack(side="left", padx=(5, 0))
        spn_grid.bind("<Return>", app.on_grid_size_change)
        spn_grid.bind("<FocusOut>", app.on_grid_size_change)
        add_tooltip(spn_grid, "Изменить шаг сетки (Enter для применения)")

        tk.Label(
            other_sections, text="Свойства связи", bg="#f0f0f0", font=("Arial", 12, "bold")
        ).pack(pady=(20, 5))

        connection_section = tk.Frame(other_sections, bg="#f0f0f0")
        connection_section.pack(fill="x", padx=10, pady=2)

        style_label = tk.Label(connection_section, text="Тип линии:", bg="#f0f0f0")
        style_label.pack(anchor="w")
        add_tooltip(style_label, "Выберите форму линии между карточками")

        style_buttons = tk.Frame(connection_section, bg="#f0f0f0")
        style_buttons.pack(fill="x", pady=(0, 6))

        btn_style_straight = tk.Radiobutton(
            style_buttons,
            text="Прямая",
            variable=app.var_connection_style,
            value="straight",
            bg="#f0f0f0",
            command=app.on_connection_style_change,
        )
        btn_style_straight.pack(side="left", expand=True)
        add_tooltip(btn_style_straight, "Соединить карточки прямой линией")

        btn_style_elbow = tk.Radiobutton(
            style_buttons,
            text="Ломаная",
            variable=app.var_connection_style,
            value="elbow",
            bg="#f0f0f0",
            command=app.on_connection_style_change,
        )
        btn_style_elbow.pack(side="left", expand=True)
        add_tooltip(btn_style_elbow, "Соединить карточки угловой линией с изломом")

        btn_style_rounded = tk.Radiobutton(
            style_buttons,
            text="Закруглённая",
            variable=app.var_connection_style,
            value="rounded",
            bg="#f0f0f0",
            command=app.on_connection_style_change,
        )
        btn_style_rounded.pack(side="left", expand=True)
        add_tooltip(btn_style_rounded, "Плавная линия с закруглением и кривизной")

        app.connection_style_controls = [
            btn_style_straight,
            btn_style_elbow,
            btn_style_rounded,
        ]

        radius_frame = tk.Frame(connection_section, bg="#f0f0f0")
        radius_frame.pack(fill="x")
        tk.Label(radius_frame, text="Радиус:", bg="#f0f0f0").pack(side="left")
        radius_scale = tk.Scale(
            radius_frame,
            from_=0,
            to=300,
            orient="horizontal",
            resolution=1,
            variable=app.var_connection_radius,
            command=app.on_connection_radius_change,
            length=150,
            bg="#f0f0f0",
            highlightthickness=0,
        )
        radius_scale.pack(side="left", padx=(6, 0))
        app.connection_radius_scale = radius_scale
        add_tooltip(radius_scale, "Настройка длины ручек для закруглённой линии связи")

        return sidebar
