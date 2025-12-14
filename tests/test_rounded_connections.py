from typing import Any, Dict, List

import pytest

from src.board_model import (
    BoardData,
    Card,
    Connection,
    DEFAULT_CONNECTION_CURVATURE,
    DEFAULT_CONNECTION_RADIUS,
)
from src.canvas_view import CanvasView
from src.config import THEMES
from src.history import History


class RecordingCanvas:
    """Minimal canvas stub to record drawing commands for snapshot-style tests."""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.items: Dict[int, Dict[str, Any]] = {}
        self._next_id = 1

    # Geometry helpers used by CanvasView
    def winfo_width(self) -> int:
        return self.width

    def winfo_reqwidth(self) -> int:
        return self.width

    # Drawing API subset
    def create_line(self, *coords: float, **kwargs: Any) -> int:
        item_id = self._next_id
        self._next_id += 1
        self.items[item_id] = {"type": "line", "coords": list(coords), "kwargs": dict(kwargs)}
        return item_id

    def create_text(self, x: float, y: float, **kwargs: Any) -> int:
        item_id = self._next_id
        self._next_id += 1
        self.items[item_id] = {"type": "text", "coords": [x, y], "kwargs": dict(kwargs)}
        return item_id

    def itemconfig(self, item_id: int, **kwargs: Any) -> None:
        if item_id in self.items:
            self.items[item_id]["kwargs"].update(kwargs)

    def coords(self, item_id: int, *coords: float):
        if coords:
            self.items[item_id]["coords"] = list(coords)
        return tuple(self.items[item_id]["coords"])

    def bbox(self, item_id: int):
        # Not needed for current connection tests
        return None

    def delete(self, item_id: int) -> None:
        self.items.pop(item_id, None)

    def config(self, **kwargs: Any) -> None:
        # Compatibility shim
        self.items[0] = self.items.get(0, {}) | {"config": kwargs}

    def tag_lower(self, *_, **__):
        pass

    def tag_raise(self, *_, **__):
        pass


@pytest.fixture
def recording_canvas():
    return RecordingCanvas()


@pytest.fixture
def canvas_view(recording_canvas):
    return CanvasView(recording_canvas, None, THEMES["light"])


def test_connection_serialization_preserves_anchors_and_curvature():
    connection = Connection(
        from_id=7,
        to_id=9,
        label="anchored",
        direction="start",
        style="rounded",
        radius=25.5,
        curvature=-12.0,
        from_anchor="left",
        to_anchor="bottom",
    )

    primitive = connection.to_primitive()

    assert primitive == {
        "from": 7,
        "to": 9,
        "label": "anchored",
        "direction": "start",
        "style": "rounded",
        "radius": 25.5,
        "curvature": -12.0,
        "from_anchor": "left",
        "to_anchor": "bottom",
    }

    restored = Connection.from_primitive(primitive)
    assert restored == connection


def test_connection_from_primitive_normalizes_invalid_values():
    payload = {
        "from": 1,
        "to": 2,
        "direction": "sideways",
        "style": "squiggly",
        "radius": None,
        "curvature": "oops",
    }

    restored = Connection.from_primitive(payload)

    assert restored.direction == "end"
    assert restored.style == "straight"
    assert restored.radius == DEFAULT_CONNECTION_RADIUS
    assert restored.curvature == DEFAULT_CONNECTION_CURVATURE


def test_connection_geometry_snapshot_for_curved_path(canvas_view, recording_canvas):
    from_card = Card(id=1, x=80, y=150, width=120, height=80)
    to_card = Card(id=2, x=320, y=170, width=120, height=80)
    connection = Connection(
        from_id=1,
        to_id=2,
        style="rounded",
        radius=40,
        curvature=30,
        direction="start",
        label="demo",
    )

    coords, render_info = canvas_view.connection_geometry(connection, from_card, to_card)
    canvas_view.draw_connection(connection, from_card, to_card)

    expected_coords: List[float] = [
        140.0,
        150.0,
        148.86975696227563,
        157.1749767448645,
        157.94501265868305,
        163.81140552938328,
        167.2257670892221,
        169.77039746466744,
        176.71202025389286,
        174.9130636618281,
        186.4037721526953,
        179.10051523197626,
        196.30102278562947,
        182.19386328622323,
        206.40377215269532,
        184.05421893568,
        216.71202025389283,
        184.54269329145768,
        227.22576708922207,
        183.52039746466744,
        237.94501265868305,
        180.84844256642032,
        248.86975696227563,
        176.38793970782746,
        260.0,
        170.0,
    ]

    line = recording_canvas.items[connection.line_id]
    assert line["kwargs"].get("arrow") == "first"
    assert line["coords"] == pytest.approx(expected_coords)
    assert render_info["midpoint_y"] != render_info["baseline_mid_y"]

    assert connection.label_id is not None
    label = recording_canvas.items[connection.label_id]
    assert label["coords"][0] == pytest.approx(render_info["midpoint_x"])
    assert label["coords"][1] == pytest.approx(render_info["midpoint_y"])


def test_apply_connection_direction_updates_arrow(recording_canvas, canvas_view):
    from_card = Card(id=1, x=0, y=0, width=100, height=60)
    to_card = Card(id=2, x=200, y=0, width=100, height=60)
    connection = Connection(from_id=1, to_id=2)

    canvas_view.draw_connection(connection, from_card, to_card)
    line = recording_canvas.items[connection.line_id]
    assert line["kwargs"].get("arrow") == "last"

    connection.direction = "start"
    canvas_view.apply_connection_direction(connection)
    assert line["kwargs"].get("arrow") == "first"


def test_rounded_connection_end_to_end_flow(recording_canvas, canvas_view):
    cards = {
        1: Card(id=1, x=80, y=120, width=120, height=80),
        2: Card(id=2, x=360, y=140, width=120, height=80),
    }

    initial_connection = Connection(from_id=1, to_id=2, style="rounded", radius=30, curvature=12)
    history = History()
    initial_board = BoardData(cards=cards, connections=[initial_connection], frames={})
    history.clear_and_init(initial_board.to_primitive())

    edited_connection = Connection(
        from_id=1,
        to_id=2,
        style="rounded",
        radius=45,
        curvature=-18,
        direction="start",
        label="edited",
    )
    updated_board = BoardData(cards=cards, connections=[edited_connection], frames={})
    history.push(updated_board.to_primitive())

    saved_state = updated_board.to_primitive()
    restored_board = BoardData.from_primitive(saved_state)
    restored_conn = restored_board.connections[0]

    assert restored_conn.style == "rounded"
    assert restored_conn.direction == "start"
    assert restored_conn.radius == 45
    assert restored_conn.curvature == -18

    coords, render_info = canvas_view.connection_geometry(
        restored_conn, restored_board.cards[1], restored_board.cards[2]
    )
    assert len(coords) > 4
    assert render_info["handle_length"] > 0

    handles = canvas_view.connection_handle_positions(
        restored_conn, restored_board.cards[1], restored_board.cards[2]
    )
    assert handles["radius"][0] > handles["start"][0]
    assert handles["curvature"][1] != pytest.approx(render_info["baseline_mid_y"])

    class DummyApp:
        def __init__(self):
            self.applied: list[Dict[str, Any]] = []

        def set_board_from_data(self, data: Dict[str, Any]):
            self.applied.append(data)

    undo_state = history.undo(DummyApp())
    assert undo_state["connections"][0]["style"] == "rounded"
    assert undo_state["connections"][0]["radius"] == 30
