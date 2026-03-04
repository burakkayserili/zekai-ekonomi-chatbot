"""
Zekai - TCMB Economy Chatbot by JCR-ER
Streamlit Chat Interface
"""

import streamlit as st
from pathlib import Path

from config import CHROMA_DIR, GOOGLE_API_KEY, APP_PASSWORD
from rag.chain import create_rag_chain, query_chain
from rag.prompts import WELCOME_MESSAGE

# --- Page Configuration ---
st.set_page_config(
    page_title="Zekai - Ekonomi Chatbot",
    page_icon="🧠",
    layout="centered",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        max-width: 900px;
        margin: 0 auto;
    }
    .source-box {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px;
        margin-top: 5px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# --- Password Protection ---
def check_password():
    """Show login screen and verify password."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("🧠 Zekai")
    st.caption("JCR-ER Ekonomik Araştırmalar ve İş Geliştirme | TCMB Yayınlarına Dayalı Ekonomi Chatbot'u")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Giriş Yap")
        password = st.text_input("Şifre", type="password", placeholder="Şifreyi giriniz...")
        if st.button("Giriş", use_container_width=True):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Yanlış şifre. Lütfen tekrar deneyin.")
        st.markdown(
            "<p style='text-align: center; color: gray; font-size: 0.8em; margin-top: 20px;'>"
            "Erişim için yetkili kişilerden şifreyi talep ediniz."
            "</p>",
            unsafe_allow_html=True,
        )
    return False

if APP_PASSWORD and not check_password():
    st.stop()

# --- Header ---
st.title("🧠 Zekai")
st.caption("JCR-ER Ekonomik Araştırmalar ve İş Geliştirme | TCMB Yayınlarına Dayalı Ekonomi Chatbot'u")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Ayarlar")

    # Year filter
    selected_years = st.multiselect(
        "Yıl Filtresi",
        options=[2020, 2021, 2022, 2023, 2024, 2025, 2026],
        default=[2020, 2021, 2022, 2023, 2024, 2025, 2026],
        help="Sadece seçili yıllardaki yayınlardan cevap aranır",
    )

    # Category filter
    category_options = {
        "Tümü": None,
        "Enflasyon Raporu": "enflasyon_raporu",
        "Finansal İstikrar": "finansal_istikrar",
        "Aylık Fiyat Gelişmeleri": "aylik_fiyat",
        "Para Politikası": "para_politikasi",
        "Çalışma Tebliğleri": "calisma_tebligleri",
        "Ekonomi Notları": "ekonomi_notlari",
        "Yıllık Rapor": "yillik_rapor",
    }
    selected_category = st.selectbox(
        "Yayın Türü",
        options=list(category_options.keys()),
        help="Belirli bir yayın türünde arama yapın",
    )

    st.divider()
    st.markdown("**Hakkında**")
    st.markdown(
        "**Zekai**, JCR-ER Ekonomik Araştırmalar ve İş Geliştirme "
        "tarafından geliştirilen, TCMB'nin resmi yayınlarını kullanarak "
        "Türkiye ekonomisi hakkındaki sorularınızı yanıtlayan bir "
        "yapay zeka chatbot'udur."
    )
    st.markdown("[TCMB Web Sitesi](https://www.tcmb.gov.tr)")

    st.divider()
    st.markdown("**İletişim**")
    st.markdown("Burak Kayserili")
    st.markdown("burak.kayserili@jcrer.com.tr")
    st.markdown("brkkayserili@gmail.com")

    st.divider()
    # Clear chat button
    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("chain", None)
        st.rerun()

    # Logout button
    if APP_PASSWORD:
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.messages = []
            st.session_state.pop("chain", None)
            st.rerun()

# --- Check Prerequisites ---
if not GOOGLE_API_KEY:
    st.error(
        "⚠️ Google API anahtarı bulunamadı!\n\n"
        "1. [Google AI Studio](https://aistudio.google.com/) adresinden ücretsiz API anahtarı alın\n"
        "2. Proje klasöründe `.env` dosyası oluşturun\n"
        "3. `GOOGLE_API_KEY=your_key_here` satırını ekleyin\n"
        "4. Uygulamayı yeniden başlatın"
    )
    st.stop()

if not Path(CHROMA_DIR).exists() or not any(Path(CHROMA_DIR).iterdir()):
    st.warning(
        "⚠️ Vektör veritabanı bulunamadı!\n\n"
        "Önce PDF'leri indirip işlemeniz gerekiyor:\n"
        "```bash\n"
        "python scripts/run_scraper.py    # PDF'leri indir\n"
        "python scripts/run_processing.py # Veritabanını oluştur\n"
        "```"
    )
    st.stop()

# --- Build Filters ---
def get_filters():
    """Build ChromaDB metadata filters from sidebar selections."""
    conditions = []

    if selected_years and len(selected_years) < 7:
        conditions.append({"year": {"$in": selected_years}})

    cat_value = category_options.get(selected_category)
    if cat_value:
        conditions.append({"category": cat_value})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}

# --- Initialize Chain ---
@st.cache_resource
def init_chain():
    """Initialize the RAG chain (cached)."""
    return create_rag_chain()

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Welcome Message ---
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(WELCOME_MESSAGE)

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Kaynaklar"):
                for src in msg["sources"]:
                    st.markdown(f"- {src}")

# --- Chat Input ---
if prompt := st.chat_input("Sorunuzu yazın..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            try:
                chain = init_chain()
                filters = get_filters()
                result = query_chain(chain, prompt, filters=filters)

                answer = result["answer"]
                source_docs = result["source_documents"]

                # Extract source info
                sources = []
                seen = set()
                for doc in source_docs:
                    meta = doc.metadata
                    source_str = f"{meta.get('title', meta.get('source', 'Bilinmeyen'))}"
                    if meta.get('year'):
                        source_str += f" ({meta['year']})"
                    if meta.get('page'):
                        source_str += f" - Sayfa {meta['page']}"
                    if source_str not in seen:
                        sources.append(source_str)
                        seen.add(source_str)

            except Exception as e:
                answer = f"Bir hata oluştu: {str(e)}"
                sources = []

        st.markdown(answer)
        if sources:
            with st.expander("📚 Kaynaklar"):
                for src in sources:
                    st.markdown(f"- {src}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
