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

    async def save_state(self, state_data):
        await asyncio.to_thread(self._save_state_sync, state_data)

    def _save_state_sync(self, state_data):
        try:
            payload = {"key": "bot_config", "value": state_data}
            self.client.table("bot_state").upsert(payload, on_conflict="key").execute()
        except Exception as e:
            logging.error(f"Supabase save_state error: {e}")

    async def load_state(self):
        return await asyncio.to_thread(self._load_state_sync)

    def _load_state_sync(self):
        try:
            res = self.client.table("bot_state").select("value").eq("key", "bot_config").limit(1).execute()
            if res.data:
                return res.data[0].get("value") or {}
        except Exception as e:
            logging.error(f"Supabase load_state error: {e}")
        return {}

    async def set_config(self, key, value):
        await asyncio.to_thread(self._set_config_sync, key, value)

    def _set_config_sync(self, key, value):
        try:
            payload = {"key": key, "value": {"text": value}}
            self.client.table("bot_state").upsert(payload, on_conflict="key").execute()
        except Exception as e:
            logging.error(f"Supabase set_config error: {e}")

    async def save_note(self, user_id, title, content):
        return await asyncio.to_thread(self._save_note_sync, user_id, title, content)

    def _save_note_sync(self, user_id, title, content):
        try:
            cipher = _get_cipher_suite()
            encrypted_content = cipher.encrypt(content.encode()).decode()
            payload = {
                "user_id": user_id,
                "title": title,
                "content": encrypted_content,
                "updated_at": datetime.utcnow().isoformat()
            }
            self.client.table("notes").upsert(payload, on_conflict="user_id,title").execute()
            return True
        except Exception as e:
            logging.error(f"Supabase save_note error: {e}")
            return False

    async def get_notes_list(self, user_id):
        return await asyncio.to_thread(self._get_notes_list_sync, user_id)

    def _get_notes_list_sync(self, user_id):
        try:
            res = (
                self.client.table("notes")
                .select("id,title,updated_at")
                .eq("user_id", user_id)
                .order("id", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logging.error(f"Supabase get_notes_list error: {e}")
            return []

    async def get_note_content(self, user_id, identifier):
        return await asyncio.to_thread(self._get_note_content_sync, user_id, identifier)

    def _get_note_content_sync(self, user_id, identifier):
        try:
            query = self.client.table("notes").select("content,title").eq("user_id", user_id)
            if str(identifier).isdigit():
                query = query.eq("id", int(identifier))
            else:
                query = query.eq("title", identifier)
            res = query.limit(1).execute()
            if not res.data:
                return None
            row = res.data[0]
            cipher = _get_cipher_suite()
            try:
                decrypted = cipher.decrypt(row["content"].encode()).decode()
            except Exception as e:
                logging.error(f"Supabase decrypt error: {e}")
                decrypted = "[Error: Gagal dekripsi catatan]"
            return {"title": row.get("title"), "content": decrypted}
        except Exception as e:
            logging.error(f"Supabase get_note_content error: {e}")
            return None

    async def delete_note(self, user_id, identifier):
        return await asyncio.to_thread(self._delete_note_sync, user_id, identifier)

    def _delete_note_sync(self, user_id, identifier):
        try:
            query = self.client.table("notes").delete().eq("user_id", user_id)
            if str(identifier).isdigit():
                query = query.eq("id", int(identifier))
            else:
                query = query.eq("title", identifier)
            res = query.execute()
            return bool(res.data)
        except Exception as e:
            logging.error(f"Supabase delete_note error: {e}")
            return False

    async def save_mail_session(self, user_id, email, password, token):
        return await asyncio.to_thread(self._save_mail_session_sync, user_id, email, password, token)

    def _save_mail_session_sync(self, user_id, email, password, token):
        try:
            payload = {
                "user_id": user_id,
                "email": email,
                "password": password,
                "token": token,
                "created_at": datetime.utcnow().isoformat(),
                "next_check_at": datetime.utcnow().isoformat()
            }
            self.client.table("temp_mail_sessions").insert(payload).execute()
            return True
        except Exception as e:
            logging.error(f"Supabase save_mail_session error: {e}")
            return False

    async def get_mail_session(self, user_id):
        return await asyncio.to_thread(self._get_mail_session_sync, user_id)

    def _get_mail_session_sync(self, user_id):
        try:
            res = (
                self.client.table("temp_mail_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logging.error(f"Supabase get_mail_session error: {e}")
            return None

    async def get_mail_sessions_list(self, user_id, limit=20):
        return await asyncio.to_thread(self._get_mail_sessions_list_sync, user_id, limit)

    def _get_mail_sessions_list_sync(self, user_id, limit):
        try:
            res = (
                self.client.table("temp_mail_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logging.error(f"Supabase get_mail_sessions_list error: {e}")
            return []

    async def delete_mail_session(self, user_id, mail_id=None):
        return await asyncio.to_thread(self._delete_mail_session_sync, user_id, mail_id)

    def _delete_mail_session_sync(self, user_id, mail_id):
        try:
            query = self.client.table("temp_mail_sessions").delete().eq("user_id", user_id)
            if mail_id:
                query = query.eq("id", mail_id)
            res = query.execute()
            return bool(res.data)
        except Exception as e:
            logging.error(f"Supabase delete_mail_session error: {e}")
            return False

    async def touch_mail_session(self, user_id, mail_id):
        return await asyncio.to_thread(self._touch_mail_session_sync, user_id, mail_id)

    def _touch_mail_session_sync(self, user_id, mail_id):
        try:
            payload = {"created_at": datetime.utcnow().isoformat()}
            res = (
                self.client.table("temp_mail_sessions")
                .update(payload)
                .eq("user_id", user_id)
                .eq("id", mail_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logging.error(f"Supabase touch_mail_session error: {e}")
            return False

    async def get_pending_mail_sessions(self, limit=50):
        return await asyncio.to_thread(self._get_pending_mail_sessions_sync, limit)

    def _get_pending_mail_sessions_sync(self, limit):
        try:
            now = datetime.utcnow().isoformat()
            res = (
                self.client.table("temp_mail_sessions")
                .select("user_id,token,last_msg_id")
                .lte("next_check_at", now)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logging.error(f"Supabase get_pending_mail_sessions error: {e}")
            return []

    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None):
        await asyncio.to_thread(self._update_mail_check_time_sync, user_id, next_check_timestamp, last_msg_id)

    def _update_mail_check_time_sync(self, user_id, next_check_timestamp, last_msg_id=None):
        try:
            payload = {"next_check_at": datetime.fromtimestamp(next_check_timestamp).isoformat()}
            if last_msg_id:
                payload["last_msg_id"] = last_msg_id
            self.client.table("temp_mail_sessions").update(payload).eq("user_id", user_id).execute()
        except Exception as e:
            logging.error(f"Supabase update_mail_check_time error: {e}")

    async def update_mail_last_id(self, user_id, msg_id):
        await self.update_mail_check_time(user_id, time.time(), msg_id)

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
            if os.getenv("RESET_DB", "").lower() in {"1", "true", "yes"}:
                logging.warning("⚠️ RESET_DB aktif, menghapus & membuat ulang semua tabel.")
                await self.recreate_tables()
            else:
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
                user_id BIGINT,
                email VARCHAR(255),
                password VARCHAR(255),
                token VARCHAR(500),
                last_msg_id VARCHAR(100),
                created_at DATETIME,
                INDEX idx_user_mail (user_id),
                INDEX idx_created (created_at)
            )"""
        ]
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for q in queries:
                    await cur.execute(q)

    async def recreate_tables(self):
        drop_queries = [
            "DROP TABLE IF EXISTS temp_mail_sessions",
            "DROP TABLE IF EXISTS notes",
            "DROP TABLE IF EXISTS activity_logs",
            "DROP TABLE IF EXISTS bot_state",
            "DROP TABLE IF EXISTS banned",
            "DROP TABLE IF EXISTS admins",
            "DROP TABLE IF EXISTS users",
        ]
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                for q in drop_queries:
                    await cur.execute(q)
        await self.initialize_tables()

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
        result = await self._exec(sql, (user_id, title, encrypted_content, encrypted_content))
        return result is not None

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
        sql = """INSERT INTO temp_mail_sessions (user_id, email, password, token, created_at) 
                 VALUES (%s, %s, %s, %s, NOW())"""
        result = await self._exec(sql, (user_id, email, password, token))
        return result is not None

    async def get_mail_session(self, user_id):
        # Get latest active session (highest ID/created_at)
        return await self._exec("SELECT * FROM temp_mail_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,), fetch_one=True, dict_cursor=True)

    async def get_mail_sessions_list(self, user_id, limit=20):
        # List history
        return await self._exec("SELECT * FROM temp_mail_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (user_id, limit), fetch=True, dict_cursor=True) or []

    async def delete_mail_session(self, user_id, mail_id=None):
        if mail_id:
            result = await self._exec(
                "DELETE FROM temp_mail_sessions WHERE user_id = %s AND email = %s",
                (user_id, mail_id)
            )
        else:
            result = await self._exec("DELETE FROM temp_mail_sessions WHERE user_id = %s", (user_id,))
        return result is not None

    async def touch_mail_session(self, user_id, mail_id):
        # Bring to top (Active) by updating created_at
        result = await self._exec(
            "UPDATE temp_mail_sessions SET created_at = NOW() WHERE user_id = %s AND email = %s",
            (user_id, mail_id)
        )
        return result is not None

    async def get_pending_mail_sessions(self, limit=50):
        return await self._exec(
            "SELECT user_id, token, last_msg_id FROM temp_mail_sessions ORDER BY created_at DESC LIMIT %s",
            (limit,),
            fetch=True,
            dict_cursor=True
        ) or []

    async def update_mail_check_time(self, user_id, next_check_timestamp, last_msg_id=None):
        if last_msg_id:
            await self._exec(
                "UPDATE temp_mail_sessions SET last_msg_id = %s WHERE user_id = %s",
                (last_msg_id, user_id)
            )

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
