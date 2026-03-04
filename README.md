# Zekai - TCMB Ekonomi Chatbot'u

**JCR-ER Ekonomik Araştırmalar ve İş Geliştirme** tarafından geliştirilen, Türkiye Cumhuriyet Merkez Bankası (TCMB) yayınlarına dayalı yapay zeka ekonomi asistanı.

Zekai; enflasyon raporları, finansal istikrar raporları, para politikası metinleri ve diğer TCMB yayınlarını kullanarak Türkiye ekonomisi hakkındaki sorularınızı yanıtlar.

## Özellikler

- TCMB'nin 2020-2025 yılları arasındaki resmi yayınlarını kullanır
- Türkçe soru-cevap desteği
- Kaynak gösterimi (hangi rapor, hangi yıl)
- Yıl ve yayın türüne göre filtreleme
- Tamamen ücretsiz (Google Gemini free tier)

## Kurulum

### Gereksinimler

- Python 3.10+
- Google Gemini API anahtarı (ücretsiz)

### Adım 1: Projeyi İndirin

```bash
git clone https://github.com/burakkayserili/zekai-ekonomi-chatbot.git
cd zekai-ekonomi-chatbot
```

### Adım 2: Sanal Ortam ve Bağımlılıklar

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Adım 3: API Anahtarı

1. [Google AI Studio](https://aistudio.google.com/) adresinden ücretsiz API anahtarı alın
2. Proje klasöründe `.env` dosyası oluşturun:

```bash
cp .env.example .env
```

3. `.env` dosyasını düzenleyip API anahtarınızı yapıştırın:

```
GOOGLE_API_KEY=your_api_key_here
```

### Adım 4: PDF'leri İndirin ve Veritabanını Oluşturun

```bash
python scripts/run_all.py
```

Bu komut:
- TCMB web sitesini tarayarak PDF'leri bulur (~297 PDF)
- PDF'leri indirir (~260MB)
- Metinleri çıkarır ve vektör veritabanını oluşturur (~22.000 metin parçası)
- İlk çalıştırmada Türkçe embedding modeli indirilir (~440MB, tek seferlik)

**Tahmini süre:** İlk kurulumda ~35-40 dakika (internet hızına bağlı)

### Adım 5: Chatbot'u Başlatın

```bash
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

## Kullanım

Chatbot'a Türkiye ekonomisi ile ilgili sorular sorabilirsiniz:

- "2024 yılında enflasyon nasıl seyretti?"
- "Merkez Bankası'nın para politikası duruşu nedir?"
- "Finansal istikrar riskleri nelerdir?"
- "Cari açık son dönemde nasıl değişti?"

Sol menüden yıl ve yayın türü filtresi uygulayabilirsiniz.

## Teknik Altyapı

| Bileşen | Teknoloji |
|---------|-----------|
| LLM | Google Gemini 2.5 Flash (ücretsiz) |
| Embedding | Turkish BERT (emrecan/bert-base-turkish-cased-mean-nli-stsb-tr) |
| Vektör DB | ChromaDB (lokal) |
| Framework | LangChain |
| Arayüz | Streamlit |
| PDF İşleme | pdfplumber |

## Proje Yapısı

```
zekai-ekonomi-chatbot/
├── app.py                 # Streamlit chat arayüzü
├── config.py              # Merkezi konfigürasyon
├── requirements.txt       # Python bağımlılıkları
├── scraper/               # TCMB PDF scraper
├── processing/            # PDF işleme ve vektör DB
├── rag/                   # RAG chain (Gemini + ChromaDB)
├── scripts/               # CLI araçları
├── data/pdfs/             # İndirilen PDF'ler (gitignore)
└── chroma_db/             # Vektör veritabanı (gitignore)
```

## İletişim

**Burak Kayserili**
- burak.kayserili@jcrer.com.tr
- brkkayserili@gmail.com

---

*JCR-ER Ekonomik Araştırmalar ve İş Geliştirme*
