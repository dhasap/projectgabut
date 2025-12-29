import os
from supabase import create_client, Client
from datetime import datetime
import logging

# --- KONFIGURASI SUPABASE ---
# Data diambil dari Environment Variables (SUPABASE_URL & SUPABASE_KEY)
# Pastikan Anda sudah mensettingnya di platform hosting (Heroku/Railway/dll)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logging.error(f"Gagal koneksi ke Supabase: {e}")
else:
    logging.error("CRITICAL: SUPABASE_URL atau SUPABASE_KEY tidak ditemukan di Environment Variables!")

# --- USERS ---
def db_save_user(user_id, username=None, first_name=None):
    """Menyimpan user ke tabel 'users' dengan username."""
    if not supabase: return
    try:
        data = {
            "user_id": user_id, 
            "username": username,
            "first_name": first_name,
            "last_seen": datetime.utcnow().isoformat()
        }
        supabase.table("users").upsert(data, on_conflict="user_id").execute()
    except Exception as e:
        logging.error(f"DB Error save_user: {e}")

def db_get_all_users():
    """Mengambil list semua user_id."""
    if not supabase: return []
    try:
        response = supabase.table("users").select("user_id").execute()
        return [item['user_id'] for item in response.data]
    except Exception as e:
        logging.error(f"DB Error get_all_users: {e}")
        return []

def db_get_users_count():
    """Menghitung total user."""
    if not supabase: return 0
    try:
        response = supabase.table("users").select("user_id", count="exact").execute()
        return response.count
    except Exception as e:
        logging.error(f"DB Error get_users_count: {e}")
        return 0

def db_get_user_info(user_id):
    """Mengambil detail user row."""
    if not supabase: return None
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logging.error(f"DB Error get_info: {e}")
    return None

# --- ADMINS ---
def db_get_admins(owner_id):
    """Mengambil set ID admin."""
    admins = {int(owner_id)}
    if not supabase: return admins
    try:
        response = supabase.table("admins").select("user_id").execute()
        for item in response.data:
            admins.add(int(item['user_id']))
    except Exception as e:
        logging.error(f"DB Error get_admins: {e}")
    return admins

def db_add_admin(user_id, username=None):
    """Menambah admin baru."""
    if not supabase: return False
    try:
        data = {
            "user_id": user_id, 
            "username": username,
            "promoted_at": datetime.utcnow().isoformat()
        }
        supabase.table("admins").insert(data).execute()
        return True
    except Exception as e:
        logging.error(f"DB Error add_admin: {e}")
        return False

def db_remove_admin(user_id):
    """Menghapus admin."""
    if not supabase: return False
    try:
        supabase.table("admins").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        logging.error(f"DB Error remove_admin: {e}")
        return False

# --- BANNED USERS ---
def db_get_banned():
    """Mengambil set user yang di-banned."""
    banned = set()
    if not supabase: return banned
    try:
        response = supabase.table("banned").select("user_id").execute()
        for item in response.data:
            banned.add(str(item['user_id']))
    except Exception as e:
        logging.error(f"DB Error get_banned: {e}")
    return banned

def db_ban_user(user_id, username=None, reason="Admin Ban"):
    """Ban user."""
    if not supabase: return False
    try:
        data = {
            "user_id": user_id, 
            "username": username,
            "reason": reason, 
            "banned_at": datetime.utcnow().isoformat()
        }
        supabase.table("banned").upsert(data).execute()
        return True
    except Exception as e:
        logging.error(f"DB Error ban_user: {e}")
        return False

def db_unban_user(user_id):
    """Unban user."""
    if not supabase: return False
    try:
        supabase.table("banned").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        logging.error(f"DB Error unban_user: {e}")
        return False

# --- BOT STATE ---
def db_save_state(state_data):
    if not supabase: return
    try:
        data = {"key": "bot_config", "value": state_data}
        supabase.table("bot_state").upsert(data, on_conflict="key").execute()
    except Exception as e:
        logging.error(f"DB Error save_state: {e}")

def db_load_state():
    if not supabase: return {}
    try:
        response = supabase.table("bot_state").select("value").eq("key", "bot_config").execute()
        if response.data:
            return response.data[0]['value']
    except Exception as e:
        logging.error(f"DB Error load_state: {e}")
    return {}

# --- ACTIVITY LOGS ---
def db_log_activity(admin_id, username, action, details):
    """Mencatat aktivitas admin."""
    if not supabase: return
    try:
        data = {
            "admin_id": admin_id,
            "username": username,
            "action": action,
            "details": details,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("activity_logs").insert(data).execute()
    except Exception as e:
        logging.error(f"DB Error log_activity: {e}")

def db_get_activity_logs(limit=10):
    """Mengambil log aktivitas terakhir."""
    if not supabase: return []
    try:
        # Order by created_at desc
        response = supabase.table("activity_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logging.error(f"DB Error get_logs: {e}")
        return []

# --- DYNAMIC TEXTS (Start/Help) ---
def db_set_config(key, value):
    """Menyimpan konfigurasi text/setting."""
    if not supabase: return
    try:
        # Value disimpan langsung, jika jsonb pastikan format sesuai
        # Di sini kita simpan sebagai JSON object sederhana {"text": "isi"} agar kompatibel dengan kolom jsonb
        data = {"key": key, "value": {"text": value}}
        supabase.table("bot_state").upsert(data, on_conflict="key").execute()
    except Exception as e:
        logging.error(f"DB Error set_config: {e}")

from cryptography.fernet import Fernet
import base64

# --- SECURE NOTES (ENCRYPTED) ---
# Generate a static key from SUPABASE_KEY (or another env var) to ensure persistence across restarts.
# In production, use a dedicated SECRET_KEY env var.
# We derive a valid 32-byte Fernet key from the existing key.

def _get_cipher_suite():
    secret = os.getenv("SECRET_KEY", "DefaultSecretKeyShouldBeChangedForProd123")
    # Pad or truncate to 32 bytes for url-safe base64
    # Fernet requires a URL-safe base64-encoded 32-byte key
    # Simple derivation:
    key_bytes = secret.ljust(32)[:32].encode()
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)

def db_save_note(user_id, title, content):
    """Menyimpan catatan terenkripsi."""
    if not supabase: return False
    try:
        cipher = _get_cipher_suite()
        encrypted_content = cipher.encrypt(content.encode()).decode()
        
        data = {
            "user_id": user_id,
            "title": title,
            "content": encrypted_content,
            "updated_at": datetime.utcnow().isoformat()
        }
        # Upsert based on composite key logic usually requires a constraint.
        # Here assuming we might have a unique constraint on (user_id, title) or just insert.
        # Supabase generic upsert checks primary key.
        # Let's assume table `notes` has columns: id (serial), user_id, title, content, updated_at
        # And a unique constraint on (user_id, title).
        supabase.table("notes").upsert(data, on_conflict="user_id, title").execute()
        return True
    except Exception as e:
        logging.error(f"DB Error save_note: {e}")
        return False

def db_get_notes_list(user_id):
    """Mengambil daftar judul catatan user."""
    if not supabase: return []
    try:
        response = supabase.table("notes").select("title, updated_at").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        logging.error(f"DB Error get_notes_list: {e}")
        return []

def db_get_note_content(user_id, title):
    """Mengambil dan mendekripsi isi catatan."""
    if not supabase: return None
    try:
        response = supabase.table("notes").select("content").eq("user_id", user_id).eq("title", title).execute()
        if response.data:
            encrypted = response.data[0]['content']
            cipher = _get_cipher_suite()
            decrypted = cipher.decrypt(encrypted.encode()).decode()
            return decrypted
    except Exception as e:
        logging.error(f"DB Error get_note_content: {e}")
    return None

def db_delete_note(user_id, title):
    """Menghapus catatan."""
    if not supabase: return False
    try:
        supabase.table("notes").delete().eq("user_id", user_id).eq("title", title).execute()
        return True
    except Exception as e:
        logging.error(f"DB Error delete_note: {e}")
        return False