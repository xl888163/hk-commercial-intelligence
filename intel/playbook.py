"""Securitas Hong Kong sales playbook: who to meet and what to pitch, per sector.

Service range (Securitas HK): guarding (static, reception/access control, retail
loss prevention, VIP/executive protection, event security), mobile patrol,
electronic security (CCTV, intrusion alarm, access control, maintenance),
remote viewing from the Securitas Operations Centre (SOC), corporate risk
management via Pinkerton, Risk Intelligence and the MySecuritas platform.
This is sales guidance written by us, not information from the sources.
"""

PLAYBOOK = {
    "Data Centre": (
        "Data-centre operators' security & facilities heads, DC developers, M&E / ELV consultants",
        "Integrated DC security: perimeter intrusion detection, multi-factor access control & mantraps, 24/7 guarding with SOC remote viewing, audit-ready MySecuritas reports"),
    "Facility Management & Real Estate": (
        "Landlords' asset & property managers, building management offices, FM companies",
        "Building guarding & concierge, mobile patrol, CCTV / alarm upgrades linked to SOC remote viewing, MySecuritas reporting for multi-site portfolios"),
    "Finance & Professional Services": (
        "Heads of corporate real estate / workplace, office managers, COOs and security / risk heads at banks, insurers, funds and law firms",
        "Reception & access-control guarding, CCTV and access control for new floors, visitor management, executive protection, Pinkerton due diligence"),
    "Infrastructure & Construction": (
        "Developers, main contractors, project managers, ELV / M&E consultants",
        "Construction-site guarding & mobile patrol, temporary CCTV with remote viewing; get Securitas specified in the building's ELV security package"),
    "Retail & Consumer": (
        "Retail operations & loss-prevention heads, mall operators",
        "Loss-prevention officers, CCTV analytics, intruder alarms with SOC response, mobile patrol"),
    "Logistics & Supply Chain": (
        "Warehouse / 3PL operations & security managers, port and air-cargo operators",
        "Perimeter & yard CCTV, dock access control, guarding & mobile patrol, remote viewing, supply-chain risk intelligence"),
    "Luxury & HNW Goods": (
        "Jewellery & watch retailers, auction houses, family offices, private banks",
        "High-grade alarms, vault & showroom CCTV, VIP / executive protection, secure event and exhibition guarding"),
    "Security & Safety": (
        "Security system integrators & vendors (partners), end-user security managers visiting; competitors (market intel)",
        "Partner with integrators on guarding + technology bundles; scout new CCTV / access tech; meet end-user security managers"),
    "AI & Technology": (
        "Workplace / office managers and COOs of tech firms, labs and scale-ups",
        "Access control & CCTV for new offices and labs, remote viewing, Risk Intelligence for IP and travel risk"),
    "Healthcare & Life Sciences": (
        "Hospital, clinic and laboratory facility & security heads",
        "Restricted-area access control, CCTV, guarding, duress / panic alarms"),
    "Education & Government": (
        "Campus estates & security offices, school administrators, public-facility managers",
        "Campus guarding, visitor management, CCTV; track upcoming tenders"),
    "Hospitality, Food & Tourism": (
        "Hotel security & engineering directors, F&B group operations heads",
        "Guarding, CCTV, back-of-house access control, event security"),
    "Energy & Environment": (
        "Utility, plant and green-facility managers",
        "Remote-site perimeter protection, mobile patrol, remote viewing"),
    "Manufacturing & Consumer Goods": (
        "Hong Kong-based brand owners, distributors and trading houses with showrooms or warehouses",
        "Showroom & warehouse CCTV, intruder alarm with SOC response, mobile patrol"),
    "Other": (
        "Senior executives (C-suite, COOs, GMs) across industries",
        "Securitas integrated security (people + technology + MySecuritas); Risk Intelligence for multinationals"),
}

EVENT_SECURITY = (
    "Organiser's event / operations manager",
    "Event security: crowd management, bag checks, badge & access control, temporary CCTV, VIP protection",
)


def play(sector):
    return PLAYBOOK.get(sector, PLAYBOOK["Other"])
