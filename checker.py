from datetime import datetime
import re
import requests
import json
import base64
import random

# --- COUNTRY TO CURRENCY MAPPING ---
COUNTRY_CURRENCY = {
    "US": "USD ($)", "GB": "GBP (£)", "JP": "JPY (¥)", "CN": "CNY (¥)",
    "EU": "EUR (€)", "DE": "EUR (€)", "FR": "EUR (€)", "ES": "EUR (€)", "IT": "EUR (€)",
    "NL": "EUR (€)", "BE": "EUR (€)", "IE": "EUR (€)",
    "ID": "IDR (Rp)", "SG": "SGD (S$)", "MY": "MYR (RM)", "TH": "THB (฿)", "VN": "VND (₫)",
    "PH": "PHP (₱)", "IN": "INR (₹)", "KR": "KRW (₩)", "RU": "RUB (₽)", "TR": "TRY (₽)",
    "BR": "BRL (R$)", "MX": "BRL (R$)", "CA": "CAD (C$)", "AU": "AUD (A$)", "NZ": "NZD (NZ$)",
    "DK": "DKK (kr)", "SE": "SEK (kr)", "NO": "NOK (kr)",
    "ZA": "ZAR (R)", "AE": "AED (د.إ)", "SA": "SAR (د.إ)"
}

# --- MINI LOCAL BIN DATABASE (OFFLINE) ---
# Supports 6 to 8 digit prefixes.
# Format: "PREFIX": {"c": "FLAG COUNTRY_CODE", "b": "BANK NAME", "t": "TYPE", "l": "LEVEL"}
LOCAL_BIN_DB = {
    # VISA
    "415464": {"c": "🇺🇸 US", "b": "JPMORGAN CHASE BANK", "t": "CREDIT", "l": "CLASSIC"},
    "400022": {"c": "🇺🇸 US", "b": "BILL ME LATER", "t": "CREDIT", "l": "UNKNOWN"},
    "451234": {"c": "🇺🇸 US", "b": "WELLS FARGO", "t": "DEBIT", "l": "CLASSIC"},
    "424242": {"c": "🇺🇸 US", "b": "STRIPE TEST CARD", "t": "CREDIT", "l": "TEST"},
    
    # MASTERCARD
    "510510": {"c": "🇺🇸 US", "b": "MASTERCARD", "t": "CREDIT", "l": "WORLD"},
    "545454": {"c": "🇺🇸 US", "b": "CITIBANK", "t": "CREDIT", "l": "PLATINUM"},
    
    # AMEX
    "378282": {"c": "🇺🇸 US", "b": "AMEX", "t": "CREDIT", "l": "PLATINUM"},
    
    # INDONESIA (GPN/LOCAL) with 8-DIGIT Examples
    "603298": {"c": "🇮🇩 ID", "b": "BANK MANDIRI (GPN)", "t": "DEBIT", "l": "GPN"},
    "461700": {"c": "🇮🇩 ID", "b": "BCA", "t": "DEBIT", "l": "GOLD"},
    "518446": {"c": "🇮🇩 ID", "b": "BCA", "t": "CREDIT", "l": "MASTERCARD"},
    "409360": {"c": "🇮🇩 ID", "b": "JENIUS (BTPN)", "t": "DEBIT", "l": "VISA"},
    "461699": {"c": "🇮🇩 ID", "b": "BANK MANDIRI", "t": "DEBIT", "l": "VISA"},
    "46169930": {"c": "🇮🇩 ID", "b": "BANK MANDIRI (Prioritas)", "t": "DEBIT", "l": "PLATINUM"}, # 8 Digit Example
    
    # OTHER REGIONS
    "501900": {"c": "🇩🇰 DK", "b": "DANSKE BANK", "t": "DEBIT", "l": "DANKORT"},
    "670300": {"c": "🇧🇪 BE", "b": "FORTIS", "t": "DEBIT", "l": "BANCONTACT"},
}

def is_card_valid(card_number: str) -> bool:
    """Validate a card number using the Luhn algorithm."""
    digits = card_number.strip()
    if not (digits.isdigit() and len(digits) >= 12):
        return False

    checksum = 0
    parity = len(digits) % 2
    for idx, char in enumerate(digits):
        num = int(char)
        if idx % 2 == parity:
            num *= 2
            if num > 9:
                num -= 9
        checksum += num

    return checksum % 10 == 0

def get_card_network(ccn):
    """
    Mendeteksi jaringan kartu (Network) dan validasi panjang digitnya.
    Prioritas: Lokal/Spesifik -> Global.
    Returns: (NetworkName, IsLengthValid)
    """
    # Regex Patterns for Major Networks
    # Urutan sangat berpengaruh! Cek yang paling spesifik dulu.
    networks = {
        # --- LOCAL / SPECIFIC NETWORKS ---
        'GPN': r'^(603298)[0-9]{10}$', # Indonesia GPN (Specific Prefix)
        'MIR': r'^220[0-4][0-9]{12}$', # Russia Mir (Standard)
        'DANKORT': r'^5019[0-9]{12}$', # Dankort Pure (Rare). Visa/Dankort starts with 4571 treated as Visa.
        'BANCONTACT': r'^6703[0-9]{12,15}$', # Belgium
        'INTERAC': r'^27[0-9]{14}$', # Pure Interac (Rare online)
        'EFTPOS': r'^606067[0-9]{10}$', # Example AU Range (often co-badged)
        'RUPAY': r'^(60|6521|6522)[0-9]{14}$', # India (Specific 60/65 ranges)
        
        # --- AMEX / DINERS / JCB ---
        'AMEX': r'^3[47][0-9]{13}$', # 15 digits
        'JCB': r'^(?:2131|1800|35\d{3})\d{11}$', # 15 or 16 digits
        'DINERS': r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$', # 14 digits
        
        # --- UNIONPAY (Bisa tumpang tindih dengan Discover di prefix 6) ---
        'UNIONPAY': r'^62[0-9]{14,17}$', # 16-19 digits (Standard 62)
        
        # --- GLOBAL NETWORKS (Broadest Ranges) ---
        'VISA': r'^4[0-9]{12}(?:[0-9]{3})?$', # 13 or 16 digits
        'MASTERCARD': r'^(5[1-5][0-9]{4}|222[1-9][0-9]{2}|22[3-9][0-9]{3}|2[3-6][0-9]{4}|27[01][0-9]{3}|2720[0-9]{2})[0-9]{10}$', # 16 digits (Series 5 & 2)
        'MAESTRO': r'^(5018|5020|5038|6304|6759|6761|6763)[0-9]{8,15}$', # 12-19 digits
        'DISCOVER': r'^6(?:011|5[0-9]{2})[0-9]{12}$', # 16 digits
    }
    
    for name, pattern in networks.items():
        if re.match(pattern, ccn):
            return name, True
            
    # Fallback / Prefix Check
    if ccn.startswith('4'): return 'VISA', False
    if ccn.startswith(('51','52','53','54','55','22','23','24','25','26','27')): return 'MASTERCARD', False
    if ccn.startswith('62'): return 'UNIONPAY', False
    if ccn.startswith('603298'): return 'GPN', False
    if ccn.startswith('220'): return 'MIR', False
    if ccn.startswith(('50','56','57','58','63','67')): return 'MAESTRO', False
    if ccn.startswith(('34','37')): return 'AMEX', False
    if ccn.startswith('35'): return 'JCB', False
    if ccn.startswith('60'): return 'RUPAY', False 
    
    return 'UNKNOWN', True

def get_mii_description(ccn):
    """Mendapatkan deskripsi Major Industry Identifier (Digit Pertama)."""
    first_digit = int(ccn[0])
    mii_map = {
        1: "Airlines",
        2: "Airlines/Future",
        3: "Travel & Entertainment (Amex/Diners)",
        4: "Banking/Financial (Visa)",
        5: "Banking/Financial (MasterCard)",
        6: "Merchandising/Banking (Discover/UnionPay)",
        7: "Petroleum",
        8: "Healthcare/Telecom",
        9: "National Assignment"
    }
    return mii_map.get(first_digit, "Unknown Industry")

# --- COUNTRY TIMEZONES (UTC OFFSET HOURS) ---
# Simplified offsets. For huge countries like US/RU, we take a major city (e.g., NY, Moscow).
COUNTRY_OFFSET = {
    "US": -5, "GB": 0, "JP": 9, "CN": 8, "ID": 7, "SG": 8, "MY": 8, "TH": 7,
    "VN": 7, "PH": 8, "IN": 5.5, "KR": 9, "RU": 3, "TR": 3, "DE": 1, "FR": 1,
    "ES": 1, "IT": 1, "NL": 1, "BR": -3, "CA": -5, "AU": 11, "NZ": 13, "ZA": 2,
    "AE": 4, "SA": 3, "DK": 1, "SE": 1, "NO": 1, "MX": -6
}

def get_country_time_info(country_code):
    """
    Menghitung waktu lokal dan status aktivitas target.
    """
    offset = COUNTRY_OFFSET.get(country_code, 0) # Default UTC
    
    # Calculate current UTC time
    utc_now = datetime.utcnow()
    
    # Apply offset manually (hours)
    # Note: This is simple arithmetic, ignores DST but robust enough for estimation.
    hours_add = int(offset)
    minutes_add = int((offset % 1) * 60)
    
    # Create simple time struct
    # We use timestamps to handle day rollover easily
    import time
    ts = utc_now.timestamp()
    local_ts = ts + (hours_add * 3600) + (minutes_add * 60)
    local_dt = datetime.fromtimestamp(local_ts)
    
    time_str = local_dt.strftime("%H:%M")
    hour = local_dt.hour
    
    # Determine Activity
    if 7 <= hour <= 22:
        status = "🟢 Active (Bank Open)"
    else:
        status = "🔴 Sleeping (Low Risk)"
        
    return f"🕒 Local: {time_str} | {status}"

def get_bin_info_range(ccn, network):
    """
    Mencari informasi BIN dari database lokal dengan dukungan range (8 digit -> 6 digit).
    Returns: (Formatted Info String, Found Boolean)
    """
    
    def estimate_tier(level_str):
        lvl = level_str.upper()
        if any(x in lvl for x in ['INFINITE', 'SIGNATURE', 'PLATINUM', 'WORLD ELITE', 'BLACK', 'CENTURION', 'PRIORITAS']):
            return "💎 HIGH TIER"
        elif any(x in lvl for x in ['GOLD', 'TITANIUM', 'WORLD', 'BUSINESS', 'CORPORATE']):
            return "🥇 MID TIER"
        elif any(x in lvl for x in ['CLASSIC', 'STANDARD', 'ELECTRON', 'GPN', 'PREPAID', 'VIRTUAL']):
            return "🥈 LOW TIER"
        return "❓ UNKNOWN TIER"

    # 1. Coba 8 Digit (Lebih Spesifik)
    prefix_8 = ccn[:8]
    if prefix_8 in LOCAL_BIN_DB:
        d = LOCAL_BIN_DB[prefix_8]
        country_code = d['c'].split()[-1] 
        currency = COUNTRY_CURRENCY.get(country_code, "Unknown")
        tier = estimate_tier(d['l'])
        time_info = get_country_time_info(country_code)
        return f"{d['c']} {d['b']} - {d['t']} {d['l']} [{currency}]\n✨ Level: {tier}\n{time_info}", True
        
    # 2. Coba 6 Digit (Standar)
    prefix_6 = ccn[:6]
    if prefix_6 in LOCAL_BIN_DB:
        d = LOCAL_BIN_DB[prefix_6]
        country_code = d['c'].split()[-1]
        currency = COUNTRY_CURRENCY.get(country_code, "Unknown")
        tier = estimate_tier(d['l'])
        time_info = get_country_time_info(country_code)
        return f"{d['c']} {d['b']} - {d['t']} {d['l']} [{currency}]\n✨ Level: {tier}\n{time_info}", True
        
    # 3. Fallback MII
    mii_info = get_mii_description(ccn)
    return f"🏳️ {network} - {mii_info} (Luhn)", False

def offline_chk_gate(ccn, mm, yy, cvv):
    """
    Validasi Kartu Lokal (Offline Validator).
    Menggantikan API eksternal.
    """
    
    # --- 0. AUTO FIX & SANITIZATION ---
    ccn = re.sub(r'[^0-9]', '', str(ccn))
    mm = re.sub(r'[^0-9]', '', str(mm))
    yy = re.sub(r'[^0-9]', '', str(yy))
    cvv = re.sub(r'[^0-9]', '', str(cvv))

    if len(mm) == 1: mm = "0" + mm
    if len(yy) == 4: yy = yy[-2:] 
        
    # 1. Validasi Luhn (Algoritma Dasar)
    if not is_card_valid(ccn):
        return {"status": "die", "msg": "❌ Invalid Luhn (Checksum Failed)", "bin_info": "Unknown", "code": 0}

    # 2. Validasi Network & Panjang Digit
    network, length_valid = get_card_network(ccn)
    if not length_valid:
        return {"status": "die", "msg": f"❌ Invalid Length for {network}", "bin_info": network, "code": 0}

    # 3. Validasi CVV Ketat
    if cvv and cvv.isdigit():
        req_cvv = 4 if network == 'AMEX' else 3
        if len(cvv) != req_cvv:
             return {"status": "die", "msg": f"❌ Invalid CVV Length (Must be {req_cvv})", "bin_info": network, "code": 0}

    # 4. Validasi Tanggal (Expiry)
    try:
        exp_m = int(mm)
        if len(yy) == 2:
            exp_y = int("20" + yy)
        else:
            exp_y = int(yy)
            
        now = datetime.now()
        current_y = now.year
        current_m = now.month
        
        if exp_y < current_y or (exp_y == current_y and exp_m < current_m):
             return {"status": "die", "msg": "❌ Expired Card", "bin_info": network, "code": 0}
        
        if not (1 <= exp_m <= 12):
             return {"status": "die", "msg": "❌ Invalid Month", "bin_info": network, "code": 0}
             
    except ValueError:
        return {"status": "die", "msg": "❌ Format Error", "bin_info": "Unknown", "code": 0}

    # 5. Info Tambahan (Range Detection + Currency)
    bin_info, _ = get_bin_info_range(ccn, network)

    # --- HASIL AKHIR ---
    return {
        "status": "live", 
        "msg": "✅ Valid Structure (Luhn Passed)",
        "bin_info": bin_info,
        "code": 1
    }

def get_random_bin_by_country(country_code):
    """Mengambil BIN acak berdasarkan kode negara (ID, US, dll)."""
    candidates = []
    target = country_code.upper()
    
    for bin_code, data in LOCAL_BIN_DB.items():
        # Data 'c' formatnya "🇺🇸 US" -> kita ambil 2 huruf terakhir
        code = data['c'].split()[-1]
        if code == target:
            candidates.append(bin_code)
            
    if candidates:
        return random.choice(candidates)
    return None

def clean_html_msg(raw_html):
    """Membersihkan tag HTML dari respons API."""
    if not raw_html: return "No message"
    # Hapus tag HTML
    clean = re.sub(r'<[^>]+>', '', raw_html)
    return clean.strip()

def local_chk_gate(ccn, mm, yy, cvv):
    """
    Main Checker Gate: Hybrid (Offline Filter -> Online Check).
    Nama fungsi 'local_chk_gate' dipertahankan agar kompatibel dengan bot.py.
    """
    # 1. Validasi Dasar (Offline) dulu untuk hemat API call
    # Kita gunakan offline_chk_gate untuk cek format, luhn, dan expiry.
    # Jika gagal di sini, langsung return status 'die' tanpa panggil API.
    offline_res = offline_chk_gate(ccn, mm, yy, cvv)
    
    if offline_res['status'] != 'live':
        # Tambahkan note bahwa ini hasil filter lokal
        offline_res['msg'] += " (Local Filter)"
        return offline_res

    # 2. Jika lolos filter offline, lanjut ke Online Check (mock.payate.com)
    api_url = "https://mock.payate.com/api.php"
    card_data = f"{ccn}|{mm}|{yy}|{cvv}"
    
    try:
        # Kirim request POST
        payload = {'data': card_data}
        # Gunakan requests library, set timeout pendek agar bot tidak hang
        r = requests.post(api_url, data=payload, timeout=15)
        
        if r.status_code == 200:
            try:
                json_data = r.json()
                raw_msg = json_data.get('msg', '')
                clean_msg = clean_html_msg(raw_msg)
                
                # Parsing Status dari teks pesan
                # API Payate biasanya return: "Status | CCN | ..."
                # Kita cari keyword kunci
                
                status = "unknown"
                code = 3 # Unknown
                
                lower_msg = clean_msg.lower()
                
                # Logika Status
                if any(x in lower_msg for x in ["live", "approved", "charged", "success", "cvv matched"]):
                    status = "live"
                    code = 1
                    # Perbaiki ikon jika perlu
                    clean_msg = "✅ " + clean_msg
                elif any(x in lower_msg for x in ["die", "declined", "insufficient", "do not honor", "error", "expired"]):
                    status = "die"
                    code = 2
                    clean_msg = "❌ " + clean_msg
                elif "unknown" in lower_msg:
                    status = "unknown"
                    code = 3
                    clean_msg = "⚠️ " + clean_msg
                
                # Ambil bin info dari offline checker (lebih lengkap/rapi)
                # karena API payate infonya kadang cuma 'Unknown' atau minim.
                bin_info = offline_res['bin_info']
                
                return {
                    "status": status,
                    "msg": clean_msg,
                    "bin_info": bin_info,
                    "code": code
                }
                
            except json.JSONDecodeError:
                 return {
                    "status": "unknown", 
                    "msg": "⚠️ API Error: Invalid JSON response", 
                    "bin_info": offline_res['bin_info'], 
                    "code": 0
                 }
        else:
            return {
                "status": "unknown", 
                "msg": f"⚠️ API Error: Status {r.status_code}", 
                "bin_info": offline_res['bin_info'], 
                "code": 0
            }
            
    except requests.exceptions.RequestException as e:
        # Jika koneksi error/timeout, fallback ke status 'unknown' tapi info valid (karena luhn pass)
        return {
            "status": "unknown",
            "msg": f"⚠️ Connection Error: {str(e)}",
            "bin_info": offline_res['bin_info'],
            "code": 0
        }
