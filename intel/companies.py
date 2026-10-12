"""Bilingual company aliases. Used to (a) name the company in a headline,
(b) match English and Chinese reports of the same deal, (c) hint the sector.
Add companies here as you meet them - matching only, never invents data."""
import re

# canonical, sector, aliases, is_landlord_or_developer
COMPANIES = [
    # finance / professional
    ("Prudential", "Finance & Professional Services", ["Prudential", "保誠"], False),
    ("AXA", "Finance & Professional Services", ["AXA", "安盛"], False),
    ("ZA Bank", "Finance & Professional Services", ["ZA Bank", "眾安銀行"], False),
    ("Susquehanna (SIG)", "Finance & Professional Services", ["Susquehanna", "SIG", "海納國際"], False),
    ("HSBC", "Finance & Professional Services", ["HSBC", "滙豐", "匯豐"], False),
    ("Standard Chartered", "Finance & Professional Services", ["Standard Chartered", "渣打"], False),
    ("Bank of China (HK)", "Finance & Professional Services", ["Bank of China", "BOCHK", "中銀香港"], False),
    ("AIA", "Finance & Professional Services", ["AIA", "友邦"], False),
    ("Manulife", "Finance & Professional Services", ["Manulife", "宏利"], False),
    ("FWD", "Finance & Professional Services", ["FWD", "富衛"], False),
    ("BlackRock", "Finance & Professional Services", ["BlackRock", "貝萊德"], False),
    ("Citadel", "Finance & Professional Services", ["Citadel"], False),
    ("Jane Street", "Finance & Professional Services", ["Jane Street"], False),
    ("Millennium", "Finance & Professional Services", ["Millennium Management"], False),
    ("Goldman Sachs", "Finance & Professional Services", ["Goldman Sachs", "Goldman", "高盛"], False),
    ("Morgan Stanley", "Finance & Professional Services", ["Morgan Stanley", "摩根士丹利", "大摩"], False),
    ("JPMorgan", "Finance & Professional Services", ["JPMorgan", "JP Morgan", "摩根大通", "小摩"], False),
    ("UBS", "Finance & Professional Services", ["UBS", "瑞銀"], False),
    ("Citi", "Finance & Professional Services", ["Citigroup", "Citibank", "Citi", "花旗"], False),
    ("GF Securities", "Finance & Professional Services", ["GF Securities", "廣發証券", "廣發證券"], False),
    ("CICC", "Finance & Professional Services", ["CICC", "中金"], False),
    ("Hang Seng Bank", "Finance & Professional Services", ["Hang Seng Bank", "恒生銀行", "恒生"], False),
    ("Jump Trading", "Finance & Professional Services", ["Jump Trading"], False),
    ("Bank of America", "Finance & Professional Services", ["Bank of America", "美銀"], False),
    ("Futu", "Finance & Professional Services", ["Futu", "富途"], False),
    ("Danantara", "Finance & Professional Services", ["Danantara"], False),
    ("Qatar Airways Cargo", "Logistics & Supply Chain", ["Qatar Airways"], False),
    # luxury / retail
    ("Christie's", "Luxury & HNW Goods", ["Christie's", "Christie’s", "佳士得"], False),
    ("Sotheby's", "Luxury & HNW Goods", ["Sotheby's", "Sotheby’s", "蘇富比"], False),
    ("Chow Tai Fook", "Luxury & HNW Goods", ["Chow Tai Fook", "周大福"], False),
    ("Hermès", "Luxury & HNW Goods", ["Hermès", "Hermes", "愛馬仕"], False),
    ("LVMH", "Luxury & HNW Goods", ["LVMH", "Louis Vuitton"], False),
    ("Rolex", "Luxury & HNW Goods", ["Rolex", "勞力士"], False),
    ("H&M", "Retail & Consumer", ["H&M"], False),
    ("W.Management", "Retail & Consumer", ["W. MANAGEMENT", "W.MANAGEMENT", "W.Management"], False),
    ("Mixue", "Retail & Consumer", ["Mixue", "蜜雪冰城"], False),
    ("Pop Mart", "Retail & Consumer", ["Pop Mart", "泡泡瑪特"], False),
    ("DFI Retail", "Retail & Consumer", ["DFI Retail", "牛奶國際"], False),
    ("Sincere", "Retail & Consumer", ["Sincere", "先施"], False),
    ("Lung Fung Pharmacy", "Healthcare & Life Sciences", ["龍豐"], False),
    ("Apple", "Retail & Consumer", ["Apple Store", "蘋果"], False),
    # tech / AI
    ("Nintendo", "AI & Technology", ["Nintendo", "任天堂"], False),
    ("Tencent", "AI & Technology", ["Tencent", "騰訊"], False),
    ("Alibaba", "AI & Technology", ["Alibaba", "阿里巴巴"], False),
    ("ByteDance", "AI & Technology", ["ByteDance", "字節跳動"], False),
    ("Huawei", "AI & Technology", ["Huawei", "華為"], False),
    ("Xiaomi", "AI & Technology", ["Xiaomi", "小米"], False),
    ("Meituan", "AI & Technology", ["Meituan", "美團"], False),
    ("JD.com", "Logistics & Supply Chain", ["JD.com", "京東"], False),
    ("Amazon", "AI & Technology", ["Amazon", "亞馬遜"], False),
    ("AgiBot", "AI & Technology", ["AGIBOT", "AgiBot", "智元"], False),
    ("AECOM", "Infrastructure & Construction", ["AECOM"], False),
    ("Arup", "Infrastructure & Construction", ["Arup", "奧雅納"], False),
    # data centres / telco
    ("Equinix", "Data Centre", ["Equinix"], False),
    ("NTT", "Data Centre", ["NTT"], False),
    ("Digital Realty", "Data Centre", ["Digital Realty"], False),
    ("SUNeVision", "Data Centre", ["SUNeVision", "新意網", "iAdvantage"], False),
    ("HKT", "Data Centre", ["HKT", "香港電訊"], False),
    ("PCCW", "AI & Technology", ["PCCW", "電訊盈科"], False),
    ("Global Switch", "Data Centre", ["Global Switch"], False),
    ("AirTrunk", "Data Centre", ["AirTrunk"], False),
    ("Princeton Digital", "Data Centre", ["Princeton Digital"], False),
    ("GDS", "Data Centre", ["GDS", "萬國數據"], False),
    # logistics
    ("DHL", "Logistics & Supply Chain", ["DHL"], False),
    ("SF Express", "Logistics & Supply Chain", ["SF Express", "順豐"], False),
    ("Cainiao", "Logistics & Supply Chain", ["Cainiao", "菜鳥"], False),
    ("Kerry Logistics", "Logistics & Supply Chain", ["Kerry Logistics", "嘉里物流"], False),
    ("Arvato", "Logistics & Supply Chain", ["Arvato"], False),
    ("Goodman", "Logistics & Supply Chain", ["Goodman"], True),
    ("ESR", "Logistics & Supply Chain", ["ESR"], True),
    # education
    ("HKUST", "Education & Government", ["HKUST", "科大"], False),
    ("CUHK", "Education & Government", ["CUHK", "中大"], False),
    ("HKU", "Education & Government", ["HKU", "港大"], False),
    # landlords / developers
    ("Sun Hung Kai Properties", "Facility Management & Real Estate", ["SHKP", "Sun Hung Kai Properties", "新地", "新鴻基地產"], True),
    ("Hysan", "Facility Management & Real Estate", ["Hysan", "希慎"], True),
    ("Swire Properties", "Facility Management & Real Estate", ["Swire Properties", "Swire", "太古地產"], True),
    ("CK Asset", "Facility Management & Real Estate", ["CK Asset", "長實", "長江實業"], True),
    ("Hongkong Land", "Facility Management & Real Estate", ["Hongkong Land", "置地"], True),
    ("Henderson Land", "Facility Management & Real Estate", ["Henderson Land", "恒基", "恒地"], True),
    ("New World Development", "Facility Management & Real Estate", ["New World Development", "NWD", "新世界"], True),
    ("Sino Land", "Facility Management & Real Estate", ["Sino Land", "信和"], True),
    ("Kerry Properties", "Facility Management & Real Estate", ["Kerry Properties", "嘉里建設"], True),
    ("Hang Lung", "Facility Management & Real Estate", ["Hang Lung", "恒隆"], True),
    ("Link REIT", "Facility Management & Real Estate", ["Link REIT", "領展"], True),
    ("Great Eagle", "Facility Management & Real Estate", ["Great Eagle", "鷹君"], True),
    ("Wharf", "Facility Management & Real Estate", ["Wharf", "九倉", "會德豐"], True),
    ("Chinachem", "Facility Management & Real Estate", ["Chinachem", "華懋"], True),
    ("Emperor", "Facility Management & Real Estate", ["Emperor International", "英皇"], True),
]


def _rx(alias):
    if re.search(r"[一-鿿]", alias):
        return re.compile(re.escape(alias))
    flags = 0 if (alias.isupper() and len(alias) <= 5) else re.I
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", flags)


_RX = [(c, s, land, _rx(a)) for c, s, aliases, land in COMPANIES for a in aliases]


def companies_in(text):
    """Return list of (canonical, sector, is_landlord) found in text, in order of appearance."""
    hits = {}
    for c, s, land, rx in _RX:
        m = rx.search(text or "")
        if m and (c not in hits or m.start() < hits[c][0]):
            hits[c] = (m.start(), s, land)
    return [(c, s, land) for c, (_, s, land) in sorted(hits.items(), key=lambda kv: kv[1][0])]
