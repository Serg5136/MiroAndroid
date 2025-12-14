import sys
from pathlib import Path

import pytest
import tkinter as tk
from _tkinter import TclError


# Ensure project root is on sys.path for imports when running pytest directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_state():
    return {"cards": [1], "connections": [], "frames": []}


@pytest.fixture
def autosave_service(tmp_path):
    from src.autosave import AutoSaveService

    return AutoSaveService(filename=tmp_path / "autosave.json")


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
        root.withdraw()
    except TclError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Tk is not available: {exc}")
    yield root
    root.destroy()
