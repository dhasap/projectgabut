import os
import logging
import json
from datetime import datetime
import base64
from cryptography.fernet import Fernet

# --- DATABASE ADAPTER INTERFACE ---
class DatabaseAdapter:
    def save_user(self, user_id, username=None, first_name=None): pass
    def get_all_users(self): return []
    def get_users_count(self): return 0
    def get_user_info(self, user_id): return None
    def get_admins(self, owner_id): return {int(owner_id)}
    def add_admin(self, user_id, username=None): return False
    def remove_admin(self, user_id): return False
    def get_banned(self): return set()
    def ban_user(self, user_id, username=None, reason="Admin Ban"): return False
    def unban_user(self, user_id): return False
    def save_state(self, state_data): pass
    def load_state(self): return {}
    def log_activity(self, admin_id, username, action, details): pass
    def get_activity_logs(self, limit=10): return []
    def set_config(self, key, value): pass
    def save_note(self, user_id, title, content): return False
    def get_notes_list(self, user_id): return []
    def get_note_content(self, user_id, title): return None
    def delete_note(self, user_id, title): return False
    def initialize(self): pass

# --- SUPABASE IMPLEMENTATION ---
class SupabaseAdapter(DatabaseAdapter):
    def __init__(self, url, key):
        from supabase import create_client
        self.client = create_client(url, key)
        logging.info("✅ Menggunakan Database: Supabase")

    def save_user(self, user_id, username=None, first_name=None):
        try:
            data = {
                "user_id": user_id, 
                "username": username,
                "first_name": first_name,
                "last_seen": datetime.utcnow().isoformat()
            }
            self.client.table("users").upsert(data, on_conflict="user_id").execute()
        except Exception as e:
            logging.error(f"Supabase Error save_user: {e}")

    def get_all_users(self):
        try:
            response = self.client.table("users").select("user_id").execute()
            return [item['user_id'] for item in response.data]
        except Exception as e:
            logging.error(f"Supabase Error get_all_users: {e}")
            return []

    def get_users_count(self):
        try:
            response = self.client.table("users").select("user_id", count="exact").execute()
            return response.count
        except Exception as e:
            logging.error(f"Supabase Error get_users_count: {e}")
            return 0

    def get_user_info(self, user_id):
        try:
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            logging.error(f"Supabase Error get_info: {e}")
        return None

    def get_admins(self, owner_id):
        admins = {int(owner_id)}
        try:
            response = self.client.table("admins").select("user_id").execute()
            for item in response.data:
                admins.add(int(item['user_id']))
        except Exception as e:
            logging.error(f"Supabase Error get_admins: {e}")
        return admins

    def add_admin(self, user_id, username=None):
        try:
            data = {
                "user_id": user_id, 
                "username": username,
                "promoted_at": datetime.utcnow().isoformat()
            }
            self.client.table("admins").insert(data).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error add_admin: {e}")
            return False

    def remove_admin(self, user_id):
        try:
            self.client.table("admins").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error remove_admin: {e}")
            return False

    def get_banned(self):
        banned = set()
        try:
            response = self.client.table("banned").select("user_id").execute()
            for item in response.data:
                banned.add(str(item['user_id']))
        except Exception as e:
            logging.error(f"Supabase Error get_banned: {e}")
        return banned

    def ban_user(self, user_id, username=None, reason="Admin Ban"):
        try:
            data = {
                "user_id": user_id, 
                "username": username,
                "reason": reason, 
                "banned_at": datetime.utcnow().isoformat()
            }
            self.client.table("banned").upsert(data).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error ban_user: {e}")
            return False

    def unban_user(self, user_id):
        try:
            self.client.table("banned").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error unban_user: {e}")
            return False

    def save_state(self, state_data):
        try:
            data = {"key": "bot_config", "value": state_data}
            self.client.table("bot_state").upsert(data, on_conflict="key").execute()
        except Exception as e:
            logging.error(f"Supabase Error save_state: {e}")

    def load_state(self):
        try:
            response = self.client.table("bot_state").select("value").eq("key", "bot_config").execute()
            if response.data:
                return response.data[0]['value']
        except Exception as e:
            logging.error(f"Supabase Error load_state: {e}")
        return {}

    def log_activity(self, admin_id, username, action, details):
        try:
            data = {
                "admin_id": admin_id,
                "username": username,
                "action": action,
                "details": details,
                "created_at": datetime.utcnow().isoformat()
            }
            self.client.table("activity_logs").insert(data).execute()
        except Exception as e:
            logging.error(f"Supabase Error log_activity: {e}")

    def get_activity_logs(self, limit=10):
        try:
            response = self.client.table("activity_logs").select("*").order("created_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logging.error(f"Supabase Error get_logs: {e}")
            return []

    def set_config(self, key, value):
        try:
            data = {"key": key, "value": {"text": value}}
            self.client.table("bot_state").upsert(data, on_conflict="key").execute()
        except Exception as e:
            logging.error(f"Supabase Error set_config: {e}")

    def save_note(self, user_id, title, content):
        try:
            cipher = _get_cipher_suite()
            encrypted_content = cipher.encrypt(content.encode()).decode()
            data = {
                "user_id": user_id,
                "title": title,
                "content": encrypted_content,
                "updated_at": datetime.utcnow().isoformat()
            }
            self.client.table("notes").upsert(data, on_conflict="user_id, title").execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error save_note: {e}")
            return False

    def get_notes_list(self, user_id):
        try:
            response = self.client.table("notes").select("title, updated_at").eq("user_id", user_id).execute()
            return response.data
        except Exception as e:
            logging.error(f"Supabase Error get_notes_list: {e}")
            return []

    def get_note_content(self, user_id, title):
        try:
            response = self.client.table("notes").select("content").eq("user_id", user_id).eq("title", title).execute()
            if response.data:
                encrypted = response.data[0]['content']
                cipher = _get_cipher_suite()
                return cipher.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logging.error(f"Supabase Error get_note_content: {e}")
        return None

    def delete_note(self, user_id, title):
        try:
            self.client.table("notes").delete().eq("user_id", user_id).eq("title", title).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase Error delete_note: {e}")
            return False

# --- MYSQL / TiDB IMPLEMENTATION ---
class MySQLAdapter(DatabaseAdapter):
    def __init__(self, host, port, user, password, db_name, ssl_ca=None):
        import mysql.connector
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': db_name,
            'autocommit': True
        }
        if ssl_ca and os.path.exists(ssl_ca):
            self.config['ssl_ca'] = ssl_ca
            
        logging.info("✅ Menggunakan Database: TiDB (MySQL)")
        self.initialize_tables()

    def get_connection(self):
        import mysql.connector
        return mysql.connector.connect(**self.config)

    def initialize_tables(self):
        """Buat tabel jika belum ada."""
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_seen DATETIME
            )""",
            """CREATE TABLE IF NOT EXISTS admins (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                promoted_at DATETIME
            )""",
            """CREATE TABLE IF NOT EXISTS banned (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                reason TEXT,
                banned_at DATETIME
            )""",
            """CREATE TABLE IF NOT EXISTS bot_state (
                `key` VARCHAR(50) PRIMARY KEY,
                value JSON
            )""",
            """CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id BIGINT,
                username VARCHAR(255),
                action VARCHAR(50),
                details TEXT,
                created_at DATETIME
            )""",
            """CREATE TABLE IF NOT EXISTS notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                title VARCHAR(100),
                content TEXT,
                updated_at DATETIME,
                UNIQUE KEY unique_note (user_id, title)
            )"""
        ]
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for q in queries:
                cursor.execute(q)
            conn.close()
        except Exception as e:
            logging.error(f"TiDB Init Error: {e}")

    def save_user(self, user_id, username=None, first_name=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                     VALUES (%s, %s, %s, NOW()) 
                     ON DUPLICATE KEY UPDATE username=%s, first_name=%s, last_seen=NOW()"""
            cursor.execute(sql, (user_id, username, first_name, username, first_name))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error save_user: {e}")

    def get_all_users(self):
        users = []
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_all_users: {e}")
        return users

    def get_users_count(self):
        count = 0
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_users_count: {e}")
        return count

    def get_user_info(self, user_id):
        data = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            data = cursor.fetchone()
            conn.close()
            # Convert datetime to ISO string for compatibility
            if data and 'last_seen' in data and data['last_seen']:
                 data['last_seen'] = data['last_seen'].isoformat()
        except Exception as e:
            logging.error(f"MySQL Error get_user_info: {e}")
        return data

    def get_admins(self, owner_id):
        admins = {int(owner_id)}
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            for row in cursor.fetchall():
                admins.add(int(row[0]))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_admins: {e}")
        return admins

    def add_admin(self, user_id, username=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = "INSERT IGNORE INTO admins (user_id, username, promoted_at) VALUES (%s, %s, NOW())"
            cursor.execute(sql, (user_id, username))
            affected = cursor.rowcount
            conn.close()
            return affected > 0
        except Exception as e:
            logging.error(f"MySQL Error add_admin: {e}")
            return False

    def remove_admin(self, user_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
            conn.close()
            return True
        except Exception as e:
            logging.error(f"MySQL Error remove_admin: {e}")
            return False

    def get_banned(self):
        banned = set()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM banned")
            for row in cursor.fetchall():
                banned.add(str(row[0]))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_banned: {e}")
        return banned

    def ban_user(self, user_id, username=None, reason="Admin Ban"):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = """INSERT INTO banned (user_id, username, reason, banned_at) 
                     VALUES (%s, %s, %s, NOW())
                     ON DUPLICATE KEY UPDATE reason=%s, banned_at=NOW()"""
            cursor.execute(sql, (user_id, username, reason, reason))
            conn.close()
            return True
        except Exception as e:
            logging.error(f"MySQL Error ban_user: {e}")
            return False

    def unban_user(self, user_id):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM banned WHERE user_id = %s", (user_id,))
            conn.close()
            return True
        except Exception as e:
            logging.error(f"MySQL Error unban_user: {e}")
            return False

    def save_state(self, state_data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Serialize JSON
            val_str = json.dumps(state_data)
            sql = "INSERT INTO bot_state (`key`, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s"
            cursor.execute(sql, ("bot_config", val_str, val_str))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error save_state: {e}")

    def load_state(self):
        state = {}
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_state WHERE `key` = 'bot_config'")
            row = cursor.fetchone()
            if row:
                # TiDB might return str or dict depending on driver version with JSON support
                val = row[0]
                if isinstance(val, str):
                    state = json.loads(val)
                else:
                    state = val
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error load_state: {e}")
        return state

    def log_activity(self, admin_id, username, action, details):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO activity_logs (admin_id, username, action, details, created_at) VALUES (%s, %s, %s, %s, NOW())"
            cursor.execute(sql, (admin_id, username, action, details))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error log_activity: {e}")

    def get_activity_logs(self, limit=10):
        logs = []
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT %s", (limit,))
            logs = cursor.fetchall()
            for log in logs:
                if 'created_at' in log:
                    log['created_at'] = log['created_at'].isoformat()
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_logs: {e}")
        return logs

    def set_config(self, key, value):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Wrapper same as Supabase
            val_json = json.dumps({"text": value})
            sql = "INSERT INTO bot_state (`key`, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s"
            cursor.execute(sql, (key, val_json, val_json))
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error set_config: {e}")

    def save_note(self, user_id, title, content):
        try:
            cipher = _get_cipher_suite()
            encrypted_content = cipher.encrypt(content.encode()).decode()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = """INSERT INTO notes (user_id, title, content, updated_at) 
                     VALUES (%s, %s, %s, NOW())
                     ON DUPLICATE KEY UPDATE content=%s, updated_at=NOW()"""
            cursor.execute(sql, (user_id, title, encrypted_content, encrypted_content))
            conn.close()
            return True
        except Exception as e:
            logging.error(f"MySQL Error save_note: {e}")
            return False

    def get_notes_list(self, user_id):
        notes = []
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT title, updated_at FROM notes WHERE user_id = %s", (user_id,))
            notes = cursor.fetchall()
            conn.close()
        except Exception as e:
            logging.error(f"MySQL Error get_notes_list: {e}")
        return notes

    def get_note_content(self, user_id, title):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM notes WHERE user_id = %s AND title = %s", (user_id, title))
            row = cursor.fetchone()
            conn.close()
            if row:
                encrypted = row[0]
                cipher = _get_cipher_suite()
                return cipher.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logging.error(f"MySQL Error get_note_content: {e}")
        return None

    def delete_note(self, user_id, title):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE user_id = %s AND title = %s", (user_id, title))
            affected = cursor.rowcount
            conn.close()
            return affected > 0
        except Exception as e:
            logging.error(f"MySQL Error delete_note: {e}")
            return False

# --- UTILS & INITIALIZATION ---

def _get_cipher_suite():
    secret = os.getenv("SECRET_KEY", "DefaultSecretKeyShouldBeChangedForProd123")
    key_bytes = secret.ljust(32)[:32].encode()
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)

# Global Adapter Instance
adapter: DatabaseAdapter = None

# Environment Config
TIDB_HOST = os.getenv("TIDB_HOST")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if TIDB_HOST:
    try:
        logging.info("⚙️ Mendeteksi konfigurasi TiDB...")
        adapter = MySQLAdapter(
            host=TIDB_HOST,
            port=int(os.getenv("TIDB_PORT", 4000)),
            user=os.getenv("TIDB_USER"),
            password=os.getenv("TIDB_PASSWORD"),
            db_name=os.getenv("TIDB_DB_NAME", "test"),
            ssl_ca=os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")
        )
    except Exception as e:
        logging.error(f"❌ Gagal inisialisasi TiDB: {e}")

if not adapter and SUPABASE_URL:
    try:
        logging.info("⚙️ Mendeteksi konfigurasi Supabase...")
        adapter = SupabaseAdapter(
            url=SUPABASE_URL,
            key=os.getenv("SUPABASE_KEY")
        )
    except Exception as e:
        logging.error(f"❌ Gagal inisialisasi Supabase: {e}")

if not adapter:
    logging.warning("⚠️ TIDAK ADA DATABASE YANG TERHUBUNG! Bot berjalan dengan fitur terbatas.")
    adapter = DatabaseAdapter() # Dummy adapter that does nothing

# --- EXPOSED FUNCTIONS (INTERFACE) ---
def db_save_user(user_id, username=None, first_name=None):
    return adapter.save_user(user_id, username, first_name)

def db_get_all_users():
    return adapter.get_all_users()

def db_get_users_count():
    return adapter.get_users_count()

def db_get_user_info(user_id):
    return adapter.get_user_info(user_id)

def db_get_admins(owner_id):
    return adapter.get_admins(owner_id)

def db_add_admin(user_id, username=None):
    return adapter.add_admin(user_id, username)

def db_remove_admin(user_id):
    return adapter.remove_admin(user_id)

def db_get_banned():
    return adapter.get_banned()

def db_ban_user(user_id, username=None, reason="Admin Ban"):
    return adapter.ban_user(user_id, username, reason)

def db_unban_user(user_id):
    return adapter.unban_user(user_id)

def db_save_state(state_data):
    return adapter.save_state(state_data)

def db_load_state():
    return adapter.load_state()

def db_log_activity(admin_id, username, action, details):
    return adapter.log_activity(admin_id, username, action, details)

def db_get_activity_logs(limit=10):
    return adapter.get_activity_logs(limit)

def db_set_config(key, value):
    return adapter.set_config(key, value)

def db_save_note(user_id, title, content):
    return adapter.save_note(user_id, title, content)

def db_get_notes_list(user_id):
    return adapter.get_notes_list(user_id)

def db_get_note_content(user_id, title):
    return adapter.get_note_content(user_id, title)

def db_delete_note(user_id, title):
    return adapter.delete_note(user_id, title)
