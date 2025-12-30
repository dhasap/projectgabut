import random

# DATABASE MANUAL LENGKAP (NAMA, PEKERJAAN, PERUSAHAAN, LOKASI)
# Format: Latin Characters Only.

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
        'jobs': [
            "Karyawan Swasta", "Pegawai Negeri Sipil (PNS)", "Wiraswasta", "Pedagang", "Mahasiswa", "Pelajar", "Guru", "Dosen", 
            "Dokter Umum", "Perawat", "Bidan", "Apoteker", "Supir", "Driver Ojek Online", "Satpam", "Buruh Pabrik", "Petani", "Nelayan", 
            "Tukang Masak (Koki)", "Pelayan Restoran", "Kasir", "Resepsionis", "Customer Service", "Sales Marketing", "Akuntan", 
            "Staff Administrasi", "Teknisi Komputer", "Programmer", "Desainer Grafis", "Penulis", "Content Creator", "Fotografer", 
            "Mekanik Bengkel", "Tukang Kayu", "Tukang Listrik", "Kuli Bangunan", "Asisten Rumah Tangga", "Ibu Rumah Tangga", "Pensiunan", 
            "TNI / POLRI", "Pengacara", "Notaris", "Konsultan Bisnis", "Manajer Toko", "Kurir Ekspedisi"
        ],
        'companies': [
            "PT Sinar Mas Group", "PT Telkom Indonesia", "PT Pertamina", "PT Gudang Garam Tbk", "PT Bank Central Asia", "PT Astra International", 
            "CV Maju Jaya", "CV Berkah Abadi", "UD Sumber Rejeki", "PT Indofood Sukses Makmur", "PT Unilever Indonesia", "PT Gojek Indonesia", 
            "PT Tokopedia", "PT Bukalapak", "PT Shopee International", "PT Mayora Indah", "PT Kalbe Farma", "PT Adaro Energy", "PT United Tractors",
            "Toko Kelontong Berkah", "Warung Makan Sederhana", "Bengkel Motor Jaya", "Klinik Sehat Sentosa", "Apotek K-24", "Indomaret", "Alfamart"
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
        'jobs': [
            "Software Engineer", "Civil Engineer", "Accountant", "Teacher", "Lecturer", "Doctor", "Nurse", "Pharmacist", "Sales Executive", "Marketing Manager", "Business Analyst",
            "Human Resources Executive", "Graphic Designer", "Technician", "Mechanic", "Driver", "Grab Driver", "Security Guard", "Factory Worker", "Chef", "Waiter", "Student", "Freelancer"
        ],
        'companies': [
            "Petronas", "Maybank", "CIMB Group", "Public Bank", "Tenaga Nasional Berhad", "Sime Darby", "Axiata Group", "Maxis", "Digi", "Celcom", "AirAsia", "Genting Group",
            "IOI Corporation", "Sunway Group", "YTL Corporation", "Top Glove", "Hartalega", "Hong Leong Bank", "RHB Bank", "AmBank"
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
        'jobs': [
            "Financial Analyst", "Data Scientist", "Software Developer", "Project Manager", "Operations Manager", "Accountant", "Auditor", "Marketing Executive", "Sales Manager",
            "Teacher", "Nurse", "Doctor", "Civil Servant", "Engineer", "Architect", "Consultant", "Research Analyst", "Banker", "Trader", "HR Manager"
        ],
        'companies': [
            "DBS Bank", "OCBC Bank", "UOB", "Singtel", "Singapore Airlines", "CapitaLand", "Keppel Corporation", "Wilmar International", "Sembcorp", "ST Engineering",
            "ComfortDelGro", "SATS", "Venture Corporation", "Genting Singapore", "City Developments Limited", "Jardine Cycle & Carriage", "Sea Limited", "Grab", "Razer"
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
        'jobs': [
            "Call Center Agent", "Virtual Assistant", "Nurse", "Engineer", "Teacher", "Accountant", "IT Specialist", "Sales Representative", "Customer Service Representative",
            "Administrative Assistant", "Driver", "Security Guard", "Construction Worker", "Farmer", "Fisherman", "Domestic Helper", "Online Seller", "Freelancer"
        ],
        'companies': [
            "SM Investments", "Ayala Corporation", "BDO Unibank", "JG Summit Holdings", "PLDT", "Globe Telecom", "Jollibee Foods Corp", "San Miguel Corporation",
            "Metrobank", "Bank of the Philippine Islands", "Meralco", "Aboitiz Equity Ventures", "International Container Terminal Services", "Megaworld", "Robinsons Land"
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
        'jobs': [
            "Office Worker", "Teacher", "Government Officer", "Merchant", "Farmer", "Doctor", "Nurse", "Engineer", "Hotel Staff", "Tour Guide", "Driver", "Factory Worker",
            "Freelancer", "Business Owner", "Chef", "Monk", "Student", "Police Officer"
        ],
        'companies': [
            "PTT Public Company", "Siam Cement Group", "CP All", "Advanced Info Service", "Airports of Thailand", "Kasikornbank", "Bangkok Bank", "Siam Commercial Bank",
            "Charoen Pokphand Foods", "Thai Beverage", "Central Pattana", "True Corporation", "Minor International", "Indorama Ventures"
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
        'jobs': [
            "Software Engineer", "Teacher", "Accountant", "Office Staff", "Worker", "Farmer", "Driver", "Salesperson", "Doctor", "Nurse", "Translator", "Tour Guide",
            "Shop Owner", "Freelancer", "Student", "Construction Worker", "Security Guard"
        ],
        'companies': [
            "Vingroup", "Vinamilk", "Vietcombank", "Hoa Phat Group", "Masan Group", "PetroVietnam", "Viettel", "FPT Corporation", "Vietnam Airlines",
            "Techcombank", "VPBank", "BIDV", "Novaland", "Mobile World Investment", "Sabeco"
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
        'jobs': [
            "Salaryman", "Office Lady", "Software Engineer", "Teacher", "Civil Servant", "Nurse", "Caregiver", "Sales Representative", "Factory Worker", "Researcher",
            "Designer", "Artist", "Musician", "Student", "Part-time Worker", "Convenience Store Staff", "Driver"
        ],
        'companies': [
            "Toyota Motor Corp", "Sony Group", "Nintendo Co Ltd", "SoftBank Group", "Honda Motor Co", "Mitsubishi UFJ Financial", "Sumitomo Mitsui", "Hitachi Ltd",
            "Panasonic Corp", "Fast Retailing (Uniqlo)", "Seven & i Holdings", "KDDI Corp", "Japan Tobacco", "Canon Inc", "Bridgestone Corp"
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
        'jobs': [
            "Office Worker", "Teacher", "Civil Servant", "Engineer", "Nurse", "Doctor", "Pharmacist", "Designer", "Programmer", "Salesperson", "Student",
            "Freelancer", "Researcher", "Business Owner", "Actor/Actress", "Singer", "Model"
        ],
        'companies': [
            "Samsung Electronics", "SK Hynix", "Hyundai Motor", "LG Electronics", "POSCO", "Kia Corp", "Naver Corp", "Kakao Corp", "Samsung Biologics",
            "Shinhan Financial", "KB Financial", "LG Chem", "Samsung SDI", "Celltrion", "Coupang"
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
        'jobs': [
            "Factory Worker", "Office Clerk", "Engineer", "Teacher", "Salesperson", "Driver", "Construction Worker", "Farmer", "IT Specialist", "Accountant",
            "Doctor", "Nurse", "Student", "Civil Servant", "Business Owner", "E-commerce Seller"
        ],
        'companies': [
            "Tencent Holdings", "Alibaba Group", "ICBC", "China Construction Bank", "PetroChina", "China Mobile", "Agricultural Bank of China", "Bank of China",
            "Kweichow Moutai", "Ping An Insurance", "Meituan", "JD.com", "Xiaomi Corp", "BYD Company", "Baidu"
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
        'jobs': [
            "Software Engineer", "IT Consultant", "Data Analyst", "Call Center Agent", "Teacher", "Professor", "Doctor", "Chartered Accountant", "Civil Engineer",
            "Government Officer", "Banker", "Sales Manager", "Business Owner", "Farmer", "Driver", "Student"
        ],
        'companies': [
            "Reliance Industries", "Tata Consultancy Services", "HDFC Bank", "Infosys", "ICICI Bank", "Hindustan Unilever", "State Bank of India", "Bharti Airtel",
            "Bajaj Finance", "Kotak Mahindra Bank", "Wipro", "HCL Technologies", "Asian Paints", "ITC Limited", "Larsen & Toubro"
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
        'jobs': [
            "Retail Manager", "Project Manager", "Software Developer", "Accountant", "Nurse", "Teacher", "Administrator", "Sales Executive", "Customer Service Advisor",
            "Driver", "Care Worker", "Electrician", "Plumber", "Carpenter", "Builder", "Cleaner", "Receptionist"
        ],
        'companies': [
            "Unilever", "AstraZeneca", "HSBC Holdings", "BP", "Royal Dutch Shell", "GlaxoSmithKline", "Diageo", "British American Tobacco", "Rio Tinto", "Vodafone Group",
            "Lloyds Banking Group", "Barclays", "Prudential", "Reckitt Benckiser", "Tesco", "Sainsbury's"
        ],
        'locations': [
            {"state": "London", "city": "London", "zip": "SW1", "streets": ["Oxford Street", "Regent Street", "Baker Street", "Piccadilly", "King's Road"]},
            {"state": "Greater Manchester", "city": "Manchester", "zip": "M1", "streets": ["Deansgate", "Market Street", "Oxford Road"]},
            {"state": "West Midlands", "city": "Birmingham", "zip": "B1", "streets": ["New Street", "Broad Street", "Corporation Street"]},
            {"state": "Scotland", "city": "Edinburgh", "zip": "EH1", "streets": ["Royal Mile", "Princes Street", "George Street"]}
        ]
    },
    'uk': { # ALIAS UK
        'first': ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "George"],
        'last': ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Johnson"],
        'jobs': ["Retail Manager", "Software Developer", "Accountant", "Nurse", "Teacher", "Sales Executive", "Driver", "Electrician"],
        'companies': ["Unilever", "AstraZeneca", "HSBC", "BP", "Shell", "GSK", "Vodafone", "Tesco"],
        'locations': [{"state": "London", "city": "London", "zip": "SW1", "streets": ["Oxford Street", "Regent Street"]}]
    },
    'de': { # GERMANY
        'first': [
            "Hans", "Klaus", "Thomas", "Michael", "Stefan", "Andreas", "Markus", "Christian", "Martin", "Peter", "Uwe", "Jorg", "Frank",
            "Ursula", "Monika", "Petra", "Sabine", "Karin", "Renate", "Helga", "Brigitte", "Claudia", "Susanne", "Julia", "Maria"
        ],
        'last': [
            "Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann", "Schafer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schroder"
        ],
        'jobs': [
            "Ingenieur", "Softwareentwickler", "Lehrer", "Arzt", "Krankenschwester", "Verkaeufer", "Bueroangestellter", "Handwerker", "Mechatroniker", "Elektriker",
            "Architekt", "Anwalt", "Polizist", "Student", "Rentner", "Geschaeftsfuehrer"
        ],
        'companies': [
            "Volkswagen AG", "Daimler AG", "Allianz SE", "BMW Group", "Siemens AG", "Bosch Group", "Deutsche Telekom", "BASF SE", "Bayer AG", "Adidas AG",
            "SAP SE", "Continental AG", "Lufthansa Group", "Deutsche Bank", "Deutsche Post DHL", "E.ON SE"
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
        'jobs': [
            "Ingenieur", "Developpeur Logiciel", "Enseignant", "Medecin", "Infirmiere", "Vendeur", "Employe de bureau", "Ouvrier", "Technicien", "Chauffeur",
            "Avocat", "Architecte", "Comptable", "Etudiant", "Retraite", "Cadre commercial"
        ],
        'companies': [
            "LVMH", "TotalEnergies", "L'Oreal", "Sanofi", "Airbus", "BNP Paribas", "AXA", "Schneider Electric", "Kering", "Hermes International",
            "Vinci", "Danone", "Air Liquide", "Orange", "Renault", "Peugeot (Stellantis)", "Carrefour"
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
        'jobs': [
            "Ingegnere", "Sviluppatore Software", "Insegnante", "Medico", "Infermiere", "Commesso", "Impiegato", "Operaio", "Tecnico", "Autista",
            "Avvocato", "Architetto", "Commercialista", "Studente", "Pensionato", "Manager", "Cuoco", "Cameriere"
        ],
        'companies': [
            "Enel", "Eni", "Intesa Sanpaolo", "Ferrari", "UniCredit", "Assicurazioni Generali", "Stellantis", "Luxottica", "Atlantia", "Snam",
            "Telecom Italia", "Leonardo", "Prada", "Pirelli", "Moncler", "Ferrero"
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
        'jobs': [
            "Ingeniero", "Desarrollador de Software", "Profesor", "Medico", "Enfermera", "Vendedor", "Administrativo", "Obrero", "Tecnico", "Conductor",
            "Abogado", "Arquitecto", "Contador", "Estudiante", "Jubilado", "Gerente", "Cocinero", "Camarero"
        ],
        'companies': [
            "Inditex (Zara)", "Iberdrola", "Banco Santander", "BBVA", "Amadeus IT Group", "Telefonica", "Repsol", "CaixaBank", "Cellnex Telecom", "Ferrovial",
            "Naturgy", "Aena", "Endesa", "Red Electrica", "Mapfre"
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
        'jobs': [
            "Ingenieur", "Softwareontwikkelaar", "Leraar", "Arts", "Verpleegkundige", "Verkoper", "Administratief medewerker", "Arbeider", "Technicus", "Chauffeur",
            "Advocaat", "Architect", "Accountant", "Student", "Gepensioneerde", "Manager"
        ],
        'companies': [
            "ASML Holding", "Royal Dutch Shell", "Unilever", "Prosus", "Adyen", "ING Group", "Philips", "Ahold Delhaize", "Heineken", "AkzoNobel",
            "DSM", "Wolters Kluwer", "Randstad", "KPN", "NN Group"
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
        'jobs': [
            "Inzynier", "Programista", "Nauczyciel", "Lekarz", "Pielegniarka", "Sprzedawca", "Pracownik biurowy", "Robotnik", "Technik", "Kierowca",
            "Prawnik", "Architekt", "Ksiegowy", "Student", "Emeryt", "Kierownik"
        ],
        'companies': [
            "PKN Orlen", "PKO Bank Polski", "PGNiG", "PZU", "KGHM Polska Miedz", "Bank Pekao", "Dino Polska", "CD Projekt", "LPP", "Cyfrowy Polsat",
            "Santander Bank Polska", "ING Bank Slaski", "Allegro", "Tauron Polska Energia", "Orange Polska"
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
        'jobs': [
            "Muhendis", "Yazilimci", "Ogretmen", "Doktor", "Hemsire", "Satis Elemani", "Memur", "Isci", "Teknisyen", "Sofor",
            "Avukat", "Mimar", "Muhasebeci", "Ogrenci", "Emekli", "Yonetici", "Esnaf"
        ],
        'companies': [
            "Koc Holding", "Sabanci Holding", "Turkcell", "Turk Hava Yollari", "Ford Otosan", "Tupras", "BIM Birlesik Magazalar", "Garanti BBVA", "Akbank", "Isbank",
            "Aselsan", "Eregli Demir Celik", "Arcelik", "Vestel", "Sise Cam"
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
        'jobs': [
            "Engineer", "Software Developer", "Teacher", "Doctor", "Nurse", "Sales Manager", "Office Manager", "Worker", "Technician", "Driver",
            "Lawyer", "Accountant", "Student", "Pensioner", "Business Owner", "Security Guard"
        ],
        'companies': [
            "Gazprom", "Sberbank", "Rosneft", "Lukoil", "Novatek", "Yandex", "Norilsk Nickel", "Polyus", "Tatneft", "Surgutneftegas",
            "VTB Bank", "Severstal", "NLMK", "X5 Retail Group", "Magnit"
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
        'jobs': [
            "Engineer", "IT Specialist", "Teacher", "Doctor", "Nurse", "Salesperson", "Office Manager", "Worker", "Technician", "Driver",
            "Lawyer", "Accountant", "Student", "Freelancer", "Business Owner"
        ],
        'companies': [
            "Metinvest", "DTEK", "Naftogaz", "Kernel", "MHP", "Ferrexpo", "PrivatBank", "Oschadbank", "Ukrzaliznytsia", "Energoatom",
            "Nova Poshta", "Rozetka", "SoftServe", "EPAM Systems"
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
        'jobs': [
            "Software Engineer", "Registered Nurse", "Teacher", "Project Manager", "Sales Representative", "Account Manager", "Office Manager", "Operations Manager",
            "Supervisor", "Administrative Assistant", "Customer Service Rep", "Driver", "Technician", "Electrician", "Mechanic", "Construction Worker", "Police Officer"
        ],
        'companies': [
            "Apple Inc.", "Microsoft Corp", "Amazon.com Inc.", "Alphabet Inc. (Google)", "Facebook (Meta)", "Tesla Inc.", "Berkshire Hathaway", "NVIDIA Corp",
            "JPMorgan Chase", "Johnson & Johnson", "Visa Inc.", "UnitedHealth Group", "Walmart Inc.", "Procter & Gamble", "Bank of America", "Mastercard"
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
        'jobs': [
            "Software Engineer", "Nurse", "Teacher", "Sales Associate", "Administrative Assistant", "Project Manager", "Accountant", "Customer Service Rep",
            "Driver", "Construction Worker", "Electrician", "Plumber", "Mechanic", "Chef", "Server"
        ],
        'companies': [
            "Royal Bank of Canada", "Toronto-Dominion Bank", "Shopify", "Enbridge", "Canadian National Railway", "Bank of Nova Scotia", "Brookfield Asset Management",
            "Bank of Montreal", "TC Energy", "Canadian Pacific Railway", "Manulife Financial", "BCE Inc. (Bell)", "Suncor Energy", "Alimentation Couche-Tard"
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
        'jobs': [
            "Engenheiro", "Desenvolvedor de Software", "Professor", "Medico", "Enfermeira", "Vendedor", "Auxiliar Administrativo", "Trabalhador", "Tecnico", "Motorista",
            "Advogado", "Arquiteto", "Contador", "Estudante", "Aposentado", "Gerente", "Seguranca"
        ],
        'companies': [
            "Petrobras", "Vale S.A.", "Itau Unibanco", "Banco Bradesco", "Ambev", "Banco do Brasil", "WEG S.A.", "Magazine Luiza", "B3 S.A.", "JBS S.A.",
            "Suzano", "Gerdau", "Eletrobras", "Localiza", "BTG Pactual"
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
        'jobs': [
            "Software Engineer", "Nurse", "Teacher", "Project Manager", "Accountant", "Electrician", "Plumber", "Carpenter", "Builder", "Sales Assistant",
            "Administrative Assistant", "Chef", "Barista", "Driver", "Cleaner", "Mining Engineer"
        ],
        'companies': [
            "Commonwealth Bank", "BHP Group", "CSL Limited", "Westpac Banking Corp", "National Australia Bank", "ANZ Banking Group", "Wesfarmers", "Macquarie Group",
            "Woolworths Group", "Rio Tinto", "Telstra", "Transurban Group", "Goodman Group", "Fortescue Metals Group"
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
        'jobs': [
            "Software Developer", "Engineer", "Teacher", "Nurse", "Sales Consultant", "Administrator", "Driver", "Security Guard", "Miner", "Farmer",
            "Accountant", "Lawyer", "Doctor", "Student", "Entrepreneur", "Domestic Worker"
        ],
        'companies': [
            "Naspers", "FirstRand", "Standard Bank Group", "Sasol", "MTN Group", "Vodacom Group", "Capitec Bank", "Anglo American Platinum", "Gold Fields",
            "Sanlam", "Absa Group", "Shoprite Holdings", "Bidvest Group", "Discovery Limited"
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

def get_custom_job(country_code):
    """Mengambil pekerjaan custom jika tersedia."""
    code = country_code.lower()
    if code == 'uk': code = 'gb'
    
    data = NAMES_DB.get(code)
    if data and 'jobs' in data:
        return random.choice(data['jobs'])
    return None

def get_custom_company(country_code):
    """Mengambil nama perusahaan custom jika tersedia."""
    code = country_code.lower()
    if code == 'uk': code = 'gb'
    
    data = NAMES_DB.get(code)
    if data and 'companies' in data:
        return random.choice(data['companies'])
    return None

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
