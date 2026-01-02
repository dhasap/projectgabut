import os
import asyncio
import libsql_client
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY", "DefaultSecretKeyShouldBeChangedForProd123")

if not TURSO_URL or not TURSO_TOKEN:
    print("❌ TURSO_URL atau TURSO_TOKEN belum di-set!")
    exit(1)

def get_cipher():
    key_bytes = SECRET_KEY.ljust(32)[:32].encode()
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(encoded_key)

def is_encrypted(text):
    if not text: return False
    # Fernet encrypted strings usually start with gAAAA
    return text.startswith("gAAAA")

async def main():
    print("🔐 Memulai Enkripsi Database...")
    client = libsql_client.create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
    cipher = get_cipher()

    # 1. Encrypt Notes Titles
    print("\n📄 Memeriksa Notes...")
    res = await client.execute("SELECT id, title FROM notes")
    count = 0
    for row in res.rows:
        try:
            # row[0] is id, row[1] is title (based on select order)
            # row might be tuple or object depending on library version, let's assume tuple/indexable
            note_id = row[0]
            title = row[1]
            
            if not is_encrypted(title):
                print(f"   -> Mengenkripsi Title ID {note_id}: {title[:10]}...")
                enc_title = cipher.encrypt(title.encode()).decode()
                await client.execute("UPDATE notes SET title = ? WHERE id = ?", (enc_title, note_id))
                count += 1
        except Exception as e:
            print(f"⚠️ Error processing note {row}: {e}")
    print(f"✅ Selesai! {count} judul catatan dienkripsi.")

    # 2. Encrypt Email & Password
    print("\n📧 Memeriksa Email Sessions...")
    try:
        res = await client.execute("SELECT id, email, password FROM mail_sessions_v2")
        count = 0
        for row in res.rows:
            try:
                sess_id = row[0]
                email = row[1]
                password = row[2]
                
                needs_update = False
                enc_email = email
                enc_pass = password

                if not is_encrypted(email):
                    enc_email = cipher.encrypt(email.encode()).decode()
                    needs_update = True
                
                if not is_encrypted(password):
                    enc_pass = cipher.encrypt(password.encode()).decode()
                    needs_update = True
                
                if needs_update:
                    print(f"   -> Mengenkripsi Email ID {sess_id}...")
                    await client.execute("UPDATE mail_sessions_v2 SET email = ?, password = ? WHERE id = ?", (enc_email, enc_pass, sess_id))
                    count += 1

            except Exception as e:
                print(f"⚠️ Error processing email {row}: {e}")
        print(f"✅ Selesai! {count} sesi email dienkripsi.")

    except Exception as e:
        print(f"⚠️ Tabel mail_sessions_v2 mungkin belum ada atau kosong: {e}")

    await client.close()
    print("\n🎉 Database Aman Terkendali!")

if __name__ == "__main__":
    asyncio.run(main())
