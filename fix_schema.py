import os
import asyncio
import logging
import aiomysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

async def fix_schema():
    """Drops the incompatible table so it can be recreated correctly by the bot."""
    
    host = os.getenv("TIDB_HOST")
    port = int(os.getenv("TIDB_PORT", 4000))
    user = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    db_name = os.getenv("TIDB_DB_NAME", "test")
    ssl_ca = os.getenv("TIDB_CA_PATH", "isrgrootx1.pem")

    if not host:
        logging.error("❌ TIDB_HOST not found in environment variables.")
        return

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
        logging.info("⚙️ Connecting to TiDB...")
        pool = await aiomysql.create_pool(**db_config)
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                logging.info("🗑️ Dropping table 'temp_mail_sessions'...")
                await cur.execute("DROP TABLE IF EXISTS temp_mail_sessions")
                logging.info("✅ Table dropped successfully.")
                
        pool.close()
        await pool.wait_closed()
        logging.info("✨ Schema fix complete. Now restart the bot to recreate the table with the correct schema.")
        
    except Exception as e:
        logging.error(f"❌ Error during schema fix: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())
