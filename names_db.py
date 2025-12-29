import random

# Database Nama Latin untuk Negara Non-Latin
# Format: First Names (Male/Female mixed usually or separated), Last Names

NAMES_DB = {
    'jp': { # Japan
        'first': [
            "Hiroshi", "Takashi", "Yuki", "Kenji", "Sora", "Rina", "Sakura", "Hina", 
            "Yuto", "Haruto", "Sota", "Ren", "Yui", "Aoi", "Riku", "Kaito", "Asahi",
            "Mio", "Mei", "Akari", "Yuna", "Misaki", "Nanami", "Kenta", "Sho", "Daiki"
        ],
        'last': [
            "Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto",
            "Nakamura", "Kobayashi", "Kato", "Yoshida", "Yamada", "Sasaki", "Yamaguchi"
        ]
    },
    'kr': { # Korea
        'first': [
            "Min-jun", "Seo-jun", "Do-yun", "Ye-jun", "Ji-hoo", "Jun-seo", "Ha-jun",
            "Ji-woo", "Seo-yun", "Min-seo", "Ha-eun", "Ji-yoo", "Su-ah", "Ji-a",
            "Joon-ho", "Hyun-woo", "Dong-hyuk", "Sung-min", "Kyung-soo", "Young-jae"
        ],
        'last': [
            "Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Jo", "Yoon", "Jang", "Lim",
            "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang", "Ahn", "Song", "Jeon", "Hong"
        ]
    },
    'cn': { # China
        'first': [
            "Wei", "Jie", "Hao", "Yi", "Jun", "Feng", "Lei", "Yang", "Ming", "Qiang",
            "Fang", "Na", "Min", "Jing", "Yan", "Li", "Juan", "Xiu", "Ying", "Hua",
            "Bo", "Gang", "Yong", "Jian", "Ping", "Gui", "Dan", "Ping", "Xin"
        ],
        'last': [
            "Li", "Wang", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu",
            "Xu", "Sun", "Hu", "Zhu", "Gao", "Lin", "He", "Guo", "Ma", "Luo"
        ]
    },
    'ru': { # Russia
        'first': [
            "Alexander", "Sergey", "Dmitry", "Andrey", "Alexey", "Maxim", "Ivan", "Mikhail",
            "Elena", "Olga", "Natalia", "Tatiana", "Svetlana", "Irina", "Anna", "Maria",
            "Vladimir", "Nikolay", "Evgeny", "Yuri", "Oleg", "Roman", "Victor", "Igor"
        ],
        'last': [
            "Ivanov", "Smirnov", "Kuznetsov", "Popov", "Vasiliev", "Petrov", "Sokolov",
            "Mikhailov", "Novikov", "Fedorov", "Morozov", "Volkov", "Alekseev", "Lebedev",
            "Semenov", "Egorov", "Pavlov", "Kozlov", "Stepanov", "Nikolaev", "Orlov"
        ]
    },
    'th': { # Thailand
        'first': [
            "Somchai", "Somsak", "Arthit", "Kittisak", "Malee", "Ratana", "Siriporn",
            "Prasert", "Thongchai", "Wichai", "Sombat", "Boonsong", "Aroon", "Kamala",
            "Sunee", "Nipa", "Wilai", "Ubol", "Mali", "Pensri", "Pornthip"
        ],
        'last': [
            "Saunkham", "Khamdee", "Srithong", "Wongwai", "Srisuk", "Chaichana", "Saelim",
            "Saeli", "Saetang", "Phonpraseut", "Bunrueang", "Thongdee", "Kaewmanee"
        ]
    },
    'ua': { # Ukraine
        'first': [
            "Oleksandr", "Serhiy", "Volodymyr", "Mykola", "Ivan", "Vasyl", "Yuriy",
            "Oksana", "Tetyana", "Nataliya", "Halyna", "Lyudmyla", "Iryna", "Olena",
            "Dmytro", "Andriy", "Viktor", "Petro", "Anatoliy", "Ihor", "Oleh"
        ],
        'last': [
            "Melnyk", "Shevchenko", "Boyko", "Kovalenko", "Bondarenko", "Tkachenko",
            "Kravchenko", "Koval", "Oliynyk", "Shevchuk", "Polishchuk", "Lysenko"
        ]
    },
    'vn': { # Vietnam
        'first': [
            "Hung", "Dung", "Tuan", "Minh", "Thang", "Hoang", "Hai", "Nam", "Son", "Long",
            "Huong", "Lan", "Trang", "Huyen", "Thuy", "Mai", "Phuong", "Thu", "Ha", "Linh"
        ],
        'last': [
            "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo", "Dang",
            "Bui", "Do", "Ho", "Ngo", "Duong", "Ly"
        ]
    }
}

def get_romanized_name(country_code):
    """
    Mengembalikan nama format Latin untuk negara tertentu.
    Format: First Last
    """
    code = country_code.lower()
    data = NAMES_DB.get(code)
    
    if not data:
        return None
        
    first = random.choice(data['first'])
    last = random.choice(data['last'])
    
    # Format nama Jepang/China/Korea/Vietnam biasanya Last First secara formal,
    # tapi di format internasional sering First Last. Kita pakai First Last biar standar bot.
    # Kecuali User request specific order? Default First Last aman.
    
    return f"{first} {last}"
