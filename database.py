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
    async def delete_mail_session(self, user_id): return False
    async def get_pending_mail_sessions(self, limit=50): return []
    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None): pass
    async def touch_mail_session(self, user_id, mail_id): return False
    async def update_mail_last_id(self, user_id, msg_id): pass
    
    # Metrics
    metrics = {'count': 0, 'latency_sum': 0, 'errors': 0}

# --- SUPABASE IMPLEMENTATION (ASYNC WRAPPER) ---
class AsyncSupabaseAdapter(AsyncDatabaseAdapter):
    def __init__(self, url, key):
        from supabase import create_client
        self.client = create_client(url, key)
        logging.info("✅ Menggunakan Database: Supabase (Wrapped Async)")

    async def save_user(self, user_id, username=None, first_name=None):
        await asyncio.to_thread(self._save_user_sync, user_id, username, first_name)
    
    def _save_user_sync(self, user_id, username, first_name):
        try:
            data = {"user_id": user_id, "username": username, "first_name": first_name, "last_seen": datetime.utcnow().isoformat()}
            self.client.table("users").upsert(data, on_conflict="user_id").execute()
        except: pass

    async def get_admins(self, owner_id):
        return {int(owner_id)} 

# --- MYSQL / TiDB IMPLEMENTATION (PURE ASYNC) ---
class AsyncMySQLAdapter(AsyncDatabaseAdapter):
    def __init__(self, host, port, user, password, db_name, ssl_ca=None):
        self.db_config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db_name,
            'autocommit': True,
            'connect_timeout': 10,
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        if ssl_ca and os.path.exists(ssl_ca):
            self.db_config['ssl'] = {'ca': ssl_ca}
        
        self.pool = None

    async def initialize(self):
        import aiomysql
        try:
            self.pool = await aiomysql.create_pool(
                minsize=5, 
                maxsize=20, 
                pool_recycle=300, 
                **self.db_config
            )
            logging.info("✅ Menggunakan Database: TiDB (Async Pool Optimized)")
            await self.initialize_tables()
        except Exception as e:
            logging.error(f"❌ Failed creating DB Pool: {e}")
            raise e

    async def initialize_tables(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_seen DATETIME,
                INDEX idx_last_seen (last_seen)
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
                created_at DATETIME,
                INDEX idx_created (created_at)
            )""",
            """CREATE TABLE IF NOT EXISTS notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                title VARCHAR(100),
                content TEXT,
                updated_at DATETIME,
                UNIQUE KEY unique_note (user_id, title),
                INDEX idx_user_note (user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS temp_mail_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                email VARCHAR(255),
                password VARCHAR(255),
                token VARCHAR(500),
                last_msg_id VARCHAR(100),
                next_check_at DATETIME,
                created_at DATETIME,
                INDEX idx_user_mail (user_id),
                INDEX idx_next_check (next_check_at)
            )"""
        ]
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for q in queries:
                    await cur.execute(q)

    async def _exec(self, query, args=None, fetch=False, fetch_one=False, dict_cursor=False):
        """Internal helper for metrics and execution."""
        start_time = time.time()
        try:
            import aiomysql
            cursor_cls = aiomysql.DictCursor if dict_cursor else aiomysql.Cursor
            
            async with self.pool.acquire() as conn:
                async with conn.cursor(cursor_cls) as cur:
                    await cur.execute(query, args)
                    if fetch:
                        return await cur.fetchall()
                    if fetch_one:
                        return await cur.fetchone()
                    return cur.rowcount
        except Exception as e:
            self.metrics['errors'] += 1
            logging.error(f"DB Query Error: {e} | Query: {query[:50]}...")
            return None
        finally:
            self.metrics['count'] += 1
            self.metrics['latency_sum'] += (time.time() - start_time)

    # --- USER MANAGEMENT ---
    
    async def save_user(self, user_id, username=None, first_name=None):
        sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                 VALUES (%s, %s, %s, NOW()) 
                 ON DUPLICATE KEY UPDATE username=%s, first_name=%s, last_seen=NOW()"""
        await self._exec(sql, (user_id, username, first_name, username, first_name))

    async def get_users_batch(self, last_id=0, limit=100):
        rows = await self._exec("SELECT user_id FROM users WHERE user_id > %s ORDER BY user_id ASC LIMIT %s", (last_id, limit), fetch=True)
        return [row[0] for row in rows] if rows else []

    async def get_users_count(self):
        row = await self._exec("SELECT COUNT(1) FROM users", fetch_one=True)
        return row[0] if row else 0

    async def get_user_info(self, user_id):
        data = await self._exec("SELECT * FROM users WHERE user_id = %s", (user_id,), fetch_one=True, dict_cursor=True)
        if data and 'last_seen' in data and data['last_seen']:
            data['last_seen'] = data['last_seen'].isoformat()
        return data

    # --- ADMIN & BANNED ---

    async def get_admins(self, owner_id):
        cached = await cache.get("admins")
        if cached: return set(cached)

        admins = {int(owner_id)}
        rows = await self._exec("SELECT user_id FROM admins", fetch=True)
        if rows:
            for row in rows: admins.add(int(row[0]))
        await cache.set("admins", admins, CACHE_TTL)
        return admins

    async def add_admin(self, user_id, username=None):
        affected = await self._exec("INSERT IGNORE INTO admins (user_id, username, promoted_at) VALUES (%s, %s, NOW())", (user_id, username))
        await cache.delete("admins")
        return affected and affected > 0

    async def remove_admin(self, user_id):
        await self._exec("DELETE FROM admins WHERE user_id = %s", (user_id,))
        await cache.delete("admins")
        return True

    async def get_banned(self):
        cached = await cache.get("banned")
        if cached: return set(cached)
            
        banned = set()
        rows = await self._exec("SELECT user_id FROM banned", fetch=True)
        if rows:
            for row in rows: banned.add(str(row[0]))
        await cache.set("banned", banned, CACHE_TTL)
        return banned

    async def ban_user(self, user_id, username=None, reason="Admin Ban"):
        sql = """INSERT INTO banned (user_id, username, reason, banned_at) 
                 VALUES (%s, %s, %s, NOW())
                 ON DUPLICATE KEY UPDATE reason=%s, banned_at=NOW()"""
        await self._exec(sql, (user_id, username, reason, reason))
        await cache.delete("banned")
        return True

    async def unban_user(self, user_id):
        await self._exec("DELETE FROM banned WHERE user_id = %s", (user_id,))
        await cache.delete("banned")
        return True

    # --- STATE & LOGS ---

    async def save_state(self, state_data):
        val_str = json.dumps(state_data)
        sql = "INSERT INTO bot_state (`key`, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s"
        await self._exec(sql, ("bot_config", val_str, val_str))

    async def load_state(self):
        row = await self._exec("SELECT value FROM bot_state WHERE `key` = 'bot_config'", fetch_one=True)
        if row:
            val = row[0]
            return json.loads(val) if isinstance(val, str) else val
        return {}

    async def log_activity(self, admin_id, username, action, details):
        sql = "INSERT INTO activity_logs (admin_id, username, action, details, created_at) VALUES (%s, %s, %s, %s, NOW())"
        await self._exec(sql, (admin_id, username, action, details))

    async def get_activity_logs(self, limit=10):
        sql = "SELECT id, admin_id, username, action, details, created_at FROM activity_logs ORDER BY created_at DESC LIMIT %s"
        logs = await self._exec(sql, (limit,), fetch=True, dict_cursor=True)
        if logs:
            for log in logs:
                if 'created_at' in log: log['created_at'] = log['created_at'].isoformat()
        return logs or []

    async def set_config(self, key, value):
        val_json = json.dumps({"text": value})
        sql = "INSERT INTO bot_state (`key`, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s"
        await self._exec(sql, (key, val_json, val_json))

    # --- NOTES ---

    async def save_note(self, user_id, title, content):
        cipher = _get_cipher_suite()
        encrypted_content = cipher.encrypt(content.encode()).decode()
        sql = """INSERT INTO notes (user_id, title, content, updated_at) 
                 VALUES (%s, %s, %s, NOW())
                 ON DUPLICATE KEY UPDATE content=%s, updated_at=NOW()"""
        await self._exec(sql, (user_id, title, encrypted_content, encrypted_content))
        return True

    async def get_notes_list(self, user_id):
        # Select ID and Title explicitly for the menu
        return await self._exec("SELECT id, title, updated_at FROM notes WHERE user_id = %s ORDER BY id DESC", (user_id,), fetch=True, dict_cursor=True) or []

    async def get_note_content(self, user_id, identifier):
        # Identifier can be ID (int/digit str) or Title (str)
        if str(identifier).isdigit():
            row = await self._exec("SELECT content, title FROM notes WHERE user_id = %s AND id = %s", (user_id, identifier), fetch_one=True, dict_cursor=True)
        else:
            row = await self._exec("SELECT content, title FROM notes WHERE user_id = %s AND title = %s", (user_id, identifier), fetch_one=True, dict_cursor=True)
            
        if row:
            cipher = _get_cipher_suite()
            try:
                decrypted = cipher.decrypt(row['content'].encode()).decode()
                return {"title": row['title'], "content": decrypted}
            except Exception as e:
                logging.error(f"Decryption failed: {e}")
                return {"title": row['title'], "content": "[Error: Gagal dekripsi catatan]"}
        return None

    async def delete_note(self, user_id, identifier):
        if str(identifier).isdigit():
            affected = await self._exec("DELETE FROM notes WHERE user_id = %s AND id = %s", (user_id, identifier))
        else:
            affected = await self._exec("DELETE FROM notes WHERE user_id = %s AND title = %s", (user_id, identifier))
        return affected and affected > 0

    # --- MAIL SESSIONS (ADAPTIVE & HISTORY) ---

    async def save_mail_session(self, user_id, email, password, token):
        # Insert as new history record
        sql = """INSERT INTO temp_mail_sessions (user_id, email, password, token, created_at, next_check_at) 
                 VALUES (%s, %s, %s, %s, NOW(), NOW())"""
        await self._exec(sql, (user_id, email, password, token))
        return True

    async def get_mail_session(self, user_id):
        # Get latest active session (highest ID/created_at)
        return await self._exec("SELECT * FROM temp_mail_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,), fetch_one=True, dict_cursor=True)

    async def get_mail_sessions_list(self, user_id, limit=20):
        # List history
        return await self._exec("SELECT * FROM temp_mail_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (user_id, limit), fetch=True, dict_cursor=True) or []

    async def delete_mail_session(self, user_id, mail_id=None):
        if mail_id:
            await self._exec("DELETE FROM temp_mail_sessions WHERE user_id = %s AND id = %s", (user_id, mail_id))
        else:
            await self._exec("DELETE FROM temp_mail_sessions WHERE user_id = %s", (user_id,))
        return True

    async def touch_mail_session(self, user_id, mail_id):
        # Bring to top (Active) by updating created_at
        await self._exec("UPDATE temp_mail_sessions SET created_at = NOW() WHERE user_id = %s AND id = %s", (user_id, mail_id))
        return True

    async def get_pending_mail_sessions(self, limit=50):
        # Fetch sessions where next_check_at is in the past
        return await self._exec("SELECT user_id, token, last_msg_id FROM temp_mail_sessions WHERE next_check_at <= NOW() LIMIT %s", (limit,), fetch=True, dict_cursor=True) or []

    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None):
        next_dt = datetime.fromtimestamp(next_check_timestamp)
        if last_msg_id:
            await self._exec("UPDATE temp_mail_sessions SET next_check_at = %s, last_msg_id = %s WHERE user_id = %s", (next_dt, last_msg_id, user_id))
        else:
            await self._exec("UPDATE temp_mail_sessions SET next_check_at = %s WHERE user_id = %s", (next_dt, user_id))

    async def update_mail_last_id(self, user_id, msg_id):
        await self.update_mail_check_time(user_id, time.time(), msg_id)

# --- UTILS ---

def _get_cipher_suite():
    secret = os.getenv("SECRET_KEY", "DefaultSecretKeyShouldBeChangedForProd123")
    key_bytes = secret.ljust(32)[:32].encode()
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)

# Global Adapter
adapter: AsyncDatabaseAdapter = None

# Env Config
TIDB_HOST = os.getenv("TIDB_HOST")
SUPABASE_URL = os.getenv("SUPABASE_URL")

async def init_db():
    global adapter
    if TIDB_HOST:
        try:
            logging.info("⚙️ Connecting to TiDB (Async)...")
            adapter = AsyncMySQLAdapter(
                host=TIDB_HOST,
                port=int(os.getenv("TIDB_PORT", 4000)),
                user=os.getenv("TIDB_USER"),
                password=os.getenv("TIDB_PASSWORD"),
                db_name=os.getenv("TIDB_DB_NAME", "test"),
                ssl_ca=os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")
            )
            await adapter.initialize()
        except Exception as e:
            logging.error(f"❌ TiDB Async Init Failed: {e}")

    if not adapter and SUPABASE_URL:
        try:
            adapter = AsyncSupabaseAdapter(url=SUPABASE_URL, key=os.getenv("SUPABASE_KEY"))
        except: pass

    if not adapter:
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
