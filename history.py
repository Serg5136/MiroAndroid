# history.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import copy


@dataclass
class SnapshotCommand:
    """
    Простейшая команда: хранит состояние ДО и ПОСЛЕ.
    apply/rollback подставляют соответствующий снапшот борда.
    В дальнейшем можно добавлять более "тонкие" команды.
    """

    before: Dict[str, Any]
    after: Dict[str, Any]

    def rollback(self, app) -> Dict[str, Any]:
        """
        Откатить состояние борда к before.
        """

        state = copy.deepcopy(self.before)
        app.set_board_from_data(state)
        return state

    def apply(self, app) -> Dict[str, Any]:
        """
        Применить состояние after.
        """

        state = copy.deepcopy(self.after)
        app.set_board_from_data(state)
        return state


class History:
    """
    История на основе команд.

    - initial_state: состояние борда "по умолчанию" (после открытия/создания).
    - commands: список SnapshotCommand.
    - index: индекс последней применённой команды, -1 = initial_state.
    """

    def __init__(self) -> None:
        self.initial_state: Optional[Dict[str, Any]] = None
        self.commands: List[SnapshotCommand] = []
        self.index: int = -1

    # --- Базовые операции над историей ---

    def clear_and_init(self, state: Dict[str, Any]) -> None:
        """
        Сбросить историю и задать начальное состояние борда.
        """
        self.initial_state = copy.deepcopy(state)
        self.commands = []
        self.index = -1

    def current_state(self) -> Optional[Dict[str, Any]]:
        """
        Текущее состояние борда с точки зрения истории.
        """
        if self.index < 0:
            return copy.deepcopy(self.initial_state) if self.initial_state is not None else None
        return copy.deepcopy(self.commands[self.index].after)

    def push(self, after_state: Dict[str, Any]) -> None:
        """
        Добавить новую команду (состояние после изменения).
        before_state берётся как текущее состояние истории.
        """
        if self.initial_state is None:
            # Если по какой-то причине нет initial_state — считаем его текущим
            self.initial_state = copy.deepcopy(after_state)
            self.commands = []
            self.index = -1
            return

        before_state = self.current_state()
        if before_state is None:
            before_state = copy.deepcopy(self.initial_state)

        # обрезаем "будущее", если были откаты
        if self.index < len(self.commands) - 1:
            self.commands = self.commands[: self.index + 1]

        cmd = SnapshotCommand(
            before=before_state,
            after=copy.deepcopy(after_state),
        )
        self.commands.append(cmd)
        self.index = len(self.commands) - 1

    # --- Undo / Redo ---

    def can_undo(self) -> bool:
        """
        Можно откатить, если есть хотя бы одна команда.
        """
        return self.index >= 0

    def can_redo(self) -> bool:
        """
        Можно повторить, если есть команды "впереди".
        """
        return self.index < len(self.commands) - 1

    def undo(self, app) -> Optional[Dict[str, Any]]:
        if not self.can_undo():
            return None

        cmd = self.commands[self.index]
        self.index -= 1
        return cmd.rollback(app)

    def redo(self, app) -> Optional[Dict[str, Any]]:
        if not self.can_redo():
            return None

        self.index += 1
        cmd = self.commands[self.index]
        return cmd.apply(app)
