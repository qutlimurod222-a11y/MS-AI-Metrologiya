
import streamlit as st
from pathlib import Path
from pypdf import PdfReader
from docx import Document
import re
import hmac

st.set_page_config(
    page_title="MS AI",
    page_icon="📚",
    layout="wide"
)

KUTUBXONA = Path("materials")
KUTUBXONA.mkdir(exist_ok=True)

# Admin ma'lumotlarini xavfsiz Secrets bo'limidan olish
try:
    ADMIN_USERNAME = st.secrets["admin"]["username"]
    ADMIN_PASSWORD = st.secrets["admin"]["password"]
except Exception:
    ADMIN_USERNAME = None
    ADMIN_PASSWORD = None

# Foydalanuvchi holatini saqlash
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


def matnni_ol(fayl):
    natija = []

    if fayl.suffix.lower() == ".pdf":
        pdf = PdfReader(str(fayl))

        for raqam, sahifa in enumerate(pdf.pages, start=1):
            matn = sahifa.extract_text() or ""

            if matn.strip():
                natija.append({
                    "matn": matn,
                    "manba": fayl.name,
                    "sahifa": raqam
                })

    elif fayl.suffix.lower() == ".docx":
        doc = Document(str(fayl))
        paragraflar = [
            p.text.strip()
            for p in doc.paragraphs
            if p.text.strip()
        ]

        for i in range(0, len(paragraflar), 4):
            matn = "\n".join(paragraflar[i:i + 4])

            natija.append({
                "matn": matn,
                "manba": fayl.name,
                "sahifa": None
            })

    return natija


def sozlarni_ajrat(matn):
    matn = matn.lower()

    for belgi in ["‘", "’", "ʻ", "ʼ", "'"]:
        matn = matn.replace(belgi, "")

    return set(re.findall(r"[^\W_]+", matn, flags=re.UNICODE))


def javob_qidir(savol):
    qidiruv_sozlari = sozlarni_ajrat(savol)

    keraksiz_sozlar = {
        "va", "yoki", "bu", "shu", "uchun",
        "nima", "qanday", "qaysi", "haqida",
        "bilan", "ning", "dan", "ga", "ni"
    }

    qidiruv_sozlari -= keraksiz_sozlar

    if not qidiruv_sozlari:
        return []

    topilmalar = []

    for fayl in KUTUBXONA.iterdir():
        if fayl.suffix.lower() not in [".pdf", ".docx"]:
            continue

        try:
            parchalar = matnni_ol(fayl)

            for parcha in parchalar:
                matn_sozlari = sozlarni_ajrat(parcha["matn"])
                mos_sozlar = qidiruv_sozlari & matn_sozlari

                if mos_sozlar:
                    ball = len(mos_sozlar) / len(qidiruv_sozlari)

                    topilmalar.append({
                        "ball": ball,
                        "moslik": len(mos_sozlar),
                        **parcha
                    })

        except Exception:
            continue

    topilmalar.sort(
        key=lambda x: (x["ball"], x["moslik"]),
        reverse=True
    )

    return [
        x for x in topilmalar
        if x["ball"] >= 0.3
    ][:5]


# ADMIN KIRISH TIZIMI
st.sidebar.title("🔐 Hisob")

if st.session_state.is_admin:
    st.sidebar.success("Admin sifatida kirdingiz")

    if st.sidebar.button("Hisobdan chiqish"):
        st.session_state.is_admin = False
        st.rerun()

else:
    with st.sidebar.form("admin_login"):
        st.markdown("**Admin kirish**")

        login = st.text_input("Login")
        parol = st.text_input("Parol", type="password")

        kirish = st.form_submit_button("Kirish")

    if kirish:
        if ADMIN_USERNAME is None or ADMIN_PASSWORD is None:
            st.sidebar.error("Admin hisobi hali sozlanmagan.")
        elif (
            hmac.compare_digest(login, str(ADMIN_USERNAME))
            and hmac.compare_digest(parol, str(ADMIN_PASSWORD))
        ):
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("Login yoki parol noto‘g‘ri.")

if st.session_state.is_admin:
    st.sidebar.caption("Sizda administrator huquqi bor.")
else:
    st.sidebar.caption("Oddiy foydalanuvchi rejimi")


# ASOSIY SAHIFA
st.title("📚 MS AI")
st.subheader("Metrologiya bo‘yicha shaxsiy bilimlar bazasi")
st.divider()

bolim = st.sidebar.radio(
    "Bo‘limni tanlang",
    [
        "Bosh sahifa",
        "Mening kutubxonam",
        "MS AI bilan suhbat"
    ]
)

if bolim == "Bosh sahifa":
    st.header("Xush kelibsiz!")
    st.write(
        "MS AI — metrologiya kitoblari asosida "
        "ma'lumot qidiruvchi yordamchi."
    )
    st.info(
        "Kitoblar bazasidan foydalanib, "
        "metrologiyaga oid savollaringizga javob qidiring."
    )

elif bolim == "Mening kutubxonam":
    st.header("📚 Mening kutubxonam")

    if st.session_state.is_admin:
        st.success("Admin paneli: kitob yuklash huquqi mavjud.")

        fayllar = st.file_uploader(
            "PDF yoki Word kitoblarni yuklang",
            type=["pdf", "docx"],
            accept_multiple_files=True
        )

        if fayllar:
            for fayl in fayllar:
                manzil = KUTUBXONA / Path(fayl.name).name

                if not manzil.exists():
                    manzil.write_bytes(fayl.getbuffer())
                    st.success(f"{fayl.name} saqlandi.")
                else:
                    st.info(f"{fayl.name} avval saqlangan.")
    else:
        st.info(
            "Kitoblarni yuklash faqat administrator uchun ochiq."
        )

    st.divider()
    st.subheader("📖 Saqlangan kitoblar")

    saqlangan = [
        f for f in KUTUBXONA.iterdir()
        if f.is_file() and f.suffix.lower() in [".pdf", ".docx"]
    ]

    if saqlangan:
        for fayl in saqlangan:
            st.write("📄", fayl.name)
    else:
        st.warning("Hozircha kitob yuklanmagan.")

elif bolim == "MS AI bilan suhbat":
    st.header("💬 Metrologiyadan savol bering")

    savol = st.text_area(
        "Savolingizni yozing",
        placeholder="Masalan: Metrologiya nima?"
    )

    if st.button("Javob qidirish"):
        if savol.strip():
            with st.spinner("Kitoblar tekshirilmoqda..."):
                topilmalar = javob_qidir(savol)

            if topilmalar:
                st.success(
                    f"{len(topilmalar)} ta mos ma'lumot topildi."
                )

                for i, topilma in enumerate(topilmalar, start=1):
                    st.markdown(f"### {i}. {topilma['manba']}")

                    if topilma["sahifa"] is not None:
                        st.caption(
                            f"Manba: {topilma['manba']}, "
                            f"{topilma['sahifa']}-sahifa"
                        )
                    else:
                        st.caption(
                            "Manba: Word hujjati. "
                            "Aniq sahifa raqami mavjud emas."
                        )

                    st.write(topilma["matn"][:1200])
                    st.divider()

            else:
                st.warning(
                    "Bu savolga mos ma'lumot yuklangan "
                    "kitoblardan topilmadi."
                )
        else:
            st.warning("Avval savol yozing!")

st.divider()
st.caption("MS AI | Metrologiya bilimlar bazasi")
