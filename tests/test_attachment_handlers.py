import base64
import shutil
from pathlib import Path
from unittest import mock

import pytest
from PIL import Image

import src.main as main
from src.board_model import Card as ModelCard
from src.main import BoardApp


def _make_app(tmp_root: Path):
    app = BoardApp.__new__(BoardApp)
    app.max_attachment_bytes = 1024 * 1024
    app.attachments_dir = tmp_root
    app.cards = {1: ModelCard(id=1, x=0, y=0, width=10, height=10, text="")}
    app.selected_cards = {1}
    app.selected_card_id = None
    app.canvas_view = mock.Mock()
    app.canvas_view.compute_card_layout.return_value = {
        "text_top": 0,
        "text_width": app.cards[1].width,
        "image_top": 0,
        "image_height": app.cards[1].height,
        "image_width": app.cards[1].width,
    }
    app.render_card_attachments = lambda _cid: None
    app.push_history = lambda: None
    return app


@pytest.fixture
def attachments_root(tmp_path):
    root = Path.cwd() / "attachments_test"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(exist_ok=True)
    yield root
    shutil.rmtree(root, ignore_errors=True)


def test_attach_clipboard_image_saves_file_and_base64(monkeypatch, attachments_root):
    app = _make_app(attachments_root)
    image = Image.new("RGBA", (8, 8), (255, 0, 0, 255))

    monkeypatch.setattr(app, "_read_clipboard_image", lambda: (image, "PNG", "image/png", "clip.png"))
    monkeypatch.setattr(main.messagebox, "showerror", mock.Mock())

    result = app._attach_clipboard_image_to_card()

    assert result is True
    attachment = app.cards[1].attachments[0]
    assert attachment.source_type == "clipboard"
    assert attachment.data_base64 is not None
    assert base64.b64decode(attachment.data_base64)  # decodes without error
    assert Path(attachment.storage_path).exists()


def test_attach_clipboard_image_rejects_large_payload(monkeypatch, attachments_root):
    app = _make_app(attachments_root)
    app.max_attachment_bytes = 10  # trigger size guard
    image = Image.new("RGBA", (4, 4), (0, 255, 0, 255))

    monkeypatch.setattr(app, "_read_clipboard_image", lambda: (image, "PNG", "image/png", "clip.png"))
    showerror = mock.Mock()
    monkeypatch.setattr(main.messagebox, "showerror", showerror)

    result = app._attach_clipboard_image_to_card()

    assert result is True
    showerror.assert_called_once()
    assert app.cards[1].attachments == []


def test_clipboard_missing_xclip_shows_hint(monkeypatch, attachments_root):
    app = _make_app(attachments_root)

    import PIL.ImageGrab as imagegrab

    monkeypatch.setattr(imagegrab, "grabclipboard", mock.Mock(side_effect=FileNotFoundError("xclip")))
    showerror = mock.Mock()
    monkeypatch.setattr(main.messagebox, "showerror", showerror)

    result = app._read_clipboard_image()

    assert result is None
    showerror.assert_called_once()


def test_attach_image_from_file_validates_format(monkeypatch, attachments_root, tmp_path):
    app = _make_app(attachments_root)
    bad_file = tmp_path / "note.txt"
    bad_file.write_text("not an image")

    monkeypatch.setattr(main.filedialog, "askopenfilename", lambda **_: str(bad_file))
    showerror = mock.Mock()
    monkeypatch.setattr(main.messagebox, "showerror", showerror)

    result = app._attach_image_from_file()

    assert result is True
    showerror.assert_called_once()
    assert app.cards[1].attachments == []


def test_attach_image_from_file_rejects_oversized(monkeypatch, attachments_root, tmp_path):
    app = _make_app(attachments_root)
    app.max_attachment_bytes = 10
    oversized = tmp_path / "big.png"
    img = Image.new("RGB", (10, 10), (0, 0, 255))
    img.save(oversized)

    monkeypatch.setattr(main.filedialog, "askopenfilename", lambda **_: str(oversized))
    showerror = mock.Mock()
    monkeypatch.setattr(main.messagebox, "showerror", showerror)

    result = app._attach_image_from_file()

    assert result is True
    showerror.assert_called_once()
    assert app.cards[1].attachments == []
