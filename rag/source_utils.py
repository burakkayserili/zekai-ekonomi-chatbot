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


def extract_ekonomi_notu_number(filename: str) -> str | None:
    """
    Extract note number from ekonomi notu filenames.

    Patterns:
        en2501.pdf → 2025/01
        en202523.pdf → 2025/23
        en2018.pdf → 2020/18
        en2417.pdf → 2024/17
    """
    name = filename.lower().replace(".pdf", "")
    # Pattern: en + 4-digit year + note number (e.g., en202523)
    m = re.match(r'^en(\d{4})(\d{2})$', name)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # Pattern: en + 2-digit year + 2-digit note (e.g., en2501, en2018)
    m = re.match(r'^en(\d{2})(\d{2})$', name)
    if m:
        yr = int(m.group(1))
        full_year = 2000 + yr if yr < 50 else 1900 + yr
        return f"{full_year}/{m.group(2)}"
    return None


# Fix Turkish characters in category names (stored without Turkish chars in DB)
CATEGORY_DISPLAY_NAMES = {
    "Finansal Istikrar Raporu": "Finansal İstikrar Raporu",
    "Aylik Fiyat Gelismeleri": "Aylık Fiyat Gelişmeleri",
    "Para Politikasi Metinleri": "Para Politikası Metinleri",
    "Calisma Tebligleri": "Çalışma Tebliğleri",
    "Ekonomi Notlari": "Ekonomi Notları",
    "Yillik Rapor": "Yıllık Rapor",
    "Odeme Sistemleri Raporu": "Ödeme Sistemleri Raporu",
}


def get_readable_source(source_file: str, category_name: str, year: int | str,
                        title: str = "") -> str:
    """
    Convert raw filename + metadata to TCMB official naming format.

    Examples:
        enf25_iii_tam.pdf → "📄 Enflasyon Raporu 2025-III"
        1b26_i.pdf → "📄 Enflasyon Raporu 2026-I"
        afiyatmart25.pdf → "📄 Aylık Fiyat Gelişmeleri (Mart 2025)"
        en2501.pdf + title → "📄 Ekonomi Notu 2025/01 — Kredi Kartı Kullanım Eğilimleri"
    """
    if not category_name or not year:
        return f"📄 {source_file} ({year})"

    # Fix Turkish characters
    display_name = CATEGORY_DISPLAY_NAMES.get(category_name, category_name)

    # Try to extract period info
    roman = extract_roman_numeral(source_file)
    month = extract_month(source_file)
    ekon_no = extract_ekonomi_notu_number(source_file)

    # Build the display string based on category
    if roman and "nflasyon" in category_name:
        # Enflasyon Raporu 2026-I format
        return f"📄 Enflasyon Raporu {year}-{roman}"
    elif roman:
        return f"📄 {display_name} {year}-{roman}"
    elif ekon_no:
        # Ekonomi notları: show real title if available
        note_label = f"📄 Ekonomi Notu {ekon_no}"
        if title and "?" not in title and len(title) > 5:
            return f"{note_label} — {title}"
        return note_label
    elif month:
        return f"📄 {display_name} ({month} {year})"
    else:
        return f"📄 {display_name} ({year})"


def get_source_key(source_file: str, category_name: str, year: int | str) -> str:
    """
    Create a unique key for deduplication.
    Groups all sections (1b, 2b, 3b, enf_tam, ki) of the same report together.
    Ekonomi notları are unique per note number (not grouped by year).
    """
    ekon_no = extract_ekonomi_notu_number(source_file)
    if ekon_no:
        # Each ekonomi notu is a separate publication
        return f"ekonomi_notu_{ekon_no}"
    roman = extract_roman_numeral(source_file)
    month = extract_month(source_file)
    period = roman or month or ""
    return f"{category_name}_{year}_{period}"
