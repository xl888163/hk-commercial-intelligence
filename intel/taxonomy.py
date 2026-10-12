"""Keyword taxonomy: sectors, Hong Kong areas, buildings and venues.

Edit these lists to tune classification. Everything here is used only to
*label* items that were actually found in a source - nothing is generated.
"""
import re

# --- Sectors -------------------------------------------------------------
# Order = priority when picking the primary sector.
SECTORS = [
    ("Data Centre", r"data[- ]?cent(?:er|re)s?|colocation|hyperscal|\bIDC\b|數據中心|資料中心|數據園"),
    ("Security & Safety", r"\bsecurity\b|safety|\bfire\b|surveillance|\bCCTV\b|access control|\balarms?\b|interpol|police|law enforcement|保安|消防|監控|安防"),
    ("Infrastructure & Construction", r"infrastructure|construction|engineering|contractor|northern metropolis|railway|\bMTR\b|bridge|land sale|\btenders?\b|\bsites?\b|\bplots?\b|redevelop|property development|architect|基建|建造|工程|地皮|用地|招標|北部都會區|重建"),
    ("AI & Technology", r"(?-i:\bAI\b)|artificial intelligence|\btech\b|technolog|fintech|digital|\bcyber|electronic|software|semiconductor|robot|innovation|start-?up|\bICT\b|smart home|smart city|gaming|esports|人工智能|科技|機械人|機器人|金融科技|創科"),
    ("Logistics & Supply Chain", r"logistic|supply chain|warehous|\bcargo\b|freight|shipping|\bports?\b|container terminal|cold storage|courier|maritime|terminal expo|\bterminals?\b|物流|貨倉|倉庫|貨運|港口|供應鏈|冷庫"),
    ("Luxury & HNW Goods", r"luxury|jewel(?:le)?ry|\bwatch(?:es)?\b|diamond|\bgems?\b|\bgold\b|\bwine\b|art basel|art fair|connoisseur|family office|private bank|\byachts?\b|antique|collectible|珠寶|鐘錶|名錶|奢侈|藝術品|家族辦公室|豪宅"),
    ("Retail & Consumer", r"retail|\bshops?\b|\bstores?\b|\bmalls?\b|shopping|consumer|fashion|lifestyle|cosmetic|beauty|supermarket|outlet|零售|商場|商舖|舖位|旗艦店|美妝|wedding|homex|houseware|mega showcase|creators"),
    ("Manufacturing & Consumer Goods", r"\btoys?\b|games fair|gifts?\b|premium|\bbaby\b|optical|stationery|printing|packaging|printpack|cosmo|mega show|electronics|lighting|玩具|禮品|印刷|包裝"),
    ("Finance & Professional Services", r"\bbanks?\b|banking|insur|\bfunds?\b|asset manag|securities|investment|financ|hedge|law firm|legal|arbitration|accounting|consult|\bIPO\b|brokerage|prudential|\bAIA\b|\bHSBC\b|standard chartered|citi(?:bank|group)?\b|jpmorgan|goldman|morgan stanley|\bUBS\b|blackrock|manulife|\bAXA\b|sun life|\bFWD\b|susquehanna|citadel|millennium management|\bZA Bank\b|銀行|保險|基金|證券|律師|投資|會計"),
    ("Healthcare & Life Sciences", r"health|medical|hospital|pharma|biotech|life science|clinic|longevity|medicine|cardio|respirat|immunolog|endocrin|diabet|clinical|gerontech|醫院|中醫|醫療|生物科技|藥"),
    ("Energy & Environment", r"\benergy\b|environment|\bgreen\b|\beco\b|sustainab|\bESG\b|solar|hydrogen|carbon|lighting|能源|環保|綠色|減碳"),
    ("Hospitality, Food & Tourism", r"\bhotels?\b|hospitality|\bfood\b|\bF&B\b|restaurant|touris|travel|catering|酒店|餐飲|旅遊"),
    ("Education & Government", r"education|school|universit|government|public sector|consul|教育|大學|政府"),
    ("Facility Management & Real Estate", r"facilit(?:y|ies) manag|property manag|real estate|\bproperty\b|properties|landlord|developer|\bREIT\b|office space|grade a|物業|地產|寫字樓|甲廈|設施管理"),
]
SECTOR_NAMES = [s for s, _ in SECTORS] + ["Other"]
_SECTOR_RX = [(name, re.compile(rx, re.I)) for name, rx in SECTORS]


def sectors_for(text):
    hits = [name for name, rx in _SECTOR_RX if rx.search(text or "")]
    return hits or ["Other"]


# --- Areas -----------------------------------------------------------------
AREA_UNSTATED = "Hong Kong (district not stated)"
AREAS = [
    ("Central / Sheung Wan", ["Central", "Sheung Wan", "SoHo", "中環", "上環"]),
    ("Admiralty", ["Admiralty", "金鐘"]),
    ("Wan Chai", ["Wan Chai", "Wanchai", "灣仔"]),
    ("Causeway Bay", ["Causeway Bay", "銅鑼灣"]),
    ("Island East (North Point / Quarry Bay / Taikoo)", ["Quarry Bay", "North Point", "Taikoo", "Tai Koo", "Island East", "Chai Wan", "鰂魚涌", "北角", "太古", "柴灣", "港島東"]),
    ("Southern (Wong Chuk Hang / Aberdeen / Cyberport)", ["Wong Chuk Hang", "Aberdeen", "Cyberport", "Ap Lei Chau", "Pok Fu Lam", "黃竹坑", "香港仔", "數碼港", "鴨脷洲"]),
    ("Tsim Sha Tsui / West Kowloon", ["Tsim Sha Tsui", "TST", "West Kowloon", "Austin", "尖沙咀", "西九"]),
    ("Mong Kok / Yau Ma Tei", ["Mong Kok", "Mongkok", "Yau Ma Tei", "Jordan", "旺角", "油麻地", "佐敦"]),
    ("Kowloon East (Kwun Tong / Kowloon Bay / Kai Tak)", ["Kwun Tong", "Kowloon Bay", "Kai Tak", "Kowloon East", "Ngau Tau Kok", "San Po Kong", "觀塘", "九龍灣", "啟德", "九龍東", "新蒲崗"]),
    ("Hung Hom / Kowloon City", ["Hung Hom", "To Kwa Wan", "Kowloon City", "Kowloon Tong", "紅磡", "土瓜灣", "九龍城", "九龍塘"]),
    ("Cheung Sha Wan / Lai Chi Kok", ["Cheung Sha Wan", "Lai Chi Kok", "Sham Shui Po", "長沙灣", "荔枝角", "深水埗"]),
    ("Kwai Tsing / Tsuen Wan", ["Kwai Chung", "Tsing Yi", "Tsuen Wan", "Kwai Tsing", "葵涌", "青衣", "荃灣", "葵青"]),
    ("Sha Tin / Tai Po (incl. Science Park)", ["Sha Tin", "Shatin", "Science Park", "Tai Po", "Fo Tan", "Ma On Shan", "沙田", "科學園", "大埔", "火炭"]),
    ("Tseung Kwan O / Sai Kung", ["Tseung Kwan O", "TKO", "Sai Kung", "Clear Water Bay", "將軍澳", "西貢"]),
    ("Lantau / Airport", ["Chek Lap Kok", "Tung Chung", "Lantau", "SKYCITY", "11 SKIES", "Hong Kong International Airport", "HKIA", "Airport City", "機場", "東涌", "大嶼山", "赤鱲角"]),
    ("Northern Metropolis / NT North-West", ["Northern Metropolis", "San Tin", "Kwu Tung", "Hung Shui Kiu", "Lok Ma Chau", "Yuen Long", "Tuen Mun", "Fanling", "Sheung Shui", "Tin Shui Wai", "北部都會區", "新田", "古洞", "洪水橋", "落馬洲", "元朗", "屯門", "粉嶺", "上水", "天水圍"]),
    ("Online / Virtual", ["Webinar", "Virtual", "Online", "網上"]),
]
AREA_NAMES = [a for a, _ in AREAS] + [AREA_UNSTATED]

# Buildings and venues -> area (matched case-insensitively as whole phrases).
BUILDINGS = {
    "Central / Sheung Wan": ["International Finance Centre", "IFC", "One IFC", "Two IFC", "Exchange Square", "The Henderson", "Cheung Kong Center II", "Cheung Kong Center", "長江二期", "長江中心", "長實中心", "Jardine House", "AIA Central", "The Landmark", "Alexandra House", "Chater House", "Prince's Building", "York House", "Gloucester Tower", "Edinburgh Tower", "Champion Tower", "Bank of China Tower", "HSBC Main Building", "Nine Queen's Road", "LHT Tower", "Central Tower", "World-Wide House", "The Center", "Infinitus Plaza", "COSCO Tower", "Shun Tak Centre", "Four Seasons", "Mandarin Oriental", "Hong Kong Club", "國際金融中心", "國金", "交易廣場", "長江集團中心", "置地廣場", "怡和大廈", "中環中心", "恒基"],
    "Admiralty": ["Pacific Place", "One Pacific Place", "Two Pacific Place", "Three Pacific Place", "Lippo Centre", "Admiralty Centre", "British Consulate", "Bank of America Tower", "美銀中心", "Far East Finance Centre", "United Centre", "CITIC Tower", "Conrad", "JW Marriott", "Island Shangri-La", "太古廣場", "力寶中心", "統一中心", "中信大廈"],
    "Wan Chai": ["Hong Kong Convention and Exhibition Centre", "HKCEC", "Central Plaza", "Hopewell Centre", "Shui On Centre", "瑞安中心", "Sun Hung Kai Centre", "China Resources Building", "Great Eagle Centre", "Harbour Centre", "The Hennessy", "Grand Hyatt", "Renaissance Harbour View", "Hotel Indigo", "會展", "會議展覽中心", "中環廣場", "合和中心", "新鴻基中心", "華潤大廈"],
    "Causeway Bay": ["Lee Garden", "利園八期", "利園8期", "One Causeway Bay", "Lee Garden One", "Lee Garden Two", "Lee Garden Three", "Lee Garden Eight", "Hysan Place", "Times Square", "World Trade Centre", "Sino Plaza", "Lee Gardens", "利園", "希慎廣場", "時代廣場", "世貿中心"],
    "Island East (North Point / Quarry Bay / Taikoo)": ["Taikoo Place", "One Taikoo Place", "Two Taikoo Place", "Dorset House", "Lincoln House", "One Island East", "Oxford House", "Cityplaza", "Devon House", "Cambridge House", "PCCW Tower", "Harbour East", "太古坊", "港島東中心", "太古城中心"],
    "Southern (Wong Chuk Hang / Aberdeen / Cyberport)": ["The Southside", "Ocean Park", "One Island South", "Ocean Park Marriott"],
    "Tsim Sha Tsui / West Kowloon": ["International Commerce Centre", "ICC", "International Gateway Centre", "IGC", "環球匯", "K11 Atelier", "K11 Musea", "Harbour City", "Ocean Centre", "The Gateway", "Victoria Dockside", "World Commerce Centre", "China Hong Kong City", "Rosewood", "The Peninsula", "Kowloon Shangri-La", "Hong Kong Cultural Centre", "Ritz-Carlton", "Regent Hong Kong", "InterContinental Grand Stanford", "Hyatt Regency Tsim Sha Tsui", "The Langham", "M+", "Xiqu Centre", "環球貿易廣場", "海港城", "海洋中心"],
    "Mong Kok / Yau Ma Tei": ["Langham Place", "Cordis", "MOKO", "Grand Century Place", "朗豪坊"],
    "Kowloon East (Kwun Tong / Kowloon Bay / Kai Tak)": ["Manulife Financial Centre", "One Bay East", "Two Bay East", "Millennium City", "Landmark East", "AIRSIDE", "Kai Tak Sports Park", "Kowloon Bay International Trade & Exhibition Centre", "KITEC", "Star Hall", "Megabox", "Enterprise Square", "The Quayside", "Exchange Tower", "Kerry Hotel", "宏利金融中心", "創紀之城", "九展", "啟德體育園"],
    "Hung Hom / Kowloon City": ["One Harbour Gate", "Two Harbour Gate", "Harbourfront", "Hong Kong Polytechnic University", "PolyU", "Hong Kong Coliseum", "InnoCentre", "海濱廣場", "理工大學"],
    "Cheung Sha Wan / Lai Chi Kok": ["D2 Place", "The Globe", "Billion Centre", "Kowloon Commerce Centre"],
    "Kwai Tsing / Tsuen Wan": ["Kwai Chung Container Terminals", "Hongkong International Terminals", "Kwai Tsing Container Terminals", "ATL Logistics Centre", "Asia Logistics Hub", "Nina Tower", "Mapletree Logistics Hub", "亞洲貨運中心", "如心廣場"],
    "Sha Tin / Tai Po (incl. Science Park)": ["Hong Kong Science Park", "Science Park", "New Town Plaza", "Hong Kong Heritage Museum", "科學園", "新城市廣場"],
    "Tseung Kwan O / Sai Kung": ["Tseung Kwan O Industrial Estate", "TKO InnoPark", "將軍澳工業邨"],
    "Lantau / Airport": ["AsiaWorld-Expo", "AsiaWorld-Arena", "SKYCITY", "11 SKIES", "Cathay City", "Airport Cargo", "Hong Kong International Airport", "亞洲國際博覽館", "博覽館"],
}

_WORD = r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])"


def _compile(alias):
    if alias == "Central":
        return re.compile(r"(?<![A-Za-z])Central(?!\s+(?:Asia|Europe|America|bank|government|Kowloon|Plaza|Tower|Library|Police|Market))")
    if re.search(r"[\u4e00-\u9fff]", alias):
        return re.compile(re.escape(alias))
    if alias.isupper() and len(alias) <= 5:   # IFC, ICC, TST... case-sensitive
        return re.compile(_WORD % re.escape(alias))
    return re.compile(_WORD % re.escape(alias), re.I)


_BUILDING_RX = sorted(
    ((n, area, _compile(n)) for area, names in BUILDINGS.items() for n in names),
    key=lambda t: len(t[0]), reverse=True)
_AREA_RX = [(area, _compile(a)) for area, aliases in AREAS for a in aliases]


CANON = {
    "國際金融中心": "IFC", "國金": "IFC", "One IFC": "IFC", "Two IFC": "IFC", "International Finance Centre": "IFC",
    "交易廣場": "Exchange Square", "長江集團中心": "Cheung Kong Center", "長江中心": "Cheung Kong Center",
    "長實中心": "Cheung Kong Center", "置地廣場": "The Landmark", "怡和大廈": "Jardine House",
    "太古廣場": "Pacific Place", "力寶中心": "Lippo Centre", "統一中心": "United Centre", "中信大廈": "CITIC Tower",
    "會展": "HKCEC", "會議展覽中心": "HKCEC", "Hong Kong Convention and Exhibition Centre": "HKCEC",
    "中環廣場": "Central Plaza", "合和中心": "Hopewell Centre", "新鴻基中心": "Sun Hung Kai Centre", "華潤大廈": "China Resources Building",
    "利園": "Lee Garden", "利園八期": "Lee Garden Eight", "利園8期": "Lee Garden Eight", "Lee Gardens": "Lee Garden",
    "希慎廣場": "Hysan Place", "時代廣場": "Times Square", "世貿中心": "World Trade Centre",
    "太古坊": "Taikoo Place", "One Taikoo Place": "Taikoo Place", "Two Taikoo Place": "Taikoo Place",
    "港島東中心": "One Island East", "太古城中心": "Cityplaza",
    "環球貿易廣場": "ICC", "International Commerce Centre": "ICC", "環球匯": "IGC", "International Gateway Centre": "IGC",
    "海港城": "Harbour City", "海洋中心": "Ocean Centre", "朗豪坊": "Langham Place",
    "宏利金融中心": "Manulife Financial Centre", "創紀之城": "Millennium City", "九展": "KITEC",
    "Kowloon Bay International Trade & Exhibition Centre": "KITEC", "啟德體育園": "Kai Tak Sports Park",
    "海濱廣場": "Harbourfront", "理工大學": "PolyU", "Hong Kong Polytechnic University": "PolyU",
    "亞洲貨運中心": "ATL Logistics Centre", "如心廣場": "Nina Tower", "科學園": "Hong Kong Science Park",
    "Science Park": "Hong Kong Science Park", "新城市廣場": "New Town Plaza", "將軍澳工業邨": "Tseung Kwan O Industrial Estate",
    "亞洲國際博覽館": "AsiaWorld-Expo", "博覽館": "AsiaWorld-Expo", "Cheung Kong Center II": "Cheung Kong Center II", "長江二期": "Cheung Kong Center II", "美銀中心": "Bank of America Tower", "瑞安中心": "Shui On Centre",
}


def building_for(text):
    """Return (building, area) for the first known building named in text."""
    for name, area, rx in _BUILDING_RX:
        if rx.search(text or ""):
            return CANON.get(name, name), area
    return None, None


def area_for(text):
    """Area from a known building/venue (most specific), else a district name."""
    text = text or ""
    _, area = building_for(text)
    if area:
        return area
    best = None
    for area, rx in _AREA_RX:          # earliest-mentioned district wins
        m = rx.search(text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), area)
    return best[1] if best else None


# Places that indicate an item is NOT about Hong Kong (used to drop noise).
NON_HK = re.compile(
    r"Singapore|Shanghai|Beijing|Shenzhen|Guangzhou|Macau|Macao|Taipei|Taiwan|Tokyo|Seoul|Sydney|Melbourne|"
    r"London|New York|Dubai|Mumbai|India|Japan|Korea|Australia|Vietnam|Malaysia|Thailand|Indonesia|"
    r"Santa Barbara|Texas|California|Europe|Vienna|Frankfurt|Kuala Lumpur|Egypt|Africa|Nordic|Xiamen|Hangzhou|Lille|Paris|France|Germany|"
    r"Canada|Saudi|Riyadh|Abu Dhabi|Ginza|Upper East Coast|China’s|China's|mainland|Philippines|Manila|Huanggang|皇崗|"
    r"新加坡|上海|北京|深圳|廣州|澳門|台北|台灣|臺灣|台中|高雄|日本|韓國|東京|倫敦|紐約|杜拜",
    re.I)
HK = re.compile(r"Hong Kong|\bHK\b|Kowloon|New Territories|Lantau|香港|本港|港島|九龍|新界|大嶼山", re.I)
