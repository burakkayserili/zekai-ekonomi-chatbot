"""
Utility to convert raw PDF filenames into human-readable Turkish source names.
Uses TCMB's official naming convention (e.g., Enflasyon Raporu 2026-I).
"""

import re


# Roman numeral mapping
ROMAN_MAP = {
    "i": "I", "ii": "II", "iii": "III", "iv": "IV",
    "1": "I", "2": "II", "3": "III", "4": "IV",
}

# Turkish month names for aylık fiyat reports
MONTH_KEYWORDS = {
    "ocak": "Ocak", "subat": "Şubat", "şubat": "Şubat", "mart": "Mart",
    "nisan": "Nisan", "mayıs": "Mayıs", "mayis": "Mayıs",
    "haziran": "Haziran", "temmuz": "Temmuz", "ağustos": "Ağustos",
    "agustos": "Ağustos", "eylül": "Eylül", "eylul": "Eylül",
    "ekim": "Ekim", "kasim": "Kasım", "kasım": "Kasım",
    "aralik": "Aralık", "aralık": "Aralık",
}


def extract_roman_numeral(filename: str) -> str | None:
    """
    Extract report number as Roman numeral from filename.

    Patterns handled:
        enf25_iii_tam.pdf → III
        1b25_iv.pdf → IV
        2b26_i.pdf → I
        ki25_ii.pdf → II
        enf_2024-III_tam.pdf → III
        enf_2024-I_tam.pdf → I
        1b20-3.pdf → III
        ki20-4.pdf → IV
    """
    name = filename.lower().replace(".pdf", "")

    # Pattern: _i, _ii, _iii, _iv (underscore + roman)
    m = re.search(r'[_](iv|iii|ii|i)(?:[_]|$)', name)
    if m:
        return ROMAN_MAP.get(m.group(1))

    # Pattern: -1, -2, -3, -4 (dash + number, older format like 1b20-3)
    m = re.search(r'-([1-4])(?:$)', name)
    if m:
        return ROMAN_MAP.get(m.group(1))

    # Pattern: -III, -I etc. (dash + uppercase roman, like enf_2024-III)
    m = re.search(r'-(IV|III|II|I)(?:[_]|$)', filename.replace(".pdf", ""))
    if m:
        return ROMAN_MAP.get(m.group(1).lower())

    # Pattern: İV (Turkish İ variant)
    if "İv" in filename or "İV" in filename:
        return "IV"

    return None


def extract_month(filename: str) -> str | None:
    """Extract month from aylık fiyat report filenames."""
    name = filename.lower().replace(".pdf", "")

    for key, month_name in MONTH_KEYWORDS.items():
        if key in name:
            return month_name

    # Special cases: Haziran+Ayı, Nisan+Ayı etc.
    for key, month_name in MONTH_KEYWORDS.items():
        if key.capitalize() in filename:
            return month_name

    return None


def get_readable_source(source_file: str, category_name: str, year: int | str) -> str:
    """
    Convert raw filename + metadata to TCMB official naming format.

    Examples:
        enf25_iii_tam.pdf → "📄 Enflasyon Raporu 2025-III"
        1b26_i.pdf → "📄 Enflasyon Raporu 2026-I"
        afiyatmart25.pdf → "📄 Aylık Fiyat Gelişmeleri (Mart 2025)"
        Tam+Metin.pdf (finansal) → "📄 Finansal İstikrar Raporu (2024)"
        2025_Para_Politikası.pdf → "📄 Para Politikası Metni (2025)"
    """
    if not category_name or not year:
        return f"📄 {source_file} ({year})"

    # Try to extract period info
    roman = extract_roman_numeral(source_file)
    month = extract_month(source_file)

    # Build the display string based on category
    if roman and "nflasyon" in category_name:
        # Enflasyon Raporu 2026-I format
        return f"📄 Enflasyon Raporu {year}-{roman}"
    elif roman:
        return f"📄 {category_name} {year}-{roman}"
    elif month:
        return f"📄 {category_name} ({month} {year})"
    else:
        return f"📄 {category_name} ({year})"


def get_source_key(source_file: str, category_name: str, year: int | str) -> str:
    """
    Create a unique key for deduplication.
    Groups all sections (1b, 2b, 3b, enf_tam, ki) of the same report together.
    """
    roman = extract_roman_numeral(source_file)
    month = extract_month(source_file)
    period = roman or month or ""
    return f"{category_name}_{year}_{period}"
