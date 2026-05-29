from __future__ import annotations

import json
from pathlib import Path


_PATCH_INSTALLED = False


def _load_text_fix_map() -> dict[str, str]:
    fix_file = Path.cwd() / "assets" / "ocr_fix" / "ocr_text_fix.json"
    if not fix_file.is_file():
        return {}

    try:
        data = json.loads(fix_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    fix_map: dict[str, str] = {}
    for wrong_text, correct_text in data.items():
        wrong = str(wrong_text).strip()
        correct = str(correct_text).strip()
        if wrong and correct:
            fix_map[wrong] = correct
    return fix_map


def install_ocr_text_fix_patch():
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return

    from ok.task.TaskExecutor import TaskExecutor

    original_init = TaskExecutor.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.text_fix.update(_load_text_fix_map())

    TaskExecutor.__init__ = patched_init
    _PATCH_INSTALLED = True