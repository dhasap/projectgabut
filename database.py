import os
import logging
import json
import time
import asyncio
from datetime import datetime
import base64
from cryptography.fernet import Fernet

# --- ASYNC REDIS CACHE ---
try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import aiosqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

class AsyncCacheManager:
    def __init__(self):
        self.redis = None
        self.local_cache = {}
        redis_url = os.getenv("REDIS_URL")
        env_mode = os.getenv("ENV", "development").lower()
        
        if HAS_REDIS and redis_url:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                logging.info("✅ Cache: Menggunakan Redis (Async)")
            except Exception as e:
                logging.error(f"❌ Redis Init Failed: {e}")
                if env_mode == "production":
                    raise RuntimeError("Redis is MANDATORY in production!")
        elif env_mode == "production":
             raise RuntimeError("Redis URL not set in PRODUCTION mode!")

    async def get(self, key):
        # 1. Try Redis
        if self.redis:
            try:
                val = await self.redis.get(key)
                if val: return json.loads(val)
            except Exception as e:
                logging.error(f"Redis Get Error: {e}")

        # 2. Fallback to Local RAM
        entry = self.local_cache.get(key)
        if entry and entry['expiry'] > time.time():
            return entry['data']
        return None

    async def set(self, key, value, ttl=300):
        # 1. Set Redis
        if self.redis:
            try:
                # Convert sets to list for JSON serialization
                if isinstance(value, set):
                    val_serializable = list(value)
                else:
                    val_serializable = value
                await self.redis.setex(key, ttl, json.dumps(val_serializable))
            except Exception as e:
                logging.error(f"Redis Set Error: {e}")

        # 2. Set Local RAM
        self.local_cache[key] = {"data": value, "expiry": time.time() + ttl}

    async def delete(self, key):
        if self.redis:
            try: await self.redis.delete(key)
            except: pass
        if key in self.local_cache:
            del self.local_cache[key]

# Initialize Global Cache
cache = AsyncCacheManager()
CACHE_TTL = 300  # 5 Menit

# --- DATABASE ADAPTER INTERFACE ---
class AsyncDatabaseAdapter:
    async def initialize(self): pass
    async def save_user(self, user_id, username=None, first_name=None): pass
    async def get_users_batch(self, last_id=0, limit=100): return []
    async def get_users_count(self): return 0
    async def get_user_info(self, user_id): return None
    async def get_admins(self, owner_id): return {int(owner_id)}
    async def add_admin(self, user_id, username=None): return False
    async def remove_admin(self, user_id): return False
    async def get_banned(self): return set()
    async def ban_user(self, user_id, username=None, reason="Admin Ban"): return False
    async def unban_user(self, user_id): return False
    async def save_state(self, state_data): pass
    async def load_state(self): return {}
    async def log_activity(self, admin_id, username, action, details): pass
    async def get_activity_logs(self, limit=10): return []
    async def set_config(self, key, value): pass
    async def save_note(self, user_id, title, content): return False
    async def get_notes_list(self, user_id): return []
    async def get_note_content(self, user_id, title): return None
    async def delete_note(self, user_id, title): return False
    async def save_mail_session(self, user_id, email, password, token): pass
    async def get_mail_session(self, user_id): return None
    async def get_mail_sessions_list(self, user_id, limit=10): return []
    async def delete_mail_session(self, user_id, mail_id=None): return False
    async def get_pending_mail_sessions(self, limit=50): return []
    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None): pass
    async def touch_mail_session(self, user_id, mail_id): return False
    async def update_mail_last_id(self, user_id, msg_id): pass
    
    # Metrics
    metrics = {'count': 0, 'latency_sum': 0, 'errors': 0}



# --- SQLITE IMPLEMENTATION ---
class AsyncSQLiteAdapter(AsyncDatabaseAdapter):
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
        logging.info(f"✅ Menggunakan Database: SQLite ({db_path})")

    async def initialize(self):
        if not HAS_SQLITE:
            raise ImportError("aiosqlite not installed")
        
        # Init tables
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_seen TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                promoted_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS banned (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reason TEXT,
                banned_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                username TEXT,
                action TEXT,
                details TEXT,
                created_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                updated_at TEXT,
                UNIQUE (user_id, title)
            )""",
            """CREATE TABLE IF NOT EXISTS mail_sessions_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                password TEXT,
                token TEXT,
                last_msg_id TEXT,
                created_at TEXT,
                next_check_at TEXT
            )"""
        ]
        async with aiosqlite.connect(self.db_path) as db:
            for q in queries:
                await db.execute(q)
            await db.commit()

    async def _exec(self, query, args=(), fetch=False, fetch_one=False, dict_cursor=False):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if dict_cursor:
                    db.row_factory = aiosqlite.Row
                async with db.execute(query, args) as cursor:
                    if fetch:
                        res = await cursor.fetchall()
                        if dict_cursor:
                            return [dict(r) for r in res]
                        return res
                    if fetch_one:
                        res = await cursor.fetchone()
                        if dict_cursor and res:
                            return dict(res)
                        return res
                    await db.commit()
                    return cursor.rowcount
        except Exception as e:
            logging.error(f"SQLite Query Error: {e} | Query: {query}")
            return None

    # Implement all methods using SQLite syntax (?)
    
    async def save_user(self, user_id, username=None, first_name=None):
        sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                 VALUES (?, ?, ?, ?) 
                 ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name, last_seen=excluded.last_seen"""
        now = datetime.utcnow().isoformat()
        await self._exec(sql, (user_id, username, first_name, now))

    async def get_users_batch(self, last_id=0, limit=100):
        rows = await self._exec("SELECT user_id FROM users WHERE user_id > ? ORDER BY user_id ASC LIMIT ?", (last_id, limit), fetch=True)
        return [row[0] for row in rows] if rows else []

    async def get_users_count(self):
        row = await self._exec("SELECT COUNT(1) FROM users", fetch_one=True)
        return row[0] if row else 0

    async def get_user_info(self, user_id):
        return await self._exec("SELECT * FROM users WHERE user_id = ?", (user_id,), fetch_one=True, dict_cursor=True)

    async def get_admins(self, owner_id):
        admins = {int(owner_id)}
        rows = await self._exec("SELECT user_id FROM admins", fetch=True)
        if rows:
            for row in rows: admins.add(int(row[0]))
        return admins

    async def add_admin(self, user_id, username=None):
        await self._exec("INSERT OR IGNORE INTO admins (user_id, username, promoted_at) VALUES (?, ?, ?)", (user_id, username, datetime.utcnow().isoformat()))
        return True

    async def remove_admin(self, user_id):
        await self._exec("DELETE FROM admins WHERE user_id = ?", (user_id,))
        return True

    async def get_banned(self):
        banned = set()
        rows = await self._exec("SELECT user_id FROM banned", fetch=True)
        if rows:
            for row in rows: banned.add(str(row[0]))
        return banned

    async def ban_user(self, user_id, username=None, reason="Admin Ban"):
        sql = """INSERT INTO banned (user_id, username, reason, banned_at) 
                 VALUES (?, ?, ?, ?)
                 ON CONFLICT(user_id) DO UPDATE SET reason=excluded.reason, banned_at=excluded.banned_at"""
        await self._exec(sql, (user_id, username, reason, datetime.utcnow().isoformat()))
        return True

    async def unban_user(self, user_id):
        await self._exec("DELETE FROM banned WHERE user_id = ?", (user_id,))
        return True

    async def save_state(self, state_data):
        val_str = json.dumps(state_data)
        sql = "INSERT INTO bot_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        await self._exec(sql, ("bot_config", val_str))

    async def load_state(self):
        row = await self._exec("SELECT value FROM bot_state WHERE key = 'bot_config'", fetch_one=True)
        if row:
            return json.loads(row[0])
        return {}

    async def save_note(self, user_id, title, content):
        return await AsyncTursoAdapter.save_note(self, user_id, title, content) # Delegate to Turso/Shared logic

    async def get_notes_list(self, user_id):
        return await AsyncTursoAdapter.get_notes_list(self, user_id) # Delegate

    async def get_note_content(self, user_id, identifier):
        return await AsyncTursoAdapter.get_note_content(self, user_id, identifier) # Delegate

    async def delete_note(self, user_id, identifier):
        return await AsyncTursoAdapter.delete_note(self, user_id, identifier) # Delegate

    async def save_mail_session(self, user_id, email, password, token):
        return await AsyncTursoAdapter.save_mail_session(self, user_id, email, password, token)

    async def get_mail_session(self, user_id):
        return await AsyncTursoAdapter.get_mail_session(self, user_id)

    async def get_mail_sessions_list(self, user_id, limit=20):
        return await AsyncTursoAdapter.get_mail_sessions_list(self, user_id, limit)

    async def delete_mail_session(self, user_id, mail_id=None):
        return await AsyncTursoAdapter.delete_mail_session(self, user_id, mail_id)

    async def get_pending_mail_sessions(self, limit=50):
        return [] # Skipped

# --- TURSO IMPLEMENTATION (LibSQL) ---
class AsyncTursoAdapter(AsyncDatabaseAdapter):
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.client = None
        logging.info("✅ Menggunakan Database: Turso (LibSQL Remote)")

    async def initialize(self):
        import libsql_client
        self.client = libsql_client.create_client(url=self.url, auth_token=self.token)
        
        # Init tables
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_seen TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                promoted_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS banned (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reason TEXT,
                banned_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                username TEXT,
                action TEXT,
                details TEXT,
                created_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                updated_at TEXT
            )""", # Removed UNIQUE (user_id, title) because we encrypt titles now
            """CREATE TABLE IF NOT EXISTS mail_sessions_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                password TEXT,
                token TEXT,
                last_msg_id TEXT,
                created_at TEXT,
                next_check_at TEXT
            )"""
        ]
        # Note: We can't easily DROP the UNIQUE constraint on existing table in SQLite/LibSQL without recreation.
        # But we will handle logic in Python.
        for q in queries:
            try: await self.client.execute(q)
            except: pass

    async def _exec(self, query, args=(), fetch=False, fetch_one=False, dict_cursor=False):
        try:
            start_time = time.time()
            res = await self.client.execute(query, args)
            self.metrics['count'] += 1
            self.metrics['latency_sum'] += (time.time() - start_time)

            if fetch:
                if dict_cursor:
                    return [dict(zip(res.columns, row)) for row in res.rows]
                return res.rows
            if fetch_one:
                if res.rows:
                    if dict_cursor:
                        return dict(zip(res.columns, res.rows[0]))
                    return res.rows[0]
                return None
            return res.rows_affected
        except Exception as e:
            self.metrics['errors'] += 1
            logging.error(f"Turso Query Error: {e} | Query: {query[:50]}")
            return None

    # ... User/Admin/State methods (No change needed) ...
    async def save_user(self, user_id, username=None, first_name=None):
        sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                 VALUES (?, ?, ?, ?) 
                 ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name, last_seen=excluded.last_seen"""
        now = datetime.utcnow().isoformat()
        await self._exec(sql, (user_id, username, first_name, now))

    async def get_users_batch(self, last_id=0, limit=100):
        rows = await self._exec("SELECT user_id FROM users WHERE user_id > ? ORDER BY user_id ASC LIMIT ?", (last_id, limit), fetch=True)
        return [row[0] for row in rows] if rows else []

    async def get_users_count(self):
        row = await self._exec("SELECT COUNT(1) FROM users", fetch_one=True)
        return row[0] if row else 0

    async def get_user_info(self, user_id):
        return await self._exec("SELECT * FROM users WHERE user_id = ?", (user_id,), fetch_one=True, dict_cursor=True)

    async def get_admins(self, owner_id):
        cached = await cache.get("admins")
        if cached: return set(cached)
        
        admins = {int(owner_id)}
        rows = await self._exec("SELECT user_id FROM admins", fetch=True)
        if rows:
            for row in rows: admins.add(int(row[0]))
        await cache.set("admins", list(admins), CACHE_TTL)
        return admins

    async def add_admin(self, user_id, username=None):
        await self._exec("INSERT OR IGNORE INTO admins (user_id, username, promoted_at) VALUES (?, ?, ?)", (user_id, username, datetime.utcnow().isoformat()))
        await cache.delete("admins")
        return True

    async def remove_admin(self, user_id):
        await self._exec("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await cache.delete("admins")
        return True

    async def get_banned(self):
        cached = await cache.get("banned")
        if cached: return set(cached)
            
        banned = set()
        rows = await self._exec("SELECT user_id FROM banned", fetch=True)
        if rows:
            for row in rows: banned.add(str(row[0]))
        await cache.set("banned", list(banned), CACHE_TTL)
        return banned

    async def ban_user(self, user_id, username=None, reason="Admin Ban"):
        sql = """INSERT INTO banned (user_id, username, reason, banned_at) 
                 VALUES (?, ?, ?, ?)
                 ON CONFLICT(user_id) DO UPDATE SET reason=excluded.reason, banned_at=excluded.banned_at"""
        await self._exec(sql, (user_id, username, reason, datetime.utcnow().isoformat()))
        await cache.delete("banned")
        return True

    async def unban_user(self, user_id):
        await self._exec("DELETE FROM banned WHERE user_id = ?", (user_id,))
        await cache.delete("banned")
        return True

    async def save_state(self, state_data):
        val_str = json.dumps(state_data)
        sql = "INSERT INTO bot_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        await self._exec(sql, ("bot_config", val_str))

    async def load_state(self):
        row = await self._exec("SELECT value FROM bot_state WHERE key = 'bot_config'", fetch_one=True)
        if row:
            return json.loads(row[0])
        return {}

    async def log_activity(self, admin_id, username, action, details):
        sql = "INSERT INTO activity_logs (admin_id, username, action, details, created_at) VALUES (?, ?, ?, ?, ?)"
        await self._exec(sql, (admin_id, username, action, details, datetime.utcnow().isoformat()))

    async def get_activity_logs(self, limit=10):
        return await self._exec("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,), fetch=True, dict_cursor=True) or []

    async def set_config(self, key, value):
        val_json = json.dumps({"text": value})
        sql = "INSERT INTO bot_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        await self._exec(sql, (key, val_json))

    # --- NOTES WITH ENCRYPTED TITLES ---

    async def save_note(self, user_id, title, content):
        title = str(title).strip()
        
        # 1. Fetch all notes to check duplicates (Manual UNIQUE check)
        existing_notes = await self.get_notes_list(user_id)
        existing_id = None
        for note in existing_notes:
            if note['title'] == title:
                existing_id = note['id']
                break
        
        cipher = _get_cipher_suite()
        enc_title = cipher.encrypt(title.encode()).decode()
        enc_content = cipher.encrypt(content.encode()).decode()
        
        if existing_id:
            # Update existing
            sql = "UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?"
            await self._exec(sql, (enc_title, enc_content, datetime.utcnow().isoformat(), existing_id))
        else:
            # Insert new (Ignore UNIQUE constraint error if it still exists in DB)
            sql = "INSERT INTO notes (user_id, title, content, updated_at) VALUES (?, ?, ?, ?)"
            await self._exec(sql, (user_id, enc_title, enc_content, datetime.utcnow().isoformat()))
        return True

    async def get_notes_list(self, user_id):
        rows = await self._exec("SELECT id, title, updated_at FROM notes WHERE user_id = ? ORDER BY id DESC", (user_id,), fetch=True, dict_cursor=True) or []
        # Decrypt titles on the fly
        final_list = []
        for row in rows:
            row['title'] = _try_decrypt(row['title'])
            final_list.append(row)
        return final_list

    async def get_note_content(self, user_id, identifier):
        # We need to find the correct ID first because we can't search by Encrypted Title directly in SQL
        target_id = None
        target_title = None
        
        if str(identifier).isdigit():
            target_id = int(identifier)
        else:
            # Identifier is a Title (Plain Text from User)
            # We must fetch list and match
            all_notes = await self.get_notes_list(user_id)
            for note in all_notes:
                if note['title'] == identifier:
                    target_id = note['id']
                    target_title = note['title']
                    break
        
        if not target_id:
            return None
            
        row = await self._exec("SELECT content, title FROM notes WHERE id = ?", (target_id,), fetch_one=True, dict_cursor=True)
        if row:
            return {
                "title": _try_decrypt(row['title']),
                "content": _try_decrypt(row['content'])
            }
        return None

    async def delete_note(self, user_id, identifier):
        target_id = None
        if str(identifier).isdigit():
            target_id = int(identifier)
        else:
             # Identifier is a Title
            all_notes = await self.get_notes_list(user_id)
            for note in all_notes:
                if note['title'] == identifier:
                    target_id = note['id']
                    break
        
        if target_id:
            affected = await self._exec("DELETE FROM notes WHERE id = ?", (target_id,))
            return affected and affected > 0
        return False

    # --- MAIL SESSIONS WITH ENCRYPTED EMAILS ---

    async def save_mail_session(self, user_id, email, password, token):
        cipher = _get_cipher_suite()
        enc_email = cipher.encrypt(email.encode()).decode()
        enc_pass = cipher.encrypt(password.encode()).decode()

        sql = """INSERT INTO mail_sessions_v2 (user_id, email, password, token, created_at) 
                 VALUES (?, ?, ?, ?, ?)"""
        res = await self._exec(sql, (user_id, enc_email, enc_pass, token, datetime.utcnow().isoformat()))
        return res is not None

    async def get_mail_session(self, user_id):
        row = await self._exec("SELECT * FROM mail_sessions_v2 WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,), fetch_one=True, dict_cursor=True)
        if row:
            row['email'] = _try_decrypt(row['email'])
            row['password'] = _try_decrypt(row['password'])
        return row

    async def get_mail_sessions_list(self, user_id, limit=20):
        rows = await self._exec("SELECT * FROM mail_sessions_v2 WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit), fetch=True, dict_cursor=True) or []
        for row in rows:
            row['email'] = _try_decrypt(row['email'])
            row['password'] = _try_decrypt(row['password'])
        return rows

    async def delete_mail_session(self, user_id, mail_id=None):
        if mail_id:
            # mail_id here is the Email Address (Plain text)
            # We must find the ID first
            all_mails = await self.get_mail_sessions_list(user_id, limit=100)
            target_db_id = None
            for mail in all_mails:
                if mail['email'] == mail_id:
                    target_db_id = mail['id']
                    break
            
            if target_db_id:
                res = await self._exec("DELETE FROM mail_sessions_v2 WHERE id = ?", (target_db_id,))
                return res is not None
            return False
        else:
            res = await self._exec("DELETE FROM mail_sessions_v2 WHERE user_id = ?", (user_id,))
            return res is not None

    async def touch_mail_session(self, user_id, mail_id):
        # mail_id is Email Address
        all_mails = await self.get_mail_sessions_list(user_id, limit=100)
        target_db_id = None
        for mail in all_mails:
            if mail['email'] == mail_id:
                target_db_id = mail['id']
                break
        
        if target_db_id:
            sql = "UPDATE mail_sessions_v2 SET created_at = ? WHERE id = ?"
            res = await self._exec(sql, (datetime.utcnow().isoformat(), target_db_id))
            return res is not None
        return False

    async def get_pending_mail_sessions(self, limit=50):
        now = datetime.utcnow().isoformat()
        rows = await self._exec("SELECT user_id, token, last_msg_id, email, password FROM mail_sessions_v2 WHERE next_check_at <= ? OR next_check_at IS NULL ORDER BY created_at DESC LIMIT ?", (now, limit), fetch=True, dict_cursor=True) or []
        # No need to decrypt email/pass here unless the bot logic needs them decrypted to login
        # Usually checking mail requires login, so yes:
        for row in rows:
            row['email'] = _try_decrypt(row['email'])
            row['password'] = _try_decrypt(row['password'])
        return rows

    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None):
        next_check = datetime.fromtimestamp(next_check_timestamp).isoformat()
        if last_msg_id:
            await self._exec("UPDATE mail_sessions_v2 SET next_check_at = ?, last_msg_id = ? WHERE user_id = ?", (next_check, last_msg_id, user_id))
        else:
            await self._exec("UPDATE mail_sessions_v2 SET next_check_at = ? WHERE user_id = ?", (next_check, user_id))

    async def update_mail_last_id(self, user_id, msg_id):
        await self._exec("UPDATE mail_sessions_v2 SET last_msg_id = ? WHERE user_id = ?", (msg_id, user_id))

# --- UTILS ---

def _get_cipher_suite():
    secret = os.getenv("SECRET_KEY", "DefaultSecretKeyShouldBeChangedForProd123")
    key_bytes = secret.ljust(32)[:32].encode()
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)

def _try_decrypt(text):
    if not text: return ""
    try:
        cipher = _get_cipher_suite()
        return cipher.decrypt(text.encode()).decode()
    except:
        return text # Return original if decryption fails (Fallback for old data)

# Global Adapter
adapter: AsyncDatabaseAdapter = None

# Env Config
TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

async def init_db():
    global adapter
    
    if TURSO_URL and TURSO_TOKEN:
        try:
            adapter = AsyncTursoAdapter(url=TURSO_URL, token=TURSO_TOKEN)
            await adapter.initialize()
        except Exception as e:
            logging.error(f"❌ Turso Init Failed: {e}")
            adapter = None

    if not adapter and HAS_SQLITE:
        try:
            adapter = AsyncSQLiteAdapter()
            await adapter.initialize()
        except Exception as e:
            logging.error(f"❌ SQLite Init Failed: {e}")

    if not adapter:
        logging.warning("⚠️ Using Dummy Adapter (No Persistent Storage)!")
        adapter = AsyncDatabaseAdapter() # Dummy

# --- WRAPPER FUNCTIONS (GLOBAL) ---
async def db_save_user(user_id, username=None, first_name=None): return await adapter.save_user(user_id, username, first_name)
async def db_get_users_batch(last_id=0, limit=100): return await adapter.get_users_batch(last_id, limit)
async def db_get_users_count(): return await adapter.get_users_count()
async def db_get_user_info(user_id): return await adapter.get_user_info(user_id)
async def db_get_admins(owner_id): return await adapter.get_admins(owner_id)
async def db_add_admin(user_id, username=None): return await adapter.add_admin(user_id, username)
async def db_remove_admin(user_id): return await adapter.remove_admin(user_id)
async def db_get_banned(): return await adapter.get_banned()
async def db_ban_user(user_id, username=None, reason="Admin Ban"): return await adapter.ban_user(user_id, username, reason)
async def db_unban_user(user_id): return await adapter.unban_user(user_id)
async def db_save_state(state_data): return await adapter.save_state(state_data)
async def db_load_state(): return await adapter.load_state()
async def db_log_activity(admin_id, username, action, details): return await adapter.log_activity(admin_id, username, action, details)
async def db_get_activity_logs(limit=10): return await adapter.get_activity_logs(limit)
async def db_set_config(key, value): return await adapter.set_config(key, value)
async def db_save_note(user_id, title, content): return await adapter.save_note(user_id, title, content)
async def db_get_notes_list(user_id): return await adapter.get_notes_list(user_id)
async def db_get_note_content(user_id, identifier): return await adapter.get_note_content(user_id, identifier)
async def db_delete_note(user_id, identifier): return await adapter.delete_note(user_id, identifier)
async def db_save_mail_session(user_id, email, password, token): return await adapter.save_mail_session(user_id, email, password, token)
async def db_get_mail_session(user_id): return await adapter.get_mail_session(user_id)
async def db_get_mail_sessions_list(user_id, limit=20): return await adapter.get_mail_sessions_list(user_id, limit)
async def db_delete_mail_session(user_id, mail_id=None): return await adapter.delete_mail_session(user_id, mail_id)
async def db_touch_mail_session(user_id, mail_id): return await adapter.touch_mail_session(user_id, mail_id)
async def db_get_pending_mail_sessions(limit=50): return await adapter.get_pending_mail_sessions(limit)
async def db_update_mail_check_time(user_id, next_ts, last_msg_id=None): return await adapter.update_mail_check_time(user_id, next_ts, last_msg_id)
async def db_update_mail_last_id(user_id, msg_id): return await adapter.update_mail_last_id(user_id, msg_id)
async def db_get_metrics(): return adapter.metrics if adapter else {}