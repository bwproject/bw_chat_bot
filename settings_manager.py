import json
import os
from typing import Dict, Any

SETTINGS_FILE = "settings.json"
IGNORED_FILE = "ignored.json"


DEFAULT_SETTINGS = {
    "business": True,
    "userbot": True,
    "new_chats": True,
    "auto_reply": True,
    "debug": False
}


DEFAULT_IGNORED = {
    "users": [],
    "chats": []
}


class SettingsManager:
    def __init__(self):
        self.settings = self._ensure_settings()
        self.ignored = self._ensure_ignored()

    # ─────────────────────────────
    # SAFE FILE CREATE / LOAD
    # ─────────────────────────────

    def _safe_load_json(self, path: str, default: dict):
        try:
            if not os.path.exists(path):
                self._save_json(path, default)
                return default.copy()

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        except (json.JSONDecodeError, OSError):
            # если файл битый — пересоздаём
            self._save_json(path, default)
            return default.copy()

    def _save_json(self, path: str, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ─────────────────────────────
    # SETTINGS
    # ─────────────────────────────

    def _ensure_settings(self):
        return self._safe_load_json(SETTINGS_FILE, DEFAULT_SETTINGS)

    def save_settings(self):
        self._save_json(SETTINGS_FILE, self.settings)

    def toggle(self, key: str):
        self.settings[key] = not self.settings.get(key, False)
        self.save_settings()

    def get(self, key: str):
        return self.settings.get(key, False)

    def all(self):
        return self.settings

    # ─────────────────────────────
    # IGNORED
    # ─────────────────────────────

    def _ensure_ignored(self):
        return self._safe_load_json(IGNORED_FILE, DEFAULT_IGNORED)

    def save_ignored(self):
        self._save_json(IGNORED_FILE, self.ignored)

    def ignore_user(self, user_id: int):
        if user_id not in self.ignored["users"]:
            self.ignored["users"].append(user_id)
            self.save_ignored()

    def unignore_user(self, user_id: int):
        if user_id in self.ignored["users"]:
            self.ignored["users"].remove(user_id)
            self.save_ignored()

    def ignore_chat(self, chat_id: int):
        if chat_id not in self.ignored["chats"]:
            self.ignored["chats"].append(chat_id)
            self.save_ignored()

    def unignore_chat(self, chat_id: int):
        if chat_id in self.ignored["chats"]:
            self.ignored["chats"].remove(chat_id)
            self.save_ignored()

    def is_user_ignored(self, user_id: int) -> bool:
        return user_id in self.ignored["users"]

    def is_chat_ignored(self, chat_id: int) -> bool:
        return chat_id in self.ignored["chats"]

    def all_ignored(self):
        return self.ignored


settings_manager = SettingsManager()