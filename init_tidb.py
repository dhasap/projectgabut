import os
import pymysql
import certifi
from dotenv import load_dotenv

load_dotenv()

def init_tidb_manual():
    print("--- MANUAL TiDB INIT START ---")
    
    host = os.getenv("TIDB_HOST")
    port = int(os.getenv("TIDB_PORT", 4000))
    user = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    db_name = os.getenv("TIDB_DB_NAME", "test")
    ssl_ca = os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")
    
    print(f"Connecting to {host} as {user}...")
    
    # Smart SSL Handling
    ssl_config = None
    if ssl_ca and os.path.exists(ssl_ca):
        ssl_config = {'ca': ssl_ca}
        print(f"🔒 Using provided CA: {ssl_ca}")
    else:
        print(f"⚠️ Provided CA '{ssl_ca}' not found. Falling back to certifi.")
        ssl_config = {'ca': certifi.where()}

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            ssl=ssl_config,
            autocommit=True
        )
        
        with conn.cursor() as cur:
            # Create Table mail_sessions_v2
            print("Creating table 'mail_sessions_v2'...")
            sql = """
            CREATE TABLE IF NOT EXISTS mail_sessions_v2 (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                email VARCHAR(255),
                password VARCHAR(255),
                token VARCHAR(500),
                last_msg_id VARCHAR(100),
                created_at DATETIME,
                INDEX idx_user_mail (user_id),
                INDEX idx_created (created_at)
            )
            """
            cur.execute(sql)
            print("✅ Table created successfully!")
            
            # Verify
            cur.execute("SHOW TABLES LIKE 'mail_sessions_v2'")
            result = cur.fetchone()
            if result:
                print(f"🔍 Verification: Table found -> {result}")
            else:
                print("❌ Verification FAILED: Table not found.")

        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_tidb_manual()
