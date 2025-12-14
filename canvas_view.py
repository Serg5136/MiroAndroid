import math
import tkinter as tk
from typing import Dict, Iterable, Sequence

from .board_model import (
    Card,
    Connection,
    Frame,
    DEFAULT_CONNECTION_CURVATURE,
    DEFAULT_CONNECTION_RADIUS,
    DEFAULT_CONNECTION_STYLE,
)


class CanvasView:
    def __init__(self, canvas: tk.Canvas, minimap: tk.Canvas | None, theme: Dict[str, str]):
        self.text_padding_min = 8
        self.text_padding_max = 16
        self.text_margin_min = 2
        self.text_margin_max = 6
        self.base_font_size = 10
        self.canvas = canvas
        self.minimap = minimap
        self.theme = theme

    def _responsive_scale(self, card: Card) -> float:
        """Return scale factor for compact layouts (akin to a mobile breakpoint)."""

        canvas_width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        if canvas_width and canvas_width <= 480:
            return 0.85
        if card.width <= 240:
            return 0.9
        return 1.0

    def _compute_spacing(self, card: Card, scale: float) -> tuple[float, float]:
        """Return adaptive (padding, margin) for the given card."""

        padding = max(
            self.text_padding_min * scale,
            min(card.width * 0.05, self.text_padding_max * scale),
        )
        margin_base = padding * 0.4
        margin = max(self.text_margin_min * scale, min(margin_base, self.text_margin_max * scale))
        return padding, margin

    def set_theme(self, theme: Dict[str, str]) -> None:
        self.theme = theme
        self.canvas.config(bg=self.theme["bg"])
        if self.minimap:
            self.minimap.config(bg=self.theme["minimap_bg"])

    def compute_card_layout(self, card: Card) -> Dict[str, float]:
        """Calculate positions for text and image areas inside the card."""

        scale = self._responsive_scale(card)
        padding, margin = self._compute_spacing(card, scale)
        y1 = card.y - card.height / 2
        font_size = max(8, int(self.base_font_size * scale))
        font = ("Arial", font_size, "bold")
        text_width = max(card.width - 2 * padding, 20)

        measure_id = self.canvas.create_text(
            0,
            0,
            text=card.text or " ",
            width=text_width,
            anchor="nw",
            font=font,
            state="hidden",
        )
        bbox = self.canvas.bbox(measure_id)
        self.canvas.delete(measure_id)
        text_height = (bbox[3] - bbox[1]) if bbox else max(font_size + 4, 14)

        text_top = y1 + padding
        image_top = text_top + text_height + padding
        image_height = max(card.height - (image_top - y1) - padding, 0)
        if scale < 1.0:
            image_height = min(image_height, card.height * 0.6)
        image_width = max(card.width - 2 * padding, 0)

        return {
            "text_top": text_top,
            "text_width": text_width,
            "image_top": image_top,
            "image_height": image_height,
            "image_width": image_width,
            "padding": padding,
            "margin": margin,
            "font": font,
        }

    def apply_card_layout(self, card: Card, layout: Dict[str, float]) -> None:
        text_width = layout["text_width"]
        text_top = layout["text_top"]
        font = layout.get("font")

        if card.text_id:
            self.canvas.itemconfig(
                card.text_id,
                width=text_width,
                anchor="n",
                font=font or ("Arial", self.base_font_size, "bold"),
            )
            self.canvas.coords(card.text_id, card.x, text_top)

        if card.text_bg_id:
            bbox = self.canvas.bbox(card.text_id) if card.text_id else None
            if bbox:
                margin = layout.get("margin", self.text_margin_min)
                self.canvas.coords(
                    card.text_bg_id,
                    bbox[0] - margin,
                    bbox[1] - margin,
                    bbox[2] + margin,
                    bbox[3] + margin,
                )
                self.canvas.tag_lower(card.text_bg_id, card.text_id)

    def draw_grid(self, grid_size: int, visible: bool = True) -> None:
        self.canvas.delete("grid")
        spacing = grid_size
        x_max = 4000
        y_max = 4000
        state = "normal" if visible else "hidden"
        for x in range(0, x_max + 1, spacing):
            self.canvas.create_line(
                x,
                0,
                x,
                y_max,
                fill=self.theme["grid"],
                tags=("grid",),
                state=state,
            )
        for y in range(0, y_max + 1, spacing):
            self.canvas.create_line(
                0,
                y,
                x_max,
                y,
                fill=self.theme["grid"],
                tags=("grid",),
                state=state,
            )
        self.canvas.tag_lower("grid")

    def set_grid_visibility(self, visible: bool) -> None:
        state = "normal" if visible else "hidden"
        self.canvas.itemconfigure("grid", state=state)
        if visible:
            self.canvas.tag_lower("grid")

    def draw_card(self, card: Card) -> None:
        x1 = card.x - card.width / 2
        y1 = card.y - card.height / 2
        x2 = card.x + card.width / 2
        y2 = card.y + card.height / 2

        rect_id = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=card.color,
            outline=self.theme["card_outline"],
            width=1.5,
            tags=("card", f"card_{card.id}"),
        )
        layout = self.compute_card_layout(card)
        font = layout.get("font", ("Arial", self.base_font_size, "bold"))
        text_id = self.canvas.create_text(
            card.x,
            layout["text_top"],
            text=card.text,
            width=layout["text_width"],
            anchor="n",
            font=font,
            fill=self.theme["text"],
            tags=("card_text", f"card_{card.id}"),
        )
        text_bbox = self.canvas.bbox(text_id) or (
            card.x,
            layout["text_top"],
            card.x,
            layout["text_top"] + 14,
        )
        margin = layout.get("margin", self.text_margin_min)
        text_bg_id = self.canvas.create_rectangle(
            text_bbox[0] - margin,
            text_bbox[1] - margin,
            text_bbox[2] + margin,
            text_bbox[3] + margin,
            fill=card.color,
            outline="",
            tags=("card_text_bg", f"card_{card.id}"),
        )
        self.canvas.tag_lower(text_bg_id, text_id)

        card.rect_id = rect_id
        card.text_id = text_id
        card.text_bg_id = text_bg_id

    def update_card_color(self, card: Card) -> None:
        if card.rect_id:
            self.canvas.itemconfig(card.rect_id, fill=card.color)
        if card.text_bg_id:
            self.canvas.itemconfig(card.text_bg_id, fill=card.color)

    def draw_frame(self, frame: Frame) -> None:
        rect_id = self.canvas.create_rectangle(
            frame.x1,
            frame.y1,
            frame.x2,
            frame.y2,
            fill=self.theme["frame_collapsed_bg"] if frame.collapsed else self.theme["frame_bg"],
            outline=self.theme["frame_outline"],
            width=2,
            dash=(3, 3) if frame.collapsed else (),
            tags=("frame", f"frame_{frame.id}"),
        )
        title_id = self.canvas.create_text(
            frame.x1 + 10,
            frame.y1 + 15,
            text=frame.title,
            anchor="w",
            font=("Arial", 10, "bold"),
            fill=self.theme["text"],
            tags=("frame_title", f"frame_{frame.id}"),
        )

        self.canvas.tag_lower(rect_id)
        self.canvas.tag_lower("grid")

        frame.rect_id = rect_id
        frame.title_id = title_id

    def card_handle_positions(self, card: Card) -> Dict[str, tuple[float, float]]:
        half_w = card.width / 2
        half_h = card.height / 2
        return {
            "n": (card.x, card.y - half_h),
            "e": (card.x + half_w, card.y),
            "s": (card.x, card.y + half_h),
            "w": (card.x - half_w, card.y),
        }

    def _auto_anchors(self, from_card: Card, to_card: Card) -> tuple[str, str]:
        dx = to_card.x - from_card.x
        dy = to_card.y - from_card.y
        if abs(dx) > abs(dy):
            return ("e" if dx > 0 else "w", "w" if dx > 0 else "e")
        return ("s" if dy > 0 else "n", "n" if dy > 0 else "s")

    def _resolve_anchor(
        self, card: Card, preferred: str | None, fallback: str
    ) -> tuple[str, tuple[float, float]]:
        positions = self.card_handle_positions(card)
        anchor = preferred if preferred in positions else fallback
        return anchor, positions[anchor]

    def _connection_anchors(
        self, from_card: Card, to_card: Card, connection: Connection | None = None
    ) -> Sequence[float]:
        default_from, default_to = self._auto_anchors(from_card, to_card)
        from_anchor, (sx, sy) = self._resolve_anchor(
            from_card, getattr(connection, "from_anchor", None), default_from
        )
        to_anchor, (tx, ty) = self._resolve_anchor(
            to_card, getattr(connection, "to_anchor", None), default_to
        )

        if connection is not None:
            connection.from_anchor = from_anchor
            connection.to_anchor = to_anchor

        return sx, sy, tx, ty

    def _anchor_direction(self, anchor: str | None, fallback: tuple[float, float]) -> tuple[float, float]:
        directions = {
            "n": (0.0, -1.0),
            "e": (1.0, 0.0),
            "s": (0.0, 1.0),
            "w": (-1.0, 0.0),
        }
        return directions.get(anchor, fallback)

    def _bezier_point(
        self,
        start: tuple[float, float],
        ctrl1: tuple[float, float],
        ctrl2: tuple[float, float],
        end: tuple[float, float],
        t: float,
    ) -> tuple[float, float]:
        inv_t = 1 - t
        x = (
            inv_t**3 * start[0]
            + 3 * inv_t**2 * t * ctrl1[0]
            + 3 * inv_t * t**2 * ctrl2[0]
            + t**3 * end[0]
        )
        y = (
            inv_t**3 * start[1]
            + 3 * inv_t**2 * t * ctrl1[1]
            + 3 * inv_t * t**2 * ctrl2[1]
            + t**3 * end[1]
        )
        return x, y

    def _sample_cubic_bezier(
        self,
        start: tuple[float, float],
        ctrl1: tuple[float, float],
        ctrl2: tuple[float, float],
        end: tuple[float, float],
        *,
        steps: int,
    ) -> list[float]:
        samples: list[float] = []
        for i in range(steps + 1):
            t = i / steps
            x, y = self._bezier_point(start, ctrl1, ctrl2, end, t)
            samples.extend([x, y])
        return samples

    def _segments_intersect(
        self,
        a1: tuple[float, float],
        a2: tuple[float, float],
        b1: tuple[float, float],
        b2: tuple[float, float],
    ) -> bool:
        def _orientation(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

        def _on_segment(p, q, r):
            return (
                min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
                and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
            )

        o1 = _orientation(a1, a2, b1)
        o2 = _orientation(a1, a2, b2)
        o3 = _orientation(b1, b2, a1)
        o4 = _orientation(b1, b2, a2)

        if (o1 == 0 and _on_segment(a1, b1, a2)) or (o2 == 0 and _on_segment(a1, b2, a2)):
            return True
        if (o3 == 0 and _on_segment(b1, a1, b2)) or (o4 == 0 and _on_segment(b1, a2, b2)):
            return True

        return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)

    def _polyline_self_intersects(self, coords: Sequence[float]) -> bool:
        points = list(zip(coords[0::2], coords[1::2]))
        for i in range(len(points) - 1):
            a1, a2 = points[i], points[i + 1]
            for j in range(i + 2, len(points) - 1):
                # Adjacent segments share a point and should not be treated as intersections
                if j == i + 1:
                    continue
                b1, b2 = points[j], points[j + 1]
                if self._segments_intersect(a1, a2, b1, b2):
                    return True
        return False

    def _straight_connection(
        self, connection: Connection, sx: float, sy: float, tx: float, ty: float
    ) -> tuple[Sequence[float], Dict[str, float | bool]]:
        midpoint = ((sx + tx) / 2, (sy + ty) / 2)
        length = math.hypot(tx - sx, ty - sy) or 1.0
        dir_x = (tx - sx) / length
        dir_y = (ty - sy) / length
        return (
            (sx, sy, tx, ty),
            {
                "smooth": False,
                "midpoint_x": midpoint[0],
                "midpoint_y": midpoint[1],
                "normal_x": 0.0,
                "normal_y": 0.0,
                "length": length,
                "start_dir": self._anchor_direction(
                    getattr(connection, "from_anchor", None), (dir_x, dir_y)
                ),
                "handle_length": 0.0,
                "baseline_mid_x": midpoint[0],
                "baseline_mid_y": midpoint[1],
            },
        )

    def _connection_points(
        self, connection: Connection, sx: float, sy: float, tx: float, ty: float
    ) -> tuple[Sequence[float], Dict[str, float | bool]]:
        style = getattr(connection, "style", DEFAULT_CONNECTION_STYLE)

        if style == "elbow":
            dx = tx - sx
            dy = ty - sy
            via_horizontal_first = abs(dx) >= abs(dy)
            if via_horizontal_first:
                corner = (tx, sy)
                start_dir = self._anchor_direction(
                    getattr(connection, "from_anchor", None),
                    (1.0 if dx >= 0 else -1.0, 0.0),
                )
            else:
                corner = (sx, ty)
                start_dir = self._anchor_direction(
                    getattr(connection, "from_anchor", None),
                    (0.0, 1.0 if dy >= 0 else -1.0),
                )

            first_len = abs(corner[0] - sx) + abs(corner[1] - sy)
            second_len = abs(tx - corner[0]) + abs(ty - corner[1])
            total_len = max(first_len + second_len, 1.0)

            half = total_len / 2
            if half <= first_len and first_len:
                ratio = half / first_len
                mid_x = sx + (corner[0] - sx) * ratio
                mid_y = sy + (corner[1] - sy) * ratio
            else:
                remain = half - first_len
                segment_len = max(second_len, 1.0)
                ratio = remain / segment_len
                mid_x = corner[0] + (tx - corner[0]) * ratio
                mid_y = corner[1] + (ty - corner[1]) * ratio

            return (
                (sx, sy, corner[0], corner[1], tx, ty),
                {
                    "smooth": False,
                    "midpoint_x": mid_x,
                    "midpoint_y": mid_y,
                    "normal_x": 0.0,
                    "normal_y": 0.0,
                    "length": total_len,
                    "start_dir": start_dir,
                    "handle_length": 0.0,
                    "baseline_mid_x": mid_x,
                    "baseline_mid_y": mid_y,
                },
            )

        if style != "rounded":
            return self._straight_connection(connection, sx, sy, tx, ty)

        radius = max(getattr(connection, "radius", DEFAULT_CONNECTION_RADIUS), 0.0)
        curvature = getattr(connection, "curvature", DEFAULT_CONNECTION_CURVATURE)

        if radius <= 0 and curvature == 0:
            return self._straight_connection(connection, sx, sy, tx, ty)

        dx = tx - sx
        dy = ty - sy
        length = math.hypot(dx, dy) or 1.0
        dir_x = dx / length
        dir_y = dy / length
        normal_x = -dy / length
        normal_y = dx / length

        handle_base = radius if radius > 0 else length * 0.25
        max_handle_length = length * 0.45
        if radius > 0 and handle_base > max_handle_length:
            return self._straight_connection(connection, sx, sy, tx, ty)

        handle_length = max(length * 0.1, min(handle_base, max_handle_length))
        if handle_length <= 0:
            return self._straight_connection(connection, sx, sy, tx, ty)

        start_dir = self._anchor_direction(getattr(connection, "from_anchor", None), (dir_x, dir_y))
        end_dir_outward = self._anchor_direction(
            getattr(connection, "to_anchor", None), (-dir_x, -dir_y)
        )
        end_dir = (-end_dir_outward[0], -end_dir_outward[1])

        start_ctrl = (sx + start_dir[0] * handle_length, sy + start_dir[1] * handle_length)
        end_ctrl = (tx - end_dir[0] * handle_length, ty - end_dir[1] * handle_length)

        curve_shift = max(-length / 2, min(curvature, length / 2))
        if curve_shift:
            shift_x = normal_x * curve_shift
            shift_y = normal_y * curve_shift
            start_ctrl = (start_ctrl[0] + shift_x, start_ctrl[1] + shift_y)
            end_ctrl = (end_ctrl[0] + shift_x, end_ctrl[1] + shift_y)

        steps = max(12, int(length / 18))
        coords = self._sample_cubic_bezier((sx, sy), start_ctrl, end_ctrl, (tx, ty), steps=steps)
        if self._polyline_self_intersects(coords):
            return self._straight_connection(connection, sx, sy, tx, ty)

        mid_x, mid_y = self._bezier_point((sx, sy), start_ctrl, end_ctrl, (tx, ty), 0.5)

        return coords, {
            "smooth": False,
            "midpoint_x": mid_x,
            "midpoint_y": mid_y,
            "normal_x": normal_x,
            "normal_y": normal_y,
            "length": length,
            "start_dir": start_dir,
            "handle_length": handle_length,
            "baseline_mid_x": (sx + tx) / 2,
            "baseline_mid_y": (sy + ty) / 2,
        }

    def _label_position(
        self, coords: Sequence[float], render_info: Dict[str, float | bool]
    ) -> tuple[float, float]:
        if "midpoint_x" in render_info and "midpoint_y" in render_info:
            return render_info["midpoint_x"], render_info["midpoint_y"]
        if render_info.get("smooth") and len(coords) >= 4:
            return coords[2], coords[3]
        return (coords[0] + coords[-2]) / 2, (coords[1] + coords[-1]) / 2

    def _arrow_for_direction(self, direction: str) -> str:
        return tk.FIRST if direction == "start" else tk.LAST

    def connection_geometry(
        self, connection: Connection, from_card: Card, to_card: Card
    ) -> tuple[Sequence[float], Dict[str, float | bool]]:
        sx, sy, tx, ty = self._connection_anchors(from_card, to_card, connection)
        coords, render_info = self._connection_points(connection, sx, sy, tx, ty)
        render_info["start_x"] = sx
        render_info["start_y"] = sy
        render_info["end_x"] = tx
        render_info["end_y"] = ty
        return coords, render_info

    def connection_handle_positions(
        self, connection: Connection, from_card: Card, to_card: Card
    ) -> Dict[str, tuple[float, float]]:
        coords, render_info = self.connection_geometry(connection, from_card, to_card)
        _ = coords  # keep for potential future use
        sx = render_info.get("start_x", from_card.x)
        sy = render_info.get("start_y", from_card.y)
        tx = render_info.get("end_x", to_card.x)
        ty = render_info.get("end_y", to_card.y)

        midpoint_x = render_info.get("baseline_mid_x", (sx + tx) / 2)
        midpoint_y = render_info.get("baseline_mid_y", (sy + ty) / 2)
        normal_x = render_info.get("normal_x", 0.0)
        normal_y = render_info.get("normal_y", 0.0)
        length = render_info.get("length", math.hypot(tx - sx, ty - sy)) or 1.0
        start_dir = render_info.get("start_dir", (1.0, 0.0))
        handle_length = render_info.get("handle_length", 0.0)
        curvature = getattr(connection, "curvature", DEFAULT_CONNECTION_CURVATURE)

        radius_ctrl = (sx + start_dir[0] * handle_length, sy + start_dir[1] * handle_length)
        curvature_ctrl = (
            midpoint_x + normal_x * max(-length / 2, min(curvature, length / 2)),
            midpoint_y + normal_y * max(-length / 2, min(curvature, length / 2)),
        )

        return {
            "start": (sx, sy),
            "end": (tx, ty),
            "radius": radius_ctrl,
            "curvature": curvature_ctrl,
        }

    def set_connection_hover(self, connection: Connection, hovered: bool) -> None:
        if not connection.line_id:
            return
        width = 3 if hovered else 2
        self.canvas.itemconfig(connection.line_id, width=width)

    def apply_connection_direction(self, connection: Connection) -> None:
        if not connection.line_id:
            return
        arrow = self._arrow_for_direction(connection.direction)
        self.canvas.itemconfig(connection.line_id, arrow=arrow)

    def draw_connection(self, connection: Connection, from_card: Card, to_card: Card) -> None:
        coords, render_info = self.connection_geometry(connection, from_card, to_card)
        arrow = self._arrow_for_direction(connection.direction)
        line_kwargs = {
            "arrow": arrow,
            "width": 2,
            "fill": self.theme["connection"],
            "tags": ("connection",),
        }
        if render_info.get("smooth"):
            line_kwargs["smooth"] = True

        line_id = self.canvas.create_line(*coords, **line_kwargs)

        label_id = None
        if connection.label:
            mx, my = self._label_position(coords, render_info)
            label_id = self.canvas.create_text(
                mx,
                my,
                text=connection.label,
                font=("Arial", 9, "italic"),
                fill=self.theme["connection_label"],
                tags=("connection_label",),
            )

        connection.line_id = line_id
        connection.label_id = label_id

    def update_connection_positions(
        self,
        connections: Iterable[Connection],
        cards: Dict[int, Card],
        target_card_id: int | None = None,
    ) -> None:
        for conn in connections:
            if target_card_id is not None and conn.from_id != target_card_id and conn.to_id != target_card_id:
                continue
            from_card = cards.get(conn.from_id)
            to_card = cards.get(conn.to_id)
            if from_card is None or to_card is None:
                continue
            coords, render_info = self.connection_geometry(conn, from_card, to_card)
            if conn.line_id:
                self.canvas.coords(conn.line_id, *coords)
                self.apply_connection_direction(conn)
            if conn.label_id:
                mx, my = self._label_position(coords, render_info)
                self.canvas.coords(conn.label_id, mx, my)

    def render_board(
        self,
        cards: Dict[int, Card],
        frames: Dict[int, Frame],
        connections: Iterable[Connection],
        grid_size: int,
        show_grid: bool,
    ) -> None:
        self.canvas.delete("all")
        self.draw_grid(grid_size, visible=show_grid)

        for frame in frames.values():
            self.draw_frame(frame)
        for card in cards.values():
            self.draw_card(card)
        for connection in connections:
            from_card = cards.get(connection.from_id)
            to_card = cards.get(connection.to_id)
            if from_card is None or to_card is None:
                continue
            self.draw_connection(connection, from_card, to_card)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.config(scrollregion=bbox)

        self.render_minimap(cards.values(), frames.values())

    def render_selection(
        self,
        cards: Dict[int, Card],
        frames: Dict[int, Frame],
        selected_cards: Iterable[int],
        selected_frame_id: int | None,
        connections: Iterable[Connection] | None = None,
        selected_connection: Connection | None = None,
    ) -> None:
        selected_cards_set = set(selected_cards)
        for cid, card in cards.items():
            if card.rect_id:
                width = 3 if cid in selected_cards_set else 1.5
                self.canvas.itemconfig(card.rect_id, width=width)
        for fid, frame in frames.items():
            if frame.rect_id:
                width = 3 if fid == selected_frame_id else 2
                self.canvas.itemconfig(frame.rect_id, width=width)

        if connections is None:
            return

        for conn in connections:
            if conn.line_id:
                width = 3 if conn is selected_connection else 2
                self.canvas.itemconfig(conn.line_id, width=width, fill=self.theme["connection"])
            if conn.label_id:
                label_color = self.theme["connection_label"]
                if conn is selected_connection:
                    label_color = self.theme.get("connection_label_selected", label_color)
                self.canvas.itemconfig(conn.label_id, fill=label_color)

    def render_minimap(self, cards: Iterable[Card], frames: Iterable[Frame]) -> None:
        if not self.minimap:
            return
        self.minimap.delete("all")
        self.minimap.config(bg=self.theme["minimap_bg"])
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

        def map_point(px: float, py: float) -> tuple[float, float]:
            mx = (px - x1) * scale
            my = (py - y1) * scale
            return mx, my

        for card in cards:
            cx, cy = card.x, card.y
            w, h = card.width, card.height
            mx1, my1 = map_point(cx - w / 2, cy - h / 2)
            mx2, my2 = map_point(cx + w / 2, cy + h / 2)
            self.minimap.create_rectangle(
                mx1,
                my1,
                mx2,
                my2,
                outline=self.theme["minimap_card_outline"],
                fill="",
                tags=("minimap_card",),
            )

        for frame in frames:
            if frame.rect_id is None:
                fx1, fy1, fx2, fy2 = frame.x1, frame.y1, frame.x2, frame.y2
            else:
                fx1, fy1, fx2, fy2 = self.canvas.coords(frame.rect_id)
            mx1, my1 = map_point(fx1, fy1)
            mx2, my2 = map_point(fx2, fy2)
            self.minimap.create_rectangle(
                mx1,
                my1,
                mx2,
                my2,
                outline=self.theme["minimap_frame_outline"],
                dash=(2, 2),
                tags=("minimap_frame",),
            )

        vx0, vx1 = self.canvas.xview()
        vy0, vy1 = self.canvas.yview()
        view_x1 = x1 + vx0 * (x2 - x1)
        view_x2 = x1 + vx1 * (x2 - x1)
        view_y1 = y1 + vy0 * (y2 - y1)
        view_y2 = y1 + vy1 * (y2 - y1)
        mvx1, mvy1 = map_point(view_x1, view_y1)
        mvx2, mvy2 = map_point(view_x2, view_y2)
        self.minimap.create_rectangle(
            mvx1,
            mvy1,
            mvx2,
            mvy2,
            outline=self.theme["minimap_viewport"],
            tags=("minimap_viewport",),
        )
