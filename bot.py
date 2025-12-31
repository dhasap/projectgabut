import logging
import os
import requests
import time
import string
import random
import yaml
import asyncio
import re
import socket # Added for network fix
import aiohttp # Added for network fix
from datetime import datetime

# --- NETWORK FIX: FORCE IPV4 ---
# Masalah: Railway/Docker sering gagal konek ke Telegram via IPv6 (Network is unreachable)
# Solusi: Paksa aiohttp (yang dipakai aiogram) untuk hanya menggunakan IPv4
old_connector_init = aiohttp.TCPConnector.__init__

def new_connector_init(self, *args, **kwargs):
    # Paksa family menjadi AF_INET (IPv4)
    kwargs['family'] = socket.AF_INET
    old_connector_init(self, *args, **kwargs)

aiohttp.TCPConnector.__init__ = new_connector_init
# -------------------------------

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import Throttled
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class NoteState(StatesGroup):
    title = State()
    content = State()

class MailCustomState(StatesGroup):
    username = State()
    password = State()

# --- DYNAMIC MENU STATES ---
class MenuReplyState(StatesGroup):
    waiting_label = State()
    waiting_row = State()
    waiting_response = State()
    waiting_inline_choice = State()
    waiting_inline_conf = State()

class MenuInlineState(StatesGroup):
    waiting_key = State()
    waiting_title = State()
    waiting_content = State()
    waiting_buttons = State()

from bs4 import BeautifulSoup as bs
from faker import Faker
import checker
import iban
import names_db
import identity
import menu_manager
from checker import is_card_valid, local_chk_gate


# Configure vars get from env or config.yml


def load_config(path: str = 'config.yml') -> dict:
    """Muat konfigurasi dari berkas YAML dengan fallback aman.

    Jika berkas tidak ditemukan atau kontennya tidak sesuai, kita kembalikan
    konfigurasi minimal supaya bot tetap bisa diimpor atau dijalankan dengan
    variabel lingkungan saja tanpa memicu error FileNotFound.
    """

    defaults = {
        'token': '',
        'blacklisted': '',
        'prefix': '/',
        'owner': 0,
        'antispam': 10,
    }

    try:
        with open(path, 'r') as fh:
            loaded = yaml.load(fh, Loader=yaml.SafeLoader) or {}
    except FileNotFoundError:
        logging.warning("%s tidak ditemukan, menggunakan konfigurasi default.", path)
        return defaults
    except yaml.YAMLError as exc:  # pragma: no cover - defensive fallback
        logging.warning("Konfigurasi %s tidak bisa diurai: %s", path, exc)
        return defaults

    if not isinstance(loaded, dict):
        logging.warning("Format %s tidak sesuai, menggunakan default.", path)
        return defaults

    merged = {**defaults, **loaded}
    return merged


CONFIG = load_config()

TOKEN_PATTERN = re.compile(r"^\d{5,16}:[A-Za-z0-9_-]{35}$")
DEFAULT_TOKEN = "000000:TESTTOKENSTRINGWITH35CHARSABCDE1234"


def resolve_token(raw_token: str) -> str:
    """Return a Telegram token that passes aiogram validation.

    When running locally tanpa token valid, aiogram akan melempar
    ``ValidationError`` pada saat import. Kita fallback ke placeholder
    berformat benar supaya fungsi util seperti ``is_card_valid`` bisa
    dipakai untuk pengujian tanpa Telegram.
    """

    if TOKEN_PATTERN.match(raw_token or ""):
        return raw_token

    logging.warning("Token tidak valid, menggunakan placeholder untuk import offline.")
    return DEFAULT_TOKEN


TOKEN = resolve_token(os.getenv('TOKEN', CONFIG['token']))
BLACKLISTED = os.getenv('BLACKLISTED', CONFIG['blacklisted']).split()
PREFIX = os.getenv('PREFIX', CONFIG['prefix'])
OWNER = int(os.getenv('OWNER', CONFIG['owner']))
ANTISPAM = int(os.getenv('ANTISPAM', CONFIG['antispam']))

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

# SECURITY SETTINGS
USER_THROTTLE = {} 
USER_MAIL_COOLDOWN = {} # Anti-Spam Mail (2 Menit)
THROTTLE_TIME = 1.5 # Detik (Jeda antar pesan)
FORCE_SUB_CHANNEL = "@azkuraairdrop"
FORCE_SUB_CACHE = {} # Cache status sub selama 5 menit

# AUTO-BAN SYSTEM (Anti-DDoS Application Layer)
USER_VIOLATIONS = {} # {user_id: count}
TEMP_BANNED = {}     # {user_id: expiry_timestamp}
VIOLATION_LIMIT = 5  # Max spam
BAN_DURATION = 600   # 10 Menit

# --- NON-BLOCKING SECURITY CACHE ---
LOCAL_BANNED_CACHE = set()
LOCAL_ADMINS_CACHE = {OWNER}

async def refresh_security_cache():
    """Background task to refresh security cache without blocking main loop."""
    global LOCAL_BANNED_CACHE, LOCAL_ADMINS_CACHE
    while True:
        try:
            # Run blocking DB calls in executor
            banned = await loop.run_in_executor(None, db.db_get_banned)
            admins = await loop.run_in_executor(None, lambda: db.db_get_admins(OWNER))
            
            if banned is not None: LOCAL_BANNED_CACHE = banned
            if admins is not None: LOCAL_ADMINS_CACHE = admins
            
        except Exception as e:
            logging.error(f"Security cache refresh failed: {e}")
        
        await asyncio.sleep(60) # Refresh every 1 minute

class AccessMiddleware(BaseMiddleware):
    """Middleware: Auto-Ban, Rate Limit, Ban, Maintenance, Force Sub."""
    
    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        current_time = time.time()
        
        # 2. CEK BANNED (RAM Cache - Non-Blocking)
        if str(user_id) in LOCAL_BANNED_CACHE:
             raise CancelHandler()
             
        # Pre-fetch Admin Status (RAM Cache - Non-Blocking)
        is_admin = (user_id == OWNER) or (user_id in LOCAL_ADMINS_CACHE)

        # 3. CEK MAINTENANCE
        if BOT_STATE["maintenance"] and not is_admin:
            await message.reply("🚧 <b>BOT UNDER MAINTENANCE</b>\nBot sedang dalam perbaikan. Silakan coba lagi nanti.")
            raise CancelHandler()

        # 4. FORCE SUBSCRIBE (API Call - Slowest, executed last)
        if message.chat.type == 'private' and not is_admin:
            if user_id not in FORCE_SUB_CACHE or current_time > FORCE_SUB_CACHE[user_id]:
                try:
                    member = await bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
                    if member.status in ['left', 'kicked']:
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("🚀 GABUNG CHANNEL", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@', '')}"))
                        kb.add(types.InlineKeyboardButton("🔄 CEK STATUS", callback_data="check_sub"))
                        
                        text = (
                            "<b>🔐 AKSES TERKUNCI</b>\n"
                            "━━━━━━━━━━━━━━━━━━\n"
                            "Halo kawan! 👋\n"
                            "Untuk menggunakan bot ini secara <b>GRATIS</b>, mohon dukung kami dengan bergabung ke channel resmi.\n\n"
                            "✅ <i>Update Fitur Terbaru</i>\n"
                            "✅ <i>Info Airdrop Legit</i>\n"
                            "✅ <i>Komunitas Solid</i>\n\n"
                            "<b>Klik tombol di bawah untuk membuka kunci!</b> 🔓"
                        )
                        await message.answer(text, reply_markup=kb)
                        raise CancelHandler()
                    else:
                        FORCE_SUB_CACHE[user_id] = current_time + 300
                except Exception:
                    pass

        # 5. SPY MODE CHECK
        if SPY_MODE and SPY_ADMIN and not is_admin and user_id != SPY_ADMIN:
            try:
                spy_msg = (
                    f"🕵️ <b>SPY ALERT</b>\n"
                    f"👤 <b>User:</b> {message.from_user.first_name} (@{message.from_user.username})\n"
                    f"🆔 <code>{user_id}</code>\n"
                    f"💬 <b>Msg:</b> {message.text}"
                )
                await bot.send_message(SPY_ADMIN, spy_msg)
            except: pass

# Initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(AccessMiddleware()) # Register Middleware

# Configure logging
# Create file handler
file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.WARNING) # Log warnings and errors to file
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add to root logger
logging.getLogger().addHandler(file_handler)
logging.basicConfig(level=logging.INFO)

import database as db

# DATABASE INTEGRATION (SUPABASE)
def save_user(user: types.User):
    """Simpan user_id dan username ke database via Supabase."""
    db.db_save_user(user.id, user.username, user.first_name)

def get_users_count():
    return db.db_get_users_count()

def get_all_users():
    return db.db_get_all_users()

# ADMIN MANAGEMENT
def get_admins():
    """Mengambil set ID admin (Owner + Supabase Admins)."""
    return db.db_get_admins(OWNER)

def add_new_admin(user_id, username=None):
    """Menambah admin baru ke database."""
    current = get_admins()
    if user_id in current: return False
    return db.db_add_admin(user_id, username)

def remove_admin(user_id):
    """Menghapus admin dari database."""
    if user_id == OWNER: return False
    return db.db_remove_admin(user_id)

# GLOBAL STATE & SECURITY (BANNED, MAINTENANCE, FEATURES)
# In-Memory State
BOT_STATE = {
    "maintenance": False,
    "disabled_features": [] # list of feature codes: 'chk', 'gen', 'bin', 'mail'
}

# SPY MODE STATE
SPY_MODE = False
SPY_ADMIN = None

def load_bot_state():
    """Load state dari Database."""
    global BOT_STATE
    saved = db.db_load_state()
    if saved:
        BOT_STATE.update(saved)

def save_bot_state():
    """Save state ke Database."""
    db.db_save_state(BOT_STATE)

# Load initial state
load_bot_state()

def get_banned_users():
    """Get set of banned user IDs."""
    return db.db_get_banned()

def ban_user(user_id):
    current = get_banned_users()
    if str(user_id) in current: return False
    return db.db_ban_user(user_id)

def unban_user(user_id):
    return db.db_unban_user(user_id)


# TEMP MAIL STORAGE
# USER_MAILS = {} # Moved to DB: temp_mail_sessions
LAST_GEN_ID = {} # Last Generated Fake ID (for Save to Note feature)
SAVED_MAILS = {} # History List: {user_id: [ {email, password, token}, ... ]}

def save_email_session(user_id, email, password, token):
    """Menyimpan sesi email ke history user."""
    if user_id not in SAVED_MAILS:
        SAVED_MAILS[user_id] = []
    
    # Cek duplikasi, jika ada hapus yang lama agar yang baru naik ke atas
    SAVED_MAILS[user_id] = [x for x in SAVED_MAILS[user_id] if x['email'] != email]
    
    # Masukkan ke index 0 (paling baru)
    new_data = {"email": email, "password": password, "token": token}
    SAVED_MAILS[user_id].insert(0, new_data)
    
    # Batasi maksimal 10 akun terakhir
    if len(SAVED_MAILS[user_id]) > 10:
        SAVED_MAILS[user_id].pop()

# BOT INFO
loop = asyncio.get_event_loop()

# Default values allow the module to be imported without needing Telegram
# credentials or network connectivity. Real bot metadata is populated at
# runtime via ``initialize_bot_info`` before polling starts.
BOT_USERNAME = os.getenv('BOT_USERNAME', 'unknown_bot')
BOT_NAME = os.getenv('BOT_NAME', 'Bot')
BOT_ID = int(os.getenv('BOT_ID', '0'))


def initialize_bot_info():
    """Safely populate bot metadata.

    ``Bot.get_me`` requires a valid token and network access. In automated
    environments (or when credentials are missing) we gracefully degrade to
    the default placeholders above so imports do not crash.
    """

    global BOT_USERNAME, BOT_NAME, BOT_ID

    try:
        bot_info = loop.run_until_complete(bot.get_me())
    except Exception as exc:  # pragma: no cover - defensive guard
        logging.warning("Unable to fetch bot info: %s", exc)
        return

    BOT_USERNAME = bot_info.username or BOT_USERNAME
    BOT_NAME = bot_info.first_name or BOT_NAME
    BOT_ID = bot_info.id or BOT_ID

# USE YOUR ROTATING PROXY API IN DICT FORMAT http://user:pass@providerhost:port
proxies = {
           'http': 'http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/',
           'https': 'http://qnuomzzl-rotate:4i44gnayqk7c@p.webshare.io:80/'
}

session = requests.Session()

# Random DATA
letters = string.ascii_lowercase
First = ''.join(random.choice(letters) for _ in range(6))
Last = ''.join(random.choice(letters) for _ in range(6))
PWD = ''.join(random.choice(letters) for _ in range(10))
Name = f'{First}+{Last}'
Email = f'{First}.{Last}@gmail.com'
UA = 'Mozilla/5.0 (X11; Linux i686; rv:102.0) Gecko/20100101 Firefox/102.0'


async def is_owner(user_id):
    return user_id in get_admins()




def start_keyboard():
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    keyboard_markup.row(
        types.InlineKeyboardButton("💳 BIN Lookup", callback_data="m_bin"),
        types.InlineKeyboardButton("🎲 Rnd BIN", callback_data="m_rnd")
    )
    keyboard_markup.row(
        types.InlineKeyboardButton("✅ VCC Checker", callback_data="m_chk"),
        types.InlineKeyboardButton("⚙️ Generator", callback_data="m_gen")
    )
    keyboard_markup.row(
        types.InlineKeyboardButton("👤 Fake ID", callback_data="m_fake"),
        types.InlineKeyboardButton("🏦 Fake IBAN", callback_data="m_iban")
    )
    keyboard_markup.row(
        types.InlineKeyboardButton("📧 Temp Mail", callback_data="m_mail"),
        types.InlineKeyboardButton("📝 Notes", callback_data="m_notes")
    )
    keyboard_markup.row(
        types.InlineKeyboardButton("ℹ️ Info", callback_data="m_info"),
        types.InlineKeyboardButton("💬 Support", url=f"tg://user?id={OWNER}")
    )
    return keyboard_markup


def menu_keyboard():
    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
    keyboard_markup.add(
        types.InlineKeyboardButton("📋 Menu", callback_data="m_main")
    )
    return keyboard_markup


def get_reply_keyboard(is_admin=False):
    """Membuat custom reply keyboard dari config JSON."""
    return menu_manager.get_reply_keyboard_markup(is_admin)

def get_admin_keyboard():
    """Keyboard khusus Admin."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("📊 Stats", "📢 Broadcast")
    markup.row("⛔ User Control", "🎛️ Features")
    markup.row("🎹 Menu Editor", "✏️ Edit Texts") # Added Menu Editor
    markup.row("👁️ Spy Mode", "🚧 Maint. Mode")
    markup.row("📜 Admin Logs", "🏥 System Health")
    markup.row("👥 Admins", "🔙 Exit Admin")
    return markup

def log_admin_action(user, action, details):
    """Helper untuk mencatat log."""
    try:
        db.db_log_activity(user.id, user.username, action, details)
    except: pass


async def run_command_from_start(message: types.Message, command_text: str, handler):
    # Check if feature is disabled
    cmd = command_text.split()[0].replace(PREFIX, '')
    if cmd in BOT_STATE["disabled_features"]:
        return await message.reply("⚠️ <b>Fitur ini sedang dimatikan sementara.</b>")

    original_text = message.text
    message.text = command_text
    try:
        await handler(message)
    finally:
        message.text = original_text


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('gen_'))
async def process_gen_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    bin_to_gen = callback_query.data.split('_')[1]
    
    # Simulate a message object to reuse gen_cc function logic
    # We construct a fake message object that looks like the user sent "/gen BIN"
    fake_message = callback_query.message
    fake_message.from_user = callback_query.from_user
    fake_message.text = f"{PREFIX}gen {bin_to_gen}"
    
    # Call the existing generator handler
    await gen_cc(fake_message)


@dp.callback_query_handler(lambda c: c.data == 'check_sub', state="*")
async def check_sub_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        # Re-check membership
        member = await bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ['left', 'kicked']:
            await callback_query.answer("❌ Kamu belum join channel! Silakan gabung dulu.", show_alert=True)
        else:
            # Update Cache (Allow access)
            FORCE_SUB_CACHE[user_id] = time.time() + 300
            await callback_query.answer("✅ Akses Diterima! Selamat datang.", show_alert=True)
            
            # Delete lock message
            try: await callback_query.message.delete()
            except: pass
            
            # Send Start Menu
            fake_msg = callback_query.message
            fake_msg.from_user = callback_query.from_user
            fake_msg.text = "/start"
            await helpstr(fake_msg)
            
    except Exception:
        # If error (bot not admin), allow pass to avoid getting stuck
        FORCE_SUB_CACHE[user_id] = time.time() + 300
        await callback_query.answer("⚠️ Bot error, passing allowed.", show_alert=True)
        try: await callback_query.message.delete()
        except: pass


@dp.callback_query_handler(lambda c: c.data in ['m_bin', 'm_chk', 'm_info', 'm_main', 'm_gen', 'm_mail', 'm_fake', 'm_rnd', 'm_iban'])
async def process_callback_button(callback_query: types.CallbackQuery):
    code = callback_query.data
    user = callback_query.from_user
    await bot.answer_callback_query(callback_query.id)
    
    # Check disabled
    f_code = code.replace('m_', '')
    if f_code in BOT_STATE["disabled_features"]:
        return await bot.send_message(user.id, "⚠️ <b>Fitur ini sedang dimatikan sementara.</b>")

    if code == 'm_bin':
        await bot.send_message(
            user.id,
            f'''
<b>💳 BIN Lookup</b>
Gunakan perintah <code>{PREFIX}bin 123456</code> untuk mengecek informasi BIN.
'''
        )
    elif code == 'm_rnd':
        await bot.send_message(
            user.id,
            f'''
<b>🎲 Random BIN</b>
Dapatkan BIN acak yang valid dengan perintah <code>{PREFIX}rnd</code>.
'''
        )
    elif code == 'm_chk':
        await bot.send_message(
            user.id,
            f'''
<b>✅ VCC Checker</b>
Silakan kirim kartu dengan format <code>cc|mm|yy|cvv</code> atau gunakan perintah <code>{PREFIX}chk</code>.
'''
        )
    elif code == 'm_gen':
        await bot.send_message(
            user.id,
            f'''
<b>⚙️ VCC Generator</b>
Gunakan perintah <code>{PREFIX}gen bin</code> untuk membuat kartu.
Contoh:
• <code>{PREFIX}gen 415464</code>
• <code>{PREFIX}gen 415464|xx|xx|xxx</code>
'''
        )
    elif code == 'm_mail':
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.row(
            types.InlineKeyboardButton("🎲 Random", callback_data="m_mail_create"),
            types.InlineKeyboardButton("✍️ Custom", callback_data="m_mail_custom")
        )
        kb.row(
            types.InlineKeyboardButton("🔑 Login", callback_data="m_mail_login"),
            types.InlineKeyboardButton("📋 List Akun", callback_data="m_mail_list")
        )
        
        await bot.send_message(
            user.id,
            f"<b>📧 MENU TEMP MAIL</b>\nPilih metode pembuatan email:",
            reply_markup=kb
        )
    elif code == 'm_fake':
        await bot.send_message(
            user.id,
            f'''
<b>👤 Fake Identity</b>
Buat identitas palsu lengkap dengan email aktif.
Gunakan: <code>{PREFIX}fake [negara]</code>
Contoh:
• <code>{PREFIX}fake id</code> (Indonesia)
• <code>{PREFIX}fake us</code> (Amerika)
• <code>{PREFIX}fake kr</code> (Korea)
'''
        )
    elif code == 'm_iban':
        kb = types.InlineKeyboardMarkup(row_width=3)
        # Ambil negara dari scraper
        countries = list(iban.FAKEIBAN_COUNTRIES.items())
        
        btns = []
        for c_code, c_name in countries:
             # Simple flag mapping
             flag_offset = 127397
             try:
                flag = chr(ord(c_code[0].upper()) + flag_offset) + chr(ord(c_code[1].upper()) + flag_offset)
             except: flag = "🏳️"
             
             label = f"{flag} {c_code.upper()}"
             btns.append(types.InlineKeyboardButton(label, callback_data=f"iban_gen_{c_code}"))
        
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("🔙 Menu Utama", callback_data="m_main"))
        
        await bot.edit_message_text(
            f"<b>🏦 FAKE IBAN GENERATOR</b>\n"
            f"Silakan pilih negara asal bank:\n"
            f"<i>Data diambil dari fakeiban.org (scraped) & Faker.</i>",
            chat_id=user.id,
            message_id=callback_query.message.message_id,
            reply_markup=kb,
            parse_mode=types.ParseMode.HTML
        )

    elif code == 'm_info':
        is_owner_val = await is_owner(user.id)
        await bot.send_message(
            user.id,
            f'''
<b>ℹ️ Info</b>
═════════╕
<b>USER INFO</b>
<b>USER ID:</b> <code>{user.id}</code>
<b>USERNAME:</b> @{user.username}
<b>FIRSTNAME:</b> {user.first_name}
<b>BOT:</b> {user.is_bot}
<b>BOT-OWNER:</b> {is_owner_val}
╘═════════'''
        )
    elif code == 'm_main':
        # keyboard_markup = start_keyboard() # Start keyboard is Inline, we want to keep it in message but ensure user has Reply Keyboard too? 
        # Actually start_keyboard is the Inline one inside the message. get_reply_keyboard is the bottom one.
        # We can re-send the welcome message with the inline keyboard.
        
        keyboard_markup = start_keyboard()
        first_name = user.first_name or "Teman"
        MSG = f'''
<b>Halo {first_name}!</b> 👋
Selamat datang di <b>{BOT_NAME}</b> — asistennya cek kartu & BIN yang cepat dan tertata.

<b>Mulai cepat</b>
• <code>{PREFIX}chk 0000|00|00|000</code> untuk cek kartu
• <code>{PREFIX}gen 415464</code> untuk generator vcc
• <code>{PREFIX}fake us</code> untuk identitas palsu
• <code>{PREFIX}mail</code> untuk temp mail
• <code>{PREFIX}bin 000000</code> untuk info BIN

<b>Output ringkas</b>
<code>✅CC ➟ 0000|00|00|000</code>
<code>STATUS ➟ #CCN / #CHARGED / #Declined</code>

<i>Butuh panduan lebih? Tekan Help atau Support di bawah.</i>
'''
        # We can't update Reply Keyboard via edit_message_reply_markup (only Inline).
        # To show Reply Keyboard, we must send a new message.
        # Since this is a callback (edit), we just edit the message content. 
        # User usually already has the Reply Keyboard from /start.
        await bot.edit_message_text(MSG, chat_id=user.id, message_id=callback_query.message.message_id, reply_markup=keyboard_markup, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)


@dp.message_handler(commands=['start', 'help'], commands_prefix=PREFIX)
async def helpstr(message: types.Message):
    # Log user
    save_user(message.from_user)
    
    # Handle deep linking arguments (e.g. /start bin)
    args = message.get_args()
    if args == "bin":
        return await run_command_from_start(message, f"{PREFIX}bin", binio)
    if args == "chk":
        return await run_command_from_start(message, f"{PREFIX}chk", ch)
    if args == "info":
        return await run_command_from_start(message, f"{PREFIX}info", info)

    text_lower = (message.text or "").lower()
    is_help = text_lower.startswith(f"{PREFIX}help") or text_lower.startswith("/help")
    
    first_name = message.from_user.first_name or "Teman"
    
    if is_help:
        # --- HELP MESSAGE ---
        help_msg = (
            "<b>📖 PANDUAN LENGKAP PENGGUNAAN</b>\n\n"
            "Berikut adalah daftar perintah yang bisa Anda gunakan:\n\n"
            "<b>🛠 TOOLS KARTU & BIN</b>\n"
            f"• <code>{PREFIX}chk cc|mm|yy|cvv</code> : Cek kartu (Mode: Auth/Charge)\n"
            f"• <code>{PREFIX}gen 454141</code> : Generate kartu dari BIN\n"
            f"• <code>{PREFIX}bin 454141</code> : Cek detail Bank/Negara BIN\n"
            f"• <code>{PREFIX}rnd</code> : Cari BIN valid secara acak\n\n"
            "<b>👤 IDENTITAS & EMAIL</b>\n"
            f"• <code>{PREFIX}fake id</code> : Identitas palsu (Ganti kode negara: us, jp, uk, dll)\n"
            f"• <code>{PREFIX}mail</code> : Buat alamat email sementara\n"
            f"• <code>{PREFIX}iban de</code> : Buat IBAN Bank (contoh: Jerman)\n\n"
            "<b>🔐 FITUR TAMBAHAN</b>\n"
            f"• <code>{PREFIX}info</code> : Cek status dan ID akun Anda\n"
            f"• <code>{PREFIX}note</code> : Simpan catatan secara aman\n\n"
            "<b>💡 Tips Pro:</b>\n"
            f"<i>Anda bisa membalas (reply) pesan yang berisi daftar kartu dengan perintah <code>{PREFIX}chk</code> untuk pengecekan massal otomatis.</i>\n\n"
            "<b>📞 Butuh Bantuan Lebih Lanjut?</b>\n"
            "Hubungi admin support kami jika menemukan kendala."
        )
        
        # Inline Keyboard for Help
        kb_help = types.InlineKeyboardMarkup(row_width=1)
        kb_help.add(types.InlineKeyboardButton("💬 Hubungi Support", url=f"tg://user?id={OWNER}"))
        kb_help.add(types.InlineKeyboardButton("🔙 Menu Utama", callback_data="m_main"))
        
        await message.answer(help_msg, reply_markup=kb_help, disable_web_page_preview=True)
        
    else:
        # --- START MESSAGE ---
        start_msg = (
            f"<b>👋 Halo {first_name}! Selamat Datang di {BOT_NAME}</b>\n\n"
            "<b>🤖 Bot Utilitas All-in-One Terbaik</b>\n"
            "Kami menyediakan berbagai alat canggih untuk membantu kebutuhan digital dan testing Anda secara <b>GRATIS</b> dan <b>CEPAT</b>.\n\n"
            "<b>🔥 Fitur Utama Kami:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>CC Checker Live</b> - Cek validitas kartu (Charge/Auth)\n"
            "⚙️ <b>VCC Generator</b> - Buat data kartu valid algoritma Luhn\n"
            "🌍 <b>Fake Identity</b> - Generator identitas lengkap (KTP/Alamat)\n"
            "📧 <b>Temp Mail</b> - Email sementara instan (Inbox Real-time)\n"
            "🏦 <b>IBAN Generator</b> - Data perbankan internasional valid\n"
            "🔍 <b>BIN Lookup</b> - Cek detail informasi BIN Bank\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>🚀 Mulai Sekarang!</b>\n"
            "Pilih salah satu menu di bawah ini untuk memulai."
        )
        
        # Inline Keyboard for Start
        kb_start = types.InlineKeyboardMarkup(row_width=2)
        kb_start.add(
            types.InlineKeyboardButton("💳 Checker", callback_data="m_chk"),
            types.InlineKeyboardButton("⚙️ Generator", callback_data="m_gen")
        )
        kb_start.add(
            types.InlineKeyboardButton("📧 Temp Mail", callback_data="m_mail"),
            types.InlineKeyboardButton("👤 Fake ID", callback_data="m_fake")
        )
        kb_start.add(
            types.InlineKeyboardButton("ℹ️ Info Akun", callback_data="m_info"),
            types.InlineKeyboardButton("❓ Bantuan", callback_data="m_info") # Pointing to info or maybe we should use a callback for help?
        )
        # Fix: The last button "Bantuan" should probably trigger help text, but callback 'm_info' shows user info. 
        # Let's create a callback for help if it doesn't exist, or just use url to /help? No, callback is better.
        # Looking at existing callbacks: m_chk, m_gen, m_mail, m_fake, m_info. 
        # Let's use 'm_main' for "Menu" but for "Bantuan" maybe we can send the help message? 
        # But wait, the user asked for "Help message".
        # Let's adjust the button to "❓ Panduan" and link it to a callback that shows help, 
        # BUT I don't want to create a NEW callback handler if not necessary.
        # I'll check if I can just use a trick. Or I can add a new callback 'm_help'.
        # For now, let's link "Bantuan" to "m_main" (Menu) or just remove it if redundant?
        # Actually, let's just make "Bantuan" trigger the help message via a new callback logic or just assume user types /help.
        # Better: I'll use a specific callback "m_help" and add it to the callback handler in the next step if needed.
        # However, to be safe and avoid adding new handlers if I can't, I will link "Bantuan" to "m_chk" (Checker) as a placeholder? No that's bad.
        # I will use 'm_main' for now as "Menu Utama". 
        # Re-reading: "start dengan lengkap kasih tombol inline keyboard juga".
        # I will stick to the plan but maybe change the last button to 'm_iban' since I highlighted it.
        
        # REVISION FOR BUTTONS:
        kb_start = types.InlineKeyboardMarkup(row_width=2)
        kb_start.add(
            types.InlineKeyboardButton("💳 Checker", callback_data="m_chk"),
            types.InlineKeyboardButton("⚙️ Generator", callback_data="m_gen")
        )
        kb_start.add(
            types.InlineKeyboardButton("📧 Temp Mail", callback_data="m_mail"),
            types.InlineKeyboardButton("👤 Fake ID", callback_data="m_fake")
        )
        kb_start.add(
            types.InlineKeyboardButton("🏦 Fake IBAN", callback_data="m_iban"),
            types.InlineKeyboardButton("🔍 Cek BIN", callback_data="m_bin")
        )
        kb_start.add(types.InlineKeyboardButton("💬 Support", url=f"tg://user?id={OWNER}"))

        await message.answer(start_msg, reply_markup=kb_start, disable_web_page_preview=True)
    
    # Send Reply Keyboard (Menu Bawah) - Persistent Menu
    # Removed separate ⌨️ message to keep it aesthetic as requested.
    # User can still access menu via the commands or previous keyboard if already present.
    pass


# --- NOTES FEATURE (INLINE INTERFACE) ---

async def show_notes_menu(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Buat Catatan", callback_data="note_add"),
        types.InlineKeyboardButton("📋 Lihat Catatan", callback_data="note_list")
    )
    
    text = (
        "<b>📝 SECURE NOTES</b>\n"
        "Simpan catatan penting Anda dengan aman.\n"
        "Silakan pilih menu di bawah:"
    )
    
    if message_id:
        try:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        except:
            await bot.send_message(chat_id, text, reply_markup=kb)
    else:
        await bot.send_message(chat_id, text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data in ['m_notes', 'note_main'], state="*")
async def cb_notes_main(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await show_notes_menu(call.message.chat.id, call.message.message_id)
    await call.answer()

@dp.callback_query_handler(text="note_list", state="*")
async def cb_notes_list(call: types.CallbackQuery):
    user_id = call.from_user.id
    notes = db.db_get_notes_list(user_id)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    text = ""
    if not notes:
        kb.add(types.InlineKeyboardButton("➕ Buat Catatan Baru", callback_data="note_add"))
        text = "📭 <b>Belum ada catatan.</b>"
    else:
        text = "<b>📂 DAFTAR CATATAN ANDA</b>\nPilih catatan untuk membuka:"
        for n in notes:
            title = n['title']
            cb_data = f"note_read:{title}"
            # Safety check for length
            if len(cb_data) > 64:
                 pass
            kb.add(types.InlineKeyboardButton(f"📄 {title}", callback_data=cb_data))
        
        kb.add(types.InlineKeyboardButton("➕ Tambah", callback_data="note_add"))
    
    kb.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="note_main"))
    
    await bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query_handler(text="note_add", state="*")
async def cb_notes_add(call: types.CallbackQuery):
    await NoteState.title.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Batal", callback_data="note_main"))
    
    await bot.edit_message_text(
        "<b>➕ BUAT CATATAN BARU</b>\n\nSilakan kirim <b>Judul Catatan</b> yang ingin dibuat.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )
    await call.answer()

@dp.message_handler(state=NoteState.title)
async def state_note_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) > 30:
        return await message.reply("⚠️ <b>Judul terlalu panjang!</b>\nMaksimal 30 karakter. Silakan kirim ulang.")
    
    # Check if title exists
    if db.db_get_note_content(message.from_user.id, title):
         return await message.reply("⚠️ <b>Judul sudah ada!</b>\nSilakan gunakan judul lain.")

    await state.update_data(title=title)
    await NoteState.next()
    await message.reply(
        f"<b>Judul:</b> {title}\n\nSekarang kirim <b>Isi Catatan</b> tersebut."
    )

@dp.message_handler(state=NoteState.content)
async def state_note_content(message: types.Message, state: FSMContext):
    content = message.text.strip()
    
    # SECURITY: Content Length Limit
    if len(content) > 2000:
        return await message.reply("⚠️ <b>Catatan Terlalu Panjang!</b>\nMaksimal 2000 karakter.")
    
    # SECURITY: Quota Limit
    existing = db.db_get_notes_list(message.from_user.id)
    if len(existing) >= 50:
        await state.finish()
        return await message.reply("⚠️ <b>Kuota Penuh!</b>\nMaksimal 50 catatan per user. Silakan hapus catatan lama.")

    data = await state.get_data()
    title = data['title']
    
    if db.db_save_note(message.from_user.id, title, content):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📂 Lihat Daftar", callback_data="note_list"))
        await message.reply(
            f"✅ Catatan <b>{title}</b> berhasil disimpan!",
            reply_markup=kb
        )
    else:
        await message.reply("⚠️ Gagal menyimpan catatan.")
        
    await state.finish()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('note_read:'), state="*")
async def cb_notes_read(call: types.CallbackQuery):
    try:
        title = call.data.split(':', 1)[1]
    except IndexError:
        return await call.answer("Error data.")

    content = db.db_get_note_content(call.from_user.id, title)
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🗑 Hapus", callback_data=f"note_del_ask:{title}"),
        types.InlineKeyboardButton("🔙 Kembali", callback_data="note_list")
    )
    
    if content:
        text = (
            f"<b>📝 {title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<code>{content}</code>\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = "⚠️ Catatan tidak ditemukan."
        
    await bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('note_del_ask:'), state="*")
async def cb_notes_del_ask(call: types.CallbackQuery):
    title = call.data.split(':', 1)[1]
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"note_del:{title}"),
        types.InlineKeyboardButton("❌ Batal", callback_data=f"note_read:{title}")
    )
    
    await bot.edit_message_text(
        f"❓ Apakah Anda yakin ingin menghapus catatan <b>{title}</b>?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('note_del:'), state="*")
async def cb_notes_del(call: types.CallbackQuery):
    title = call.data.split(':', 1)[1]
    if db.db_delete_note(call.from_user.id, title):
        await call.answer("Catatan dihapus!")
        await cb_notes_list(call)
    else:
        await call.answer("Gagal menghapus.", show_alert=True)

@dp.message_handler(commands=['note', 'notes'], commands_prefix=PREFIX)
async def cmd_notes(message: types.Message):
    user_id = message.from_user.id
    # Split: /note [action] [rest]
    args = message.text.split(maxsplit=2)
    
    if len(args) < 2:
        return await show_notes_menu(message.chat.id)
        
    action = args[1].lower()
    
    # --- ADD NOTE ---
    if action == "add":
        if len(args) < 3:
            return await message.reply("⚠️ <b>Format Salah!</b>\nGunakan: <code>/note add Judul | Isi</code>")
        
        await message.answer_chat_action('typing')
        remaining = args[2]
        
        # Logika Multi-Word Title dengan Pemisah '|'
        if '|' in remaining:
            parts = remaining.split('|', 1) # Pisah hanya pada '|' pertama
            title = parts[0].strip()
            content = parts[1].strip()
        else:
            # Fallback: Logika Lama (Spasi Pertama)
            parts = remaining.split(maxsplit=1)
            title = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
        
        # Validasi Dasar
        if not title:
             return await message.reply("⚠️ <b>Judul Kosong!</b>\nHarap masukkan judul catatan.")
             
        if not content:
             return await message.reply("⚠️ <b>Konten Kosong!</b>\nMasukkan isi catatan yang ingin disimpan.")
             
        if db.db_save_note(user_id, title, content):
            await message.reply(f"✅ Catatan <b>{title}</b> berhasil disimpan secara aman.")
        else:
            await message.reply("⚠️ <b>Gagal Menyimpan.</b>\nTerjadi kesalahan database atau judul sudah ada.")

    # --- LIST NOTES ---
    elif action == "list":
        await message.answer_chat_action('typing')
        notes = db.db_get_notes_list(user_id)
        if not notes:
            return await message.reply("📭 <b>Belum ada catatan.</b>\nBuat baru dengan <code>/note add</code>")
            
        lines = []
        for n in notes:
            title = n['title']
            lines.append(f"🔹 <code>{title}</code>")
            
        await message.reply(
            f"<b>📂 DAFTAR CATATAN ANDA</b>\n"
            f"Gunakan <code>/note get [judul]</code> untuk membuka.\n━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines)
        )

    # --- GET NOTE ---
    elif action == "get":
        if len(args) < 3:
             return await message.reply("⚠️ Format: <code>/note get [judul]</code>")
             
        await message.answer_chat_action('typing')
        # Ambil SELURUH sisa teks sebagai judul (Support Multi-word)
        title = args[2].strip()
        
        content = db.db_get_note_content(user_id, title)
        
        if content:
            await message.reply(
                f"<b>📝 CATATAN: {title}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<code>{content}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<i>🔓 Terdekripsi otomatis.</i>"
            )
        else:
            await message.reply(f"⚠️ Catatan <b>{title}</b> tidak ditemukan.")

    # --- DELETE NOTE ---
    elif action == "del":
        if len(args) < 3:
             return await message.reply("⚠️ Format: <code>/note del [judul]</code>")
             
        await message.answer_chat_action('typing')
        # Ambil SELURUH sisa teks sebagai judul
        title = args[2].strip()
        
        if db.db_delete_note(user_id, title):
            await message.reply(f"🗑️ Catatan <b>{title}</b> berhasil dihapus.")
        else:
            await message.reply(f"⚠️ Gagal menghapus. Pastikan judul benar.")
    
    else:
        await message.reply(help_msg)

@dp.message_handler(commands=['admin', 'panel'], commands_prefix=PREFIX)
async def admin_panel(message: types.Message):
    if not await is_owner(message.from_user.id):
        return # Ignore non-admins
        
    await message.reply(
        "<b>🔓 ADMIN PANEL MODE</b>\nSilakan pilih menu di bawah:",
        reply_markup=get_admin_keyboard()
    )

@dp.message_handler(commands=['addadmin'], commands_prefix=PREFIX)
async def cmd_add_admin(message: types.Message):
    if message.from_user.id != OWNER:
        return await message.reply("⚠️ Hanya Owner yang bisa menambah admin.")
        
    target_id = None
    target_username = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username
    else:
        args = message.get_args()
        if not args:
            return await message.reply(f"⚠️ Format: <code>{PREFIX}addadmin ID_USER</code> atau balas pesan user.")
        if not args.isdigit():
            return await message.reply("⚠️ ID harus berupa angka.")
        target_id = int(args)
    
    # Try fetch username if None
    if not target_username:
        try:
            chat_info = await bot.get_chat(target_id)
            target_username = chat_info.username
        except:
            target_username = None

    if add_new_admin(target_id, target_username):
        await message.reply(f"✅ User <code>{target_id}</code> (@{target_username or 'N/A'}) telah ditambahkan sebagai Admin.")
    else:
        await message.reply(f"⚠️ User <code>{target_id}</code> sudah menjadi admin.")

@dp.message_handler(commands=['deladmin'], commands_prefix=PREFIX)
async def cmd_del_admin(message: types.Message):
    if message.from_user.id != OWNER:
        return await message.reply("⚠️ Hanya Owner yang bisa menghapus admin.")
        
    args = message.get_args()
    if not args:
        return await message.reply(f"⚠️ Format: <code>{PREFIX}deladmin ID_USER</code>")
        
    if not args.isdigit():
        return await message.reply("⚠️ ID harus berupa angka.")
        
    target_id = int(args)
    if remove_admin(target_id):
        await message.reply(f"✅ User <code>{target_id}</code> dihapus dari Admin.")
    else:
        await message.reply(f"⚠️ Gagal menghapus. User <code>{target_id}</code> bukan admin tambahan atau tidak ditemukan.")

@dp.message_handler(commands=['toggle'], commands_prefix=PREFIX)
async def cmd_toggle(message: types.Message):
    if message.from_user.id not in get_admins(): return
    
    args = message.get_args().lower()
    valid_codes = ['chk', 'gen', 'mail', 'bin', 'rnd', 'fake']
    
    if args not in valid_codes:
        return await message.reply(f"⚠️ Code salah. Valid: <code>{', '.join(valid_codes)}</code>")
        
    if args in BOT_STATE["disabled_features"]:
        BOT_STATE["disabled_features"].remove(args)
        status = "🟢 ON (Enabled)"
    else:
        BOT_STATE["disabled_features"].append(args)
        status = "🔴 OFF (Disabled)"
    
    save_bot_state()
    await message.reply(f"✅ Fitur <b>{args}</b> sekarang: {status}")

@dp.message_handler(commands=['ban'], commands_prefix=PREFIX)
async def cmd_ban(message: types.Message):
    if message.from_user.id not in get_admins(): return
    target = message.get_args()
    if not target.isdigit(): return await message.reply("⚠️ Format: <code>/ban ID</code>")
    
    if int(target) in get_admins():
        return await message.reply("⚠️ Tidak bisa ban sesama Admin.")
        
    if ban_user(target):
        await message.reply(f"⛔ User <code>{target}</code> telah diblokir.")
    else:
        await message.reply(f"⚠️ User <code>{target}</code> sudah dibanned.")

@dp.message_handler(commands=['unban'], commands_prefix=PREFIX)
async def cmd_unban(message: types.Message):
    if message.from_user.id not in get_admins(): return
    target = message.get_args()
    if not target.isdigit(): return await message.reply("⚠️ Format: <code>/unban ID</code>")
    
    if unban_user(target):
        await message.reply(f"✅ User <code>{target}</code> telah dibuka blokirnya.")
    else:
        await message.reply(f"⚠️ User <code>{target}</code> tidak ditemukan di daftar ban.")

@dp.message_handler(commands=['user'], commands_prefix=PREFIX)
async def cmd_check_user(message: types.Message):
    if message.from_user.id not in get_admins(): return
    target = message.get_args()
    if not target.isdigit(): return await message.reply("⚠️ Format: <code>/user ID</code>")
    
    is_adm = int(target) in get_admins()
    is_ban = target in get_banned_users()
    
    status = "👤 User Biasa"
    if is_adm: status = "👮 Admin"
    if is_ban: status = "⛔ Banned"
    
    await message.reply(f"<b>Info User {target}</b>\nStatus: <b>{status}</b>")

@dp.message_handler(commands=['dm'], commands_prefix=PREFIX)
async def cmd_dm(message: types.Message):
    if message.from_user.id not in get_admins(): return
    try:
        args = message.text.split(maxsplit=2)
        target = args[1]
        msg = args[2]
    except:
        return await message.reply("⚠️ Format: <code>/dm ID Pesan</code>")
        
    try:
        await bot.send_message(target, f"<b>📩 PESAN DARI ADMIN</b>\n\n{msg}")
        await message.reply(f"✅ Pesan terkirim ke <code>{target}</code>")
    except Exception as e:
        await message.reply(f"❌ Gagal kirim: {e}")

@dp.message_handler(commands=['spy'], commands_prefix=PREFIX)
async def cmd_spy(message: types.Message):
    global SPY_MODE, SPY_ADMIN
    
    if message.from_user.id not in get_admins(): return
    
    args = message.get_args().lower()
    
    if args == "on":
        SPY_MODE = True
        SPY_ADMIN = message.from_user.id
        await message.reply("👁️ <b>SPY MODE ACTIVATED</b>\nSekarang Anda akan menerima laporan aktivitas user secara live.")
    elif args == "off":
        SPY_MODE = False
        SPY_ADMIN = None
        await message.reply("🙈 <b>SPY MODE DEACTIVATED</b>")
    else:
        status = "🟢 ON" if SPY_MODE else "🔴 OFF"
        await message.reply(f"<b>SPY MODE STATUS:</b> {status}\nGunakan: <code>/spy on</code> atau <code>/spy off</code>")

@dp.message_handler(commands=['bc', 'broadcast'], commands_prefix=PREFIX)
async def broadcast_msg(message: types.Message):
    if message.from_user.id not in get_admins(): return
    
    users = get_all_users()
    count = 0
    
    # Mode 1: Reply Broadcast (Forward/Copy)
    if message.reply_to_message:
        src = message.reply_to_message
        await message.reply(f"🚀 Memulai forward broadcast ke {len(users)} pengguna...")
        
        log_admin_action(message.from_user, "BROADCAST_FWD", f"To {len(users)} users")
        
        for i, uid in enumerate(users):
            try:
                # Use forward_message as it is safest in 2.x
                await src.forward(uid)
                count += 1
                
                # Smart Delay (Anti-Flood)
                if i % 20 == 0:
                    await asyncio.sleep(1.5) # Istirahat tiap 20 pesan
                else:
                    await asyncio.sleep(0.05) 
            except: pass
            
    # Mode 2: Text Broadcast (With Buttons Support)
    else:
        raw_text = message.text.split(maxsplit=1)
        if len(raw_text) < 2:
            return await message.reply(
                "⚠️ <b>Format Salah!</b>\n"
                "• Polos: <code>/bc Pesan</code>\n"
                "• Tombol: <code>/bc Pesan ~ Tombol:Link</code>\n"
                "Contoh: <code>/bc Promo Murah! ~ Beli:https://google.com</code>"
            )
        
        full_args = raw_text[1]
        
        # Parsing Buttons
        parts = full_args.split('~')
        msg_text = parts[0].strip()
        
        kb = None
        if len(parts) > 1:
            kb = types.InlineKeyboardMarkup(row_width=1)
            for btn_str in parts[1:]:
                if ':' in btn_str:
                    label, url = btn_str.split(':', 1)
                    kb.add(types.InlineKeyboardButton(label.strip(), url=url.strip()))
        
        await message.reply(f"🚀 Memulai text broadcast ke {len(users)} pengguna...")
        log_admin_action(message.from_user, "BROADCAST_TXT", f"Msg: {msg_text[:20]}...")
        
        for i, uid in enumerate(users):
            try:
                await bot.send_message(uid, f"<b>📢 PENGUMUMAN</b>\n\n{msg_text}", reply_markup=kb)
                count += 1
                
                # Smart Delay
                if i % 20 == 0:
                    await asyncio.sleep(1.5)
                else:
                    await asyncio.sleep(0.05)
            except: pass
            
    await message.reply(f"✅ Broadcast selesai. Terkirim ke {count} pengguna.")

async def background_broadcast(text):
    """Kirim pesan ke semua user secara background."""
    users = get_all_users()
    for uid in users:
        try:
            await bot.send_message(uid, text)
            await asyncio.sleep(0.05) # Rate limit safe
        except: pass

@dp.callback_query_handler(lambda c: c.data in ['maint_on', 'maint_off'])
async def process_maint_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in get_admins():
        return await bot.answer_callback_query(callback_query.id, "❌ Akses Ditolak", show_alert=True)

    mode = callback_query.data == 'maint_on'
    
    # Update State
    BOT_STATE["maintenance"] = mode
    save_bot_state()
    
    # Log
    action_str = "ON" if mode else "OFF"
    log_admin_action(callback_query.from_user, "MAINTENANCE", f"Set to {action_str}")
    
    # AUTO BROADCAST
    if mode:
        msg_bc = "🚧 <b>MAINTENANCE ALERT</b> 🚧\nMohon maaf, bot sedang dalam perbaikan sementara. Silakan kembali lagi nanti."
    else:
        msg_bc = "✅ <b>BOT ONLINE</b> ✅\nMaintenance selesai! Silakan gunakan bot kembali."
        
    asyncio.create_task(background_broadcast(msg_bc))
    
    # Feedback UI Update
    status_txt = "🔴 ON (Maintenance)" if mode else "🟢 OFF (Normal)"
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔴 Aktifkan", callback_data="maint_on"),
        types.InlineKeyboardButton("🟢 Matikan", callback_data="maint_off")
    )

    try:
        await bot.edit_message_text(
            f"<b>🚧 MAINTENANCE MODE CONTROL</b>\n"
            f"Status saat ini: <b>{status_txt}</b>\n\n"
            f"<i>Jika mode ini aktif, bot hanya bisa digunakan oleh Admin.</i>\n"
            f"✅ <b>Berhasil diubah ke {action_str}!</b>\n"
            f"📢 <i>Broadcast pemberitahuan sedang dikirim ke semua user...</i>",
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            reply_markup=kb,
            parse_mode=types.ParseMode.HTML
        )
    except: pass
    
    await bot.answer_callback_query(callback_query.id, f"Maintenance: {action_str}")

@dp.message_handler(commands=['setstart'], commands_prefix=PREFIX)
async def cmd_set_start(message: types.Message):
    if message.from_user.id not in get_admins(): return
    # Ambil full text setelah command (raw) untuk mempertahankan format baris
    text = message.text.split(maxsplit=1)
    if len(text) < 2: return await message.reply(f"⚠️ Gunakan: <code>{PREFIX}setstart [pesan baru]</code>")
    
    content = text[1]
    db.db_set_config("start_text", content)
    log_admin_action(message.from_user, "SET_START", "Updated start message")
    await message.reply("✅ Pesan Start berhasil diubah!")

@dp.message_handler(commands=['sethelp'], commands_prefix=PREFIX)
async def cmd_set_help(message: types.Message):
    if message.from_user.id not in get_admins(): return
    text = message.text.split(maxsplit=1)
    if len(text) < 2: return await message.reply(f"⚠️ Gunakan: <code>{PREFIX}sethelp [pesan baru]</code>")
    
    content = text[1]
    db.db_set_config("help_text", content)
    log_admin_action(message.from_user, "SET_HELP", "Updated help message")
    await message.reply("✅ Pesan Help berhasil diubah!")

@dp.message_handler(lambda message: message.text in ["📊 Stats", "📢 Broadcast", "⛔ User Control", "🎛️ Features", "👁️ Spy Mode", "🚧 Maint. Mode", "🏥 System Health", "👥 Admins", "🔙 Exit Admin", "✏️ Edit Texts", "📜 Admin Logs", "🎹 Menu Editor"])
async def process_admin_keyboard(message: types.Message):
    if message.from_user.id not in get_admins(): return
    
    text = message.text
    
    if text == "📊 Stats":
        u_count = get_users_count()
        b_count = len(get_banned_users())
        # mail_sessions = len(USER_MAILS) # Deprecated
        
        # System Info
        import platform, psutil
        uname = platform.uname()
        ram = psutil.virtual_memory()
        
        info_txt = f"""
<b>📊 BOT STATISTICS</b>
━━━━━━━━━━━━━━━━━━
👥 <b>Total Users:</b> {u_count}
⛔ <b>Banned Users:</b> {b_count}
🤖 <b>OS:</b> {uname.system}
🧠 <b>RAM:</b> {ram.percent}% Used

☁️ <b>Database:</b> Supabase/TiDB (Cloud)
"""
        await message.reply(info_txt)
        
    elif text == "📢 Broadcast":
        await message.reply(
            "<b>📢 BROADCAST MENU</b>\n"
            "• <b>Biasa:</b> <code>/bc pesan</code>\n"
            "• <b>Tombol:</b> <code>/bc Pesan ~ Tombol:Link</code>\n"
            "• <b>Forward:</b> Reply pesan lalu ketik <code>/bc</code>"
        )

    elif text == "⛔ User Control":
        await message.reply(
            "<b>⛔ USER CONTROL</b>\n"
            "• <code>/ban ID</code> : Blokir user\n"
            "• <code>/unban ID</code> : Buka blokir\n"
            "• <code>/user ID</code> : Cek status user\n"
            "• <code>/dm ID pesan</code> : Kirim pesan personal"
        )

    elif text == "🎛️ Features":
        status_chk = "🔴 OFF" if "chk" in BOT_STATE["disabled_features"] else "🟢 ON"
        status_gen = "🔴 OFF" if "gen" in BOT_STATE["disabled_features"] else "🟢 ON"
        status_mail = "🔴 OFF" if "mail" in BOT_STATE["disabled_features"] else "🟢 ON"
        status_bin = "🔴 OFF" if "bin" in BOT_STATE["disabled_features"] else "🟢 ON"
        
        msg = (
            f"<b>🎛️ FEATURE TOGGLE</b>\n"
            f"Gunakan <code>/toggle [kode]</code> untuk on/off.\n\n"
            f"💳 Checker (chk): {status_chk}\n"
            f"⚙️ Generator (gen): {status_gen}\n"
            f"📧 Temp Mail (mail): {status_mail}\n"
            f"🔍 BIN Look (bin): {status_bin}"
        )
        await message.reply(msg)

    elif text == "👁️ Spy Mode":
        # Toggle Spy Mode
        global SPY_MODE, SPY_ADMIN
        SPY_MODE = not SPY_MODE
        
        if SPY_MODE:
            SPY_ADMIN = message.from_user.id
            status_txt = "🟢 ACTIVATED"
            extra_info = "\nAnda sekarang akan menerima laporan live."
        else:
            SPY_ADMIN = None
            status_txt = "🔴 DEACTIVATED"
            extra_info = ""
            
        await message.reply(f"<b>👁️ SPY MODE {status_txt}</b>{extra_info}")

    elif text == "🚧 Maint. Mode":
        is_maint = BOT_STATE["maintenance"]
        status_txt = "🔴 ON (Maintenance)" if is_maint else "🟢 OFF (Normal)"
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🔴 Aktifkan", callback_data="maint_on"),
            types.InlineKeyboardButton("🟢 Matikan", callback_data="maint_off")
        )
        
        await message.reply(
            f"<b>🚧 MAINTENANCE MODE CONTROL</b>\n"
            f"Status saat ini: <b>{status_txt}</b>\n\n"
            f"<i>Jika mode ini aktif, bot hanya bisa digunakan oleh Admin.</i>",
            reply_markup=kb
        )

    elif text == "🏥 System Health":
        await message.answer_chat_action('typing')
        # Check External APIs
        status_binlist = "Unknown"
        status_mailtm = "Unknown"
        status_chkr = "Unknown"
        
        try:
            r = requests.get('https://lookup.binlist.net/451234', timeout=5)
            status_binlist = "🟢 UP" if r.status_code == 200 else f"🔴 DOWN ({r.status_code})"
        except: status_binlist = "🔴 DOWN"

        try:
            r = requests.get('https://api.mail.tm/domains', timeout=5)
            status_mailtm = "🟢 UP" if r.status_code == 200 else f"🔴 DOWN ({r.status_code})"
        except: status_mailtm = "🔴 DOWN"
        
        try:
            # Checker is now Local
            status_chkr = "🟢 LOCAL (Internal)"
        except: status_chkr = "🔴 ERROR"
        
        msg = (
            "<b>🏥 SYSTEM HEALTH CHECK</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"💳 <b>Binlist API:</b> {status_binlist}\n"
            f"📧 <b>Mail.tm API:</b> {status_mailtm}\n"
            f"✅ <b>Checker API:</b> {status_chkr}"
        )
        await message.reply(msg)

    elif text == "👥 Admins":
        admins = get_admins()
        admin_list = "\n".join([f"• <code>{aid}</code> {'(Owner)' if aid == OWNER else ''}" for aid in admins])
        
        await message.reply(
            f"<b>👥 DAFTAR ADMIN</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{admin_list}\n\n"
            f"<b>Kelola Admin (Hanya Owner):</b>\n"
            f"• <code>{PREFIX}addadmin ID</code>\n"
            f"• <code>{PREFIX}deladmin ID</code>"
        )
    
    elif text == "✏️ Edit Texts":
        await message.reply(
            "<b>✏️ EDIT DYNAMIC TEXTS</b>\n"
            "Panduan mengubah pesan bot secara real-time.\n\n"
            "<b>1. Variabel Otomatis</b>\n"
            "Gunakan kode ini di dalam pesan Anda:\n"
            "• <code>{first_name}</code> : Nama depan user\n"
            "• <code>{username}</code> : Username user\n"
            "• <code>{id}</code> : ID user\n\n"
            "<b>2. Format Tombol (Inline)</b>\n"
            "Pisahkan pesan dan tombol dengan tanda <code>~</code>.\n"
            "Format tombol: <code>Label:Link</code>\n\n"
            "<b>3. Contoh Penggunaan</b>\n"
            "<code>/setstart Halo {first_name}! Selamat datang. ~ Channel:https://t.me/azkura ~ Website:https://google.com</code>\n\n"
            "<b>Perintah Tersedia:</b>\n"
            "• <code>/setstart [pesan]</code>\n"
            "• <code>/sethelp [pesan]</code>"
        )

    elif text == "🎹 Menu Editor":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.row("Reply Editor", "Inline Editor")
        kb.add("🔙 Back to Admin")
        
        guide_msg = (
            "<b>🎹 PANDUAN LENGKAP MENU EDITOR</b>\n"
            "Kelola tombol dan pesan bot tanpa coding. Ikuti panduan di bawah:\n\n"
            "<b>1️⃣ REPLY EDITOR (Menu Utama)</b>\n"
            "Mengubah tombol yang muncul di keyboard bawah user.\n"
            "• <b>Langkah:</b> Klik Add -> Isi Nama -> Isi Baris (1-5) -> Isi Pesan.\n"
            "• <b>Variabel:</b> Gunakan <code>{first_name}</code> untuk panggil nama user.\n"
            "• <b>Fitur Lanjut:</b> Setelah isi pesan, Anda bisa pilih <b>YA</b> untuk tambah tombol Inline di bawah pesan tersebut.\n\n"
            "<b>2️⃣ INLINE EDITOR (Bank Pesan)</b>\n"
            "Tempat menyimpan pesan 'template' (Pengumuman/Promo/Info).\n"
            "• <b>Langkah:</b> Klik Create -> Isi <b>KODE UNIK</b> (contoh: <code>info_vip</code>) -> Isi Pesan.\n"
            "• <b>Cara Panggil:</b> Ketik <code>/show info_vip</code> di chat.\n\n"
            "<b>3️⃣ FORMAT TOMBOL INLINE</b>\n"
            "Saat diminta memasukkan format tombol, gunakan aturan ini:\n"
            "• <b>Link Web:</b> <code>Nama|https://link.com</code>\n"
            "• <b>Pesan Internal:</b> <code>Nama|msg:KODE</code> (Membuka pesan dari Inline Editor)\n"
            "• <b>Callback:</b> <code>Nama|callback:data</code> (Untuk dev lanjut)\n\n"
            "<b>📝 CONTOH INPUT TOMBOL:</b>\n"
            "<i>(Satu baris pakai koma, baris baru pakai Enter)</i>\n"
            "<code>Join Grup|https://t.me/azkura, Web|https://google.com</code>\n"
            "<code>Tentang Bot|msg:about_us</code>\n\n"
            "💡 <b>Tips:</b> Buatlah konten di <b>Inline Editor</b> terlebih dahulu jika ingin membuat tombol navigasi (Sub-Menu)."
        )
        await message.reply(guide_msg, reply_markup=kb)

    elif text == "📜 Admin Logs":
        logs = db.db_get_activity_logs(limit=15)
        if not logs:
            return await message.reply("📭 <b>Log Kosong</b>\nBelum ada aktivitas admin tercatat.")
            
        log_lines = []
        for log in logs:
            dt = log.get('created_at', '')[:16].replace('T', ' ')
            act = log.get('action', 'UNK')
            adm = log.get('username') or log.get('admin_id')
            det = log.get('details', '')
            
            # Format: [Date] Admin: Action - Details
            log_lines.append(f"<code>[{dt}]</code> <b>{act}</b> by {adm}\n└ {det}")
            
        await message.reply(
            "<b>📜 LAST 15 ADMIN LOGS</b>\n━━━━━━━━━━━━━━━━━━\n" + "\n\n".join(log_lines)
        )
        
    elif text == "🔙 Exit Admin":
        await message.reply("Kembali ke menu utama.", reply_markup=get_reply_keyboard(is_admin=True))

# --- MENU EDITOR HANDLERS ---

@dp.message_handler(lambda m: m.text == "🔙 Back to Admin", state="*")
async def back_to_admin_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await admin_panel(message)

@dp.message_handler(lambda m: m.text == "Reply Editor", state="*")
async def reply_editor_menu(message: types.Message):
    if message.from_user.id not in get_admins(): return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Add Button", callback_data="reply_add"),
        types.InlineKeyboardButton("🗑 Delete Button", callback_data="reply_del_list")
    )
    
    # Show current layout
    config = menu_manager.load_config()
    preview = "<b>CURRENT REPLY MENU LAYOUT:</b>\n"
    sorted_btns = sorted(config.get('reply_menu', []), key=lambda x: x.get('row', 99))
    
    for btn in sorted_btns:
        preview += f"[R{btn.get('row', '?')}] <b>{btn['label']}</b> ({btn.get('type','?')})\n"
        
    await message.reply(preview, reply_markup=kb, parse_mode=types.ParseMode.HTML)

@dp.callback_query_handler(text="reply_add", state="*")
async def reply_add_start(call: types.CallbackQuery):
    await MenuReplyState.waiting_label.set()
    await call.message.reply("<b>➕ ADD BUTTON</b>\n\nSilakan kirim <b>Label/Nama Tombol</b> yang diinginkan.\nContoh: <code>Info Donasi</code>")
    await call.answer()

@dp.message_handler(state=MenuReplyState.waiting_label)
async def reply_add_label(message: types.Message, state: FSMContext):
    label = message.text.strip()
    if menu_manager.get_action_by_label(label):
        return await message.reply("⚠️ Tombol dengan nama tersebut sudah ada. Gunakan nama lain.")
        
    await state.update_data(label=label)
    await MenuReplyState.next()
    await message.reply(f"<b>Label:</b> {label}\n\nSekarang kirim <b>Nomor Baris (Row)</b>.\n1-4 (Standard), 5+ (Bawah).")

@dp.message_handler(state=MenuReplyState.waiting_row)
async def reply_add_row(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.reply("⚠️ Harap kirim angka.")
        
    row = int(message.text)
    await state.update_data(row=row)
    await MenuReplyState.next()
    await message.reply("Terakhir, kirim <b>Pesan Balasan (Response)</b> ketika tombol diklik.\nBisa pakai HTML dan {first_name}.")

@dp.message_handler(state=MenuReplyState.waiting_response)
async def reply_add_response(message: types.Message, state: FSMContext):
    response = message.text 
    await state.update_data(response=response)
    await MenuReplyState.next()
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("Ya", "Tidak")
    
    await message.reply(
        "Apakah Anda ingin menambahkan <b>Tombol Inline</b> (Link/URL) di bawah pesan balasan ini?",
        reply_markup=kb
    )

@dp.message_handler(state=MenuReplyState.waiting_inline_choice)
async def reply_add_inline_choice(message: types.Message, state: FSMContext):
    choice = message.text.lower()
    
    if choice == "tidak":
        # Simpan tanpa tombol inline
        data = await state.get_data()
        if menu_manager.add_reply_button(data['label'], data['response'], data['row'], inline_buttons=[]):
            await message.reply(f"✅ Tombol <b>{data['label']}</b> berhasil ditambahkan (Tanpa Inline)!", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.reply("⚠️ Gagal menyimpan.", reply_markup=types.ReplyKeyboardRemove())
        
        await state.finish()
        # Refresh UI
        fake_msg = message
        fake_msg.text = "Reply Editor"
        await reply_editor_menu(fake_msg)
        
    elif choice == "ya":
        await MenuReplyState.next()
        await message.reply(
            "Kirim <b>TOMBOL</b> dengan format:\n"
            "<code>Label|Link</code> atau <code>Label|callback:data</code>\n"
            "Pisahkan tombol sebaris dengan koma (,).\n"
            "Pisahkan baris baru dengan Enter.\n\n"
            "Contoh:\n"
            "<code>Google|https://google.com, Menu|callback:m_main</code>",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.reply("⚠️ Pilih Ya atau Tidak.")

@dp.message_handler(state=MenuReplyState.waiting_inline_conf)
async def reply_add_inline_conf(message: types.Message, state: FSMContext):
    raw_lines = message.text.splitlines()
    buttons = []
    
    try:
        # Parsing Logic
        for line in raw_lines:
            row_btns = []
            parts = line.split(',')
            for part in parts:
                if '|' in part:
                    lbl, val = part.split('|', 1)
                    lbl = lbl.strip()
                    val = val.strip()
                    
                    btn_obj = {"text": lbl}
                    if val.startswith('msg:'):
                        code = val.replace('msg:', '', 1).strip()
                        btn_obj['data'] = f"show_msg:{code}"
                    elif val.startswith('callback:'):
                        btn_obj['data'] = val.replace('callback:', '', 1)
                    else:
                        btn_obj['url'] = val
                    row_btns.append(btn_obj)
            if row_btns:
                buttons.append(row_btns)
        
        data = await state.get_data()
        if menu_manager.add_reply_button(data['label'], data['response'], data['row'], inline_buttons=buttons):
            await message.reply(f"✅ Tombol <b>{data['label']}</b> berhasil ditambahkan (Dengan Inline)!")
        else:
            await message.reply("⚠️ Gagal menyimpan.")
            
    except Exception as e:
        await message.reply(f"⚠️ Error format: {e}")
        return # Stay in state
        
    await state.finish()
    fake_msg = message
    fake_msg.text = "Reply Editor"
    await reply_editor_menu(fake_msg)

@dp.callback_query_handler(text="reply_del_list", state="*")
async def reply_del_list(call: types.CallbackQuery):
    config = menu_manager.load_config()
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for btn in config.get('reply_menu', []):
        # Only allow deleting 'text' type buttons to prevent breaking core features
        if btn.get('type') == 'text':
            kb.add(types.InlineKeyboardButton(f"❌ {btn['label']}", callback_data=f"rdel:{btn['label']}"))
            
    kb.add(types.InlineKeyboardButton("🔙 Kembali", callback_data="ignore")) # Use reply keyboard to go back
    
    if not kb.inline_keyboard:
        await call.message.reply("⚠️ Tidak ada tombol Custom yang bisa dihapus.")
    else:
        await call.message.reply("<b>🗑 DELETE BUTTON</b>\nKlik tombol yang ingin dihapus:", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('rdel:'), state="*")
async def reply_del_action(call: types.CallbackQuery):
    label = call.data.split(':', 1)[1]
    if menu_manager.delete_reply_button(label):
        await call.answer(f"Tombol '{label}' dihapus.")
        await call.message.delete() # Remove list
    else:
        await call.answer("Gagal menghapus.", show_alert=True)

# --- INLINE EDITOR HANDLERS ---

@dp.message_handler(lambda m: m.text == "Inline Editor", state="*")
async def inline_editor_menu(message: types.Message):
    if message.from_user.id not in get_admins(): return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Create New", callback_data="inline_add"),
        types.InlineKeyboardButton("📝 List Saved", callback_data="inline_list")
    )
    
    await message.reply(
        "<b>anggo INLINE EDITOR</b>\n"
        "Buat pesan custom dengan tombol URL/Callback.\n"
        "Gunakan kode unik untuk memanggil pesan ini nanti.",
        reply_markup=kb, parse_mode=types.ParseMode.HTML
    )

@dp.callback_query_handler(text="inline_add", state="*")
async def inline_add_start(call: types.CallbackQuery):
    await MenuInlineState.waiting_key.set()
    await call.message.reply("<b>➕ NEW INLINE MESSAGE</b>\n\nKirim <b>KODE UNIK</b> (satu kata) untuk pesan ini.\nContoh: <code>promo_juni</code>")
    await call.answer()

@dp.message_handler(state=MenuInlineState.waiting_key)
async def inline_add_key(message: types.Message, state: FSMContext):
    key = message.text.strip().lower()
    if ' ' in key: return await message.reply("⚠️ Kode harus satu kata tanpa spasi.")
    
    await state.update_data(key=key)
    await MenuInlineState.next()
    await message.reply("Kirim <b>JUDUL (Title)</b> pesan.")

@dp.message_handler(state=MenuInlineState.waiting_title)
async def inline_add_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await MenuInlineState.next()
    await message.reply("Kirim <b>ISI PESAN (Content)</b>. Support HTML.")

@dp.message_handler(state=MenuInlineState.waiting_content)
async def inline_add_content(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    await MenuInlineState.next()
    await message.reply(
        "Kirim <b>TOMBOL</b> dengan format:\n"
        "<code>Label|Link</code> atau <code>Label|callback:data</code>\n"
        "Pisahkan tombol sebaris dengan koma (,).\n"
        "Pisahkan baris baru dengan Enter.\n\n"
        "Contoh:\n"
        "<code>Google|https://google.com, Menu|callback:m_main</code>\n"
        "<code>Support|https://t.me/admin</code>"
    )

@dp.message_handler(state=MenuInlineState.waiting_buttons)
async def inline_add_buttons(message: types.Message, state: FSMContext):
    raw_lines = message.text.splitlines()
    buttons = []
    
    try:
        for line in raw_lines:
            row_btns = []
            parts = line.split(',')
            for part in parts:
                if '|' in part:
                    lbl, val = part.split('|', 1)
                    lbl = lbl.strip()
                    val = val.strip()
                    
                    btn_obj = {"text": lbl}
                    if val.startswith('msg:'):
                        code = val.replace('msg:', '', 1).strip()
                        btn_obj['data'] = f"show_msg:{code}"
                    elif val.startswith('callback:'):
                        btn_obj['data'] = val.replace('callback:', '', 1)
                    else:
                        btn_obj['url'] = val
                    row_btns.append(btn_obj)
            if row_btns:
                buttons.append(row_btns)
                
        data = await state.get_data()
        menu_manager.save_inline_message(data['key'], data['title'], data['content'], buttons)
        
        await message.reply(
            f"✅ Pesan Inline <b>{data['key']}</b> berhasil disimpan!\n"
            f"Gunakan perintah: <code>/show {data['key']}</code> untuk menampilkannya."
        )
    except Exception as e:
        await message.reply(f"⚠️ Error format: {e}")
        
    await state.finish()

@dp.message_handler(commands=['show'], commands_prefix=PREFIX)
async def show_inline_msg(message: types.Message):
    key = message.get_args()
    if not key: return
    
    data = menu_manager.get_inline_message(key)
    if not data: return await message.reply("⚠️ Pesan tidak ditemukan.")
    
    # Construct Keyboard
    kb = types.InlineKeyboardMarkup()
    for row in data['buttons']:
        btns_obj = []
        for b in row:
            if 'url' in b:
                btns_obj.append(types.InlineKeyboardButton(b['text'], url=b['url']))
            elif 'data' in b:
                btns_obj.append(types.InlineKeyboardButton(b['text'], callback_data=b['data']))
        kb.row(*btns_obj)
        
    text = f"<b>{data['title']}</b>\n\n{data['content']}"
    await message.reply(text, reply_markup=kb, parse_mode=types.ParseMode.HTML)

@dp.callback_query_handler(text="inline_list", state="*")
async def inline_list_view(call: types.CallbackQuery):
    keys = menu_manager.list_inline_messages()
    if not keys:
        return await call.answer("Belum ada pesan tersimpan.", show_alert=True)
        
    text = "<b>📝 SAVED INLINE MESSAGES</b>\n"
    for k in keys:
        text += f"• <code>/show {k}</code>\n"
        
    await call.message.reply(text)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('show_msg:'))
async def show_linked_message(call: types.CallbackQuery):
    key = call.data.split(':', 1)[1]
    data = menu_manager.get_inline_message(key)
    
    if not data:
        return await call.answer("⚠️ Pesan tidak ditemukan/dihapus.", show_alert=True)
        
    # Construct Keyboard
    kb = types.InlineKeyboardMarkup()
    for row in data['buttons']:
        btns_obj = []
        for b in row:
            if 'url' in b:
                btns_obj.append(types.InlineKeyboardButton(b['text'], url=b['url']))
            elif 'data' in b:
                btns_obj.append(types.InlineKeyboardButton(b['text'], callback_data=b['data']))
        kb.row(*btns_obj)
        
    text = f"<b>{data['title']}</b>\n\n{data['content']}"
    
    # Attempt to edit message for seamless navigation
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
    except:
        await call.message.answer(text, reply_markup=kb, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        
    await call.answer()


@dp.message_handler(lambda message: menu_manager.get_action_by_label(message.text) is not None)
async def process_dynamic_reply_button(message: types.Message):
    """Handler dinamis untuk tombol Reply Keyboard."""
    text = message.text
    btn_data = menu_manager.get_action_by_label(text)
    
    if not btn_data:
        return # Should not happen due to filter
        
    b_type = btn_data.get('type', 'text')
    
    # 1. Handle Text Response (Custom Buttons)
    if b_type == 'text':
        response = btn_data.get('response', 'No response set.')
        # Support variable replacement
        response = response.replace('{first_name}', message.from_user.first_name or "")
        response = response.replace('{username}', message.from_user.username or "")
        response = response.replace('{id}', str(message.from_user.id))
        
        # Handle Inline Buttons if any
        kb = None
        inline_data = btn_data.get('inline_buttons')
        if inline_data:
            kb = types.InlineKeyboardMarkup()
            for row in inline_data:
                btns_obj = []
                for b in row:
                    if 'url' in b:
                        btns_obj.append(types.InlineKeyboardButton(b['text'], url=b['url']))
                    elif 'data' in b:
                        btns_obj.append(types.InlineKeyboardButton(b['text'], callback_data=b['data']))
                if btns_obj:
                    kb.row(*btns_obj)
        
        await message.reply(response, reply_markup=kb, parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
        return

    # 2. Handle Core Actions (Built-in Features)
    action = btn_data.get('action')
    
    # Check Disabled Features
    if action in BOT_STATE["disabled_features"]:
        return await message.reply("⚠️ <b>Fitur ini sedang dimatikan sementara oleh Admin.</b>")

    if action == 'admin':
        await admin_panel(message)
        
    elif action == 'bin':
        await message.reply(
            "<b>💳 BIN LOOKUP & INFO</b>\n"
            "Fitur untuk mengecek detail informasi Bank Identification Number (BIN).\n\n"
            "<b>Apa yang ditampilkan?</b>\n"
            "• 🏦 Nama Bank & Website\n"
            "• 🌍 Negara & Mata Uang\n"
            "• 💳 Tipe Kartu (Debit/Credit) & Level\n\n"
            "<b>Cara Penggunaan:</b>\n"
            "Ketik perintah di bawah ini:\n"
            "<code>/bin 451234</code>\n\n"
            "<i>Tips: Masukkan 6 digit pertama kartu.</i>"
        )
    elif action == 'rnd':
        await rnd_bin(message)
    elif action == 'note':
        # Fake command call
        fake_msg = message
        fake_msg.text = "/note"
        await cmd_notes(fake_msg)
    elif action == 'chk':
        await message.reply(
            "<b>✅ LIVE CC CHECKER</b>\n"
            "Validasi kartu kredit/debit secara akurat (Auth/Charge).\n\n"
            "<b>Fitur Unggulan:</b>\n"
            "• ⚡ Cek Massal (Max 50)\n"
            "• 🔍 Deteksi Level & Bank\n"
            "• 🛡️ Anti-Duplicate & Rate Limit\n\n"
            "<b>Cara Penggunaan:</b>\n"
            "1. <b>Manual:</b> Ketik <code>/chk cc|mm|yy|cvv</code>\n"
            "2. <b>Massal:</b> Reply file/pesan list kartu dengan <code>/chk</code>\n\n"
            "<i>Format: 0000000000000000|01|25|000</i>"
        )
    elif action == 'iban':
         kb = types.InlineKeyboardMarkup(row_width=3)
         countries = list(iban.FAKEIBAN_COUNTRIES.items())
         btns = []
         for c_code, c_name in countries:
             flag_offset = 127397
             try:
                flag = chr(ord(c_code[0].upper()) + flag_offset) + chr(ord(c_code[1].upper()) + flag_offset)
             except: flag = "🏳️"
             label = f"{flag} {c_code.upper()}"
             btns.append(types.InlineKeyboardButton(label, callback_data=f"iban_gen_{c_code}"))
         kb.add(*btns)
         await message.reply("<b>🏦 FAKE IBAN GENERATOR</b>\nPilih negara:", reply_markup=kb)
         
    elif action == 'fake':
        kb = types.InlineKeyboardMarkup(row_width=4)
        countries = [
            ("🇺🇸 US", "us"), ("🇮🇩 ID", "id"), ("🇯🇵 JP", "jp"), ("🇰🇷 KR", "kr"),
            ("🇬🇧 UK", "uk"), ("🇸🇬 SG", "sg"), ("🇧🇷 BR", "br"), ("🇮🇳 IN", "in"),
            ("🇩🇪 DE", "de"), ("🇫🇷 FR", "fr"), ("🇪🇸 ES", "es"), ("🇮🇹 IT", "it"),
            ("🇨🇳 CN", "cn"), ("🇷🇺 RU", "ru"), ("🇨🇦 CA", "ca"), ("🇦🇺 AU", "au"),
            ("🇳🇱 NL", "nl"), ("🇹🇷 TR", "tr"), ("🇵🇱 PL", "pl"), ("🇺🇦 UA", "ua"),
            ("🇲🇾 MY", "my"), ("🇻🇳 VN", "vn"), ("🇹🇭 TH", "th"), ("🇵🇭 PH", "ph")
        ]
        btns = [types.InlineKeyboardButton(name, callback_data=f"fake_{code}") for name, code in countries]
        kb.add(*btns)
        await message.reply("<b>👤 FAKE ID GENERATOR</b>\nPilih negara target:", reply_markup=kb)
        
    elif action == 'mail':
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.row(
            types.InlineKeyboardButton("🎲 Buat Random", callback_data="m_mail_create"),
            types.InlineKeyboardButton("✍️ Buat Custom", callback_data="m_mail_custom")
        )
        kb.row(
            types.InlineKeyboardButton("📩 Cek Inbox", callback_data="refresh_mail"),
            types.InlineKeyboardButton("📋 List Akun", callback_data="m_mail_list")
        )
        kb.add(types.InlineKeyboardButton("🔑 Login Akun Lama", callback_data="m_mail_login"))
        
        await message.reply(
            "<b>📧 LAYANAN TEMP MAIL PREMIUM</b>\n"
            "Buat email sementara instan untuk verifikasi & privasi.\n\n"
            "<b>Fitur Unggulan:</b>\n"
            "• ⚡ <b>Instan:</b> Email langsung aktif.\n"
            "• 📬 <b>Live Inbox:</b> Pesan masuk otomatis.\n"
            "• 🔐 <b>Aman:</b> Lindungi email utama Anda dari spam.\n\n"
            "<i>Silakan pilih menu operasi di bawah ini:</i>",
            reply_markup=kb
        )
        
    elif action == 'gen':
        await message.reply(
            "<b>⚙️ VCC GENERATOR PRO</b>\n"
            "Buat nomor kartu valid (Luhn Algorithm) untuk keperluan testing.\n\n"
            "<b>Fitur Generator:</b>\n"
            "• 🔢 Algoritma Luhn (100% Valid)\n"
            "• 🌍 Auto Country Mode\n"
            "• 📄 Output File (Jika > 15)\n\n"
            "<b>Panduan Perintah:</b>\n"
            "• <b>Manual:</b> <code>/gen 454141</code>\n"
            "• <b>Lengkap:</b> <code>/gen 454141|xx|xx|xxx</code>\n"
            "• <b>Otomatis:</b> <code>/gen id</code> (Negara)\n"
            "• <b>Massal:</b> <code>/gen 454141 50</code> (Jumlah)\n\n"
            "<i>Contoh: /gen us 20</i>"
        )
    elif action == 'info':
        await info(message)
    elif action == 'help':
        fake_message = message
        fake_message.text = "/help"
        await helpstr(fake_message)


@dp.message_handler(commands=['info', 'id'], commands_prefix=PREFIX)
async def info(message: types.Message):
    # Determine target user
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user
        
    user_id = target.id
    username = f"@{target.username}" if target.username else "No Username"
    fullname = target.full_name
    
    # Get DB Info
    db_data = db.db_get_user_info(user_id)
    joined_date = "Unknown"
    if db_data and 'joined_at' in db_data:
        # Format ISO timestamp to readable
        try:
            ts = db_data['joined_at'][:10] # YYYY-MM-DD
            joined_date = ts
        except: pass
        
    # Check Role
    is_adm = user_id in get_admins()
    is_own = user_id == OWNER
    
    role = "👤 User Biasa"
    if is_adm: role = "👮 Admin"
    if is_own: role = "👑 Owner"
    
    # Check Temp Mail Session
    mail_sess = "Tidak ada"
    # Check DB
    db_sess = db.db_get_mail_session(user_id)
    if db_sess:
        mail_sess = f"<code>{db_sess['email']}</code>"

    msg = f'''
<b>👤 USER PROFILE</b>
━━━━━━━━━━━━━━━━━━
<b>Biodata</b>
🆔 <b>ID:</b> <code>{user_id}</code>
👤 <b>Nama:</b> {fullname}
🔗 <b>Username:</b> {username}
📅 <b>Join Date:</b> {joined_date}

<b>Status Akun</b>
🔰 <b>Role:</b> {role}
📧 <b>Temp Mail:</b> {mail_sess}
━━━━━━━━━━━━━━━━━━
<i>Gunakan bot dengan bijak.</i>
'''
    await message.reply(msg)


@dp.message_handler(commands=['rnd'], commands_prefix=PREFIX)
async def rnd_bin(message: types.Message):
    await message.answer_chat_action('typing')
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    keyboard_markup = menu_keyboard()

    try:
        fake = Faker()
        raw_cc = fake.credit_card_number()
        BIN = raw_cc[:6]
        
        # Primary API: HandyAPI
        try:
            r = requests.get(f'https://data.handyapi.com/bin/{BIN}', timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('Status') == 'SUCCESS' or 'Scheme' in data:
                    # Parsing HandyAPI (Title Case)
                    scheme = (data.get('Scheme') or '-').upper()
                    card_type = (data.get('Type') or '-').upper()
                    brand = (data.get('CardTier') or '-').upper()
                    
                    c_data = data.get('Country', {})
                    c_name = c_data.get('Name') or '-'
                    c_emoji = "🏳️" # HandyAPI doesn't give emoji, maybe map code?
                    c_code = c_data.get('A2')
                    
                    # Simple Flag Mapper
                    if c_code:
                        flag_offset = 127397
                        c_emoji = chr(ord(c_code[0]) + flag_offset) + chr(ord(c_code[1]) + flag_offset)
                    
                    c_currency = "-" # Not provided directly usually
                    
                    bank_name = (data.get('Issuer') or '-').upper()
                    bank_url = (data.get('Website') or '-')
                    bank_phone = "-"
                    
                    # Construct Info
                    INFO = f'''
<b>🎲 RANDOM BIN RESULT</b>
━━━━━━━━━━━━━━━━━━
<b>BIN:</b> <code>{BIN}</code>
<b>Scheme:</b> {scheme}
<b>Tier:</b> {brand}
<b>Type:</b> {card_type}

<b>🌍 Country</b>
<b>Name:</b> {c_name} {c_emoji}
<b>Code:</b> {c_code}

<b>🏦 Bank</b>
<b>Name:</b> {bank_name}
<b>Web:</b> {bank_url}
━━━━━━━━━━━━━━━━━━
<b>Generated by:</b> <a href="tg://user?id={ID}">{FIRST}</a>
'''
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton(f"⚙️ Generate {BIN}", callback_data=f"gen_{BIN}"))
                    return await message.reply(INFO, reply_markup=kb, disable_web_page_preview=True)
        except: pass

        # Fallback API: Binlist
        r = requests.get(
            f'https://lookup.binlist.net/{BIN}',
            headers={'Accept-Version': '3'},
            timeout=10
        )
        
        data = {}
        if r.status_code == 200:
            data = r.json()
        
    except Exception as exc:
        logging.error("Gagal mengambil data Random BIN: %s", exc)
        return await message.reply(
            '<b>Gagal membuat Random BIN, coba lagi nanti.</b>',
            reply_markup=keyboard_markup
        )

    # Parsing JSON Data (Binlist)
    scheme = (data.get('scheme') or '-').upper()
    brand = (data.get('brand') or '-').upper()
    card_type = (data.get('type') or '-').upper()
    prepaid = "YES" if data.get('prepaid') else "NO"
    
    country_data = data.get('country') or {}
    c_name = country_data.get('name') or '-'
    c_emoji = country_data.get('emoji') or '🏳️'
    c_currency = country_data.get('currency') or '-'
    
    bank_data = data.get('bank') or {}
    bank_name = bank_data.get('name') or '-'
    bank_url = bank_data.get('url') or '-'
    bank_phone = bank_data.get('phone') or '-'

    INFO = f'''
<b>🎲 RANDOM BIN RESULT</b>
━━━━━━━━━━━━━━━━━━
<b>BIN:</b> <code>{BIN}</code>
<b>Scheme:</b> {scheme}
<b>Brand:</b> {brand}
<b>Type:</b> {card_type}
<b>Prepaid:</b> {prepaid}

<b>🌍 Country</b>
<b>Name:</b> {c_name} {c_emoji}
<b>Currency:</b> {c_currency}

<b>🏦 Bank</b>
<b>Name:</b> {bank_name}
<b>Web:</b> {bank_url}
<b>Phone:</b> {bank_phone}
━━━━━━━━━━━━━━━━━━
<b>Generated by:</b> <a href="tg://user?id={ID}">{FIRST}</a>
'''
    # Add Generate Button for this BIN
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"⚙️ Generate {BIN}", callback_data=f"gen_{BIN}"))
    
    await message.reply(INFO, reply_markup=kb, disable_web_page_preview=True)


@dp.message_handler(commands=['bin'], commands_prefix=PREFIX)
async def binio(message: types.Message):
    await message.answer_chat_action('typing')
    ID = message.from_user.id
    FIRST = message.from_user.first_name
    keyboard_markup = menu_keyboard()
    parts = (message.text or "").split(maxsplit=1)
    BIN = parts[1] if len(parts) > 1 else ''
    BIN = re.sub(r'[^0-9]', '', BIN)  # Clean non-numeric chars
    
    if len(BIN) < 6:
        return await message.reply(
            '<b>Mohon masukkan 6 digit BIN ya.</b> 😊\nContoh: <code>/bin 454123</code>',
            reply_markup=keyboard_markup
        )
    
    # --- DUAL API STRATEGY ---
    data = None
    source = "Unknown"
    
    # 1. Try HandyAPI (Better Limits)
    try:
        r = requests.get(f'https://data.handyapi.com/bin/{BIN[:6]}', timeout=5)
        if r.status_code == 200:
            json_data = r.json()
            if json_data.get('Status') == 'SUCCESS' or 'Scheme' in json_data:
                data = json_data
                source = "Handy"
    except: pass
    
    # 2. Try Binlist (Fallback) if Handy failed
    if not data:
        try:
            r = requests.get(f'https://lookup.binlist.net/{BIN[:6]}', headers={'Accept-Version': '3'}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                source = "Binlist"
            elif r.status_code == 429:
                return await message.reply('⚠️ <b>Limit API Habis.</b>\nSilakan coba beberapa saat lagi.')
        except: pass

    if not data:
        return await message.reply(f'❌ <b>BIN {BIN[:6]} tidak ditemukan atau server sibuk.</b>', reply_markup=keyboard_markup)

    # --- PARSING ---
    if source == "Handy":
        scheme = (data.get('Scheme') or '-').upper()
        brand = (data.get('CardTier') or '-').upper()
        card_type = (data.get('Type') or '-').upper()
        
        c_data = data.get('Country', {})
        c_name = c_data.get('Name') or '-'
        c_code = c_data.get('A2')
        try:
            c_emoji = chr(ord(c_code[0]) + 127397) + chr(ord(c_code[1]) + 127397)
        except: c_emoji = "🏳️"
        
        bank_name = (data.get('Issuer') or '-').upper()
        bank_url = data.get('Website') or '-'
        bank_phone = "-"
        prepaid = "-" # Not usually in Handy
        c_currency = "-"
        
    else: # Binlist
        scheme = (data.get('scheme') or '-').upper()
        brand = (data.get('brand') or '-').upper()
        card_type = (data.get('type') or '-').upper()
        prepaid = "YES" if data.get('prepaid') else "NO"
        
        country_data = data.get('country') or {}
        c_name = country_data.get('name') or '-'
        c_emoji = country_data.get('emoji') or '🏳️'
        c_currency = country_data.get('currency') or '-'
        
        bank_data = data.get('bank') or {}
        bank_name = bank_data.get('name') or '-'
        bank_url = bank_data.get('url') or '-'
        bank_phone = bank_data.get('phone') or '-'

    INFO = f'''
<b>🔍 BIN LOOKUP RESULT</b>
━━━━━━━━━━━━━━━━━━
<b>BIN:</b> <code>{BIN[:6]}</code>
<b>Scheme:</b> {scheme}
<b>Brand:</b> {brand}
<b>Type:</b> {card_type}
<b>Prepaid:</b> {prepaid}

<b>🌍 Country</b>
<b>Name:</b> {c_name} {c_emoji}
<b>Currency:</b> {c_currency}

<b>🏦 Bank</b>
<b>Name:</b> {bank_name}
<b>Web:</b> {bank_url}
<b>Phone:</b> {bank_phone}
━━━━━━━━━━━━━━━━━━
<b>Checked by:</b> <a href="tg://user?id={ID}">{FIRST}</a>
'''
    await message.reply(INFO, reply_markup=keyboard_markup, disable_web_page_preview=True)






@dp.message_handler(commands=['chk'], commands_prefix=PREFIX)
async def ch(message: types.Message):
    await message.answer_chat_action('typing')
    tic = time.perf_counter()
    keyboard_markup = menu_keyboard()
    s = requests.Session()
    
    try:
        await dp.throttle('chk', rate=ANTISPAM)
    except Throttled:
        await message.reply(
            f'<b>Terlalu sering, yuk jeda sebentar.</b>\nCoba lagi dalam <code>{ANTISPAM}</code> detik.',
            reply_markup=keyboard_markup
        )
        return
    else:
        if message.reply_to_message:
            raw_cards = message.reply_to_message.text
        else:
            parts = message.text.split(' ', 1)
            raw_cards = parts[1] if len(parts) > 1 else ''

        if not raw_cards.strip():
            return await message.reply(
                "<b>Belum ada data kartu yang bisa dicek.</b>\nKirim dengan format <code>0000|00|00|000</code> atau balas pesan kartu lalu ketik perintah ini.",
                reply_markup=keyboard_markup
            )

        card_lines = [line.strip() for line in raw_cards.splitlines() if line.strip()]

        if not card_lines:
            return await message.reply(
                "<b>Belum ada data kartu yang bisa dicek.</b>\nKirim dengan format <code>0000|00|00|000</code> atau balas pesan kartu lalu ketik perintah ini.",
                reply_markup=keyboard_markup
            )

        if len(card_lines) > 50:
            card_lines = card_lines[:50]

        # Cool loading message
        loading_msg = await message.reply(
            "<b>⚡ AZKURA BOT PROCESS ⚡</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💀 <b>Starting Checker Engine...</b>\n"
            f"💳 <b>Target:</b> {len(card_lines)} CC\n"
            "⌛ <b>Status:</b> <i>Authenticating...</i>",
            reply_markup=keyboard_markup
        )

        live_results = []
        die_results = []
        unknown_results = []
        
        last_edit_time = 0
        total_cards = len(card_lines)

        for idx, card_line in enumerate(card_lines, start=1):
            try:
                x = re.findall(r'\d+', card_line)
                ccn = x[0]
                mm = x[1]
                yy = x[2]
                cvv = x[3]
            except Exception:
                unknown_results.append(
                    f"<code>{card_line}</code>\n⚠️ <b>Result:</b> Format Salah"
                )
                continue

            if mm.startswith('2'):
                mm, yy = yy, mm
            if len(mm) >= 3:
                mm, yy, cvv = yy, cvv, mm
            mm = mm.zfill(2)[:2]
            yy = yy[-2:]
            
            # Relaxed validation: 12-19 digits allowed (Maestro, UnionPay, etc.)
            if len(ccn) < 12 or len(ccn) > 19 or not is_card_valid(ccn):
                unknown_results.append(
                    f"<code>{ccn}|{mm}|{yy}|{cvv}</code>\n⚠️ <b>Result:</b> Invalid Card/Luhn"
                )
                continue
                
            if ccn[:6] in BLACKLISTED:
                unknown_results.append(
                    f"<code>{ccn}|{mm}|{yy}|{cvv}</code>\n⚠️ <b>Result:</b> Blacklisted BIN"
                )
                continue
                
            # --- CALL LOCAL CHECKER ---
            res = local_chk_gate(ccn, mm, yy, cvv)
            
            # Parse Response
            bin_info = res.get("bin_info", "Unknown")
            msg_text = res.get("msg", "No message")
            status = res.get("status", "unknown")
            
            # Clean up response message (remove unwanted credits)
            clean_res = msg_text.replace("Checked - Shinji", "").replace("unknown", "").strip()
            if clean_res.startswith("✅ ") or clean_res.startswith("❌ ") or clean_res.startswith("⚠️ "):
                 clean_res = clean_res[2:].strip() # Remove icon prefix to avoid double icon

            # Detect Balance/Saldo
            balance_info = ""
            if "balance" in clean_res.lower() or "insufficient funds" in clean_res.lower() or "$" in clean_res:
                 # If balance is explicitly mentioned
                 pass

            # Icon Status
            if status == "live":
                stat_icon = "✅ <b>LIVE / CHARGED</b>"
            elif status == "die":
                stat_icon = "❌ <b>DEAD / DECLINED</b>"
            else:
                stat_icon = "⚠️ <b>UNKNOWN / ERROR</b>"

            # Format Output Modern & SEO Friendly
            result_line = (
                f"<b>↯ 🌩️ AZKURA GATE 🌩️</b>\n"
                f"{stat_icon}\n"
                f"<b>CC:</b> <code>{ccn}|{mm}|{yy}|{cvv}</code>\n"
                f"<b>Response:</b> {clean_res}\n"
                f"<b>Bin Info:</b> {bin_info}\n"
                f"<b>Time:</b> {time.strftime('%H:%M:%S')} - <b>Took:</b> {time.perf_counter() - tic:0.2f}s"
            )

            if status == "live":
                live_results.append(result_line)
            elif status == "die":
                die_results.append(result_line)
            else:
                unknown_results.append(result_line)

            # Update message logic (Throttle: every 3 seconds or last item)
            current_time = time.time()
            if current_time - last_edit_time > 3 or idx == total_cards:
                sections = []
                if live_results:
                    sections.append("<b>✅ Live Cards</b>\n" + "\n\n".join(live_results))
                if die_results:
                    sections.append("<b>❌ Dead Cards</b>\n" + "\n\n".join(die_results))
                if unknown_results:
                    sections.append("<b>⚠️ Unknown</b>\n" + "\n\n".join(unknown_results))
                
                body = "\n\n━━━━━━━━━━━━━━━━━━\n\n".join(sections) if sections else "<b>Processing...</b>"
                
                toc = time.perf_counter()
                footer = f"\n\n━━━━━━━━━━━━━━━━━━\n<b>Checked: {idx}/{total_cards}</b> - <b>Took: {toc - tic:0.2f}s</b>"
                
                try:
                    await loading_msg.edit_text(
                        body + footer,
                        reply_markup=keyboard_markup,
                        disable_web_page_preview=True
                    )
                    last_edit_time = current_time
                except Exception:
                    pass  # Ignore edit errors (flood control)


def luhn_verification(base):
    """Menghitung check digit Luhn untuk string angka."""
    digits = [int(x) for x in base]
    checksum = 0
    parity = len(digits) % 2
    for idx, num in enumerate(digits):
        if idx % 2 != parity:
            num *= 2
            if num > 9:
                num -= 9
        checksum += num
    
    return (10 - (checksum % 10)) % 10


@dp.message_handler(commands=['gen'], commands_prefix=PREFIX)
async def gen_cc(message: types.Message):
    await message.answer_chat_action('typing')
    
    # Parsing Arguments
    # Possible formats:
    # 1. /gen id (Country)
    # 2. /gen 454141 (BIN)
    # 3. /gen 454141 20 (BIN + Amount)
    # 4. /gen id 20 (Country + Amount)
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply(
            f"<b>Gunakan format:</b>\n"
            f"• <code>{PREFIX}gen 415464</code> (Standar)\n"
            f"• <code>{PREFIX}gen id</code> (Auto Indo)\n"
            f"• <code>{PREFIX}gen us 50</code> (50x Auto US)\n"
            f"• <code>{PREFIX}gen 415464 100</code> (Mass Gen)"
        )

    param1 = args[1].lower().strip()
    amount = 10 # Default
    
    # Cek apakah param2 ada (Amount)
    if len(args) > 2 and args[2].isdigit():
        amount = int(args[2])
        if amount > 1000: amount = 1000 # Limit safety
    
    # 1. Cek Mode Country
    # Coba cari BIN berdasarkan kode negara (2 huruf)
    if len(param1) == 2 and param1.isalpha():
        found_bin = checker.get_random_bin_by_country(param1)
        if not found_bin:
            return await message.reply(f"⚠️ <b>Maaf, belum ada data BIN untuk negara '{param1.upper()}'.</b>")
        raw_data = found_bin
        origin_type = f"Auto-{param1.upper()}"
    else:
        raw_data = param1
        # SECURITY CHECK (Input Validation)
        # Hanya izinkan angka, 'x' (random), dan '|' (pemisah)
        if not re.match(r'^[0-9xX|]+$', raw_data):
            return await message.reply(
                "⚠️ <b>Input Tidak Aman!</b>\n"
                "Format BIN hanya boleh mengandung Angka dan 'x'.\n"
                "Contoh: <code>454141xxxx</code>"
            )
        origin_type = "Manual"

    # Parsing Format (CC|MM|YY|CVV)
    cc_fmt, mm_fmt, yy_fmt, cvv_fmt = "", "x", "x", "x"
    if '|' in raw_data:
        parts = raw_data.split('|')
        cc_fmt = parts[0]
        if len(parts) > 1: mm_fmt = parts[1]
        if len(parts) > 2: yy_fmt = parts[2]
        if len(parts) > 3: cvv_fmt = parts[3]
    else:
        cc_fmt = raw_data

    cc_fmt = re.sub(r'[^0-9x]', '', cc_fmt)
    if not cc_fmt: return await message.reply("<b>Format BIN tidak valid.</b>")

    # --- NETWORK-AWARE LOGIC ---
    target_len = 16 
    if cc_fmt.startswith(('34', '37')): target_len = 15
    elif cc_fmt.startswith(('30', '36', '38', '39')): target_len = 14
    elif cc_fmt.startswith(('603298')): target_len = 16
    
    # FIX: Always ensure length matches target_len
    if len(cc_fmt) < target_len:
        cc_fmt += 'x' * (target_len - len(cc_fmt))
    elif len(cc_fmt) > target_len:
        cc_fmt = cc_fmt[:target_len]

    generated_list = []
    max_attempts = amount * 100 # Safety limit
    
    while len(generated_list) < amount and max_attempts > 0:
        max_attempts -= 1
        
        # 1. Fill 'x' (Skip last digit for Luhn calculation)
        temp_cc = list(cc_fmt)
        # Identify positions of 'x'
        x_indices = [i for i, char in enumerate(temp_cc) if char == 'x']
        
        for i in x_indices:
            temp_cc[i] = str(random.randint(0, 9))
            
        # 2. Luhn Calculation (Force Valid)
        # We calculate the required check digit for the last position
        # Only if the last digit was originally 'x' or we want to force validity on generated cards
        
        # Strategy: Construct candidate excluding last digit, calculate what last digit should be.
        # But wait, user might provide fixed last digit.
        # If user provided fixed full pattern that is invalid Luhn, we skip it?
        # Or we fix it? Usually generators fix the checksum.
        
        # Let's check if the original format had 'x' at the end or if we extended it.
        # Since we extended it with 'x' above if it was short, likely the last digit is generated.
        
        candidate_str = "".join(temp_cc)
        
        if not is_card_valid(candidate_str):
             # Try to fix the last digit to make it valid
             # Calculate Luhn Checksum for first N-1 digits
             digits = [int(x) for x in candidate_str[:-1]]
             checksum = 0
             parity = (len(digits) + 1) % 2 
             
             for idx, num in enumerate(digits):
                 if idx % 2 != parity:
                     num *= 2
                     if num > 9: num -= 9
                 checksum += num
                 
             # Calculate required check digit
             required_digit = (10 - (checksum % 10)) % 10
             
             # Replace last digit
             temp_cc[-1] = str(required_digit)
             candidate_str = "".join(temp_cc)
        
        # Double check validity (just in case)
        if not is_card_valid(candidate_str):
             continue 
        
        # 3. Generate Details
        if 'x' in mm_fmt or not mm_fmt: mm = str(random.randint(1, 12)).zfill(2)
        else: mm = mm_fmt.zfill(2)

        if 'x' in yy_fmt or not yy_fmt:
            curr_year = int(datetime.now().year)
            yy = str(random.randint(curr_year + 1, curr_year + 5))[-2:]
        else: yy = yy_fmt[-2:]

        if 'x' in cvv_fmt or not cvv_fmt:
            if candidate_str.startswith(('34', '37')): cvv = str(random.randint(1000, 9999))
            else: cvv = str(random.randint(100, 999))
        else: cvv = cvv_fmt
            
        full_result = f"{candidate_str}|{mm}|{yy}|{cvv}"
        if full_result not in generated_list:
            generated_list.append(full_result)

    if not generated_list:
        return await message.reply("⚠️ <b>Gagal generate.</b> Cek format BIN Anda.")

    # OUTPUT HANDLING
    # Jika hasil sedikit, kirim teks. Jika banyak, kirim file.
    
    sample_cc = generated_list[0].split('|')[0]
    bin_info_str, _ = checker.get_bin_info_range(sample_cc, "UNKNOWN")
    simple_info = bin_info_str.split('\n')[0]
    
    if len(generated_list) <= 15:
        result_text = "\n".join(generated_list)
        await message.reply(
            f"<b>⚙️ AZKURA GEN ({origin_type})</b>\n"
            f"<b>Info:</b> {simple_info}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<code>{result_text}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Total:</b> {len(generated_list)} CC"
        )
    else:
        # Kirim File
        import io
        output_str = "\n".join(generated_list)
        file_bio = io.BytesIO(output_str.encode('utf-8'))
        file_bio.name = f"cc_gen_{sample_cc[:6]}_{len(generated_list)}.txt"
        
        caption = (
            f"<b>⚙️ MASS GENERATED ({origin_type})</b>\n"
            f"<b>Info:</b> {simple_info}\n"
            f"<b>Total:</b> {len(generated_list)} CC\n"
            f"<i>File terlampir karena jumlah > 15</i>"
        )
        await message.reply_document(file_bio, caption=caption)

# --- MAIL.TM HELPERS (ASYNC) ---

async def get_mail_domains():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.mail.tm/domains") as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("hydra:member", [])
    except Exception as e:
        logging.error(f"Mail.tm domain error: {e}")
    return []

async def create_mail_account(email, password):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"address": email, "password": password}
            async with session.post("https://api.mail.tm/accounts", json=payload) as r:
                return r.status in [200, 201]
    except Exception as e:
        logging.error(f"Mail.tm create error: {e}")
        return False

async def get_mail_token(email, password):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"address": email, "password": password}
            async with session.post("https://api.mail.tm/token", json=payload) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("token")
    except Exception as e:
        logging.error(f"Mail.tm token error: {e}")
    return None

async def get_mail_messages(token):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get("https://api.mail.tm/messages", headers=headers) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("hydra:member", [])
    except:
        pass
    return None

@dp.message_handler(commands=['mail'], commands_prefix=PREFIX)
async def gen_mail(message: types.Message):
    # SECURITY: Cooldown 30 Seconds
    user_id = message.from_user.id
    last_gen = USER_MAIL_COOLDOWN.get(user_id, 0)
    if time.time() - last_gen < 30 and user_id not in get_admins():
        return await message.reply("⏳ <b>Cooldown!</b>\nMohon tunggu 30 detik sebelum membuat email baru lagi.")

    await message.answer_chat_action('typing')
    
    # Arg parsing: /mail [username] [password]
    args = message.text.split()
    custom_user = None
    custom_pass = None
    
    if len(args) > 1:
        custom_user = args[1].lower()
    if len(args) > 2:
        custom_pass = args[2]
        
    # 1. Get Domain
    domains = await get_mail_domains()
    if not domains:
        return await message.reply("⚠️ <b>Gagal mengambil domain email. Coba lagi nanti.</b>")
    
    domain = domains[0]['domain']
    
    # 2. Determine Username
    if custom_user:
        # Basic validation: only alphanumeric, dot, dash
        if not re.match(r'^[a-z0-9.-]+$', custom_user):
             return await message.reply("⚠️ <b>Username tidak valid!</b>\nHanya gunakan huruf, angka, titik (.), dan strip (-).")
        email = f"{custom_user}@{domain}"
    else:
        # Random Username
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{random_str}@{domain}"

    # 3. Determine Password
    if custom_pass:
        password = custom_pass
    else:
        password = "Pwd" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # 4. Create Account
    if await create_mail_account(email, password):
        # 5. Get Token
        token = await get_mail_token(email, password)
        if token:
            # Update Cooldown
            USER_MAIL_COOLDOWN[user_id] = time.time()
            
            # Save to DB
            db.db_save_mail_session(user_id, email, password, token)
            save_email_session(user_id, email, password, token)
            
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("📩 Cek Inbox (0)", callback_data="refresh_mail"))
            kb.add(types.InlineKeyboardButton("🔄 Ganti Akun", callback_data="m_mail_list"))
            
            await message.reply(
                f"<b>📧 TEMP MAIL CREATED</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<b>Email:</b> <code>{email}</code>\n"
                f"<b>Password:</b> <code>{password}</code>\n\n"
                f"<i>Klik tombol di bawah untuk cek pesan masuk.</i>\n"
                f"💡 <b>Simpan akses ini!</b> Jika bot restart, ketik:\n"
                f"<code>{PREFIX}login {email} {password}</code>",
                reply_markup=kb
            )
        else:
             await message.reply("⚠️ <b>Gagal mengambil token akun.</b>")
    else:
        await message.reply(
            f"⚠️ <b>Gagal membuat akun email.</b>\n"
            f"Kemungkinan username <code>{email.split('@')[0]}</code> sudah terpakai atau domain sedang bermasalah."
        )

@dp.message_handler(commands=['login'], commands_prefix=PREFIX)
async def login_mail(message: types.Message):
    await message.answer_chat_action('typing')
    user_id = message.from_user.id
    args = message.get_args().split()
    
    if len(args) != 2:
        return await message.reply(
            f"<b>Format salah!</b>\nGunakan: <code>{PREFIX}login email password</code>\n"
            f"Contoh: <code>{PREFIX}login user@domain.com rahasia123</code>"
        )
        
    email, password = args[0], args[1]
    
    # Try to get token
    token = get_mail_token(email, password)
    
    if token:
        # Save to DB
        db.db_save_mail_session(user_id, email, password, token)
        save_email_session(user_id, email, password, token)
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📩 Cek Inbox", callback_data="refresh_mail"))
        kb.add(types.InlineKeyboardButton("🔄 Ganti Akun", callback_data="m_mail_list"))
        
        await message.reply(
            f"<b>✅ Login Berhasil!</b>\n"
            f"Sesi email <code>{email}</code> telah dipulihkan.\n"
            f"Silakan cek inbox Anda.",
            reply_markup=kb
        )
    else:
        await message.reply("⚠️ <b>Login gagal!</b> Email atau password salah, atau akun sudah dihapus oleh server.")

@dp.callback_query_handler(lambda c: c.data.startswith('fake_'))
async def fake_country_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    country_code = callback_query.data.split('_')[1]
    
    # Trigger fake_identity logic
    fake_msg = callback_query.message
    fake_msg.from_user = callback_query.from_user
    fake_msg.text = f"/fake {country_code}"
    
    await fake_identity(fake_msg)

@dp.callback_query_handler(lambda c: c.data == 'm_mail_create')
async def create_mail_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    # Trigger gen_mail logic
    fake_msg = callback_query.message
    fake_msg.from_user = callback_query.from_user
    fake_msg.text = "/mail" # Reset args
    await gen_mail(fake_msg)

@dp.callback_query_handler(lambda c: c.data == 'm_mail_custom', state="*")
async def custom_mail_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish() # Reset any previous state
    await MailCustomState.username.set()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Batal", callback_data="m_mail"))
    
    await bot.edit_message_text(
        "<b>✍️ CUSTOM TEMP MAIL</b>\n\n"
        "Silakan masukkan <b>Username</b> yang diinginkan.\n"
        "<i>(Hanya huruf, angka, titik, dan strip)</i>",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=kb
    )
    await callback_query.answer()

@dp.message_handler(state=MailCustomState.username)
async def state_mail_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    
    if not re.match(r'^[a-z0-9.-]+$', username):
         return await message.reply("⚠️ <b>Username tidak valid!</b>\nHanya gunakan huruf, angka, titik (.), dan strip (-). Silakan coba lagi.")
    
    if len(username) < 3 or len(username) > 30:
        return await message.reply("⚠️ Username harus 3-30 karakter.")
        
    await state.update_data(username=username)
    await MailCustomState.next()
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎲 Acak Saja", callback_data="mail_pass_random"))
    
    await message.reply(
        f"<b>Username:</b> {username}\n\n"
        "Sekarang masukkan <b>Password</b> yang diinginkan.\n"
        "<i>Atau klik tombol 'Acak Saja' untuk password otomatis.</i>",
        reply_markup=kb
    )

@dp.callback_query_handler(text="mail_pass_random", state=MailCustomState.password)
async def cb_mail_pass_random(call: types.CallbackQuery, state: FSMContext):
    await execute_custom_mail(call.message, state, use_random_pass=True)
    await call.answer()

@dp.message_handler(state=MailCustomState.password)
async def state_mail_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 5:
        return await message.reply("⚠️ Password terlalu pendek (min 5 karakter).")
        
    await execute_custom_mail(message, state, password=password)

async def execute_custom_mail(message: types.Message, state: FSMContext, password=None, use_random_pass=False):
    # SECURITY: Cooldown
    user_id = message.chat.id
    last_gen = USER_MAIL_COOLDOWN.get(user_id, 0)
    if time.time() - last_gen < 30 and user_id not in get_admins():
        await state.finish()
        return await message.reply("⏳ <b>Cooldown!</b>\nTunggu 30 detik sebelum membuat email baru.")

    data = await state.get_data()
    username = data['username']
    # user_id already defined above
    
    if use_random_pass:
        password = "Pwd" + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
    # Get Domain
    domains = await get_mail_domains()
    if not domains:
        await state.finish()
        return await message.reply("⚠️ <b>Gagal mengambil domain email. Coba lagi nanti.</b>")
    
    domain = domains[0]['domain']
    email = f"{username}@{domain}"
    
    await message.answer_chat_action('typing')
    
    # Create Account
    if await create_mail_account(email, password):
        token = await get_mail_token(email, password)
        if token:
            # Update Cooldown
            USER_MAIL_COOLDOWN[user_id] = time.time()
            
            # Save
            db.db_save_mail_session(user_id, email, password, token)
            save_email_session(user_id, email, password, token)
            
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton("📩 Cek Inbox (0)", callback_data="refresh_mail"))
            kb.add(types.InlineKeyboardButton("🔄 Ganti Akun", callback_data="m_mail_list"))
            
            await message.reply(
                f"<b>📧 CUSTOM MAIL CREATED</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<b>Email:</b> <code>{email}</code>\n"
                f"<b>Password:</b> <code>{password}</code>\n\n"
                f"<i>Klik tombol di bawah untuk cek pesan masuk.</i>",
                reply_markup=kb
            )
        else:
            await message.reply("⚠️ <b>Gagal mengambil token akun.</b>")
    else:
        await message.reply(
            f"⚠️ <b>Gagal membuat akun email.</b>\n"
            f"Kemungkinan username <code>{username}</code> sudah terpakai."
        )
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'm_mail_login')
async def login_mail_menu_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        f"<b>🔑 LOGIN TEMP MAIL</b>\n"
        f"Akses kembali inbox email lama Anda.\n\n"
        f"<b>Format Perintah:</b>\n"
        f"<code>{PREFIX}login [email] [password]</code>\n\n"
        f"<b>Contoh:</b>\n"
        f"<code>{PREFIX}login budi@kuearas.com a1b2c3d4</code>\n\n"
        f"<i>Catatan: Hanya bisa login jika akun belum dihapus dari server.</i>"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('m_mail_list'))
async def list_emails_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Parse data: m_mail_list:page:mode
    parts = callback_query.data.split(':')
    page = 0
    mode = "view" # view or del
    
    if len(parts) > 1:
        try: page = int(parts[1])
        except: page = 0
    if len(parts) > 2:
        mode = parts[2]

    saved = SAVED_MAILS.get(user_id, [])
    if not saved:
        return await callback_query.message.edit_text(
            "⚠️ <b>Belum ada riwayat email.</b>\nBuat dulu dengan opsi di menu Temp Mail.",
            reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Menu Temp Mail", callback_data="m_mail"))
        )

    # Pagination Logic
    MAX_PER_PAGE = 5
    total_items = len(saved)
    total_pages = (total_items + MAX_PER_PAGE - 1) // MAX_PER_PAGE
    
    if page < 0: page = 0
    if page >= total_pages and total_pages > 0: page = total_pages - 1
    
    start_idx = page * MAX_PER_PAGE
    end_idx = start_idx + MAX_PER_PAGE
    current_page_items = saved[start_idx:end_idx]
    
    sess = db.db_get_mail_session(user_id)
    current_email = sess['email'] if sess else ''
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    # List Buttons
    for i, data in enumerate(current_page_items):
        actual_idx = start_idx + i
        email = data['email']
        is_active = "✅ " if email == current_email else ""
        
        if mode == "del":
            # Delete Mode: Button deletes the email
            btn_text = f"🗑 Hapus: {email}"
            cb_data = f"dm_mail_{actual_idx}_{page}"
        else:
            # View Mode: Button switches account
            btn_text = f"{is_active}{email}"
            cb_data = f"sw_mail_{actual_idx}_{page}"
            
        kb.add(types.InlineKeyboardButton(btn_text, callback_data=cb_data))
    
    # Navigation Buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"m_mail_list:{page-1}:{mode}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="ignore"))
    
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"m_mail_list:{page+1}:{mode}"))
    
    kb.row(*nav_buttons)
    
    # Control Buttons
    if mode == "del":
        kb.add(types.InlineKeyboardButton("🔙 Selesai Hapus", callback_data=f"m_mail_list:{page}:view"))
    else:
        kb.row(
            types.InlineKeyboardButton("🗑 Hapus Akun", callback_data=f"m_mail_list:{page}:del"),
            types.InlineKeyboardButton("🔙 Menu Temp Mail", callback_data="m_mail")
        )

    title_mode = "MENGHAPUS AKUN" if mode == "del" else "Saved Emails"
    instr = "Klik akun untuk <b>MENGHAPUS</b> permanen." if mode == "del" else "Klik akun di bawah untuk ganti sesi (Switch)."
    
    text = f"<b>📧 {title_mode} ({total_items})</b>\n{instr}"
    
    # Edit message text if it's a callback update
    try:
        await callback_query.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass # Content same
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('dm_mail_'))
async def delete_saved_mail_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    parts = callback_query.data.split('_')
    # Format: dm_mail_{index}_{page}
    
    try:
        idx = int(parts[2])
        page = int(parts[3])
    except:
        return await callback_query.answer("Error data.")
        
    saved = SAVED_MAILS.get(user_id, [])
    if idx < 0 or idx >= len(saved):
        return await callback_query.answer("Data tidak ditemukan.", show_alert=True)
    
    # Get email to be deleted
    deleted_email = saved[idx]['email']
    
    # Check if active
    current = db.db_get_mail_session(user_id) or {}
    if current.get('email') == deleted_email:
        # Clear active session if we delete the active one
        db.db_delete_mail_session(user_id)
        
    # Delete from list
    saved.pop(idx)
    SAVED_MAILS[user_id] = saved
    
    await callback_query.answer(f"🗑 {deleted_email} dihapus.")
    
    # Refresh list (stay in delete mode)
    # Redirect to list handler
    # Note: indices shift after delete, but we refresh the list so it should be fine.
    # However, if we are on the last item of a page, we might need to adjust page?
    # The list handler handles page >= total_pages adjustment.
    
    callback_query.data = f"m_mail_list:{page}:del"
    await list_emails_callback(callback_query)


@dp.message_handler(commands=['emails', 'listmail'], commands_prefix=PREFIX)
async def list_emails(message: types.Message):
    # Wrapper to call the callback logic with a dummy callback query
    # Need to simulate sending the initial message first
    user_id = message.from_user.id
    saved = SAVED_MAILS.get(user_id, [])
    
    if not saved:
        return await message.reply("⚠️ <b>Belum ada riwayat email.</b>")

    # Construct initial view (Page 0)
    # We can't reuse the callback handler directly easily because it expects a CallbackQuery object
    # So we replicate the page 0 logic briefly or create a dummy object.
    # Replicating page 0 logic is safer here.
    
    MAX_PER_PAGE = 5
    total_items = len(saved)
    total_pages = (total_items + MAX_PER_PAGE - 1) // MAX_PER_PAGE
    page = 0
    
    current_page_items = saved[0:MAX_PER_PAGE]
    sess = db.db_get_mail_session(user_id)
    current_email = sess['email'] if sess else ''
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, data in enumerate(current_page_items):
        email = data['email']
        is_active = "✅ " if email == current_email else ""
        kb.add(types.InlineKeyboardButton(f"{is_active}{email}", callback_data=f"sw_mail_{i}_{page}"))
        
    nav_buttons = []
    nav_buttons.append(types.InlineKeyboardButton(f"📄 1/{total_pages}", callback_data="ignore"))
    if total_pages > 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"m_mail_list:1"))
    
    kb.row(*nav_buttons)
    kb.add(types.InlineKeyboardButton("🔙 Menu Temp Mail", callback_data="m_mail"))
    
    await message.reply(
        f"<b>📧 Saved Emails ({total_items})</b>\nKlik akun di bawah untuk ganti sesi (Switch).",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith('sw_mail_'))
async def switch_mail_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    parts = callback_query.data.split('_')
    # Format: sw_mail_{index}_{page}
    
    try:
        idx = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
    except ValueError:
        return await callback_query.answer("Error data.")

    saved = SAVED_MAILS.get(user_id, [])
    
    if idx < 0 or idx >= len(saved):
        return await bot.answer_callback_query(callback_query.id, "⚠️ Data tidak ditemukan.", show_alert=True)
        
    selected_account = saved[idx]
    
    # Set as Active
    db.db_save_mail_session(user_id, selected_account['email'], selected_account['password'], selected_account['token'])
    
    email = selected_account['email']
    
    await bot.answer_callback_query(callback_query.id, f"✅ Switched to: {email}")
    
    # Refresh List UI to show checkmark (Reuse logic by redirecting to m_mail_list:page)
    # We can manually trigger the UI update by modifying the callback data and calling the list handler
    callback_query.data = f"m_mail_list:{page}"
    await list_emails_callback(callback_query)


# Handler for 'ignore' callback (static buttons)
@dp.callback_query_handler(lambda c: c.data == 'ignore')
async def ignore_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)


def get_mail_message_detail(token, msg_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def delete_mail_message(token, msg_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.delete(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
        return r.status_code == 204
    except:
        return False

@dp.callback_query_handler(lambda c: c.data.startswith('read_'))
async def read_mail_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    msg_id = callback_query.data.split('_')[1]
    user_data = db.db_get_mail_session(user_id)
    
    if not user_data:
        return await bot.answer_callback_query(callback_query.id, "⚠️ Sesi berakhir.", show_alert=True)
        
    await bot.answer_callback_query(callback_query.id, "📖 Membuka pesan...")
    
    msg = get_mail_message_detail(user_data['token'], msg_id)
    if not msg:
        return await bot.send_message(user_id, "⚠️ Gagal membaca pesan.")
        
    sender = msg.get('from', {}).get('address', 'Unknown')
    subject = msg.get('subject', 'No Subject')
    date_str = msg.get('createdAt', '')[:10]
    
    # Prefer HTML if available (stripped), else Text
    body = msg.get('text') or "No content"
    if len(body) > 3500: body = body[:3500] + "... (truncated)"
    
    text_out = (
        f"<b>📨 PESAN MASUK</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Dari:</b> {sender}\n"
        f"<b>Subjek:</b> {subject}\n"
        f"<b>Tanggal:</b> {date_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{body}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔙 Kembali", callback_data="refresh_mail"),
        types.InlineKeyboardButton("🗑️ Hapus", callback_data=f"del_{msg_id}")
    )
    
    # Send as new message because body can be long
    await bot.send_message(user_id, text_out, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query_handler(lambda c: c.data.startswith('del_'))
async def delete_mail_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    msg_id = callback_query.data.split('_')[1]
    user_data = db.db_get_mail_session(user_id)
    
    if user_data and delete_mail_message(user_data['token'], msg_id):
        await bot.answer_callback_query(callback_query.id, "✅ Pesan dihapus.")
        # Delete the message viewer
        try:
            await bot.delete_message(user_id, callback_query.message.message_id)
        except: pass
        # Ideally we could return to inbox, but simpler to just delete for now.
    else:
        await bot.answer_callback_query(callback_query.id, "⚠️ Gagal menghapus.", show_alert=True)









@dp.message_handler(commands=['fake'], commands_prefix=PREFIX)
async def fake_identity(message: types.Message):
    await message.answer_chat_action('typing')
    user_id = message.from_user.id
    first_name_user = message.from_user.first_name
    
    args = message.text.split()
    country_code = 'us'
    if len(args) > 1:
        country_code = args[1].lower()
    
    try:
        # Generate Identity using the new module
        data = identity.generate_identity(country_code)
        
        # Save to memory for "Save to Note" feature
        LAST_GEN_ID[user_id] = data

        # --- MAIL GENERATION INTEGRATION ---
        # Use generated email/pass from identity module
        email_addr = data['email']
        password = data['password']
        
        # Try to register to Mail.tm
        domains = await get_mail_domains()
        token = None
        email_status = "🔴 Offline"
        
        if domains:
            valid_domain = domains[0]['domain']
            # Re-construct email with valid domain
            user_part = data['email'].split('@')[0]
            email_addr = f"{user_part}@{valid_domain}"
            
            # Update data dictionary
            data['email'] = email_addr
            
            if await create_mail_account(email_addr, password):
                token = await get_mail_token(email_addr, password)
                if token:
                    db.db_save_mail_session(user_id, email_addr, password, token)
                    save_email_session(user_id, email_addr, password, token)
                    email_status = "🟢 Active"
                else:
                    email_status = "🔴 Error (Token)"
            else:
                email_status = "🔴 Fail (Create)"
        
        OUTPUT = identity.format_identity_message(data, first_name_user, user_id)
        
        # Keyboard Setup
        kb = types.InlineKeyboardMarkup(row_width=2)
        
        # Mail Buttons (Only if token exists)
        if token:
            kb.add(types.InlineKeyboardButton("📩 Check Inbox", callback_data="refresh_mail"))
            kb.add(types.InlineKeyboardButton("🔄 Switch Account", callback_data="m_mail_list"))
        
        # Save Button (Always Available)
        kb.add(types.InlineKeyboardButton("💾 Simpan ke Catatan", callback_data="save_fake_id"))
            
        await message.reply(OUTPUT, reply_markup=kb, disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Error generating fake ID: {e}")
        await message.reply(f"⚠️ <b>Error:</b> {e}\nTry another country code.")

@dp.callback_query_handler(lambda c: c.data == 'save_fake_id')
async def save_fake_id_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = LAST_GEN_ID.get(user_id)
    
    if not data:
        return await callback_query.answer("⚠️ Data kadaluarsa/hilang. Silakan generate ulang.", show_alert=True)
    
    # Create Title: "ID [CODE] - Name"
    title = f"ID {data['country_code'].upper()}: {data['name']}"
    
    # Create Clean Content (Plain Text for Note)
    content = (
        f"Name: {data['name']}\n"
        f"Gender: {data['gender']}\n"
        f"DOB: {data['dob']} ({data['age']} yo)\n"
        f"Job: {data['job']}\n"
        f"ID/SSN: {data['ssn']}\n"
        f"Address: {data['address']}, {data['city']}\n"
        f"Phone: {data['phone']}\n\n"
        f"Email: {data['email']}\n"
        f"Pass: {data['password']}"
    )
    
    # Save to DB
    if db.db_save_note(user_id, title, content):
        await callback_query.answer("✅ Identitas berhasil disimpan ke Catatan!", show_alert=True)
    else:
        # If duplicate title or other error
        # Try appending random digit if duplicate
        title_alt = f"{title} ({random.randint(1,99)})"
        if db.db_save_note(user_id, title_alt, content):
             await callback_query.answer("✅ Tersimpan! (Judul disesuaikan)", show_alert=True)
        else:
             await callback_query.answer("⚠️ Gagal menyimpan. Cek kuota catatan Anda.", show_alert=True)



@dp.callback_query_handler(lambda c: c.data and c.data.startswith('iban_gen_'))
async def process_iban_gen(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    country_code = callback_query.data.split('_')[2]
    
    # Loading animation
    try:
        await bot.edit_message_text(
            "⏳ <i>Sedang mengambil data IBAN...</i>",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            parse_mode=types.ParseMode.HTML
        )
    except: pass
    
    # Run in executor to avoid blocking
    iban_res = await loop.run_in_executor(None, iban.get_fake_iban, country_code)
    country_name = iban.get_country_name(country_code)
    
    res_text = (
        f"<b>🏦 FAKE IBAN RESULT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Country:</b> {country_name}\n"
        f"<b>IBAN:</b> <code>{iban_res}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Data generated from fakeiban.org / Faker</i>"
    )
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Generate Lagi", callback_data=f"iban_gen_{country_code}"))
    kb.add(types.InlineKeyboardButton("🔙 Menu Negara", callback_data="m_iban"))
    
    await bot.edit_message_text(
        res_text,
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=kb,
        parse_mode=types.ParseMode.HTML
    )

@dp.message_handler(commands=['iban'], commands_prefix=PREFIX)
async def cmd_iban(message: types.Message):
    args = message.get_args()
    if not args:
        return await message.reply(f"⚠️ Format: <code>{PREFIX}iban [kode_negara]</code>\nContoh: <code>{PREFIX}iban de</code>")
        
    country_code = args.split()[0].lower()
    if country_code not in iban.FAKEIBAN_COUNTRIES:
         return await message.reply("⚠️ Kode negara tidak didukung atau tidak valid.")
         
    msg = await message.reply("⏳ <i>Generating...</i>")
    
    # Run in executor
    iban_res = await loop.run_in_executor(None, iban.get_fake_iban, country_code)
    country_name = iban.get_country_name(country_code)
    
    res_text = (
        f"<b>🏦 FAKE IBAN RESULT</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Country:</b> {country_name}\n"
        f"<b>IBAN:</b> <code>{iban_res}</code>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Generate Lagi", callback_data=f"iban_gen_{country_code}"))
    
    await msg.edit_text(res_text, reply_markup=kb, parse_mode=types.ParseMode.HTML)


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Mulai Bot"),
        types.BotCommand("help", "Bantuan & Menu"),
        types.BotCommand("chk", "Cek Kartu Kredit"),
        types.BotCommand("gen", "Generator VCC"),
        types.BotCommand("fake", "Fake Identity"),
        types.BotCommand("iban", "Fake IBAN"), 
        types.BotCommand("mail", "Temp Mail"),
        types.BotCommand("note", "Catatan Aman"), # NEW
        types.BotCommand("emails", "Kelola Email"),
        types.BotCommand("login", "Login Temp Mail"),
        types.BotCommand("bin", "Informasi BIN"),
        types.BotCommand("rnd", "Random BIN"),
        types.BotCommand("info", "Info Pengguna/Bot"),
    ])


async def auto_check_mail():
    """Background task to check for new emails for all active users."""
    while True:
        try:
            # Iterate active sessions from DB
            sessions = db.db_get_all_mail_sessions()
            for data in sessions:
                user_id = data['user_id']
                token = data.get('token')
                last_id = data.get('last_msg_id')
                
                msgs = await get_mail_messages(token)
                if msgs and len(msgs) > 0:
                    newest_msg = msgs[0] # First item is newest
                    newest_id = newest_msg.get('id')
                    
                    if newest_id != last_id:
                        # New message found!
                        # Update last_id immediately to avoid spam
                        db.db_update_mail_last_id(user_id, newest_id)
                        
                        sender = newest_msg.get('from', {}).get('address', 'Unknown')
                        subject = newest_msg.get('subject', 'No Subject')
                        
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("📖 Baca Pesan", callback_data=f"read_{newest_id}"))
                        
                        try:
                            await bot.send_message(
                                user_id,
                                f"<b>🔔 EMAIL BARU MASUK!</b>\n"
                                f"━━━━━━━━━━━━━━━━━━\n"
                                f"<b>Dari:</b> {sender}\n"
                                f"<b>Subjek:</b> {subject}",
                                reply_markup=kb
                            )
                        except Exception as e:
                            # User might have blocked bot
                            if "bot was blocked" in str(e):
                                db.db_delete_mail_session(user_id)
                                
        except Exception as e:
            logging.error(f"Auto check mail error: {e}")
            
        await asyncio.sleep(15) # Check every 15 seconds

async def on_startup(dp):
    # Try to set commands with retry logic
    for i in range(10):
        try:
            await set_default_commands(dp)
            logging.info("Default commands set successfully.")
            break
        except Exception as e:
            logging.error(f"Network error on startup (Attempt {i+1}/10): {e}")
            await asyncio.sleep(5)
    
    # Start background tasks
    asyncio.create_task(auto_check_mail())
    asyncio.create_task(refresh_security_cache())

if __name__ == '__main__':
    initialize_bot_info()
    executor.start_polling(dp, skip_updates=True, loop=loop, on_startup=on_startup)
