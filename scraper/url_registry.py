"""
TCMB website URL patterns for each publication category.
All paths are relative to TCMB_BASE_URL.
"""

PUBLICATIONS_BASE = "/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Yayinlar"

PUBLICATION_SOURCES = {
    "enflasyon_raporu": {
        "name": "Enflasyon Raporu",
        "path": f"{PUBLICATIONS_BASE}/Raporlar/Enflasyon+Raporu",
        "has_year_pages": True,
        "subfolder": "raporlar/enflasyon",
    },
    "finansal_istikrar": {
        "name": "Finansal Istikrar Raporu",
        "path": f"{PUBLICATIONS_BASE}/Raporlar/Finansal+Istikrar+Raporu",
        "has_year_pages": True,
        "subfolder": "raporlar/finansal_istikrar",
    },
    "aylik_fiyat": {
        "name": "Aylik Fiyat Gelismeleri",
        "path": f"{PUBLICATIONS_BASE}/Raporlar/Aylik+Fiyat+Gelismeleri",
        "has_year_pages": False,
        "subfolder": "raporlar/aylik_fiyat",
    },
    "para_politikasi": {
        "name": "Para Politikasi Metinleri",
        "path": f"{PUBLICATIONS_BASE}/Para+Politikasi+Metinleri",
        "has_year_pages": False,
        "subfolder": "para_politikasi",
    },
    "calisma_tebligleri": {
        "name": "Calisma Tebligleri",
        "path": f"{PUBLICATIONS_BASE}/Arastirma+Yayinlari/Calisma+Tebligleri",
        "has_year_pages": False,
        "subfolder": "arastirma/calisma_tebligleri",
    },
    "ekonomi_notlari": {
        "name": "Ekonomi Notlari",
        "path": "/wps/wcm/connect/tr/tcmb+tr/main+menu/yayinlar/arastirma+yayinlari/ekonomi+notlari",
        "has_year_pages": True,
        "subfolder": "arastirma/ekonomi_notlari",
    },
    "yillik_rapor": {
        "name": "Yillik Rapor",
        "path": f"{PUBLICATIONS_BASE}/Raporlar/Yillik+Rapor",
        "has_year_pages": False,
        "subfolder": "raporlar/yillik",
    },
    "odeme_sistemleri": {
        "name": "Odeme Sistemleri Raporu",
        "path": f"{PUBLICATIONS_BASE}/Raporlar/Odeme+Sistemleri",
        "has_year_pages": False,
        "subfolder": "raporlar/odeme_sistemleri",
    },
}
