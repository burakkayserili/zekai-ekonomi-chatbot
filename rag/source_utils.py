"""
Utility to convert raw PDF filenames into human-readable Turkish source names.
Extracts quarter and month information from TCMB publication filenames.
"""

import re


# Roman numeral to Turkish quarter name
QUARTER_MAP = {
    "i": "1. Çeyrek", "ii": "2. Çeyrek", "iii": "3. Çeyrek", "iv": "4. Çeyrek",
    "1": "1. Çeyrek", "2": "2. Çeyrek", "3": "3. Çeyrek", "4": "4. Çeyrek",
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


def extract_quarter(filename: str) -> str | None:
    """Extract quarter from enflasyon/finansal report filenames."""
    name = filename.lower().replace(".pdf", "")

    # Pattern: enf25_iii_tam, 1b25_iii, 2b25_iv, ki25_ii
    m = re.search(r'[_\-](i{1,3}v?|iv|[1-4])(?:[_\-]|$)', name)
    if m:
        q = m.group(1).lower()
        return QUARTER_MAP.get(q)

    # Pattern: enf_2024-III_tam, ki_2024-I
    m = re.search(r'[\-_](I{1,3}V?|IV|[1-4])(?:[\-_]|$)', filename.replace(".pdf", ""))
    if m:
        q = m.group(1).lower()
        return QUARTER_MAP.get(q)

    return None


def extract_month(filename: str) -> str | None:
    """Extract month from aylık fiyat report filenames."""
    name = filename.lower().replace(".pdf", "")

    for key, month_name in MONTH_KEYWORDS.items():
        if key in name:
            return month_name
    return None


def get_readable_source(source_file: str, category_name: str, year: int | str) -> str:
    """
    Convert raw filename + metadata to a readable source string.

    Examples:
        enf25_iii_tam.pdf + Enflasyon Raporu + 2025 → "Enflasyon Raporu (2025, 3. Çeyrek)"
        afiyatmart25.pdf + Aylik Fiyat + 2025 → "Aylık Fiyat Gelişmeleri (2025, Mart)"
        Tam+Metin.pdf + Finansal Istikrar + 2024 → "Finansal İstikrar Raporu (2024)"
        2025_Para_Politikası.pdf + Para Politikasi + 2025 → "Para Politikası Metni (2025)"
    """
    if not category_name or not year:
        return f"📄 {source_file} ({year})"

    # Try to extract period info
    quarter = extract_quarter(source_file)
    month = extract_month(source_file)

    # Build the display string
    if quarter:
        return f"📄 {category_name} ({year}, {quarter})"
    elif month:
        return f"📄 {category_name} ({year}, {month})"
    else:
        return f"📄 {category_name} ({year})"


def get_source_key(source_file: str, category_name: str, year: int | str) -> str:
    """
    Create a unique key for deduplication.
    Same category + year + quarter/month = same source.
    """
    quarter = extract_quarter(source_file)
    month = extract_month(source_file)
    period = quarter or month or ""
    return f"{category_name}_{year}_{period}"
