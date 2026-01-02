import os
import asyncio
import logging
from supabase import create_client
import libsql_client
from dotenv import load_dotenv

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- KONFIGURASI ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

if not all([SUPABASE_URL, SUPABASE_KEY, TURSO_URL, TURSO_TOKEN]):
    print("❌ ERROR: Pastikan variabel environment SUPABASE_URL, SUPABASE_KEY, TURSO_URL, dan TURSO_TOKEN sudah diisi di .env atau environment system.")
    exit(1)

async def migrate_users(supa, turso):
    print("🚀 Memulai Migrasi: USERS...")
    try:
        # Ambil semua data users dari Supabase (pagination jika banyak, tapi default 1000)
        # Supabase default limit 1000
        res = supa.table("users").select("*" ).execute()
        users = res.data
        if not users:
            print("ℹ️ Tidak ada data Users di Supabase.")
            return

        print(f"📦 Ditemukan {len(users)} users. Memasukkan ke Turso...")
        
        count = 0
        for user in users:
            try:
                sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                         VALUES (?, ?, ?, ?) 
                         ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name, last_seen=excluded.last_seen"""
                await turso.execute(sql, (
                    user.get("user_id"),
                    user.get("username"),
                    user.get("first_name"),
                    user.get("last_seen")
                ))
                count += 1
            except Exception as e:
                print(f"⚠️ Gagal migrasi User ID {user.get('user_id')}: {e}")
        
        print(f"✅ Berhasil migrasi {count} users.")
    except Exception as e:
        print(f"❌ Error Migrasi Users: {e}")

async def migrate_bot_state(supa, turso):
    print("\n🚀 Memulai Migrasi: BOT STATE (Config)...")
    try:
        res = supa.table("bot_state").select("*" ).execute()
        states = res.data
        if not states:
            print("ℹ️ Tidak ada data Bot State.")
            return

        for state in states:
            try:
                # Periksa apakah value adalah JSON object atau string
                val = state.get("value")
                # Supabase mungkin mengembalikan dict, kita perlu stringify jika perlu, 
                # tapi adapter Turso kita mengharapkan JSON string jika itu object kompleks,
                # namun untuk fleksibilitas kita simpan apa adanya jika adapter menghandle loadnya.
                # Di adapter turso: load_state mereturn json.loads(row[0]). Jadi kita harus simpan sebagai string JSON.
                
                import json
                if isinstance(val, (dict, list)):
                    val_str = json.dumps(val)
                else:
                    val_str = str(val)

                sql = "INSERT INTO bot_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
                await turso.execute(sql, (state.get("key"), val_str))
            except Exception as e:
                print(f"⚠️ Gagal migrasi State Key {state.get('key')}: {e}")
        print(f"✅ Berhasil migrasi {len(states)} config items.")

    except Exception as e:
        print(f"❌ Error Migrasi Bot State: {e}")

async def migrate_notes(supa, turso):
    print("\n🚀 Memulai Migrasi: NOTES (Catatan)...")
    try:
        res = supa.table("notes").select("*" ).execute()
        notes = res.data
        if not notes:
            print("ℹ️ Tidak ada data Notes.")
            return
        
        count = 0
        for note in notes:
            try:
                sql = """INSERT INTO notes (user_id, title, content, updated_at) 
                         VALUES (?, ?, ?, ?)
                         ON CONFLICT(user_id, title) DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at"""
                await turso.execute(sql, (
                    note.get("user_id"),
                    note.get("title"),
                    note.get("content"), # Sudah terenkripsi di Supabase, pindahkan saja raw-nya
                    note.get("updated_at")
                ))
                count += 1
            except Exception as e:
                print(f"⚠️ Gagal migrasi Note {note.get('title')} (User {note.get('user_id')}): {e}")
        print(f"✅ Berhasil migrasi {count} notes.")

    except Exception as e:
        print(f"❌ Error Migrasi Notes: {e}")

async def migrate_mail_sessions(supa, turso):
    print("\n🚀 Memulai Migrasi: MAIL SESSIONS...")
    try:
        res = supa.table("mail_sessions_v2").select("*" ).execute()
        mails = res.data
        if not mails:
            print("ℹ️ Tidak ada data Mail Sessions.")
            return

        count = 0
        for mail in mails:
            try:
                sql = """INSERT INTO mail_sessions_v2 (user_id, email, password, token, last_msg_id, created_at, next_check_at) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)"""
                await turso.execute(sql, (
                    mail.get("user_id"),
                    mail.get("email"),
                    mail.get("password"),
                    mail.get("token"),
                    mail.get("last_msg_id"),
                    mail.get("created_at"),
                    mail.get("next_check_at")
                ))
                count += 1
            except Exception as e:
                print(f"⚠️ Gagal migrasi Email {mail.get('email')}: {e}")
        print(f"✅ Berhasil migrasi {count} mail sessions.")

    except Exception as e:
        print(f"❌ Error Migrasi Mail Sessions: {e}")

async def main():
    print("🔌 Menghubungkan ke Database...")
    
    # 1. Connect Supabase (Sync Client Wrapper)
    supa = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 2. Connect Turso (Async Client)
    turso = libsql_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
    
    try:
        # Buat tabel dulu di Turso (Just in case belum ada)
        # Kita pakai script initialize manual yang sederhana
        await create_tables(turso)
        
        await migrate_users(supa, turso)
        await migrate_bot_state(supa, turso)
        await migrate_notes(supa, turso)
        await migrate_mail_sessions(supa, turso)
        
        print("\n🎉🎉 MIGRASI SELESAI! 🎉🎉")
        print("Sekarang bot kamu sudah siap menggunakan Turso sepenuhnya.")
        
    finally:
        await turso.close()

async def create_tables(client):
    print("🛠️ Memastikan tabel tersedia di Turso...")
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
    for q in queries:
        await client.execute(q)

if __name__ == "__main__":
    asyncio.run(main())
