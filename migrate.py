import os
import logging
import time
from database import SupabaseAdapter, MySQLAdapter, _get_cipher_suite

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def migrate_data():
    logging.info("🚀 MEMULAI MIGRASI DATA: SUPABASE -> TIDB")
    
    # 1. KONEKSI KE SUMBER (SUPABASE)
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_KEY")
    
    if not sb_url or not sb_key:
        logging.error("❌ Variable SUPABASE_URL atau SUPABASE_KEY belum di-set!")
        return

    try:
        logging.info("🔌 Menghubungkan ke Supabase...")
        src = SupabaseAdapter(sb_url, sb_key)
    except Exception as e:
        logging.error(f"❌ Gagal koneksi Supabase: {e}")
        return

    # 2. KONEKSI KE TUJUAN (TIDB)
    tidb_host = os.getenv("TIDB_HOST")
    tidb_user = os.getenv("TIDB_USER")
    tidb_pass = os.getenv("TIDB_PASSWORD")
    
    if not tidb_host or not tidb_user:
        logging.error("❌ Variable TIDB_HOST/USER/PASSWORD belum di-set!")
        return

    try:
        logging.info("🔌 Menghubungkan ke TiDB...")
        dst = MySQLAdapter(
            host=tidb_host,
            port=int(os.getenv("TIDB_PORT", 4000)),
            user=tidb_user,
            password=tidb_pass,
            db_name=os.getenv("TIDB_DB_NAME", "test"),
            ssl_ca=os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")
        )
        # Pastikan tabel dibuat dulu
        dst.initialize_tables()
    except Exception as e:
        logging.error(f"❌ Gagal koneksi TiDB: {e}")
        return

    # --- HELPER INSERT ---
    def raw_insert(sql, params):
        try:
            conn = dst.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.close()
            return True
        except Exception as e:
            logging.error(f"⚠️ Insert Error: {e}")
            return False

    # 3. MIGRASI USERS
    logging.info("📦 Memindahkan data USERS...")
    try:
        # Ambil raw data dari Supabase client
        users = src.client.table("users").select("*").execute().data
        count = 0
        for u in users:
            # Gunakan INSERT IGNORE atau ON DUPLICATE UPDATE
            sql = """INSERT INTO users (user_id, username, first_name, last_seen) 
                     VALUES (%s, %s, %s, %s)
                     ON DUPLICATE KEY UPDATE username=%s, first_name=%s, last_seen=%s"""
            
            # Parsing timestamp agar sesuai format MySQL
            ls = u.get('last_seen')
            if ls: ls = ls.replace('T', ' ')[:19] # Simple clean ISO format
            
            params = (u['user_id'], u.get('username'), u.get('first_name'), ls,
                      u.get('username'), u.get('first_name'), ls)
            
            if raw_insert(sql, params):
                count += 1
        logging.info(f"✅ Berhasil memindahkan {count} Users.")
    except Exception as e:
        logging.error(f"❌ Gagal migrasi Users: {e}")

    # 4. MIGRASI ADMINS
    logging.info("📦 Memindahkan data ADMINS...")
    try:
        admins = src.client.table("admins").select("*").execute().data
        count = 0
        for a in admins:
            sql = """INSERT IGNORE INTO admins (user_id, username, promoted_at) 
                     VALUES (%s, %s, %s)"""
            pa = a.get('promoted_at')
            if pa: pa = pa.replace('T', ' ')[:19]
            
            if raw_insert(sql, (a['user_id'], a.get('username'), pa)):
                count += 1
        logging.info(f"✅ Berhasil memindahkan {count} Admins.")
    except Exception as e:
        logging.error(f"❌ Gagal migrasi Admins: {e}")

    # 5. MIGRASI NOTES (Penting: Struktur Enkripsi Sama)
    logging.info("📦 Memindahkan data NOTES...")
    try:
        notes = src.client.table("notes").select("*").execute().data
        count = 0
        for n in notes:
            sql = """INSERT INTO notes (user_id, title, content, updated_at) 
                     VALUES (%s, %s, %s, %s)
                     ON DUPLICATE KEY UPDATE content=%s, updated_at=%s"""
            ua = n.get('updated_at')
            if ua: ua = ua.replace('T', ' ')[:19]
            
            # Content sudah terenkripsi di Supabase, kita pindahkan mentah-mentah
            # agar bisa didekripsi oleh key yang sama di TiDB
            params = (n['user_id'], n['title'], n['content'], ua,
                      n['content'], ua)
            
            if raw_insert(sql, params):
                count += 1
        logging.info(f"✅ Berhasil memindahkan {count} Notes.")
    except Exception as e:
        logging.error(f"❌ Gagal migrasi Notes: {e}")

    # 6. MIGRASI BANNED
    logging.info("📦 Memindahkan data BANNED USERS...")
    try:
        bans = src.client.table("banned").select("*").execute().data
        count = 0
        for b in bans:
            sql = """INSERT IGNORE INTO banned (user_id, username, reason, banned_at) 
                     VALUES (%s, %s, %s, %s)"""
            ba = b.get('banned_at')
            if ba: ba = ba.replace('T', ' ')[:19]
            
            if raw_insert(sql, (b['user_id'], b.get('username'), b.get('reason'), ba)):
                count += 1
        logging.info(f"✅ Berhasil memindahkan {count} Banned Users.")
    except Exception as e:
        logging.error(f"❌ Gagal migrasi Banned: {e}")

    # 7. MIGRASI BOT STATE / CONFIG
    logging.info("📦 Memindahkan CONFIG (Bot State)...")
    try:
        states = src.client.table("bot_state").select("*").execute().data
        count = 0
        import json
        for s in states:
            val = s['value']
            # Pastikan format string JSON jika perlu
            if isinstance(val, dict) or isinstance(val, list):
                val = json.dumps(val)
                
            sql = """INSERT INTO bot_state (`key`, value) VALUES (%s, %s)
                     ON DUPLICATE KEY UPDATE value=%s"""
            if raw_insert(sql, (s['key'], val, val)):
                count += 1
        logging.info(f"✅ Berhasil memindahkan {count} Configs.")
    except Exception as e:
        logging.error(f"❌ Gagal migrasi Config: {e}")

    logging.info("🎉 MIGRASI SELESAI!")

if __name__ == "__main__":
    logging.info("⚠️  Pastikan Variable Supabase DAN TiDB sudah aktif di environment ini.")
    logging.info("⚠️  Script akan berjalan dalam 3 detik...")
    time.sleep(3)
    migrate_data()
