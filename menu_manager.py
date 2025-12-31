import json
import os
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

CONFIG_FILE = 'menu_config.json'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILE)
_CONFIG_CACHE = None

def load_config():
    global _CONFIG_CACHE
    # Always reload for dev/debug, or implement TTL if needed
    try:
        if not os.path.exists(CONFIG_PATH):
            return {"reply_menu": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            _CONFIG_CACHE = json.load(f)
    except Exception as e:
        logging.error(f"Error loading menu_config: {e}")
        return {"reply_menu": []}
    return _CONFIG_CACHE

def get_reply_keyboard_markup(is_admin=False):
    config = load_config()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # 1. Main Menu (Group by row)
    rows = {}
    for btn in config.get('reply_menu', []):
        r = btn.get('row', 99)
        if r not in rows: rows[r] = []
        rows[r].append(KeyboardButton(btn['label']))
    
    for r in sorted(rows.keys()):
        markup.row(*rows[r])
        
    # 2. Admin Menu (Appended if admin)
    if is_admin:
        admin_rows = {}
        for btn in config.get('admin_menu', []):
            r = btn.get('row', 99)
            if r not in admin_rows: admin_rows[r] = []
            admin_rows[r].append(KeyboardButton(btn['label']))
        
        for r in sorted(admin_rows.keys()):
            markup.row(*admin_rows[r])
            
    return markup

def get_action_by_label(text):
    if not text: return None
    config = load_config()
    
    # Check regular menu
    for btn in config.get('reply_menu', []):
        if btn['label'] == text:
            return btn
            
    # Check admin menu
    for btn in config.get('admin_menu', []):
        if btn['label'] == text:
            return btn
            
    return None

def add_reply_button(label, response_text, row=4, inline_buttons=None):
    config = load_config()
    # Check duplicate
    for btn in config.get('reply_menu', []):
        if btn['label'] == label:
            return False
            
    new_btn = {
        "label": label,
        "type": "text",
        "response": response_text,
        "row": row,
        "inline_buttons": inline_buttons or []
    }
    if 'reply_menu' not in config: config['reply_menu'] = []
    config['reply_menu'].append(new_btn)
    save_config(config)
    return True

def delete_reply_button(label):
    config = load_config()
    initial_len = len(config.get('reply_menu', []))
    config['reply_menu'] = [b for b in config.get('reply_menu', []) if b['label'] != label]
    
    if len(config['reply_menu']) < initial_len:
        save_config(config)
        return True
    return False

def save_config(data):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving menu config: {e}")

# --- INLINE MESSAGE MANAGER ---

def save_inline_message(key, title, content, buttons):
    config = load_config()
    if 'inline_messages' not in config:
        config['inline_messages'] = {}
        
    config['inline_messages'][key] = {
        "title": title,
        "content": content,
        "buttons": buttons
    }
    save_config(config)

def get_inline_message(key):
    config = load_config()
    return config.get('inline_messages', {}).get(key)

def list_inline_messages():
    config = load_config()
    return list(config.get('inline_messages', {}).keys())