import os
import asyncio
import logging
import aiomysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

async def force_reset_table():
    """Drops and recreates the temp_mail_sessions table."""
    
    print("--- FORCE RESET TABLE START ---")
    
    host = os.getenv("TIDB_HOST")
    if not host:
        print("❌ TIDB_HOST not found. Skipping TiDB reset.")
        print("If you are using SQLite (local/Railway fallback), simply delete 'bot.db' to reset.")
        return

    port = int(os.getenv("TIDB_PORT", 4000))
    user = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    db_name = os.getenv("TIDB_DB_NAME", "test")
    ssl_ca = os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")

    db_config = {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'db': db_name,
        'autocommit': True,
        'connect_timeout': 10
    }
    
    if ssl_ca and os.path.exists(ssl_ca):
        db_config['ssl'] = {'ca': ssl_ca}

    try:
        logging.info(f"⚙️ Connecting to TiDB at {host}...")
        pool = await aiomysql.create_pool(**db_config)
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 1. Drop Table
                logging.info("🗑️ Dropping table 'temp_mail_sessions'...")
                await cur.execute("DROP TABLE IF EXISTS temp_mail_sessions")
                
                # 2. Recreate Table (New Schema with ID)
                logging.info("✨ Creating table 'temp_mail_sessions' (New Schema)...")
                create_sql = """CREATE TABLE IF NOT EXISTS temp_mail_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    email VARCHAR(255),
                    password VARCHAR(255),
                    token VARCHAR(500),
                    last_msg_id VARCHAR(100),
                    created_at DATETIME,
                    INDEX idx_user_mail (user_id),
                    INDEX idx_created (created_at)
                )"""
                await cur.execute(create_sql)
                logging.info("✅ Table recreated successfully.")
                
        pool.close()
        await pool.wait_closed()
        print("--- SUCCESS ---")
        
    except Exception as e:
        logging.error(f"❌ Error during table reset: {e}")

if __name__ == "__main__":
    asyncio.run(force_reset_table())
