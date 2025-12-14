mini-miro-board/
├─ app.py                    # Точка входа для запуска приложения
├─ src/                      # Основной код приложения (пакет src)
│  ├─ __init__.py            # Определяет пакет
│  ├─ autosave.py            # Сервис автосохранения
│  ├─ board_model.py         # Модель данных (Card, Frame, Connection, BoardData)
│  ├─ canvas_view.py         # Отрисовка карточек, рамок и связей на Canvas
│  ├─ config.py              # Темы и загрузка/сохранение настроек
│  ├─ connect_controller.py  # Управление режимом соединения карточек
│  ├─ drag_controller.py     # Логика перетаскивания карточек и рамок
│  ├─ events.py              # Константы биндингов и EventBinder
│  ├─ files.py               # Сохранение/загрузка доски и экспорт
│  ├─ history.py             # История действий и команды
│  ├─ layout.py              # Построение тулбара и Canvas
│  ├─ main.py                # BoardApp и основная логика UI
│  ├─ selection_controller.py# Работа с выделением карточек
│  ├─ sidebar.py             # Сайдбар и вспомогательные контролы
│  └─ tooltips.py            # Подсказки для элементов интерфейса
│
├─ tests/                    # Автотесты
│  ├─ conftest.py
│  ├─ test_attachment_handlers.py
│  ├─ test_board_model.py
│  ├─ test_connection_routes.py
│  ├─ test_dummy.py
│  ├─ test_grid_settings.py
│  ├─ test_history.py
│  ├─ test_rounded_connections.py
│  └─ test_sidebar_file_menu.py
│
├─ attachments/              # Пример ресурсов вложений
│  ├─ 1-1.jpg
│  └─ 4-1.png
│
├─ _mini_miro_autosave.json  # Пример сохранения борда
├─ README.md
├─ requirements.txt          # Зависимости (Pillow + опциональные)
├─ LICENSE                   # Лицензия
└─ ё1.json                   # Пример сохранённой доски
