"""Утилиты для сохранения, загрузки и экспорта доски."""

from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any, Callable, Dict, Iterable

from tkinter import filedialog, messagebox

from .board_model import SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS


class BoardFileError(Exception):
    """Исключение, описывающее проблемы с содержимым файла доски."""


REQUIRED_KEYS = ("cards", "connections", "frames")


def save_board(board_data: Dict[str, Any]) -> bool:
    """Открывает диалог и сохраняет данные борда в JSON.

    Возвращает ``True`` при успешном сохранении и ``False`` если пользователь
    отменил диалог или произошла ошибка.
    """

    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
    )
    if not filename:
        return False

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(board_data, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл:\n{e}")
        return False


def load_board() -> Dict[str, Any] | None:
    """Читает и валидирует JSON с диска.

    Возвращает словарь с данными или ``None`` если пользователь отменил диалог
    либо данные не прошли валидацию.
    """

    filename = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
    )
    if not filename:
        return None

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except JSONDecodeError as e:
        messagebox.showerror(
            "Ошибка загрузки",
            "Файл не является корректным JSON.\n"
            f"Проверьте содержимое файла. Детали:\n{e}",
        )
        return None
    except OSError as e:
        messagebox.showerror("Ошибка загрузки", f"Не удалось открыть файл:\n{e}")
        return None

    try:
        _validate_board_data(data)
    except BoardFileError as e:
        messagebox.showerror("Ошибка загрузки", str(e))
        return None

    return data


def export_png(
    *,
    canvas,
    cards: Dict[int, Any],
    frames: Dict[int, Any],
    connections: Iterable[Any],
    theme: Dict[str, Any],
    connection_anchor_fn: Callable[[Any, Any, Any | None], tuple[float, float, float, float]],
) -> bool:
    """Экспортирует содержимое доски в PNG через диалог выбора файла."""

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        messagebox.showerror(
            "Экспорт в PNG",
            "Для экспорта нужен пакет Pillow.\n"
            "Установите его командой:\n\npip install pillow",
        )
        return False

    connections_list = list(connections)
    if not cards and not frames and not connections_list:
        messagebox.showinfo("Экспорт в PNG", "Нечего экспортировать: борд пуст.")
        return False

    filename = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG изображения", "*.png"), ("Все файлы", "*.*")],
    )
    if not filename:
        return False

    items_bbox = None

    def update_bbox(bbox, x1, y1, x2, y2):
        if bbox is None:
            return (x1, y1, x2, y2)
        bx1, by1, bx2, by2 = bbox
        return (min(bx1, x1), min(by1, y1), max(bx2, x2), max(by2, y2))

    for frame in frames.values():
        coords = canvas.coords(frame.rect_id)
        if coords:
            fx1, fy1, fx2, fy2 = coords
            items_bbox = update_bbox(items_bbox, fx1, fy1, fx2, fy2)
    for card in cards.values():
        cx1 = card.x - card.width / 2
        cy1 = card.y - card.height / 2
        cx2 = card.x + card.width / 2
        cy2 = card.y + card.height / 2
        items_bbox = update_bbox(items_bbox, cx1, cy1, cx2, cy2)
    for conn in connections_list:
        coords = canvas.coords(conn.line_id)
        if coords and len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            items_bbox = update_bbox(items_bbox, x1, y1, x2, y2)

    if items_bbox is None:
        messagebox.showinfo("Экспорт в PNG", "Не найдено объектов для экспорта.")
        return False

    x1, y1, x2, y2 = items_bbox
    padding = 20
    width = int(x2 - x1 + 2 * padding)
    height = int(y2 - y1 + 2 * padding)
    if width <= 0 or height <= 0:
        messagebox.showerror("Экспорт в PNG", "Некорректный размер изображения.")
        return False

    img = Image.new("RGB", (width, height), theme["bg"])
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    def map_xy(x, y):
        return (x - x1 + padding, y - y1 + padding)

    for frame in frames.values():
        coords = canvas.coords(frame.rect_id)
        if not coords:
            continue
        fx1, fy1, fx2, fy2 = coords
        mx1, my1 = map_xy(fx1, fy1)
        mx2, my2 = map_xy(fx2, fy2)
        collapsed = frame.collapsed
        fill = theme["frame_collapsed_bg"] if collapsed else theme["frame_bg"]
        outline = theme["frame_outline"]
        draw.rectangle([mx1, my1, mx2, my2], outline=outline, fill=fill)
        title = frame.title
        if title:
            draw.text((mx1 + 8, my1 + 8), title, font=font, fill=theme["text"])

    for conn in connections_list:
        from_card = cards.get(conn.from_id)
        to_card = cards.get(conn.to_id)
        if not from_card or not to_card:
            continue
        sx, sy, tx, ty = connection_anchor_fn(from_card, to_card, conn)
        msx, msy = map_xy(sx, sy)
        mtx, mty = map_xy(tx, ty)
        draw.line([msx, msy, mtx, mty], fill=theme["connection"], width=2)
        if conn.label:
            mx = (msx + mtx) / 2
            my = (msy + mty) / 2
            try:
                draw.text(
                    (mx, my),
                    conn.label,
                    font=font,
                    fill=theme["connection_label"],
                    anchor="mm",
                )
            except TypeError:
                draw.text((mx, my), conn.label, font=font, fill=theme["connection_label"])

    for card in cards.values():
        cx1 = card.x - card.width / 2
        cy1 = card.y - card.height / 2
        cx2 = card.x + card.width / 2
        cy2 = card.y + card.height / 2
        mx1, my1 = map_xy(cx1, cy1)
        mx2, my2 = map_xy(cx2, cy2)
        fill = card.color or theme["card_default"]
        outline = theme["card_outline"]
        draw.rectangle([mx1, my1, mx2, my2], fill=fill, outline=outline)
        text = card.text
        if text:
            tx, ty = map_xy(card.x, card.y)
            try:
                draw.multiline_text(
                    (tx, ty),
                    text,
                    font=font,
                    fill=theme["text"],
                    align="center",
                    anchor="mm",
                )
            except TypeError:
                draw.multiline_text(
                    (mx1 + 5, my1 + 5), text, font=font, fill=theme["text"]
                )

    try:
        img.save(filename, "PNG")
    except OSError as e:
        messagebox.showerror("Ошибка экспорта", f"Не удалось сохранить PNG:\n{e}")
        return False

    messagebox.showinfo("Экспорт в PNG", "Изображение сохранено:\n" + filename)
    return True


def _validate_board_data(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise BoardFileError(
            "Файл не соответствует формату доски: ожидается JSON-объект с данными."
        )

    version = data.get("schema_version")
    if version is None:
        raise BoardFileError(
            "Файл не содержит информацию о версии схемы (schema_version)."
        )
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise BoardFileError(
            "Неподдерживаемая версия схемы: "
            f"{version}. Ожидается один из: {sorted(SUPPORTED_SCHEMA_VERSIONS)}."
        )

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        missing_str = ", ".join(missing)
        raise BoardFileError(
            f"В файле отсутствуют обязательные разделы: {missing_str}."
        )

    list_checks = {
        "cards": list,
        "connections": list,
        "frames": list,
    }
    bad_types = [
        key for key, expected_type in list_checks.items() if not isinstance(data[key], expected_type)
    ]
    if bad_types:
        readable = ", ".join(bad_types)
        raise BoardFileError(
            f"Некорректный формат разделов: ожидаются списки для {readable}."
        )
