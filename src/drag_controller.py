from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import BoardApp


class DragController:
    def __init__(self, app: "BoardApp") -> None:
        self.app = app

    def on_canvas_click(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)
        item = app.canvas.find_withtag("current")
        item_id = item[0] if item else None
        tags = app.canvas.gettags(item_id) if item_id else ()

        if "connection_handle" in tags:
            conn = app.connection_handle_map.get(item_id) or app.get_connection_from_item(item_id)
            if conn:
                app.select_connection(conn)
                app.drag_data["dragging"] = True
                app.drag_data["moved"] = False
                if "connection_handle_start" in tags or "connection_handle_end" in tags:
                    endpoint = "start" if "connection_handle_start" in tags else "end"
                    app.drag_data["mode"] = "connection_endpoint"
                    app.drag_data["connection_edit"] = {
                        "connection": conn,
                        "endpoint": endpoint,
                        "original": {
                            "from_id": conn.from_id,
                            "to_id": conn.to_id,
                            "from_anchor": conn.from_anchor,
                            "to_anchor": conn.to_anchor,
                        },
                    }
                elif "connection_handle_radius" in tags:
                    app.drag_data["mode"] = "connection_radius"
                    from_card = app.cards.get(conn.from_id)
                    to_card = app.cards.get(conn.to_id)
                    if from_card and to_card:
                        _, geom = app.canvas_view.connection_geometry(conn, from_card, to_card)
                        app.drag_data["connection_edit"] = {
                            "connection": conn,
                            "length": geom.get("length", 1.0),
                            "start": (geom.get("start_x", from_card.x), geom.get("start_y", from_card.y)),
                            "start_dir": geom.get("start_dir", (1.0, 0.0)),
                        }
                elif "connection_handle_curvature" in tags:
                    app.drag_data["mode"] = "connection_curvature"
                    from_card = app.cards.get(conn.from_id)
                    to_card = app.cards.get(conn.to_id)
                    if from_card and to_card:
                        _, geom = app.canvas_view.connection_geometry(conn, from_card, to_card)
                        app.drag_data["connection_edit"] = {
                            "connection": conn,
                            "length": geom.get("length", 1.0),
                            "baseline_mid": (
                                geom.get("baseline_mid_x", (from_card.x + to_card.x) / 2),
                                geom.get("baseline_mid_y", (from_card.y + to_card.y) / 2),
                            ),
                            "normal": (geom.get("normal_x", 0.0), geom.get("normal_y", 0.0)),
                        }
                return "break"

        conn = app.get_connection_from_item(item_id)
        if conn is not None:
            app.select_connection(conn)
            return "break"

        if "resize_handle" in tags:
            card_id = app.get_card_id_from_item(item)
            if card_id is not None:
                app.selection_controller.select_card(card_id, additive=False)
                card = app.cards[card_id]
                x1 = card.x - card.width / 2
                y1 = card.y - card.height / 2
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "resize_card"
                app.drag_data["resize_card_id"] = card_id
                app.drag_data["resize_origin"] = (x1, y1)
                app.drag_data["moved"] = False
                app.drag_data["dragged_cards"] = {card_id}
            return

        if "attachment_resize_handle" in tags:
            target_tag = next((t for t in tags if t.startswith("attachment_") and len(t.split("_")) == 3), None)
            handle_tag = next((t for t in tags if t.startswith("attachment_handle_") and len(t.split("_")) == 3), None)
            if target_tag and handle_tag:
                _, card_raw, attachment_raw = target_tag.split("_", 2)
                _, _, anchor = handle_tag.split("_", 2)
                try:
                    card_id = int(card_raw)
                    attachment_id = int(attachment_raw)
                except ValueError:
                    return
                app.select_attachment(card_id, attachment_id)
                key = (card_id, attachment_id)
                item_id = app.attachment_items.get(key)
                bbox = app.canvas.bbox(item_id) if item_id else None
                if not bbox:
                    return
                center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "resize_attachment"
                app.drag_data["resize_attachment"] = {
                    "card_id": card_id,
                    "attachment_id": attachment_id,
                    "anchor": anchor,
                    "center": center,
                }
                app.drag_data["moved"] = False
            return

        if "connect_handle" in tags:
            card_id = app.get_card_id_from_item(item)
            if card_id is not None:
                app.selection_controller.select_card(card_id, additive=False)
                card = app.cards[card_id]
                anchor = next(
                    (
                        tag.split("_")[2]
                        for tag in tags
                        if tag.startswith("connect_handle_") and len(tag.split("_")) == 3
                    ),
                    None,
                )
                positions = app._card_handle_positions(card)
                sx, sy = positions.get(anchor, (card.x + card.width / 2, card.y))
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "connect_drag"
                app.drag_data["connect_from_card"] = card_id
                app.drag_data["connect_from_anchor"] = anchor
                app.drag_data["connect_start"] = (sx, sy)
                app.drag_data["temp_line_id"] = app.canvas.create_line(
                    sx, sy, sx, sy,
                    fill=app.theme["connection"],
                    width=2,
                    dash=(4, 2),
                    arrow=tk.LAST,
                    tags=("temp_connection",)
                )
            return

        if "frame_handle" in tags:
            frame_id = app.get_frame_id_from_item(item)
            if frame_id is not None:
                app.selection_controller.select_frame(frame_id)
                x1, y1, x2, y2 = app.canvas.coords(app.frames[frame_id].rect_id)
                handle_dir = next((t.split("_")[2] for t in tags if t.startswith("frame_handle_") and len(t.split("_")) == 3), None)
                anchor = (x1, y1)
                if handle_dir == "ne":
                    anchor = (x1, y2)
                elif handle_dir == "sw":
                    anchor = (x2, y1)
                elif handle_dir == "se":
                    anchor = (x1, y1)
                app.drag_data["dragging"] = True
                app.drag_data["mode"] = "resize_frame"
                app.drag_data["resize_frame_id"] = frame_id
                app.drag_data["resize_frame_handle"] = handle_dir
                app.drag_data["resize_frame_anchor"] = anchor
                app.drag_data["moved"] = False
            return

        card_id = app.get_card_id_from_item(item)
        frame_id = app.get_frame_id_from_item(item)

        if app.connect_mode:
            if card_id is not None:
                if app.connect_from_card_id is None:
                    app.connect_from_card_id = card_id
                    app.selection_controller.select_card(card_id, additive=False)
                else:
                    if card_id != app.connect_from_card_id:
                        app.create_connection(app.connect_from_card_id, card_id)
                        app.push_history()
                    app.connect_controller.set_connect_mode(False)
                    app.selection_controller.select_card(card_id, additive=False)
            return

        app.drag_data["dragging"] = False
        app.drag_data["dragged_cards"] = set()
        app.drag_data["moved"] = False
        app.drag_data["mode"] = None
        app.drag_data["frame_id"] = None
        app.drag_data["resize_card_id"] = None
        app.drag_data["resize_origin"] = None
        app.drag_data["resize_frame_id"] = None
        app.drag_data["resize_frame_handle"] = None
        app.drag_data["resize_frame_anchor"] = None
        app.drag_data["resize_attachment"] = None
        app.drag_data["connect_from_card"] = None
        app.drag_data["connect_from_anchor"] = None
        if app.drag_data["temp_line_id"]:
            app.canvas.delete(app.drag_data["temp_line_id"])
        app.drag_data["temp_line_id"] = None
        app.drag_data["connection_edit"] = None
        app.selection_start = None
        if app.selection_rect_id is not None:
            app.canvas.delete(app.selection_rect_id)
            app.selection_rect_id = None

        if card_id is not None:
            if card_id in app.selected_cards:
                app.selected_card_id = card_id
            else:
                app.selection_controller.select_card(card_id, additive=False)

            app.drag_data["dragging"] = True
            app.drag_data["dragged_cards"] = set(app.selected_cards)
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            app.drag_data["mode"] = "cards"

        elif frame_id is not None:
            app.selection_controller.select_frame(frame_id)
            app.drag_data["dragging"] = True
            app.drag_data["mode"] = "frame"
            app.drag_data["frame_id"] = frame_id
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            x1, y1, x2, y2 = app.canvas.coords(app.frames[frame_id].rect_id)
            app.drag_data["dragged_cards"] = {
                cid for cid, card in app.cards.items()
                if x1 <= card.x <= x2 and y1 <= card.y <= y2
            }
        else:
            app.selection_controller.select_card(None)
            app.selection_start = (cx, cy)
            app.selection_rect_id = app.canvas.create_rectangle(
                cx, cy, cx, cy,
                outline="#999999",
                dash=(2, 2),
                fill="",
                tags=("selection_rect",),
            )

    def on_mouse_drag(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)

        if app.drag_data["dragging"]:
            mode = app.drag_data["mode"]

            if mode == "resize_card":
                card_id = app.drag_data["resize_card_id"]
                card = app.cards.get(card_id)
                if not card:
                    return
                old_w, old_h = card.width, card.height
                ox1, oy1 = app.drag_data["resize_origin"]
                layout = app.canvas_view.compute_card_layout(card)
                attach_min_w, attach_min_h = app._compute_attachments_min_size(card, layout)
                min_w = max(60, attach_min_w)
                min_h = max(40, attach_min_h)
                new_x2 = max(ox1 + min_w, cx)
                new_y2 = max(oy1 + min_h, cy)
                w = new_x2 - ox1
                h = new_y2 - oy1
                card.width = w
                card.height = h
                card.x = ox1 + w / 2
                card.y = oy1 + h / 2
                x1 = ox1
                y1 = oy1
                x2 = new_x2
                y2 = new_y2
                app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                width_scale = w / old_w if old_w else 1.0
                height_scale = h / old_h if old_h else 1.0
                app.update_card_layout(
                    card_id,
                    redraw_attachment=False,
                    attachment_scale=(width_scale, height_scale),
                )
                app.update_card_handles_positions(card_id)
                app.update_connections_for_card(card_id)
                app.drag_data["moved"] = True
                return

            if mode == "resize_attachment":
                resize_data = app.drag_data.get("resize_attachment")
                if not resize_data:
                    return
                card_id = resize_data.get("card_id")
                attachment_id = resize_data.get("attachment_id")
                center = resize_data.get("center")
                if not center:
                    return
                _, attachment = app._get_attachment(card_id, attachment_id)
                if not attachment:
                    return
                center_x, center_y = center
                new_w = max(abs(cx - center_x) * 2, 1)
                new_h = max(abs(cy - center_y) * 2, 1)
                base_w = max(attachment.width, 1)
                base_h = max(attachment.height, 1)
                width_scale = new_w / base_w
                height_scale = new_h / base_h
                new_scale = max(width_scale, height_scale)
                new_scale = max(0.1, min(new_scale, 10.0))
                attachment.preview_scale = new_scale
                app.render_card_attachments(card_id)
                app._show_attachment_selection(card_id, attachment)
                app.update_minimap()
                app.drag_data["moved"] = True
                return

            if mode == "resize_frame":
                frame_id = app.drag_data["resize_frame_id"]
                frame = app.frames.get(frame_id)
                handle = app.drag_data["resize_frame_handle"]
                anchor = app.drag_data["resize_frame_anchor"]
                if not frame or not frame.rect_id or anchor is None:
                    return
                ax, ay = anchor
                min_w = app.min_frame_width
                min_h = app.min_frame_height

                if handle == "nw":
                    new_x1 = min(cx, ax - min_w)
                    new_y1 = min(cy, ay - min_h)
                    new_x2, new_y2 = ax, ay
                elif handle == "ne":
                    new_x1, new_y2 = ax, ay
                    new_x2 = max(cx, ax + min_w)
                    new_y1 = min(cy, ay - min_h)
                elif handle == "sw":
                    new_x2, new_y1 = ax, ay
                    new_x1 = min(cx, ax - min_w)
                    new_y2 = max(cy, ay + min_h)
                else:  # "se" и запасной вариант
                    new_x1, new_y1 = ax, ay
                    new_x2 = max(cx, ax + min_w)
                    new_y2 = max(cy, ay + min_h)

                app.canvas.coords(frame.rect_id, new_x1, new_y1, new_x2, new_y2)
                if frame.title_id:
                    app.canvas.coords(frame.title_id, new_x1 + 10, new_y1 + 15)
                frame.x1, frame.y1, frame.x2, frame.y2 = new_x1, new_y1, new_x2, new_y2
                app.update_frame_handles_positions(frame_id)
                app.update_minimap()
                app.drag_data["moved"] = True
                return

            if mode == "connect_drag":
                line_id = app.drag_data["temp_line_id"]
                if line_id:
                    sx, sy = app.drag_data["connect_start"]
                    app.canvas.coords(line_id, sx, sy, cx, cy)
                    app.drag_data["moved"] = True
                return

            if mode == "connection_radius":
                edit_data = app.drag_data.get("connection_edit") or {}
                conn = edit_data.get("connection")
                if not conn:
                    return
                length = max(1.0, edit_data.get("length", 1.0))
                start = edit_data.get("start", (cx, cy))
                dir_x, dir_y = edit_data.get("start_dir", (1.0, 0.0))
                proj = (cx - start[0]) * dir_x + (cy - start[1]) * dir_y
                new_radius = max(0.0, min(length * 0.6, proj))
                conn.radius = new_radius
                app.canvas_view.update_connection_positions([conn], app.cards)
                app.show_connection_handles(conn)
                app.drag_data["moved"] = True
                return

            if mode == "connection_curvature":
                edit_data = app.drag_data.get("connection_edit") or {}
                conn = edit_data.get("connection")
                if not conn:
                    return
                baseline_mid = edit_data.get("baseline_mid", (cx, cy))
                normal_x, normal_y = edit_data.get("normal", (0.0, 1.0))
                length = max(1.0, edit_data.get("length", 1.0))
                offset = (cx - baseline_mid[0]) * normal_x + (cy - baseline_mid[1]) * normal_y
                offset = max(-length / 2, min(length / 2, offset))
                conn.curvature = offset
                app.canvas_view.update_connection_positions([conn], app.cards)
                app.show_connection_handles(conn)
                app.drag_data["moved"] = True
                return

            if mode == "connection_endpoint":
                edit_data = app.drag_data.get("connection_edit") or {}
                conn = edit_data.get("connection")
                endpoint = edit_data.get("endpoint")
                if not conn or endpoint not in {"start", "end"}:
                    return

                target_id = None
                target_anchor = None
                items = app.canvas.find_overlapping(cx, cy, cx, cy)
                for it in items:
                    cid = app.get_card_id_from_item((it,))
                    if cid is not None:
                        other_id = conn.to_id if endpoint == "start" else conn.from_id
                        if cid != other_id:
                            target_id = cid
                            target_card = app.cards.get(cid)
                            if target_card:
                                target_anchor = app._closest_card_anchor(target_card, cx, cy)
                        break

                if target_id is None:
                    return

                if endpoint == "start":
                    conn.from_id = target_id
                    conn.from_anchor = target_anchor
                else:
                    conn.to_id = target_id
                    conn.to_anchor = target_anchor

                app.canvas_view.update_connection_positions([conn], app.cards)
                if app.selected_connection is conn:
                    app.show_connection_handles(conn)
                app.drag_data["moved"] = True
                return

            dx = cx - app.drag_data["last_x"]
            dy = cy - app.drag_data["last_y"]
            if dx == 0 and dy == 0:
                return
            app.drag_data["last_x"] = cx
            app.drag_data["last_y"] = cy
            app.drag_data["moved"] = True

            if mode == "cards":
                for card_id in app.drag_data["dragged_cards"]:
                    card = app.cards.get(card_id)
                    if not card:
                        continue
                    card.x += dx
                    card.y += dy
                    x1 = card.x - card.width / 2
                    y1 = card.y - card.height / 2
                    x2 = card.x + card.width / 2
                    y2 = card.y + card.height / 2
                    app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                    app.update_card_layout(card_id, redraw_attachment=False)
                    app.update_card_handles_positions(card_id)
                    app.update_connections_for_card(card_id)

            elif mode == "frame":
                frame_id = app.drag_data["frame_id"]
                frame = app.frames.get(frame_id)
                if frame:
                    app.canvas.move(frame.rect_id, dx, dy)
                    app.canvas.move(frame.title_id, dx, dy)
                    x1, y1, x2, y2 = app.canvas.coords(frame.rect_id)
                    frame.x1, frame.y1, frame.x2, frame.y2 = x1, y1, x2, y2
                    app.update_frame_handles_positions(frame_id)
                    app.update_minimap()

                for card_id in app.drag_data["dragged_cards"]:
                    card = app.cards.get(card_id)
                    if not card:
                        continue
                    card.x += dx
                    card.y += dy
                    x1 = card.x - card.width / 2
                    y1 = card.y - card.height / 2
                    x2 = card.x + card.width / 2
                    y2 = card.y + card.height / 2
                    app.canvas.coords(card.rect_id, x1, y1, x2, y2)
                    app.update_card_layout(card_id, redraw_attachment=False)
                    app.update_card_handles_positions(card_id)
                    app.update_connections_for_card(card_id)

        elif app.selection_start is not None and app.selection_rect_id is not None:
            x0, y0 = app.selection_start
            app.canvas.coords(app.selection_rect_id, x0, y0, cx, cy)

    def on_mouse_release(self, event):
        app = self.app
        cx = app.canvas.canvasx(event.x)
        cy = app.canvas.canvasy(event.y)
        mode = app.drag_data["mode"]

        if mode == "connect_drag":
            from_id = app.drag_data["connect_from_card"]
            from_anchor = app.drag_data.get("connect_from_anchor")
            if app.drag_data["temp_line_id"]:
                app.canvas.delete(app.drag_data["temp_line_id"])
            target_id = None
            items = app.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                cid = app.get_card_id_from_item((it,))
                if cid is not None:
                    target_id = cid
                    break
            if from_id is not None and target_id is not None and target_id != from_id:
                target_card = app.cards.get(target_id)
                target_anchor = None
                if target_card:
                    target_anchor = app._closest_card_anchor(target_card, cx, cy)
                app.create_connection(
                    from_id,
                    target_id,
                    from_anchor=from_anchor,
                    to_anchor=target_anchor,
                )
                app.push_history()

            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["connect_from_card"] = None
            app.drag_data["connect_from_anchor"] = None
            app.drag_data["temp_line_id"] = None
            app.drag_data["moved"] = False
            return

        if mode == "resize_card":
            if app.drag_data["moved"]:
                app.snap_cards_to_grid(app.drag_data["dragged_cards"])
                app.push_history()
            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["resize_card_id"] = None
            app.drag_data["resize_origin"] = None
            app.drag_data["dragged_cards"] = set()
            app.drag_data["moved"] = False
            app.update_controls_state()
            return

        if mode == "resize_frame":
            if app.drag_data["moved"]:
                app.push_history()
            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["resize_frame_id"] = None
            app.drag_data["resize_frame_handle"] = None
            app.drag_data["resize_frame_anchor"] = None
            app.drag_data["moved"] = False
            return

        if mode == "resize_attachment":
            if app.drag_data["moved"]:
                app.push_history()
                app.update_minimap()
            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["resize_attachment"] = None
            app.drag_data["moved"] = False
            return

        if mode in {"connection_radius", "connection_curvature"}:
            if app.drag_data["moved"]:
                app.push_history()
            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["connection_edit"] = None
            app.drag_data["moved"] = False
            return

        if mode == "connection_endpoint":
            edit_data = app.drag_data.get("connection_edit") or {}
            conn = edit_data.get("connection")
            original = edit_data.get("original") or {}
            invalid_target = conn and conn.from_id == conn.to_id
            if (not app.drag_data["moved"]) or invalid_target:
                if conn and original:
                    conn.from_id = original.get("from_id", conn.from_id)
                    conn.to_id = original.get("to_id", conn.to_id)
                    conn.from_anchor = original.get("from_anchor")
                    conn.to_anchor = original.get("to_anchor")
                    app.canvas_view.update_connection_positions([conn], app.cards)
                    app.show_connection_handles(conn)
            else:
                app.push_history()

            app.drag_data["dragging"] = False
            app.drag_data["mode"] = None
            app.drag_data["connection_edit"] = None
            app.drag_data["moved"] = False
            return

        if app.drag_data["dragging"] and app.drag_data["moved"]:
            app.snap_cards_to_grid(app.drag_data["dragged_cards"])
            app.push_history()

        app.drag_data["dragging"] = False
        app.drag_data["dragged_cards"] = set()
        app.drag_data["moved"] = False
        app.drag_data["mode"] = None

        if app.selection_start is not None and app.selection_rect_id is not None:
            x1, y1, x2, y2 = app.canvas.coords(app.selection_rect_id)
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)

            app.selection_controller.select_card(None)
            for card_id, card in app.cards.items():
                if left <= card.x <= right and top <= card.y <= bottom:
                    app.selection_controller.select_card(card_id, additive=True)

            app.canvas.delete(app.selection_rect_id)
            app.selection_rect_id = None
            app.selection_start = None


# Keep tkinter import local to avoid circular import issues
import tkinter as tk  # noqa: E402  pylint: disable=wrong-import-position
