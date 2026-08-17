# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARACTERS_FILE = os.path.join(BASE_DIR, "data", "characters.json")
DEFAULT_CHARACTERS_FILE = os.path.join(BASE_DIR, "data", "default_characters.json")
API_KEY_FILE = os.path.join(BASE_DIR, "config", "api_key.txt")

def load_characters():
    if not os.path.exists(CHARACTERS_FILE):
        return {}
    with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_default_characters():
    if not os.path.exists(DEFAULT_CHARACTERS_FILE):
        return {}
    with open(DEFAULT_CHARACTERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_characters(chars):
    with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)

SETTINGS_FILE = os.path.join(BASE_DIR, "config", "settings.json")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "api_port": 50022,  # 他ソフトと競合しないようデフォルトを50022にする
            "api_auto_start": False,
            "font_family": "Meiryo"
        }
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "YOUR_GEMINI_API_KEY" not in line:
                    return line
    return os.environ.get("GEMINI_API_KEY", "")
SPEECH_LIST_FILE = os.path.join(BASE_DIR, "data", "speech_list.json")

def load_speech_list():
    if not os.path.exists(SPEECH_LIST_FILE):
        return []
    try:
        with open(SPEECH_LIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_speech_list(speech_list):
    os.makedirs(os.path.dirname(SPEECH_LIST_FILE), exist_ok=True)
    with open(SPEECH_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(speech_list, f, indent=2, ensure_ascii=False)
