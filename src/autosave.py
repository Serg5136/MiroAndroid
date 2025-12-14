"""Сервис для работы с автосохранением борда."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


class AutoSaveService:
    def __init__(self, filename: str = "_mini_miro_autosave.json") -> None:
        self.filename = filename

    def exists(self) -> bool:
        return os.path.exists(self.filename)

    def load(self) -> Dict[str, Any]:
        with open(self.filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        if self.exists():
            os.remove(self.filename)
