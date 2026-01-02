import random

# DATABASE MANUAL LENGKAP (NAMA, PEKERJAAN + PERUSAHAAN, LOKASI)
# Format: Latin Characters Only.
# Updated: Jobs & Companies are now paired logically in 'occupations'.

NAMES_DB = {
    # ==========================================
    # ASIA TENGGARA (SOUTH EAST ASIA)
    # ==========================================
    'id': { # INDONESIA
        'first': [
            "Aditya", "Agus", "Ahmad", "Aji", "Akbar", "Aldi", "Alif", "Andi", "Angga", "Anugrah", "Ari", "Arief", "Aris", "Arya", "Asep", 
            "Bagas", "Bagus", "Bambang", "Bayu", "Bima", "Bintang", "Budi", "Cahyo", "Candra", "Daffa", "Dani", "Dedi", "Deni", "Diki", "Dimas", "Doni", "Dwi", 
            "Eko", "Fajar", "Faris", "Farhan", "Feri", "Firman", "Galang", "Galih", "Gilang", "Guntur", "Gus", "Hadi", "Hafiz", "Hanafi", "Hendra", "Heru", "Iko", "Ilham", "Imam", "Indra", "Irfan", "Irwan", 
            "Jaka", "Jamal", "Joko", "Kevin", "Kiki", "Krisna", "Kurniawan", "Kusnadi", "Lutfi", "Mahendra", "Maulana", "Miko", "Muhamad", "Muhammad", "Nanda", "Nugraha", "Nur", 
            "Oki", "Pandu", "Panji", "Prasetyo", "Pratama", "Putra", "Rahmat", "Rama", "Ramadhan", "Randy", "Rangga", "Rendi", "Reza", "Rian", "Ricky", "Rizky", "Robby", "Rudi", "Ryan", 
            "Satria", "Septian", "Setiawan", "Sigit", "Slamet", "Soni", "Surya", "Syahrul", "Taufik", "Tegar", "Tio", "Toni", "Tri", "Wahyu", "Wawan", "Wibowo", "Wildan", "Wisnu", "Yoga", "Yudi", "Yusuf", "Zainal", "Zulfikar",
            "Adelia", "Aisyah", "Amelia", "Anisa", "Anita", "Aprilia", "Ayu", "Bella", "Bunga", "Cahya", "Cindy", "Citra", "Clarissa", "Dewi", "Dian", "Dina", "Dinda", "Dwi", 
            "Eka", "Elisa", "Elsya", "Ema", "Eva", "Fani", "Fia", "Fitri", "Gabriella", "Gita", "Hana", "Hani", "Hesti", "Ika", "Indah", "Intan", "Ira", "Irma", "Jessica", "Julia", "Juwita", 
            "Kartika", "Khusnul", "Laras", "Lestari", "Lia", "Lina", "Lisa", "Lusi", "Maya", "Mega", "Melati", "Mela", "Melisa", "Mutiara", "Nadia", "Nanda", "Nia", "Nina", "Nisa", "Novita", "Nur", "Nurul", 
            "Olivia", "Putri", "Rahma", "Rani", "Ratih", "Ratna", "Rina", "Rini", "Rika", "Risma", "Rosa", "Rosmala", "Santi", "Sari", "Sekar", "Siti", "Siska", "Sri", "Suci", "Syifa", 
            "Tia", "Tiara", "Tina", "Tri", "Vania", "Vina", "Winda", "Wulan", "Yani", "Yulia", "Yuni", "Yusnita", "Zahra", "Zaskia"
        ],
        'last': [
            "Adriansyah", "Afandi", "Agustina", "Alamsyah", "Anggraini", "Anwar", "Aprianto", "Ardiansyah", "Arifin", "Astuti", "Aziz", 
            "Basri", "Budiman", "Cahyono", "Darmawan", "Efendi", "Fauzi", "Febrianto", "Firmansyah", "Gunawan", "Hakim", "Halim", "Hamzah", "Handayani", "Hartono", "Hasan", "Hermawan", "Hidayat", "Hidayatullah", 
            "Ibrahim", "Irawan", "Ismail", "Jaya", "Kusuma", "Kurnia", "Kurniawan", "Lestari", "Mahardika", "Maulana", "Mustofa", "Nasution", "Nugroho", "Nurhadi", 
            "Pambudi", "Pamungkas", "Permana", "Pradana", "Prakoso", "Pratama", "Pratiwi", "Prayoga", "Purnomo", "Putra", "Putri", "Rahayu", "Rahman", "Ramadhan", "Rianto", "Riyadi", "Rosyid", "Rusli", 
            "Safitri", "Sahputra", "Saleh", "Salim", "Santoso", "Saputra", "Sari", "Setiawan", "Setiyono", "Siregar", "Sitepu", "Sitorus", "Subagyo", "Suharto", "Sulistyo", "Sumantri", "Supriyadi", "Susanto", "Susilo", "Sutrisno", "Syahputra", 
            "Tan", "Tanjung", "Utama", "Utami", "Wahyudi", "Wardana", "Wibowo", "Wibisono", "Widodo", "Wijaya", "Winarto", "Wirawan", "Yuliana", "Yusuf", "Zakaria", "Zulkarnain"
        ],
        'occupations': [
            {"job": "Kasir", "company": "Indomaret"},
            {"job": "Pramuniaga", "company": "Alfamart"},
            {"job": "Driver", "company": "Gojek Indonesia"},
            {"job": "Driver", "company": "Grab Indonesia"},
            {"job": "Kurir", "company": "JNE Express"},
            {"job": "Kurir", "company": "J&T Express"},
            {"job": "Staff Administrasi", "company": "PT Telkom Indonesia"},
            {"job": "Customer Service", "company": "PT Bank Central Asia (BCA)"},
            {"job": "Teller", "company": "Bank Rakyat Indonesia (BRI)"},
            {"job": "Security", "company": "PT Sinar Mas Group"},
            {"job": "Operator Produksi", "company": "PT Gudang Garam Tbk"},
            {"job": "Buruh Pabrik", "company": "PT Unilever Indonesia"},
            {"job": "Sales Marketing", "company": "PT Astra International"},
            {"job": "Mekanik", "company": "Auto2000"},
            {"job": "Dokter Umum", "company": "RS Siloam Hospitals"},
            {"job": "Perawat", "company": "RS Cipto Mangunkusumo"},
            {"job": "Apoteker", "company": "Apotek K-24"},
            {"job": "Barista", "company": "Kopi Kenangan"},
            {"job": "Chef", "company": "Warung Makan Sederhana"},
            {"job": "Guru", "company": "SD Negeri 01 Pagi"},
            {"job": "Dosen", "company": "Universitas Indonesia"},
            {"job": "Software Engineer", "company": "Tokopedia"},
            {"job": "Data Analyst", "company": "Traveloka"},
            {"job": "Content Creator", "company": "Shopee Indonesia"}
        ],
        'locations': [
            {"state": "DKI Jakarta", "city": "Jakarta Selatan", "zip": "12", "streets": ["Jl. Sudirman", "Jl. Fatmawati", "Jl. Antasari", "Jl. Kemang Raya", "Jl. Radio Dalam"]},
            {"state": "DKI Jakarta", "city": "Jakarta Pusat", "zip": "10", "streets": ["Jl. MH Thamrin", "Jl. Gajah Mada", "Jl. Cikini Raya", "Jl. Kramat Raya"]},
            {"state": "Jawa Barat", "city": "Bandung", "zip": "40", "streets": ["Jl. Dago", "Jl. Riau", "Jl. Braga", "Jl. Setiabudi", "Jl. Cihampelas"]},
            {"state": "Jawa Barat", "city": "Bekasi", "zip": "17", "streets": ["Jl. Ahmad Yani", "Jl. Juanda", "Jl. Kalimalang", "Jl. Narogong"]},
            {"state": "Jawa Timur", "city": "Surabaya", "zip": "60", "streets": ["Jl. Tunjungan", "Jl. Darmo", "Jl. Basuki Rahmat", "Jl. Pemuda"]},
            {"state": "Bali", "city": "Denpasar", "zip": "80", "streets": ["Jl. Teuku Umar", "Jl. Gajah Mada", "Jl. Imam Bonjol", "Jl. Diponegoro"]},
            {"state": "Sumatera Utara", "city": "Medan", "zip": "20", "streets": ["Jl. Sisingamangaraja", "Jl. Gatot Subroto", "Jl. Sudirman", "Jl. Ahmad Yani"]}
        ]
    },
    'my': { # MALAYSIA
        'first': [
            "Ahmad", "Muhammad", "Adam", "Rayyan", "Daniel", "Amir", "Harith", "Izzat", "Khairul", "Luqman", "Chong", "Wei", "Jian", "Jun", "Ming", "Seng", "Keong", "Yong", "Sanjay", "Muthu", "Ravi", "Dev", "Vikram",
            "Siti", "Nur", "Aishah", "Zara", "Sofia", "Nora", "Farah", "Huda", "Ying", "Mei", "Ling", "Siew", "Yee", "Priya", "Devi", "Kavitha"
        ],
        'last': [
            "bin Abdullah", "bin Ismail", "bin Ibrahim", "bin Rosli", "bin Zakaria", "bin Othman", "bin Rahman", "bin Mat", "binti Ali", "binti Osman", "binti Yusof", "binti Razak",
            "Lee", "Tan", "Wong", "Lim", "Ng", "Teoh", "Yap", "Fong", "Lau", "Chong", "Chin", "Rao", "Nair", "Subramaniam", "Menon", "Krishnan", "Govind"
        ],
        'occupations': [
            {"job": "Petroleum Engineer", "company": "Petronas"},
            {"job": "Bank Teller", "company": "Maybank"},
            {"job": "Customer Service", "company": "CIMB Bank"},
            {"job": "Technician", "company": "Tenaga Nasional Berhad"},
            {"job": "Sales Executive", "company": "Proton Holdings"},
            {"job": "Flight Attendant", "company": "AirAsia"},
            {"job": "Software Developer", "company": "Grab Malaysia"},
            {"job": "Accountant", "company": "Public Bank"},
            {"job": "Plantation Worker", "company": "Sime Darby"},
            {"job": "Network Engineer", "company": "Maxis"},
            {"job": "Store Manager", "company": "99 Speedmart"},
            {"job": "Pharmacist", "company": "Watsons Malaysia"},
            {"job": "Lecturer", "company": "Universiti Malaya"},
            {"job": "Doctor", "company": "Gleneagles Hospital"},
            {"job": "Security Guard", "company": "Top Glove"}
        ],
        'locations': [
            {"state": "Selangor", "city": "Shah Alam", "zip": "40", "streets": ["Jalan Plumbum", "Jalan Kristal", "Persiaran Tasik", "Jalan Sementa"]},
            {"state": "Selangor", "city": "Petaling Jaya", "zip": "46", "streets": ["Jalan Gasing", "Jalan Templer", "Jalan Universiti", "Damansara Utama"]},
            {"state": "Kuala Lumpur", "city": "Kuala Lumpur", "zip": "50", "streets": ["Jalan Ampang", "Jalan Bukit Bintang", "Jalan Tun Razak", "Jalan Sultan Ismail"]},
            {"state": "Johor", "city": "Johor Bahru", "zip": "80", "streets": ["Jalan Wong Ah Fook", "Jalan Tebrau", "Jalan Skudai"]},
            {"state": "Penang", "city": "George Town", "zip": "10", "streets": ["Jalan Penang", "Jalan Burma", "Lebuh Chulia"]}
        ]
    },
    'sg': { # SINGAPORE
        'first': [
            "Kelvin", "Alvin", "Jason", "Wei Ming", "Jun Jie", "Hafiz", "Farhan", "Ravi", "Kumar", "Aloysius", "Desmond", "Gabriel",
            "Jessica", "Rachel", "Michelle", "Hui Ling", "Yi Ting", "Siti", "Nurul", "Priya", "Charmaine", "Xinyi", "Vivian"
        ],
        'last': [
            "Tan", "Lee", "Lim", "Ng", "Ong", "Wong", "Goh", "Chua", "Teo", "Koh", "Yeo", "Tay", "Ho", "Low", "bin Ahmad", "bin Yusof", "Singh", "Pillay", "Jayakumar"
        ],
        'occupations': [
            {"job": "Financial Analyst", "company": "DBS Bank"},
            {"job": "Investment Banker", "company": "OCBC Bank"},
            {"job": "Software Engineer", "company": "Shopee Singapore"},
            {"job": "Data Scientist", "company": "Grab"},
            {"job": "Cabin Crew", "company": "Singapore Airlines"},
            {"job": "Civil Servant", "company": "Ministry of Education"},
            {"job": "Nurse", "company": "Singapore General Hospital"},
            {"job": "Retail Manager", "company": "FairPrice"},
            {"job": "Operations Manager", "company": "Changi Airport Group"},
            {"job": "Network Engineer", "company": "Singtel"},
            {"job": "Real Estate Agent", "company": "PropNex"},
            {"job": "Bus Captain", "company": "SBS Transit"}
        ],
        'locations': [
            {"state": "Singapore", "city": "Singapore", "zip": "04", "streets": ["Raffles Place", "Cecil Street", "Robinson Road", "Shenton Way"]},
            {"state": "Singapore", "city": "Singapore", "zip": "23", "streets": ["Orchard Road", "Somerset Road", "River Valley Road"]},
            {"state": "Singapore", "city": "Singapore", "zip": "52", "streets": ["Tampines Ave", "Simei Street", "Pasir Ris Drive"]},
            {"state": "Singapore", "city": "Singapore", "zip": "60", "streets": ["Jurong West", "Boon Lay Way", "Pioneer Road"]}
        ]
    },
    'ph': { # PHILIPPINES
        'first': [
            "Jose", "Juan", "Gabriel", "Mark", "Angelo", "Christian", "Joshua", "Rogelio", "Eduardo", "Paolo", "Miguel", "Rico", "Jayson",
            "Maria", "Angela", "Kristine", "Jasmine", "Rose", "Grace", "Jennifer", "Lourdes", "Mae", "Bea", "Camille", "Angel"
        ],
        'last': [
            "Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Flores", "Dela Cruz", "Gonzales", "Rivera", "Castillo", "Villanueva", "Ramos", "Vargas", "Fernandez", "Aquino", "Mercado"
        ],
        'occupations': [
            {"job": "Call Center Agent", "company": "Concentrix"},
            {"job": "Virtual Assistant", "company": "Upwork"},
            {"job": "Bank Teller", "company": "BDO Unibank"},
            {"job": "Sales Associate", "company": "SM Supermalls"},
            {"job": "Nurse", "company": "St. Luke's Medical Center"},
            {"job": "Civil Engineer", "company": "DMCI Holdings"},
            {"job": "Fast Food Crew", "company": "Jollibee"},
            {"job": "Flight Attendant", "company": "Philippine Airlines"},
            {"job": "IT Specialist", "company": "Globe Telecom"},
            {"job": "Accountant", "company": "Ayala Corporation"},
            {"job": "Teacher", "company": "DepEd"},
            {"job": "Security Guard", "company": "San Miguel Corporation"}
        ],
        'locations': [
            {"state": "Metro Manila", "city": "Makati", "zip": "12", "streets": ["Ayala Avenue", "Gil Puyat Avenue", "Makati Avenue", "Chino Roces"]},
            {"state": "Metro Manila", "city": "Quezon City", "zip": "11", "streets": ["Commonwealth Avenue", "Quezon Avenue", "EDSA", "Aurora Boulevard"]},
            {"state": "Metro Manila", "city": "Manila", "zip": "10", "streets": ["Rizal Avenue", "Taft Avenue", "Espana Boulevard", "Roxas Boulevard"]},
            {"state": "Cebu", "city": "Cebu City", "zip": "60", "streets": ["Osmena Boulevard", "Colon Street", "Mango Avenue"]},
            {"state": "Davao", "city": "Davao City", "zip": "80", "streets": ["San Pedro Street", "Quirino Avenue", "JP Laurel Avenue"]}
        ]
    },
    'th': { # THAILAND
        'first': [
            "Somchai", "Somsak", "Arthit", "Kittisak", "Prasert", "Thongchai", "Wichai", "Nattapong", "Anan", "Chai", "Narong",
            "Malee", "Ratana", "Siriporn", "Kamala", "Sunee", "Nipa", "Wilai", "Pornthip", "Kanya", "Suda", "Wanee"
        ],
        'last': [
            "Saunkham", "Khamdee", "Srithong", "Wongwai", "Srisuk", "Chaichana", "Saelim", "Sukhum", "Charoen",
            "Saeli", "Saetang", "Phonpraseut", "Bunrueang", "Thongdee", "Kaewmanee", "Suwannarat", "Ratanaporn"
        ],
        'occupations': [
            {"job": "Store Manager", "company": "7-Eleven Thailand"},
            {"job": "Bank Clerk", "company": "Kasikornbank"},
            {"job": "Office Worker", "company": "PTT Public Company"},
            {"job": "Engineer", "company": "Siam Cement Group"},
            {"job": "Hotel Receptionist", "company": "Centara Hotels"},
            {"job": "Chef", "company": "MK Restaurants"},
            {"job": "Sales Representative", "company": "Toyota Thailand"},
            {"job": "Nurse", "company": "Bumrungrad Hospital"},
            {"job": "Government Officer", "company": "Bangkok Metropolitan Admin"},
            {"job": "Brewery Worker", "company": "Thai Beverage"},
            {"job": "Telecom Engineer", "company": "AIS Thailand"}
        ],
        'locations': [
            {"state": "Bangkok", "city": "Bangkok", "zip": "10", "streets": ["Sukhumvit Road", "Silom Road", "Sathorn Road", "Rama IV Road", "Phetchaburi Road"]},
            {"state": "Chiang Mai", "city": "Chiang Mai", "zip": "50", "streets": ["Nimmanhaemin Road", "Huay Kaew Road", "Tha Phae Road"]},
            {"state": "Phuket", "city": "Phuket", "zip": "83", "streets": ["Patong Beach Road", "Bangla Road", "Thepkrasattri Road"]},
            {"state": "Chon Buri", "city": "Pattaya", "zip": "20", "streets": ["Beach Road", "Second Road", "North Pattaya Road"]}
        ]
    },
    'vn': { # VIETNAM
        'first': [
            "Hung", "Dung", "Tuan", "Minh", "Thang", "Hoang", "Hai", "Nam", "Son", "Long", "Duc", "Phuc", "Quang", "Dat",
            "Huong", "Lan", "Trang", "Huyen", "Thuy", "Mai", "Phuong", "Thu", "Ha", "Linh", "Vy", "Nhu", "Tam"
        ],
        'last': [
            "Nguyen", "Tran", "Le", "Pham", "Hoang", "Huynh", "Phan", "Vu", "Vo", "Dang", "Bui", "Do", "Ho", "Ngo", "Duong"
        ],
        'occupations': [
            {"job": "Software Engineer", "company": "FPT Software"},
            {"job": "Real Estate Agent", "company": "Vingroup"},
            {"job": "Dairy Worker", "company": "Vinamilk"},
            {"job": "Bank Teller", "company": "Vietcombank"},
            {"job": "Teacher", "company": "Vinschool"},
            {"job": "Sales Manager", "company": "Masan Group"},
            {"job": "Pilot", "company": "Vietnam Airlines"},
            {"job": "Network Engineer", "company": "Viettel"},
            {"job": "Factory Supervisor", "company": "Samsung Vietnam"},
            {"job": "Barista", "company": "Highlands Coffee"}
        ],
        'locations': [
            {"state": "Ho Chi Minh City", "city": "Ho Chi Minh City", "zip": "70", "streets": ["Nguyen Hue", "Le Loi", "Dong Khoi", "Pasteur", "Hai Ba Trung"]},
            {"state": "Hanoi", "city": "Hanoi", "zip": "10", "streets": ["Trang Tien", "Hang Bai", "Pho Hue", "Kim Ma", "Cau Giay"]},
            {"state": "Da Nang", "city": "Da Nang", "zip": "55", "streets": ["Bach Dang", "Le Duan", "Nguyen Van Linh"]},
            {"state": "Hai Phong", "city": "Hai Phong", "zip": "18", "streets": ["Lach Tray", "Dien Bien Phu", "Tran Phu"]}
        ]
    },

    # ==========================================
    # ASIA TIMUR (EAST ASIA)
    # ==========================================
    'jp': { # JAPAN
        'first': [
            "Hiroshi", "Takashi", "Yuki", "Kenji", "Sora", "Yuto", "Haruto", "Sota", "Ren", "Riku", "Kaito", "Asahi", "Kenta", "Sho", "Daiki", "Tatsuya", "Kazuki",
            "Rina", "Sakura", "Hina", "Yui", "Aoi", "Mio", "Mei", "Akari", "Yuna", "Misaki", "Nanami", "Ai", "Ayumi", "Emi", "Kaori", "Yoko"
        ],
        'last': [
            "Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato",
            "Yoshida", "Yamada", "Sasaki", "Yamaguchi", "Matsumoto", "Inoue", "Kimura", "Shimizu", "Hayashi"
        ],
        'occupations': [
            {"job": "Automotive Engineer", "company": "Toyota Motor Corp"},
            {"job": "Game Designer", "company": "Nintendo"},
            {"job": "Electronics Technician", "company": "Sony Group"},
            {"job": "Salesman", "company": "Uniqlo"},
            {"job": "Banker", "company": "Mitsubishi UFJ"},
            {"job": "Store Staff", "company": "7-Eleven Japan"},
            {"job": "Research Scientist", "company": "Takeda Pharmaceutical"},
            {"job": "Salaryman", "company": "SoftBank Group"},
            {"job": "Animator", "company": "Studio Ghibli"},
            {"job": "Train Driver", "company": "JR East"}
        ],
        'locations': [
            {"state": "Tokyo", "city": "Shinjuku", "zip": "16", "streets": ["Yasukuni Dori", "Meiji Dori", "Koshu Kaido"]},
            {"state": "Tokyo", "city": "Shibuya", "zip": "15", "streets": ["Dogenzaka", "Omotesando", "Aoyama Dori"]},
            {"state": "Osaka", "city": "Osaka", "zip": "54", "streets": ["Midosuji", "Sakaisuji", "Naniwa suji"]},
            {"state": "Kyoto", "city": "Kyoto", "zip": "60", "streets": ["Shijo Dori", "Kawaramachi Dori", "Karasuma Dori"]},
            {"state": "Hokkaido", "city": "Sapporo", "zip": "06", "streets": ["Odori", "Susukino", "Ekimae Dori"]}
        ]
    },
    'kr': { # KOREA
        'first': [
            "Min-jun", "Seo-jun", "Do-yun", "Ye-jun", "Ji-hoo", "Jun-seo", "Ha-jun", "Ji-woo", "Joon-ho", "Hyun-woo", "Dong-hyuk", "Sung-min",
            "Seo-yun", "Min-seo", "Ha-eun", "Ji-yoo", "Su-ah", "Ji-a", "Eun-ji", "So-yeon", "Hye-jin", "Ji-eun"
        ],
        'last': [
            "Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Jo", "Yoon", "Jang", "Lim", "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang", "Song"
        ],
        'occupations': [
            {"job": "Semiconductor Engineer", "company": "Samsung Electronics"},
            {"job": "Automotive Designer", "company": "Hyundai Motor"},
            {"job": "K-Pop Producer", "company": "HYBE Corporation"},
            {"job": "Chemical Engineer", "company": "LG Chem"},
            {"job": "Software Developer", "company": "Naver"},
            {"job": "Bank Clerk", "company": "KB Kookmin Bank"},
            {"job": "Steel Worker", "company": "POSCO"},
            {"job": "Cosmetics Researcher", "company": "Amorepacific"},
            {"job": "Coffee Shop Manager", "company": "Ediya Coffee"},
            {"job": "Delivery Driver", "company": "Coupang"}
        ],
        'locations': [
            {"state": "Seoul", "city": "Gangnam-gu", "zip": "06", "streets": ["Teheran-ro", "Gangnam-daero", "Apgujeong-ro"]},
            {"state": "Seoul", "city": "Jongno-gu", "zip": "03", "streets": ["Sejong-daero", "Jong-ro", "Samil-daero"]},
            {"state": "Busan", "city": "Haeundae-gu", "zip": "48", "streets": ["Haeundae-ro", "Dalmaji-gil", "Marine City-ro"]},
            {"state": "Incheon", "city": "Yeonsu-gu", "zip": "21", "streets": ["Songdo-daero", "Convensia-daero", "Art center-daero"]}
        ]
    },
    'cn': { # CHINA
        'first': [
            "Wei", "Jie", "Hao", "Yi", "Jun", "Feng", "Lei", "Yang", "Ming", "Qiang", "Bo", "Gang", "Yong", "Jian",
            "Fang", "Na", "Min", "Jing", "Yan", "Li", "Juan", "Xiu", "Ying", "Hua", "Dan", "Ping", "Xin", "Hui"
        ],
        'last': [
            "Li", "Wang", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu", "Xu", "Sun", "Hu", "Zhu", "Gao", "Lin", "He", "Guo", "Ma", "Luo"
        ],
        'occupations': [
            {"job": "E-commerce Manager", "company": "Alibaba Group"},
            {"job": "Game Developer", "company": "Tencent"},
            {"job": "Factory Worker", "company": "Foxconn"},
            {"job": "Bank Officer", "company": "ICBC"},
            {"job": "Delivery Driver", "company": "Meituan"},
            {"job": "AI Researcher", "company": "Baidu"},
            {"job": "Mobile Engineer", "company": "Xiaomi"},
            {"job": "Oil Engineer", "company": "PetroChina"},
            {"job": "Insurance Agent", "company": "Ping An Insurance"},
            {"job": "Construction Worker", "company": "China State Construction"}
        ],
        'locations': [
            {"state": "Beijing", "city": "Beijing", "zip": "10", "streets": ["Chang'an Avenue", "Wangfujing Street", "Sanlitun Road"]},
            {"state": "Shanghai", "city": "Shanghai", "zip": "20", "streets": ["Nanjing Road", "Huaihai Road", "The Bund"]},
            {"state": "Guangdong", "city": "Guangzhou", "zip": "51", "streets": ["Beijing Road", "Tianhe Road", "Shamian Street"]},
            {"state": "Guangdong", "city": "Shenzhen", "zip": "51", "streets": ["Shennan Boulevard", "Huaqiang North Road", "Binhai Boulevard"]}
        ]
    },
    'in': { # INDIA
        'first': [
            "Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Rohan", "Rahul", "Amit", "Vikram", "Karan", "Siddharth", "Manish", "Ravi",
            "Diya", "Saanvi", "Anya", "Aditi", "Priya", "Neha", "Pooja", "Anjali", "Sushma", "Kavita", "Divya", "Ishita"
        ],
        'last': [
            "Patel", "Sharma", "Singh", "Kumar", "Gupta", "Rao", "Desai", "Mehta", "Reddy", "Iyer", "Jain", "Verma", "Mishra", "Shah", "Malhotra"
        ],
        'occupations': [
            {"job": "IT Consultant", "company": "Tata Consultancy Services"},
            {"job": "Software Engineer", "company": "Infosys"},
            {"job": "Petrochemical Engineer", "company": "Reliance Industries"},
            {"job": "Bank Manager", "company": "HDFC Bank"},
            {"job": "Call Center Agent", "company": "Wipro"},
            {"job": "Data Analyst", "company": "HCL Technologies"},
            {"job": "Civil Engineer", "company": "Larsen & Toubro"},
            {"job": "Doctor", "company": "Apollo Hospitals"},
            {"job": "Sales Executive", "company": "Maruti Suzuki"},
            {"job": "Railway Officer", "company": "Indian Railways"}
        ],
        'locations': [
            {"state": "Maharashtra", "city": "Mumbai", "zip": "40", "streets": ["Marine Drive", "Linking Road", "Hill Road", "Colaba Causeway"]},
            {"state": "Delhi", "city": "New Delhi", "zip": "11", "streets": ["Connaught Place", "Chandni Chowk", "Lodhi Road", "Rajpath"]},
            {"state": "Karnataka", "city": "Bangalore", "zip": "56", "streets": ["MG Road", "Brigade Road", "Indiranagar 100 Feet Road"]},
            {"state": "Tamil Nadu", "city": "Chennai", "zip": "60", "streets": ["Anna Salai", "Mount Road", "Marina Beach Road"]},
            {"state": "West Bengal", "city": "Kolkata", "zip": "70", "streets": ["Park Street", "College Street", "Chowringhee Road"]}
        ]
    },

    # ==========================================
    # EROPA (EUROPE)
    # ==========================================
    'gb': { # UNITED KINGDOM
        'first': [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "George", "Harry", "Jack", "Oliver", "Jacob", "Charlie",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Olivia", "Amelia", "Isla", "Emily", "Ava"
        ],
        'last': [
            "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Johnson", "Roberts", "Robinson", "Thompson", "Wright", "Walker", "White", "Edwards"
        ],
        'occupations': [
            {"job": "Banker", "company": "HSBC"},
            {"job": "Pharmacist", "company": "Boots UK"},
            {"job": "Retail Manager", "company": "Tesco"},
            {"job": "Software Developer", "company": "Vodafone UK"},
            {"job": "Energy Consultant", "company": "BP"},
            {"job": "Nurse", "company": "NHS"},
            {"job": "Journalist", "company": "BBC"},
            {"job": "Flight Attendant", "company": "British Airways"},
            {"job": "Accountant", "company": "Barclays"},
            {"job": "Professor", "company": "University of Oxford"}
        ],
        'locations': [
            {"state": "London", "city": "London", "zip": "SW1", "streets": ["Oxford Street", "Regent Street", "Baker Street", "Piccadilly", "King's Road"]},
            {"state": "Greater Manchester", "city": "Manchester", "zip": "M1", "streets": ["Deansgate", "Market Street", "Oxford Road"]},
            {"state": "West Midlands", "city": "Birmingham", "zip": "B1", "streets": ["New Street", "Broad Street", "Corporation Street"]},
            {"state": "Scotland", "city": "Edinburgh", "zip": "EH1", "streets": ["Royal Mile", "Princes Street", "George Street"]}
        ]
    },
    'de': { # GERMANY
        'first': [
            "Hans", "Klaus", "Thomas", "Michael", "Stefan", "Andreas", "Markus", "Christian", "Martin", "Peter", "Uwe", "Jorg", "Frank",
            "Ursula", "Monika", "Petra", "Sabine", "Karin", "Renate", "Helga", "Brigitte", "Claudia", "Susanne", "Julia", "Maria"
        ],
        'last': [
            "Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Schafer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schroder"
        ],
        'occupations': [
            {"job": "Automotive Engineer", "company": "Volkswagen AG"},
            {"job": "Mechanical Engineer", "company": "Siemens"},
            {"job": "Chemical Engineer", "company": "BASF"},
            {"job": "Software Developer", "company": "SAP"},
            {"job": "Insurance Agent", "company": "Allianz"},
            {"job": "Postal Worker", "company": "Deutsche Post DHL"},
            {"job": "Bank Clerk", "company": "Deutsche Bank"},
            {"job": "Sales Associate", "company": "Adidas"},
            {"job": "Technician", "company": "Bosch"},
            {"job": "Pilot", "company": "Lufthansa"}
        ],
        'locations': [
            {"state": "Berlin", "city": "Berlin", "zip": "10", "streets": ["Unter den Linden", "Friedrichstrasse", "Kurfuerstendamm", "Torstrasse"]},
            {"state": "Bavaria", "city": "Munich", "zip": "80", "streets": ["Maximilianstrasse", "Leopoldstrasse", "Schellingstrasse"]},
            {"state": "Hamburg", "city": "Hamburg", "zip": "20", "streets": ["Reeperbahn", "Jungfernstieg", "Moenckebergstrasse"]},
            {"state": "Hesse", "city": "Frankfurt", "zip": "60", "streets": ["Zeil", "Mainzer Landstrasse", "Eschersheimer Landstrasse"]}
        ]
    },
    'fr': { # FRANCE
        'first': [
            "Jean", "Pierre", "Michel", "Philippe", "Alain", "Patrick", "Nicolas", "Christophe", "Louis", "Gabriel", "Leo", "Lucas", "Adam",
            "Marie", "Nathalie", "Isabelle", "Sylvie", "Catherine", "Martine", "Veronique", "Francoise", "Emma", "Louise", "Alice", "Chloe"
        ],
        'last': [
            "Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David"
        ],
        'occupations': [
            {"job": "Fashion Designer", "company": "LVMH"},
            {"job": "Cosmetics Researcher", "company": "L'Oreal"},
            {"job": "Aerospace Engineer", "company": "Airbus"},
            {"job": "Banker", "company": "BNP Paribas"},
            {"job": "Energy Consultant", "company": "TotalEnergies"},
            {"job": "Chef", "company": "Michelin Star Restaurant"},
            {"job": "Retail Manager", "company": "Carrefour"},
            {"job": "Automotive Technician", "company": "Renault"},
            {"job": "Telecom Engineer", "company": "Orange"},
            {"job": "Insurance Broker", "company": "AXA"}
        ],
        'locations': [
            {"state": "Ile-de-France", "city": "Paris", "zip": "75", "streets": ["Champs-Elysees", "Rue de Rivoli", "Boulevard Saint-Germain", "Avenue Montaigne"]},
            {"state": "Auvergne-Rhone-Alpes", "city": "Lyon", "zip": "69", "streets": ["Rue de la Republique", "Rue Victor Hugo", "Cours Lafayette"]},
            {"state": "Provence-Alpes-Cote d'Azur", "city": "Marseille", "zip": "13", "streets": ["La Canebiere", "Rue Paradis", "Corniche Kennedy"]}
        ]
    },
    'it': { # ITALY
        'first': [
            "Alessandro", "Lorenzo", "Mattia", "Leonardo", "Francesco", "Andrea", "Marco", "Antonio", "Giuseppe", "Luca", "Giovanni", "Roberto", "Stefano",
            "Sofia", "Giulia", "Aurora", "Alice", "Giorgia", "Martina", "Chiara", "Anna", "Sara", "Francesca", "Maria", "Silvia"
        ],
        'last': [
            "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano"
        ],
        'occupations': [
            {"job": "Automotive Engineer", "company": "Ferrari"},
            {"job": "Fashion Designer", "company": "Prada"},
            {"job": "Energy Technician", "company": "Enel"},
            {"job": "Bank Clerk", "company": "Intesa Sanpaolo"},
            {"job": "Confectioner", "company": "Ferrero"},
            {"job": "Insurance Agent", "company": "Generali"},
            {"job": "Tyre Specialist", "company": "Pirelli"},
            {"job": "Optician", "company": "Luxottica"},
            {"job": "Petroleum Engineer", "company": "Eni"},
            {"job": "Chef", "company": "Trattoria Romana"}
        ],
        'locations': [
            {"state": "Lazio", "city": "Rome", "zip": "00", "streets": ["Via del Corso", "Via Condotti", "Via Veneto", "Via Nazionale"]},
            {"state": "Lombardy", "city": "Milan", "zip": "20", "streets": ["Via Montenapoleone", "Corso Buenos Aires", "Via Dante"]},
            {"state": "Campania", "city": "Naples", "zip": "80", "streets": ["Spaccanapoli", "Via Toledo", "Corso Umberto I"]},
            {"state": "Tuscany", "city": "Florence", "zip": "50", "streets": ["Via de' Tornabuoni", "Via Calzaiuoli", "Ponte Vecchio"]}
        ]
    },
    'es': { # SPAIN
        'first': [
            "Antonio", "Jose", "Manuel", "Francisco", "David", "Juan", "Javier", "Daniel", "Carlos", "Jesus", "Alejandro", "Miguel",
            "Maria", "Carmen", "Ana", "Isabel", "Laura", "Cristina", "Marta", "Lucia", "Elena", "Paula", "Raquel", "Sara"
        ],
        'last': [
            "Garcia", "Gonzalez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Sanchez", "Perez", "Martin", "Gomez", "Ruiz", "Diaz", "Hernandez", "Alvarez", "Moreno"
        ],
        'occupations': [
            {"job": "Store Manager", "company": "Zara (Inditex)"},
            {"job": "Banker", "company": "Banco Santander"},
            {"job": "Energy Engineer", "company": "Iberdrola"},
            {"job": "Telecom Technician", "company": "Telefonica"},
            {"job": "Oil Rig Worker", "company": "Repsol"},
            {"job": "Software Developer", "company": "Amadeus IT"},
            {"job": "Insurance Agent", "company": "Mapfre"},
            {"job": "Construction Manager", "company": "Ferrovial"},
            {"job": "Hotel Manager", "company": "Melia Hotels"},
            {"job": "Airport Staff", "company": "Aena"}
        ],
        'locations': [
            {"state": "Madrid", "city": "Madrid", "zip": "28", "streets": ["Gran Via", "Calle de Alcala", "Paseo de la Castellana", "Calle Serrano"]},
            {"state": "Catalonia", "city": "Barcelona", "zip": "08", "streets": ["La Rambla", "Passeig de Gracia", "Avinguda Diagonal"]},
            {"state": "Valencia", "city": "Valencia", "zip": "46", "streets": ["Calle Colon", "Calle Xativa", "Avenida del Puerto"]},
            {"state": "Andalusia", "city": "Seville", "zip": "41", "streets": ["Calle Sierpes", "Avenida de la Constitucion", "Calle Betis"]}
        ]
    },
    'nl': { # NETHERLANDS
        'first': [
            "Jan", "Johannes", "Cornelis", "Hendrik", "Willem", "Pieter", "Gerrit", "Daan", "Sem", "Lucas", "Levi", "Milan",
            "Johanna", "Maria", "Anna", "Elisabeth", "Cornelia", "Wilhelmina", "Catharina", "Emma", "Julia", "Mila", "Sophie", "Tess"
        ],
        'last': [
            "de Vries", "Jansen", "van de Berg", "Bakker", "van Dijk", "Visser", "Janssen", "Smit", "Meijer", "de Boer", "Mulder", "de Groot", "Bos", "Vos"
        ],
        'occupations': [
            {"job": "Semiconductor Engineer", "company": "ASML"},
            {"job": "Supply Chain Manager", "company": "Heineken"},
            {"job": "Banker", "company": "ING Group"},
            {"job": "Consumer Goods Specialist", "company": "Unilever"},
            {"job": "Petrochemical Engineer", "company": "Shell"},
            {"job": "Healthcare Tech", "company": "Philips"},
            {"job": "Retail Manager", "company": "Ahold Delhaize"},
            {"job": "Telecom Engineer", "company": "KPN"},
            {"job": "Paint Specialist", "company": "AkzoNobel"},
            {"job": "Fintech Developer", "company": "Adyen"}
        ],
        'locations': [
            {"state": "North Holland", "city": "Amsterdam", "zip": "10", "streets": ["Damrak", "Kalverstraat", "Leidsestraat", "P.C. Hooftstraat"]},
            {"state": "South Holland", "city": "Rotterdam", "zip": "30", "streets": ["Coolsingel", "Lijnbaan", "Weena"]},
            {"state": "South Holland", "city": "The Hague", "zip": "25", "streets": ["Spui", "Grote Markt", "Lange Voorhout"]},
            {"state": "Utrecht", "city": "Utrecht", "zip": "35", "streets": ["Oudegracht", "Vredenburg", "Steenweg"]}
        ]
    },
    'pl': { # POLAND
        'first': [
            "Piotr", "Krzysztof", "Andrzej", "Tomasz", "Jan", "Pawel", "Michal", "Marcin", "Jakub", "Adam", "Stanislaw",
            "Anna", "Maria", "Katarzyna", "Malgorzata", "Agnieszka", "Krystyna", "Barbara", "Ewa", "Elzbieta", "Zofia"
        ],
        'last': [
            "Nowak", "Kowalski", "Wisniewski", "Wojcik", "Kowalczyk", "Kaminski", "Lewandowski", "Zielinski", "Szymanski", "Wozniak", "Dabrowski", "Kozlowski"
        ],
        'occupations': [
            {"job": "Refinery Worker", "company": "PKN Orlen"},
            {"job": "Bank Clerk", "company": "PKO Bank Polski"},
            {"job": "Game Developer", "company": "CD Projekt Red"},
            {"job": "Insurance Agent", "company": "PZU"},
            {"job": "Miner", "company": "KGHM"},
            {"job": "Retail Staff", "company": "Biedronka"},
            {"job": "E-commerce Specialist", "company": "Allegro"},
            {"job": "Telecom Technician", "company": "Orange Polska"},
            {"job": "Fashion Retailer", "company": "LPP (Reserved)"},
            {"job": "Software Engineer", "company": "Comarch"}
        ],
        'locations': [
            {"state": "Masovian", "city": "Warsaw", "zip": "00", "streets": ["Krakowskie Przedmiescie", "Nowy Swiat", "Marszalkowska", "Aleje Jerozolimskie"]},
            {"state": "Lesser Poland", "city": "Krakow", "zip": "30", "streets": ["Florianska", "Grodzka", "Rynek Glowny"]},
            {"state": "Lodz", "city": "Lodz", "zip": "90", "streets": ["Piotrkowska", "Mickiewicza", "Kosciuszki"]},
            {"state": "Lower Silesian", "city": "Wroclaw", "zip": "50", "streets": ["Swidnicka", "Olawska", "Rynek"]}
        ]
    },
    'tr': { # TURKEY
        'first': [
            "Mehmet", "Mustafa", "Ahmet", "Ali", "Huseyin", "Hasan", "Ibrahim", "Ismail", "Osman", "Yusuf", "Murat", "Omer",
            "Fatma", "Ayse", "Emine", "Hatice", "Zeynep", "Elif", "Meryem", "Esra", "Ozlem", "Hulya", "Sultan"
        ],
        'last': [
            "Yilmaz", "Kaya", "Demir", "Sahin", "Celik", "Yildiz", "Yildirim", "Ozturk", "Aydin", "Ozdemir", "Arslan", "Dogan", "Kilic", "Aslan", "Cetin"
        ],
        'occupations': [
            {"job": "Automotive Worker", "company": "Ford Otosan"},
            {"job": "Telecom Engineer", "company": "Turkcell"},
            {"job": "Flight Attendant", "company": "Turkish Airlines"},
            {"job": "Refinery Technician", "company": "Tupras"},
            {"job": "Appliance Technician", "company": "Arcelik"},
            {"job": "Banker", "company": "Garanti BBVA"},
            {"job": "Retail Manager", "company": "BIM"},
            {"job": "Defense Engineer", "company": "Aselsan"},
            {"job": "Glass Worker", "company": "Sisecam"},
            {"job": "Steel Worker", "company": "Erdemir"}
        ],
        'locations': [
            {"state": "Istanbul", "city": "Istanbul", "zip": "34", "streets": ["Istiklal Caddesi", "Bagdat Caddesi", "Abdi Ipekci Caddesi", "Nispetiye Caddesi"]},
            {"state": "Ankara", "city": "Ankara", "zip": "06", "streets": ["Ataturk Bulvari", "Tunalı Hilmi Caddesi", "Bahcelievler 7. Cadde"]},
            {"state": "Izmir", "city": "Izmir", "zip": "35", "streets": ["Kibris Sehitleri Caddesi", "Kordon Boyu", "Plevne Bulvari"]},
            {"state": "Antalya", "city": "Antalya", "zip": "07", "streets": ["Isiklar Caddesi", "Gulluk Caddesi", "Konyaalti Caddesi"]}
        ]
    },
    'ru': { # RUSSIA
        'first': [
            "Alexander", "Sergey", "Dmitry", "Andrey", "Alexey", "Maxim", "Ivan", "Mikhail", "Vladimir", "Nikolay", "Evgeny", "Yuri", "Oleg",
            "Elena", "Olga", "Natalia", "Tatiana", "Svetlana", "Irina", "Anna", "Maria", "Julia", "Marina", "Victoria", "Ekaterina"
        ],
        'last': [
            "Ivanov", "Smirnov", "Kuznetsov", "Popov", "Vasiliev", "Petrov", "Sokolov", "Mikhailov", "Novikov", "Fedorov", "Morozov", "Volkov", "Alekseev", "Lebedev"
        ],
        'occupations': [
            {"job": "Gas Engineer", "company": "Gazprom"},
            {"job": "Bank Clerk", "company": "Sberbank"},
            {"job": "Oil Rig Worker", "company": "Rosneft"},
            {"job": "Software Developer", "company": "Yandex"},
            {"job": "Retail Manager", "company": "X5 Retail Group"},
            {"job": "Steel Worker", "company": "Severstal"},
            {"job": "Miner", "company": "Norilsk Nickel"},
            {"job": "Supermarket Staff", "company": "Magnit"},
            {"job": "Telecom Technician", "company": "MTS"},
            {"job": "Banker", "company": "VTB Bank"}
        ],
        'locations': [
            {"state": "Moscow", "city": "Moscow", "zip": "10", "streets": ["Tverskaya Street", "Arbat Street", "Leninsky Prospekt", "Kutuzovsky Prospekt"]},
            {"state": "Saint Petersburg", "city": "Saint Petersburg", "zip": "19", "streets": ["Nevsky Prospekt", "Liteyny Prospekt", "Rubinstein Street"]},
            {"state": "Novosibirsk", "city": "Novosibirsk", "zip": "63", "streets": ["Krasny Prospekt", "Lenina Street", "Vokzalnaya Magistral"]},
            {"state": "Yekaterinburg", "city": "Yekaterinburg", "zip": "62", "streets": ["Lenin Avenue", "Malysheva Street", "Vaynera Street"]}
        ]
    },
    'ua': { # UKRAINE
        'first': [
            "Oleksandr", "Serhiy", "Volodymyr", "Mykola", "Ivan", "Vasyl", "Yuriy", "Dmytro", "Andriy", "Viktor",
            "Oksana", "Tetyana", "Nataliya", "Halyna", "Lyudmyla", "Iryna", "Olena", "Valentyna", "Nadiya", "Svitlana"
        ],
        'last': [
            "Melnyk", "Shevchenko", "Boyko", "Kovalenko", "Bondarenko", "Tkachenko", "Kravchenko", "Koval", "Oliynyk", "Shevchuk", "Polishchuk", "Lysenko"
        ],
        'occupations': [
            {"job": "Software Engineer", "company": "SoftServe"},
            {"job": "Steel Worker", "company": "Metinvest"},
            {"job": "Energy Technician", "company": "DTEK"},
            {"job": "Gas Engineer", "company": "Naftogaz"},
            {"job": "Railway Conductor", "company": "Ukrzaliznytsia"},
            {"job": "Delivery Driver", "company": "Nova Poshta"},
            {"job": "Bank Teller", "company": "PrivatBank"},
            {"job": "Agricultural Worker", "company": "Kernel"},
            {"job": "E-commerce Manager", "company": "Rozetka"},
            {"job": "IT Consultant", "company": "EPAM Ukraine"}
        ],
        'locations': [
            {"state": "Kyiv", "city": "Kyiv", "zip": "01", "streets": ["Khreshchatyk", "Volodymyrska", "Andriyivskyy Descent", "Saksahanskoho"]},
            {"state": "Kharkiv", "city": "Kharkiv", "zip": "61", "streets": ["Sumska", "Pushkinska", "Nauky Avenue"]},
            {"state": "Odesa", "city": "Odesa", "zip": "65", "streets": ["Deribasivska", "Hretska", "Primorsky Boulevard"]},
            {"state": "Lviv", "city": "Lviv", "zip": "79", "streets": ["Svobody Avenue", "Halytska", "Krakivska"]}
        ]
    },

    # ==========================================
    # AMERIKA (THE AMERICAS)
    # ==========================================
    'us': { # USA
        'first': [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Charles", "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Donald",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Margaret", "Betty"
        ],
        'last': [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson"
        ],
        'occupations': [
            {"job": "Software Engineer", "company": "Google"},
            {"job": "Cloud Architect", "company": "Amazon AWS"},
            {"job": "Product Designer", "company": "Apple"},
            {"job": "Investment Banker", "company": "JPMorgan Chase"},
            {"job": "Registered Nurse", "company": "UnitedHealth Group"},
            {"job": "Retail Associate", "company": "Walmart"},
            {"job": "Operations Manager", "company": "FedEx"},
            {"job": "Financial Analyst", "company": "Bank of America"},
            {"job": "Marketing Specialist", "company": "Coca-Cola"},
            {"job": "Data Scientist", "company": "Microsoft"}
        ],
        'locations': [
            {"state": "New York", "city": "New York City", "zip": "100", "streets": ["Broadway", "5th Avenue", "Madison Avenue", "Wall Street", "Park Avenue"]},
            {"state": "California", "city": "Los Angeles", "zip": "900", "streets": ["Sunset Boulevard", "Hollywood Boulevard", "Mulholland Drive", "Rodeo Drive"]},
            {"state": "Illinois", "city": "Chicago", "zip": "606", "streets": ["Michigan Avenue", "State Street", "Lake Shore Drive", "Wacker Drive"]},
            {"state": "Texas", "city": "Houston", "zip": "770", "streets": ["Westheimer Road", "Kirby Drive", "Main Street", "Richmond Avenue"]},
            {"state": "Florida", "city": "Miami", "zip": "331", "streets": ["Ocean Drive", "Collins Avenue", "Brickell Avenue", "Biscayne Boulevard"]}
        ]
    },
    'ca': { # CANADA
        'first': [
            "Liam", "Noah", "William", "Lucas", "Benjamin", "Oliver", "Jack", "Logan", "Ethan", "James",
            "Olivia", "Emma", "Charlotte", "Ava", "Sophia", "Chloe", "Amelia", "Mia", "Lily", "Emily"
        ],
        'last': [
            "Smith", "Brown", "Tremblay", "Martin", "Roy", "Wilson", "Gagnon", "Lee", "Johnson", "MacDonald", "Thompson", "White", "Campbell", "Singh", "Wong"
        ],
        'occupations': [
            {"job": "Bank Manager", "company": "RBC Royal Bank"},
            {"job": "Software Developer", "company": "Shopify"},
            {"job": "Pipeline Engineer", "company": "Enbridge"},
            {"job": "Train Conductor", "company": "CN Railway"},
            {"job": "Financial Advisor", "company": "TD Bank"},
            {"job": "Telecom Technician", "company": "Bell Canada"},
            {"job": "Insurance Broker", "company": "Manulife"},
            {"job": "Retail Manager", "company": "Loblaws"},
            {"job": "Investment Analyst", "company": "Brookfield"},
            {"job": "Civil Servant", "company": "Government of Canada"}
        ],
        'locations': [
            {"state": "Ontario", "city": "Toronto", "zip": "M5", "streets": ["Yonge Street", "Queen Street", "King Street", "Bay Street", "Bloor Street"]},
            {"state": "Quebec", "city": "Montreal", "zip": "H3", "streets": ["Sainte-Catherine Street", "Saint-Laurent Boulevard", "Sherbrooke Street"]},
            {"state": "British Columbia", "city": "Vancouver", "zip": "V6", "streets": ["Robson Street", "Granville Street", "Burrard Street"]},
            {"state": "Alberta", "city": "Calgary", "zip": "T2", "streets": ["Stephen Avenue", "17th Avenue", "Macleod Trail"]}
        ]
    },
    'br': { # BRAZIL
        'first': [
            "Jose", "Joao", "Antonio", "Francisco", "Carlos", "Paulo", "Pedro", "Lucas", "Luiz", "Marcos", "Gabriel", "Rafael", "Daniel",
            "Maria", "Ana", "Francisca", "Antonia", "Adriana", "Juliana", "Marcia", "Fernanda", "Patricia", "Aline", "Camila"
        ],
        'last': [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida"
        ],
        'occupations': [
            {"job": "Petroleum Engineer", "company": "Petrobras"},
            {"job": "Mining Engineer", "company": "Vale"},
            {"job": "Bank Teller", "company": "Itau Unibanco"},
            {"job": "Brewery Worker", "company": "Ambev"},
            {"job": "Bank Manager", "company": "Bradesco"},
            {"job": "Meat Packer", "company": "JBS"},
            {"job": "Retail Associate", "company": "Magazine Luiza"},
            {"job": "Steel Worker", "company": "Gerdau"},
            {"job": "Paper Technician", "company": "Suzano"},
            {"job": "Investment Analyst", "company": "BTG Pactual"}
        ],
        'locations': [
            {"state": "Sao Paulo", "city": "Sao Paulo", "zip": "01", "streets": ["Avenida Paulista", "Rua Augusta", "Avenida Faria Lima", "Rua Oscar Freire"]},
            {"state": "Rio de Janeiro", "city": "Rio de Janeiro", "zip": "20", "streets": ["Avenida Atlantica", "Rua Visconde de Piraja", "Avenida Vieira Souto"]},
            {"state": "Minas Gerais", "city": "Belo Horizonte", "zip": "30", "streets": ["Avenida Afonso Pena", "Avenida do Contorno", "Rua da Bahia"]},
            {"state": "Bahia", "city": "Salvador", "zip": "40", "streets": ["Avenida Sete de Setembro", "Avenida Oceanica", "Rua Chile"]}
        ]
    },

    # ==========================================
    # LAINNYA (OTHERS)
    # ==========================================
    'au': { # AUSTRALIA
        'first': [
            "Oliver", "Noah", "William", "Jack", "Leo", "Lucas", "Thomas", "Henry", "Charlie", "James", "Ethan", "Mason",
            "Charlotte", "Olivia", "Amelia", "Isla", "Mia", "Ava", "Grace", "Willow", "Harper", "Sophie", "Ruby"
        ],
        'last': [
            "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Nguyen", "Johnson", "Martin", "White", "Anderson", "Walker", "Thompson", "Thomas", "Lee"
        ],
        'occupations': [
            {"job": "Bank Manager", "company": "Commonwealth Bank"},
            {"job": "Mining Engineer", "company": "BHP"},
            {"job": "Biotech Researcher", "company": "CSL"},
            {"job": "Financial Advisor", "company": "Westpac"},
            {"job": "Retail Manager", "company": "Woolworths"},
            {"job": "Telecom Technician", "company": "Telstra"},
            {"job": "Investment Banker", "company": "Macquarie Group"},
            {"job": "Civil Engineer", "company": "Transurban"},
            {"job": "Logistics Manager", "company": "Wesfarmers"},
            {"job": "Mining Supervisor", "company": "Rio Tinto"}
        ],
        'locations': [
            {"state": "New South Wales", "city": "Sydney", "zip": "20", "streets": ["George Street", "Pitt Street", "Oxford Street", "Macquarie Street"]},
            {"state": "Victoria", "city": "Melbourne", "zip": "30", "streets": ["Collins Street", "Bourke Street", "Flinders Street", "Chapel Street"]},
            {"state": "Queensland", "city": "Brisbane", "zip": "40", "streets": ["Queen Street", "Adelaide Street", "Ann Street"]},
            {"state": "Western Australia", "city": "Perth", "zip": "60", "streets": ["St Georges Terrace", "Hay Street", "Murray Street"]}
        ]
    },
    'za': { # SOUTH AFRICA
        'first': [
            "Thabo", "Sipho", "Bongani", "Lethabo", "Johan", "Willem", "Liam", "Noah", "Junior", "Minenhle", "Bokamoso",
            "Nthabiseng", "Lerato", "Tshegofatso", "Amahle", "Mia", "Olivia", "Anna", "Lesedi", "Omphile", "Amogelang"
        ],
        'last': [
            "Dlamini", "Nkosi", "Ndlovu", "Khumalo", "Botha", "Van der Merwe", "Naidoo", "Patel", "Smith", "Sithole", "Mokoena", "Molefe", "Jacobs", "Pillay"
        ],
        'occupations': [
            {"job": "Media Specialist", "company": "Naspers"},
            {"job": "Bank Teller", "company": "Standard Bank"},
            {"job": "Chemical Engineer", "company": "Sasol"},
            {"job": "Telecom Engineer", "company": "MTN Group"},
            {"job": "Loan Officer", "company": "Capitec Bank"},
            {"job": "Mining Engineer", "company": "Anglo American"},
            {"job": "Insurance Agent", "company": "Sanlam"},
            {"job": "Retail Manager", "company": "Shoprite"},
            {"job": "Logistics Coordinator", "company": "Bidvest"},
            {"job": "Health Consultant", "company": "Discovery Health"}
        ],
        'locations': [
            {"state": "Gauteng", "city": "Johannesburg", "zip": "20", "streets": ["Mandela Bridge", "Commissioner Street", "Main Street", "Eloff Street"]},
            {"state": "Western Cape", "city": "Cape Town", "zip": "80", "streets": ["Long Street", "Bree Street", "Adderley Street", "Kloof Street"]},
            {"state": "KwaZulu-Natal", "city": "Durban", "zip": "40", "streets": ["Florida Road", "West Street", "Smith Street"]},
            {"state": "Gauteng", "city": "Pretoria", "zip": "00", "streets": ["Church Street", "Paul Kruger Street", "Pretorius Street"]}
        ]
    }
}

def get_romanized_name(country_code):
    """
    Mengembalikan nama yang akurat dan bersih dari karakter aneh
    untuk semua negara yang terdaftar.
    """
    code = country_code.lower()
    if code == 'uk': code = 'gb'
    
    data = NAMES_DB.get(code)
    if not data:
        return None
        
    first = random.choice(data['first'])
    last = random.choice(data['last'])
    return f"{first} {last}"

def get_custom_occupation(country_code):
    """
    Mengembalikan pasangan Job dan Company yang masuk akal.
    Returns: (job_title, company_name)
    """
    code = country_code.lower()
    if code == 'uk': code = 'gb'
    
    data = NAMES_DB.get(code)
    if data and 'occupations' in data:
        occ = random.choice(data['occupations'])
        return occ['job'], occ['company']
    return None, None

def get_custom_location(country_code):
    """
    Mengambil lokasi manual yang valid (City, State, Zip, Street).
    Returns dict: {city, state, zip, street, address}
    """
    code = country_code.lower()
    if code == 'uk': code = 'gb'
    
    data = NAMES_DB.get(code)
    if data and 'locations' in data:
        loc = random.choice(data['locations'])
        
        street_name = random.choice(loc['streets'])
        house_num = random.randint(1, 200)
        
        # Format zip code randomly if it's just a prefix
        zip_code = loc['zip']
        if len(zip_code) <= 3: # Assuming prefix
             zip_code = f"{zip_code}{random.randint(100, 999)}"
        
        address = f"{street_name} No. {house_num}"
        
        return {
            "city": loc['city'],
            "state": loc['state'],
            "zip": zip_code,
            "street": street_name,
            "address": address
        }
    return None