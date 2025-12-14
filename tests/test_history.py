import copy

import pytest

from src.autosave import AutoSaveService
from src.history import History


class DummyApp:
    def __init__(self):
        self.applied_states = []

    def set_board_from_data(self, data):
        # Store a deep copy to ensure immutability across history operations
        self.applied_states.append(copy.deepcopy(data))


def test_history_sequence_and_undo_redo(sample_state):
    app = DummyApp()
    history = History()

    initial_state = {"cards": [], "connections": [], "frames": []}
    state_after_first = sample_state
    state_after_second = {"cards": [1, 2], "connections": ["a->b"], "frames": []}

    history.clear_and_init(initial_state)
    history.push(state_after_first)
    history.push(state_after_second)

    assert history.current_state() == state_after_second

    undo_second = history.undo(app)
    assert undo_second == state_after_first
    assert app.applied_states[-1] == state_after_first

    undo_first = history.undo(app)
    assert undo_first == initial_state
    assert app.applied_states[-1] == initial_state

    redo_first = history.redo(app)
    assert redo_first == state_after_first
    assert history.index == 0
    assert app.applied_states[-1] == state_after_first

    history.push({"cards": ["new"], "connections": [], "frames": []})
    assert history.index == 1
    assert not history.can_redo()


def test_autosave_roundtrip(autosave_service, sample_state):
    assert not autosave_service.exists()

    autosave_service.save(sample_state)
    assert autosave_service.exists()

    loaded = autosave_service.load()
    assert loaded == sample_state

    autosave_service.clear()
    assert not autosave_service.exists()


def test_history_autosave_integration(tmp_path):
    autosave = AutoSaveService(filename=tmp_path / "state.json")
    app = DummyApp()
    history = History()

    initial_state = {"cards": [], "connections": [], "frames": []}
    updated_state = {"cards": [1], "connections": [], "frames": []}

    history.clear_and_init(initial_state)
    autosave.save(initial_state)

    history.push(updated_state)
    autosave.save(updated_state)

    # Simulate application restart and restore from autosave
    restored = autosave.load()
    assert restored == updated_state

    undo_state = history.undo(app)
    assert undo_state == initial_state
    autosave.save(undo_state)

    restored_after_undo = autosave.load()
    assert restored_after_undo == initial_state
