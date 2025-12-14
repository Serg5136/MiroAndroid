import tkinter as tk

from src.board_model import Card, Connection
from src.canvas_view import CanvasView
from src.config import THEMES


def _make_card(cid: int, x: float, y: float) -> Card:
    return Card(id=cid, x=x, y=y, width=120, height=80)


def test_rounded_connection_curves_without_intersections(tk_root):
    canvas = tk.Canvas(tk_root, width=400, height=400)
    view = CanvasView(canvas, None, THEMES["light"])

    from_card = _make_card(1, 60, 200)
    to_card = _make_card(2, 340, 220)
    connection = Connection(
        from_id=1, to_id=2, style="rounded", radius=60, curvature=30
    )

    coords, info = view.connection_geometry(connection, from_card, to_card)

    assert len(coords) > 4
    assert not view._polyline_self_intersects(coords)

    # The curved route should deviate from the straight baseline midpoint
    assert info["midpoint_y"] != info["baseline_mid_y"]


def test_rounded_connection_falls_back_to_straight_when_radius_impossible(tk_root):
    canvas = tk.Canvas(tk_root, width=200, height=200)
    view = CanvasView(canvas, None, THEMES["light"])

    from_card = _make_card(1, 80, 100)
    to_card = _make_card(2, 140, 100)
    connection = Connection(from_id=1, to_id=2, style="rounded", radius=500)

    coords, info = view.connection_geometry(connection, from_card, to_card)

    assert coords == (from_card.x + from_card.width / 2, from_card.y, to_card.x - to_card.width / 2, to_card.y)
    assert info["handle_length"] == 0.0


def test_elbow_connection_route_is_orthogonal_and_non_intersecting(tk_root):
    canvas = tk.Canvas(tk_root, width=300, height=300)
    view = CanvasView(canvas, None, THEMES["light"])

    from_card = _make_card(1, 50, 50)
    to_card = _make_card(2, 180, 110)
    connection = Connection(from_id=1, to_id=2, style="elbow")

    coords, _ = view.connection_geometry(connection, from_card, to_card)
    points = list(zip(coords[0::2], coords[1::2]))

    assert len(points) == 3
    # Expect horizontal first because dx > dy
    assert points[1][0] == points[2][0]
    assert points[0][1] == points[1][1]
    assert not view._polyline_self_intersects(coords)
