from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Literal

SCHEMA_VERSION = 5
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3, 4, SCHEMA_VERSION}


@dataclass
class Attachment:
    """Метаданные вложения (например, изображения)."""

    id: int
    name: str
    source_type: Literal["file", "clipboard"]
    mime_type: str
    width: int
    height: int
    offset_x: float = 0.0
    offset_y: float = 0.0
    preview_scale: float = 1.0
    storage_path: str | None = None
    data_base64: str | None = None

    def to_primitive(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "preview_scale": self.preview_scale,
            "storage_path": self.storage_path,
            "data_base64": self.data_base64,
        }

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "Attachment":
        return Attachment(
            id=data["id"],
            name=data["name"],
            source_type=data.get("source_type", "file"),
            mime_type=data.get("mime_type", "application/octet-stream"),
            width=data.get("width", 0),
            height=data.get("height", 0),
            offset_x=data.get("offset_x", 0.0),
            offset_y=data.get("offset_y", 0.0),
            preview_scale=data.get("preview_scale", 1.0),
            storage_path=data.get("storage_path"),
            data_base64=data.get("data_base64"),
        )


@dataclass
class Card:
    """
    Логическая модель карточки без привязки к Tkinter.
    Используется и в рантайме, и для сериализации.
    """

    id: int
    x: float
    y: float
    width: float
    height: float
    text: str = ""
    color: str = "#fff9b1"
    attachments: List[Attachment] = field(default_factory=list)

    # UI поля (не сериализуются)
    rect_id: int | None = None
    text_id: int | None = None
    text_bg_id: int | None = None
    image_id: int | None = None
    resize_handle_id: int | None = None
    connect_handles: Dict[str, int | None] = field(default_factory=dict)

    def to_primitive(self) -> Dict[str, Any]:
        """Сериализация карточки в dict для JSON."""

        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "color": self.color,
            "attachments": [a.to_primitive() for a in self.attachments],
        }

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "Card":
        """Десериализация карточки из dict."""

        return Card(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            text=data.get("text", ""),
            color=data.get("color", "#fff9b1"),
            attachments=[Attachment.from_primitive(a) for a in data.get("attachments", [])],
        )


def bulk_update_card_colors(
    cards: Dict[int, Card], card_ids: Iterable[int], color: str
) -> List[int]:
    """
    Обновляет цвет сразу для нескольких карточек и возвращает список
    идентификаторов, которые действительно изменились.
    """

    updated: List[int] = []
    for cid in card_ids:
        card = cards.get(cid)
        if card is None or card.color == color:
            continue
        card.color = color
        updated.append(cid)
    return updated


VALID_CONNECTION_DIRECTIONS = {"start", "end"}
DEFAULT_CONNECTION_DIRECTION = "end"
VALID_CONNECTION_STYLES = {"straight", "rounded", "elbow"}
DEFAULT_CONNECTION_STYLE = "straight"
DEFAULT_CONNECTION_RADIUS = 0.0
DEFAULT_CONNECTION_CURVATURE = 0.0


@dataclass
class Connection:
    """
    Логическая модель связи между карточками.
    """

    from_id: int
    to_id: int
    label: str = ""
    direction: str = DEFAULT_CONNECTION_DIRECTION
    style: str = DEFAULT_CONNECTION_STYLE
    radius: float = DEFAULT_CONNECTION_RADIUS
    curvature: float = DEFAULT_CONNECTION_CURVATURE

    from_anchor: str | None = None
    to_anchor: str | None = None

    # UI поля (не сериализуются)
    line_id: int | None = None
    label_id: int | None = None
    start_handle_id: int | None = None
    end_handle_id: int | None = None
    radius_handle_id: int | None = None
    curvature_handle_id: int | None = None

    def to_primitive(self) -> Dict[str, Any]:
        """Сериализация связи в dict для JSON."""

        payload = {
            "from": self.from_id,
            "to": self.to_id,
            "label": self.label,
            "direction": self.direction,
            "style": self.style,
            "radius": self.radius,
            "curvature": self.curvature,
        }
        if self.from_anchor is not None:
            payload["from_anchor"] = self.from_anchor
        if self.to_anchor is not None:
            payload["to_anchor"] = self.to_anchor
        return payload

    @staticmethod
    def _normalize_direction(direction: str | None) -> str:
        if direction in VALID_CONNECTION_DIRECTIONS:
            return direction
        return DEFAULT_CONNECTION_DIRECTION

    @staticmethod
    def _normalize_style(style: str | None) -> str:
        if style in VALID_CONNECTION_STYLES:
            return style
        return DEFAULT_CONNECTION_STYLE

    @staticmethod
    def _normalize_float(value: Any, default: float) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "Connection":
        """Десериализация связи из dict, поддерживает старые ключи."""

        from_raw = data.get("from", data.get("from_id"))
        to_raw = data.get("to", data.get("to_id"))
        if from_raw is None or to_raw is None:
            raise ValueError("Connection data is missing required endpoints")

        return Connection(
            from_id=from_raw,
            to_id=to_raw,
            label=data.get("label", ""),
            direction=Connection._normalize_direction(data.get("direction")),
            style=Connection._normalize_style(data.get("style")),
            radius=Connection._normalize_float(
                data.get("radius"), DEFAULT_CONNECTION_RADIUS
            ),
            curvature=Connection._normalize_float(
                data.get("curvature"), DEFAULT_CONNECTION_CURVATURE
            ),
            from_anchor=data.get("from_anchor"),
            to_anchor=data.get("to_anchor"),
        )

    def toggle_direction(self) -> None:
        self.direction = "start" if self.direction == "end" else "end"


@dataclass
class Frame:
    """
    Логическая модель рамки (группы карточек).
    """

    id: int
    x1: float
    y1: float
    x2: float
    y2: float
    title: str = "Группа"
    collapsed: bool = False

    # UI поля (не сериализуются)
    rect_id: int | None = None
    title_id: int | None = None
    resize_handles: Dict[str, int | None] = field(default_factory=dict)

    def to_primitive(self) -> Dict[str, Any]:
        """Сериализация рамки в dict для JSON."""

        return {
            "id": self.id,
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "title": self.title,
            "collapsed": self.collapsed,
        }

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "Frame":
        """Десериализация рамки из dict."""

        return Frame(
            id=data["id"],
            x1=data["x1"],
            y1=data["y1"],
            x2=data["x2"],
            y2=data["y2"],
            title=data.get("title", "Группа"),
            collapsed=data.get("collapsed", False),
        )


@dataclass
class BoardData:
    """
    Полный снимок доски: карточки, связи, рамки.
    """
    cards: Dict[int, Card]
    connections: List[Connection]
    frames: Dict[int, Frame]

    def to_primitive(self) -> Dict[str, Any]:
        """
        Преобразовать в чистый dict для JSON-сериализации.
        Добавляем schema_version и явно раскладываем поля.
        """
        return {
            "schema_version": SCHEMA_VERSION,
            "cards": [c.to_primitive() for c in self.cards.values()],
            "connections": [conn.to_primitive() for conn in self.connections],
            "frames": [f.to_primitive() for f in self.frames.values()],
        }

    @staticmethod
    def from_primitive(data: Dict[str, Any]) -> "BoardData":
        """
        Восстановить BoardData из dict (например, после json.load()).
        Поддерживает старые и новые форматы connections.
        Ожидаемый формат:

        {
          "schema_version": 2,
          "cards": [
            {
              "id": int,
              "x": float,
              "y": float,
              "width": float,
              "height": float,
              "text": str,
              "color": str,
              "attachments": [
                {
                  "id": int,
                  "name": str,
                  "source_type": "file" | "clipboard",
                  "mime_type": str,
                  "width": int,
                  "height": int,
                  "offset_x": float,
                  "offset_y": float,
                  "storage_path": str | null,
                  "data_base64": str | null
                }, ...
              ]
            }, ...
          ],
          "connections": [
            {
              "from": int,
              "to": int,
              "label": str,
              "direction": "start" | "end",
              "style": "straight" | "rounded",
              "radius": float,
              "curvature": float
            }, ...
          ],
          "frames": [
            {
              "id": int,
              "x1": float,
              "y1": float,
              "x2": float,
              "y2": float,
              "title": str,
              "collapsed": bool
            }, ...
          ]
        }
        """
        # Карточки
        cards: Dict[int, Card] = {}
        for c in data.get("cards", []):
            card = Card.from_primitive(c)
            cards[card.id] = card

        # Связи (поддержка старых ключей from_id/to_id)
        connections: List[Connection] = []
        for c in data.get("connections", []):
            try:
                connections.append(Connection.from_primitive(c))
            except ValueError:
                # Битые записи пропускаем, чтобы не падать на старых файлах
                continue

        # Рамки
        frames: Dict[int, Frame] = {}
        for f in data.get("frames", []):
            frame = Frame.from_primitive(f)
            frames[frame.id] = frame

        return BoardData(cards=cards, connections=connections, frames=frames)
