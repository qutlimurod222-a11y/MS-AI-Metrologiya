
import streamlit as st
from pathlib import Path
from pypdf import PdfReader
from docx import Document
import re

st.set_page_config(
    page_title="MS AI",
    page_icon="📚",
    layout="wide"
)

KUTUBXONA = Path("materials")
KUTUBXONA.mkdir(exist_ok=True)

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
        "Avval kitoblaringizni kutubxonaga yuklang, "
        "keyin ular bo‘yicha savol bering."
    )

elif bolim == "Mening kutubxonam":
    st.header("📚 Mening kutubxonam")

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
