import json
import os
from aiogram import types

CONFIG_FILE = 'menu_config.json'
_CONFIG_CACHE = None

def load_config():
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    if not os.path.exists(CONFIG_FILE):
        _CONFIG_CACHE = {"reply_menu": [], "inline_messages": {}}
        return _CONFIG_CACHE

    try:
        with open(CONFIG_FILE, 'r') as f:
            _CONFIG_CACHE = json.load(f)
    except:
        _CONFIG_CACHE = {"reply_menu": [], "inline_messages": {}}
    
    return _CONFIG_CACHE

def save_config(data):
    global _CONFIG_CACHE
    _CONFIG_CACHE = data # Update cache
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_reply_keyboard_markup(is_admin=False):
    config = load_config()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Group by rows
    rows = {}
    
    # 1. Main Menu
    for btn in config.get('reply_menu', []):
        r = btn.get('row', 1)
        if r not in rows: rows[r] = []
        rows[r].append(btn['label'])
        
    # 2. Admin Menu (Only if is_admin)
    if is_admin:
        for btn in config.get('admin_menu', []):
            r = btn.get('row', 99)
            if r not in rows: rows[r] = []
            rows[r].append(btn['label'])
            
    # Sort and add to markup
    for r in sorted(rows.keys()):
        markup.row(*rows[r])
        
    return markup

def get_action_by_label(label):
    config = load_config()
    # Check regular menu
    for btn in config.get('reply_menu', []):
        if btn['label'] == label:
            return btn
    # Check admin menu
    for btn in config.get('admin_menu', []):
        if btn['label'] == label:
            return btn
    return None

def add_reply_button(label, response_text, row=4, inline_buttons=None):
    config = load_config()
    # Check duplicate
    for btn in config['reply_menu']:
        if btn['label'] == label:
            return False
            
    new_btn = {
        "label": label,
        "type": "text",
        "response": response_text,
        "row": row,
        "inline_buttons": inline_buttons or []
    }
    config['reply_menu'].append(new_btn)
    save_config(config)
    return True

def delete_reply_button(label):
    config = load_config()
    initial_len = len(config['reply_menu'])
    config['reply_menu'] = [b for b in config['reply_menu'] if b['label'] != label]
    
    if len(config['reply_menu']) < initial_len:
        save_config(config)
        return True
    return False

# --- INLINE MESSAGE MANAGER ---

def save_inline_message(key, title, content, buttons):
    """
    buttons format: List of lists of dicts
    [[{"text": "Btn1", "url": "http..."}], ...]
    """
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

def delete_inline_message(key):
    config = load_config()
    if 'inline_messages' in config and key in config['inline_messages']:
        del config['inline_messages'][key]
        save_config(config)
        return True
    return False
