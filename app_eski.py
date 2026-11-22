import streamlit as st

# =====================================
# MS.Ai - SAHIFA SOZLAMALARI
# =====================================

st.set_page_config(
    page_title="MS.Ai" \
    "",
    page_icon="🤖",
    layout="wide"
)

# =====================================
# DASTUR SARLAVHASI
# =====================================

st.title("🤖 MS.Ai")
st.subheader("Shaxsiy sun'iy intellekt platformam")

st.markdown("---")

st.info(
    "MS.Ai — ChatGPT va Claude bilan "
    "hamkorlikda ishlash uchun yaratilgan platforma."
)

# =====================================
# AI TANLASH
# =====================================

st.header("⚙️ Ishlash rejimini tanlang")

rejim = st.radio(
    "Qaysi rejimda ishlamoqchisiz?",
    [
        "Faqat ChatGPT",
        "Faqat Claude",
        "ChatGPT + Claude"
    ],
    horizontal=True
)

# =====================================
# SAVOL KIRITISH
# =====================================

st.markdown("---")
st.header("✍️ Savolingizni kiriting")

savol = st.text_area(
    "Savol:",
    height=120,
    placeholder="Bu yerga savolingizni yozing..."
)

# =====================================
# SAVOLNI YUBORISH
# =====================================

if st.button("🚀 Yuborish", use_container_width=True):

    if savol.strip():

        st.session_state["savol"] = savol
        st.session_state["rejim"] = rejim

        # ChatGPT namuna javobi
        if rejim in ["Faqat ChatGPT", "ChatGPT + Claude"]:

            st.session_state["chatgpt"] = (
                "Bu ChatGPT uchun namuna javob.\n\n"
                "Sizning savolingiz: " + savol
            )

        # Claude namuna javobi
        if rejim in ["Faqat Claude", "ChatGPT + Claude"]:

            st.session_state["claude"] = (
                "Bu Claude uchun namuna javob.\n\n"
                "Sizning savolingiz: " + savol
            )

    else:

        st.warning("Iltimos, avval savol yozing!")

# =====================================
# NATIJALARNI KO'RSATISH
# =====================================

if "savol" in st.session_state:

    st.markdown("---")
    st.header("1️⃣ AI JAVOBLARI")

    # Faqat ChatGPT
    if st.session_state["rejim"] == "Faqat ChatGPT":

        st.subheader("🟢 ChatGPT")

        st.success(st.session_state["chatgpt"])

    # Faqat Claude
    elif st.session_state["rejim"] == "Faqat Claude":

        st.subheader("🔵 Claude")

        st.info(st.session_state["claude"])

    # Ikkala AI
    else:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("🟢 ChatGPT")

            st.success(st.session_state["chatgpt"])

        with col2:

            st.subheader("🔵 Claude")

            st.info(st.session_state["claude"])

        # =====================================
        # TAQQOSLASH
        # =====================================

        st.markdown("---")
        st.header("2️⃣ JAVOBLARNI TAQQOSLASH")

        st.write(
            "Bu bo'limda ChatGPT va Claude javoblarining "
            "o'xshash hamda farqli tomonlari tahlil qilinadi."
        )

        # =====================================
        # O'ZARO TEKSHIRISH
        # =====================================

        st.markdown("---")
        st.header("3️⃣ O'ZARO TEKSHIRISH")

        st.write(
            "Bu bo'limda ikkala sun'iy intellekt "
            "bir-birining javoblarini tekshiradi."
        )

        # =====================================
        # YAKUNIY XULOSA
        # =====================================

        st.markdown("---")
        st.header("4️⃣ YAKUNIY XULOSA")

        st.write(
            "Bu bo'limda ikkala AI fikri asosida "
            "umumiy yakuniy javob tayyorlanadi."
        )

# =====================================
# PASTKI QISM
# =====================================

st.markdown("---")

st.caption(
    "© 2026 MS.Ai | Shaxsiy sun'iy intellekt platformasi"
)
