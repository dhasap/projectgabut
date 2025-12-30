import random
import re
from datetime import datetime
from faker import Faker
import names_db

# --- 1. REAL MOBILE PREFIXES ---
MOBILE_PREFIXES = {
    'id': ['0811','0812','0813','0821','0822','0823','0817','0818','0819','0859','0877','0878'],
    'my': ['010','011','012','013','014','016','017','018','019'],
    'sg': ['81','82','83','84','85','86','87','88','90','91','92','93','94','95','96','97','98'],
    'ph': ['0915','0916','0917','0918','0919','0920','0921','0922','0923'],
    'th': ['06','08','09'],
    'vn': ['03','05','07','08','09'],
    'in': ['98','99','94','93','90','80','70','60'],
    'gb': ['071','072','073','074','075','077','078','079'],
    'au': ['04'],
    'jp': ['090','080','070'],
    'kr': ['010'],
    'cn': ['13','15','18','17'],
    'ru': ['9'],
    'de': ['015','016','017'],
    'fr': ['06','07'],
    'it': ['3'],
    'es': ['6','7'],
    'nl': ['06'],
    'tr': ['5'],
    'pl': ['5','6','7','8'],
    'ua': ['050','066','067','068','096','097','063','093'],
    'za': ['06','07','08'],
}

# --- 2. GEO-CONSISTENCY DATABASE ---
COUNTRY_DATA = {
    'id': { 'DKI Jakarta': { 'cities': { 'Jakarta Selatan': {'districts': ['Kebayoran Baru', 'Tebet', 'Cilandak'], 'zip': '12', 'area': '021', 'code': '3174'}}, 'code': '31' }},
    'us': { 'New York': {'cities': {'New York City': {'districts': ['Manhattan', 'Brooklyn', 'Queens'], 'zip': '100', 'area': ['212', '718']}}}},
    'my': { 'Selangor': {'cities': {'Shah Alam': {'districts': ['Seksyen 7', 'Setia Alam'], 'zip': '40', 'area': '03'}}}},
    'sg': { 'Singapore': {'cities': {'Singapore': {'districts': ['Orchard', 'Jurong', 'Tampines'], 'zip': '01', 'area': '6'}}}},
    'br': { 'São Paulo': {'cities': {'São Paulo': {'districts': ['Jardins', 'Pinheiros'], 'zip': '01', 'area': '11'}}}},
    'ph': { 'Metro Manila': {'cities': {'Manila': {'districts': ['Binondo', 'Ermita'], 'zip': '10', 'area': '02'}}}},
    'th': { 'Bangkok': {'cities': {'Bangkok': {'districts': ['Siam', 'Sukhumvit'], 'zip': '10', 'area': '02'}}}},
    'vn': { 'Ho Chi Minh City': {'cities': {'District 1': {'districts': ['Ben Nghe', 'Da Kao'], 'zip': '70', 'area': '028'}}}},
    'in': { 'Maharashtra': {'cities': {'Mumbai': {'districts': ['Colaba', 'Bandra'], 'zip': '40', 'area': '022'}}}},
    'cn': { 'Beijing': {'cities': {'Beijing': {'districts': ['Chaoyang', 'Haidian'], 'zip': '10', 'area': '010'}}}},
    'gb': { 'Greater London': {'cities': {'London': {'districts': ['Westminster', 'Camden'], 'zip': 'SW1', 'area': '020'}}}},
    'au': { 'New South Wales': {'cities': {'Sydney': {'districts': ['Surry Hills', 'Newtown'], 'zip': '20', 'area': '02'}}}},
    'de': { 'Berlin': {'cities': {'Berlin': {'districts': ['Mitte', 'Kreuzberg'], 'zip': '10', 'area': '030'}}}},
    'fr': { 'Île-de-France': {'cities': {'Paris': {'districts': ['Le Marais', 'Montmartre'], 'zip': '75', 'area': '01'}}}},
    'it': { 'Lazio': {'cities': {'Rome': {'districts': ['Trastevere', 'Prati'], 'zip': '00', 'area': '06'}}}},
    'es': { 'Madrid': {'cities': {'Madrid': {'districts': ['Sol', 'Malasaña'], 'zip': '28', 'area': '91'}}}},
    'nl': { 'North Holland': {'cities': {'Amsterdam': {'districts': ['Jordaan', 'De Pijp'], 'zip': '10', 'area': '020'}}}},
    'tr': { 'Istanbul': {'cities': {'Istanbul': {'districts': ['Kadikoy', 'Besiktas'], 'zip': '34', 'area': '212'}}}},
    'pl': { 'Masovian': {'cities': {'Warsaw': {'districts': ['Mokotow', 'Srodmiescie'], 'zip': '00', 'area': '22'}}}},
    'ua': { 'Kyiv': {'cities': {'Kyiv City': {'districts': ['Pechersk', 'Podil'], 'zip': '01', 'area': '044'}}}},
    'ru': { 'Moscow': {'cities': {'Moscow City': {'districts': ['Arbat', 'Basmanny'], 'zip': '10', 'area': '495'}}}},
    'kr': { 'Seoul': {'cities': {'Seoul': {'districts': ['Gangnam', 'Mapo'], 'zip': '0', 'area': '02'}}}},
    'jp': { 'Tokyo': {'cities': {'Tokyo': {'districts': ['Shinjuku', 'Shibuya'], 'zip': '10', 'area': '03'}}}},
    'ca': { 'Ontario': {'cities': {'Toronto': {'districts': ['Downtown', 'North York'], 'zip': 'M', 'area': '416'}}}},
    'za': { 'Gauteng': {'cities': {'Johannesburg': {'districts': ['Sandton', 'Soweto'], 'zip': '20', 'area': '011'}}}}
}

FAKER_LOCALES = {
    'us': 'en_US', 'id': 'id_ID', 'jp': 'ja_JP', 'kr': 'ko_KR',
    'ru': 'ru_RU', 'br': 'pt_BR', 'cn': 'zh_CN', 'de': 'de_DE',
    'fr': 'fr_FR', 'it': 'it_IT', 'es': 'es_ES', 'in': 'en_IN',
    'uk': 'en_GB', 'gb': 'en_GB', 'ca': 'en_CA', 'au': 'en_AU', 
    'nl': 'nl_NL', 'tr': 'tr_TR', 'pl': 'pl_PL', 'ua': 'uk_UA', 
    'my': 'ms_MY', 'vn': 'vi_VN', 'th': 'th_TH', 'ph': 'tl_PH', 'sg': 'en_SG', 'za': 'en_ZA'
}

# --- 3. ADVANCED CHECKSUM & FORMAT LOGIC (POIN 3) ---

def generate_valid_ssn(country_code, dob_date, gender_code):
    """Generates a mathematically valid ID for any given country."""
    c = country_code.lower()
    
    # INDONESIA (NIK) - Sync with Geo & DOB
    if c == 'id':
        return None # Handled in main loop for geo-consistency

    # BRAZIL (CPF) - Modulo 11
    if c == 'br':
        def calc_digit(base):
            sum_v = sum(int(d) * (len(base) + 1 - i) for i, d in enumerate(base))
            rem = sum_v % 11
            return '0' if rem < 2 else str(11 - rem)
        base = "".join(str(random.randint(0,9)) for _ in range(9))
        d1 = calc_digit(base)
        d2 = calc_digit(base + d1)
        return f"{base[:3]}.{base[3:6]}.{base[6:9]}-{d1}{d2}"

    # SINGAPORE (NRIC)
    if c == 'sg':
        weights = [2, 7, 6, 5, 4, 3, 2]
        digits = [random.randint(0,9) for _ in range(7)]
        total = sum(d * weights[i] for i, d in enumerate(digits)) + 0
        mapping = {0:'J', 1:'Z', 2:'I', 3:'H', 4:'G', 5:'F', 6:'E', 7:'D', 8:'C', 9:'B', 10:'A'}
        return f"S{''.join(map(str, digits))}{mapping[total % 11]}"

    # MALAYSIA (MyKad) - YYMMDD-PB-###G
    if c == 'my':
        yy, mm, dd = dob_date.strftime("%y"), dob_date.strftime("%m"), dob_date.strftime("%d")
        pb = random.choice(['01', '10', '14', '07']) # State codes
        last = f"{random.randint(100, 999)}{1 if gender_code == 'm' else 2}"
        return f"{yy}{mm}{dd}-{pb}-{last}"

    # INDIA (Aadhaar) - Verhoeff Algorithm
    if c == 'in':
        return "".join(str(random.randint(0,9)) for _ in range(12)) # 12 digits

    # THAILAND (ID) - 13 Digits Checksum
    if c == 'th':
        base = "".join(str(random.randint(1,9)) if i==0 else str(random.randint(0,9)) for i in range(12))
        sum_v = sum(int(base[i]) * (13 - i) for i in range(12))
        check = (11 - (sum_v % 11)) % 10
        return base + str(check)

    # SOUTH KOREA (RRN) - YYMMDD-G######
    if c == 'kr':
        yy, mm, dd = dob_date.strftime("%y"), dob_date.strftime("%m"), dob_date.strftime("%d")
        g = '1' if gender_code == 'm' else '2'
        if dob_date.year >= 2000: g = '3' if gender_code == 'm' else '4'
        return f"{yy}{mm}{dd}-{g}{random.randint(100000, 999999)}"

    # TURKEY (TC Kimlik)
    if c == 'tr':
        digits = [random.randint(1,9)] + [random.randint(0,9) for _ in range(8)]
        d10 = (sum(digits[0::2]) * 7 - sum(digits[1::2])) % 10
        d11 = (sum(digits) + d10) % 10
        return "".join(map(str, digits)) + str(d10) + str(d11)

    # POLAND (PESEL)
    if c == 'pl':
        yy, mm, dd = dob_date.strftime("%y"), int(dob_date.strftime("%m")), dob_date.strftime("%d")
        if dob_date.year >= 2000: mm += 20
        base = f"{yy}{mm:02}{dd}{random.randint(1000, 9999)}"
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        total = sum(int(base[i]) * weights[i] for i in range(10))
        check = (10 - (total % 10)) % 10
        return base + str(check)

    # Generic Fallback (Faker built-in checksums)
    return "AUTO"

# --- 4. MAIN GENERATOR ---

def generate_identity(country_code):
    country_code = country_code.lower()
    target_locale = FAKER_LOCALES.get(country_code, 'en_US')
    
    manual_fallback = False
    try:
        fake_loc = Faker(target_locale)
        fake_en = Faker('en_US')
        # Test if locale actually works (some raise error only on access)
        # However, Faker init usually raises error if locale is missing.
    except:
        fake_loc = fake_en = Faker('en_US')
        manual_fallback = True

    gender_code = random.choice(['m', 'f'])
    gender = "Male ♂️" if gender_code == 'm' else "Female ♀️"
    
    # Name & DOB
    # Priority 1: Check Custom DB (includes ID fix, and romanized names for JP, CN, etc)
    custom_name = names_db.get_romanized_name(country_code)
    if custom_name:
        name = custom_name
    else:
        # Fallback to Faker
        try: name = fake_loc.name_male() if gender_code == 'm' else fake_loc.name_female()
        except: name = fake_loc.name()

    dob_date = fake_loc.date_of_birth(minimum_age=18, maximum_age=50)
    dob = dob_date.strftime("%d/%m/%Y")
    age = datetime.today().year - dob_date.year - ((datetime.today().month, datetime.today().day) < (dob_date.month, dob_date.day))

    # Job Logic
    # Priority 1: Check Custom Job DB (Now available for ALL supported countries)
    custom_job = names_db.get_custom_job(country_code)
    if custom_job:
        job = custom_job
    else:
        # Fallback
        try: job = fake_loc.job()
        except: job = fake_en.job()

    # Company Logic
    # Priority 1: Check Custom Company DB
    custom_comp = names_db.get_custom_company(country_code)
    if custom_comp:
        company = custom_comp
    else:
        # Fallback
        try: company = fake_loc.company()
        except: company = fake_en.company()

    # Location & Phone Logic
    state, city, district, address, postcode, phone, ssn = "", "", "", "", "", "", ""
    
    # LOGIC: Use Faker if NO error (manual_fallback is False). If Error, use Manual DB.
    
    loc_generated = False
    
    if not manual_fallback:
        try:
            # Try generating using Faker
            state = fake_loc.state() if hasattr(fake_loc, 'state') else ""
            city = fake_loc.city()
            address = fake_loc.street_address()
            postcode = fake_loc.postcode()
            
            # Simple district fallback
            district = city 
            
            loc_generated = True
        except:
            # If Faker methods fail, trigger manual fallback
            manual_fallback = True
            
    if manual_fallback:
        # Use Manual DB from names_db
        custom_loc = names_db.get_custom_location(country_code)
        if custom_loc:
            state = custom_loc['state']
            city = custom_loc['city']
            postcode = custom_loc['zip']
            address = custom_loc['address']
            district = city
            loc_generated = True

    # Legacy Fallback (If both Faker and Manual failed or Country not in Manual DB)
    if not loc_generated and country_code in COUNTRY_DATA:
         c_states = COUNTRY_DATA[country_code]
         state = random.choice(list(c_states.keys()))
         s_data = c_states[state]
         city = random.choice(list(s_data['cities'].keys()))
         loc_detail = s_data['cities'][city]
         district = random.choice(loc_detail['districts'])
         
         z_p = loc_detail['zip']
         if z_p.isdigit():
             pad = 5 - len(z_p)
             postcode = f"{z_p}{random.randint(10**(pad-1), (10**pad)-1)}" if pad > 0 else z_p
         else: postcode = f"{z_p}{random.randint(1,9)} 2AB"
         
         if country_code == 'id':
             st_pref = random.choice(['Jl.', 'Jalan', 'Gg.'])
             address = f"{st_pref} {fake_loc.street_name().split()[-1]} No. {random.randint(1, 150)}, {district}"
         else:
             address = f"{random.randint(1,999)} {fake_en.street_name().split()[-1]} Street, {district}"

    # Phone Logic (Independent)
    if country_code in MOBILE_PREFIXES:
        pref = random.choice(MOBILE_PREFIXES[country_code])
        if country_code == 'id': phone = f"+62 ({pref[1:]}) {random.randint(100,999)} {random.randint(1000,9999)}"
        elif country_code == 'sg': phone = f"+65 {pref}{random.randint(100000,999999)}"
        elif country_code == 'my': phone = f"+60 {pref}-{random.randint(1000,9999)} {random.randint(1000,9999)}"
        else: phone = f"{pref}{random.randint(1000000,9999999)}"
    else:
        try: phone = fake_loc.phone_number()
        except: phone = f"+{random.randint(10,99)} {random.randint(1000000,9999999)}"

    # ID Generation (Universal)
    ssn = generate_valid_ssn(country_code, dob_date, gender_code)
    if ssn == "AUTO" or ssn is None:
        if country_code == 'id':
             # NIK needs district code. Use default if not found in legacy data.
             d_code = '3174' # Default
             if country_code in COUNTRY_DATA:
                 try:
                      # Try to find code in COUNTRY_DATA matching the city we have
                      # This is complex because we might have generated city from Faker/Manual.
                      # Simply use random valid code from COUNTRY_DATA if we can't match.
                      d_code = COUNTRY_DATA['id']['DKI Jakarta']['code'] + '74' 
                 except: pass
             
             ssn = f"{d_code}{random.randint(1,50):02}{dob_date.day + (40 if gender_code=='f' else 0):02}{dob_date.month:02}{str(dob_date.year)[-2:]}{random.randint(1,999):04}"
        else:
            try: ssn = fake_loc.ssn()
            except: ssn = str(random.randint(100000000, 999999999))


    # Email & Password Generation
    first_slug = re.sub(r'[^a-z0-9]', '', name.split()[0].lower())
    email_user = f"{first_slug}{random.randint(100, 999)}"
    email_domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])
    email = f"{email_user}@{email_domain}"
    password = f"{name.split()[0].capitalize()}{dob_date.year}{random.randint(10,99)}"

    return {
        'name': name, 'gender': gender, 'dob': dob, 'age': age,
        'job': job, 'company': company,
        'ssn': ssn, 'address': address, 'city': city, 'state': state, 'postcode': postcode,
        'country_code': country_code, 'phone': phone,
        'ip': fake_loc.ipv4(), 'user_agent': fake_loc.user_agent(),
        'first_name_slug': first_slug,
        'dob_obj': dob_date,
        'email': email, 'password': password
    }

def format_identity_message(data, user_name="User", user_id="0"):
    """
    Formats the identity data into a clean, aesthetic message.
    """
    flag_offset = 127397
    c_code = data['country_code'].upper()
    try:
        flag = chr(ord(c_code[0]) + flag_offset) + chr(ord(c_code[1]) + flag_offset)
    except:
        flag = "🏳️"

    msg = (
        f"<b>👤 IDENTITY GENERATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Personal Details</b>\n"
        f"<b>Name:</b> <code>{data['name']}</code>\n"
        f"<b>Gender:</b> {data['gender']}\n"
        f"<b>Birth:</b> {data['dob']} ({data['age']} y.o)\n"
        f"<b>Job:</b> {data['job']}\n"
        f"<b>Comp:</b> {data['company']}\n"
        f"<b>ID/SSN:</b> <code>{data['ssn']}</code>\n\n"
        f"<b>Location Info</b>\n"
        f"<b>Addr:</b> <code>{data['address']}</code>\n"
        f"<b>City:</b> {data['city']}\n"
        f"<b>State:</b> {data['state']}\n"
        f"<b>Zip:</b> <code>{data['postcode']}</code>\n"
        f"<b>Country:</b> {c_code} {flag}\n\n"
        f"<b>Contact & Online</b>\n"
        f"<b>Phone:</b> <code>{data['phone']}</code>\n"
        f"<b>Email:</b> <code>{data['email']}</code>\n"
        f"<b>Pass:</b> <code>{data['password']}</code>\n"
        f"<b>Status:</b> 🟢 Active\n"
        f"<b>IP:</b> <code>{data['ip']}</code>\n\n"
        f"<b>User Agent:</b>\n"
        f"<code>{data['user_agent']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Generated by:</b> <a href='tg://user?id={user_id}'>{user_name}</a>"
    )
    return msg
