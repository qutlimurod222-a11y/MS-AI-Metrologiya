
import streamlit as st
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from supabase import create_client
import re
import hmac

# ==========================================
# 1. SAHIFA SOZLAMALARI
# ==========================================

st.set_page_config(
    page_title="MS AI",
    page_icon="📚",
    layout="wide"
)

KUTUBXONA = Path("materials")
KUTUBXONA.mkdir(exist_ok=True)


# ==========================================
# 2. SUPABASE BILAN ULANISH
# ==========================================

try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["secret_key"]

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

except Exception:
    st.error(
        "Supabase bilan ulanishda xatolik. "
        "Streamlit Secrets sozlamalarini tekshiring."
    )
    st.stop()


# ==========================================
# 3. ADMIN MA'LUMOTLARI
# ==========================================

try:
    ADMIN_USERNAME = st.secrets["admin"]["username"]
    ADMIN_PASSWORD = st.secrets["admin"]["password"]

except Exception:
    ADMIN_USERNAME = None
    ADMIN_PASSWORD = None


if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


# ==========================================
# 4. PDF VA WORD MATNINI AJRATISH
# ==========================================

def matnni_ol(fayl):
    natija = []

    # PDF fayl
    if fayl.suffix.lower() == ".pdf":

        pdf = PdfReader(str(fayl))

        for raqam, sahifa in enumerate(
            pdf.pages,
            start=1
        ):
            matn = sahifa.extract_text() or ""

            if matn.strip():
                natija.append({
                    "matn": matn,
                    "manba": fayl.name,
                    "sahifa": raqam
                })

    # Word fayl
    elif fayl.suffix.lower() == ".docx":

        doc = Document(str(fayl))

        paragraflar = [
            p.text.strip()
            for p in doc.paragraphs
            if p.text.strip()
        ]

        for i in range(0, len(paragraflar), 4):

            matn = "\n".join(
                paragraflar[i:i + 4]
            )

            natija.append({
                "matn": matn,
                "manba": fayl.name,
                "sahifa": None
            })

    return natija


# ==========================================
# 5. MATNNI SO'ZLARGA AJRATISH
# ==========================================

def sozlarni_ajrat(matn):

    matn = matn.lower()

    for belgi in [
        "‘", "’", "ʻ", "ʼ", "'"
    ]:
        matn = matn.replace(
            belgi,
            ""
        )

    return set(
        re.findall(
            r"[^\W_]+",
            matn,
            flags=re.UNICODE
        )
    )

# ==========================================
# 6. SUPABASE'DAN YAXSHILANGAN QIDIRUV
# ==========================================

def sozlarni_normallashtir(matn):
    sozlar = sozlarni_ajrat(matn)

    natija = set()

    for soz in sozlar:
        # O'zbek tilidagi ko'p uchraydigan qo'shimchalar
        # bo'yicha sodda normallashtirish
        for qoshimcha in sorted([
            "larning", "laridan", "lariga",
            "lardan", "larga", "larni",
            "ning", "dan", "dagi", "dagi",
            "lik", "lari", "lar", "ga",
            "ni", "da", "ta", "mi"
        ], key=len, reverse=True):

            if len(soz) > len(qoshimcha) + 3:
                if soz.endswith(qoshimcha):
                    soz = soz[:-len(qoshimcha)]
                    break

        if len(soz) > 1:
            natija.add(soz)

    return natija


def javob_qidir(savol):

    qidiruv_sozlari = sozlarni_normallashtir(
        savol
    )

    keraksiz_sozlar = {
        "va", "yoki", "bu", "shu",
        "uchun", "nima", "qanday",
        "qaysi", "haqida", "bilan",
        "degani", "hisoblanadi",
        "ham", "esa", "bir", "bor"
    }

    qidiruv_sozlari -= keraksiz_sozlar

    if not qidiruv_sozlari:
        return []

    # Supabase'dan kitob parchalarini olish
    natija = (
        supabase.table("materials")
        .select(
            "id,title,content,file_name,page_number"
        )
        .limit(2000)
        .execute()
    )

    topilmalar = []

    for parcha in natija.data:

        matn = parcha.get("content") or ""

        if not matn.strip():
            continue

        matn_sozlari = sozlarni_normallashtir(
            matn
        )

        mos_sozlar = (
            qidiruv_sozlari & matn_sozlari
        )

        if not mos_sozlar:
            continue

        # Moslik darajasini hisoblash
        aniqlik = (
            len(mos_sozlar)
            / len(qidiruv_sozlari)
        )

        # Qo'shimcha moslik ballari
        ball = aniqlik

        if len(mos_sozlar) >= 2:
            ball += 0.10

        if len(mos_sozlar) >= 3:
            ball += 0.10

        topilmalar.append({
            "ball": ball,
            "aniqlik": aniqlik,
            "moslik": len(mos_sozlar),
            **parcha
        })

    # Eng mos parchalarni yuqoriga chiqarish
    topilmalar.sort(
        key=lambda x: (
            x["ball"],
            x["moslik"]
        ),
        reverse=True
    )

    return [
        x for x in topilmalar
        if x["aniqlik"] >= 0.3
    ][:5]

# ==========================================
# 7. ADMIN KIRISH TIZIMI
# ==========================================

st.sidebar.title("🔐 Hisob")

if st.session_state.is_admin:

    st.sidebar.success(
        "Admin sifatida kirdingiz"
    )

    if st.sidebar.button(
        "Hisobdan chiqish"
    ):
        st.session_state.is_admin = False
        st.rerun()

else:

    with st.sidebar.form("admin_login"):

        st.markdown("**Admin kirish**")

        login = st.text_input(
            "Login"
        )

        parol = st.text_input(
            "Parol",
            type="password"
        )

        kirish = st.form_submit_button(
            "Kirish"
        )

    if kirish:

        if (
            ADMIN_USERNAME is None
            or ADMIN_PASSWORD is None
        ):
            st.sidebar.error(
                "Admin hisobi sozlanmagan."
            )

        elif (
            hmac.compare_digest(
                login,
                str(ADMIN_USERNAME)
            )
            and hmac.compare_digest(
                parol,
                str(ADMIN_PASSWORD)
            )
        ):
            st.session_state.is_admin = True
            st.rerun()

        else:
            st.sidebar.error(
                "Login yoki parol noto‘g‘ri."
            )


if st.session_state.is_admin:
    st.sidebar.caption(
        "Administrator huquqi faol."
    )
else:
    st.sidebar.caption(
        "Oddiy foydalanuvchi rejimi."
    )


# ==========================================
# 8. ASOSIY SAHIFA
# ==========================================

st.title("📚 MS AI")

st.subheader(
    "Metrologiya bo‘yicha aqlli yordamchi"
)

st.divider()


bolim = st.sidebar.radio(
    "Bo‘limni tanlang",
    [
        "Bosh sahifa",
        "Mening kutubxonam",
        "MS AI bilan suhbat"
    ]
)


# ==========================================
# 9. BOSH SAHIFA
# ==========================================

if bolim == "Bosh sahifa":

    st.header(
        "Xush kelibsiz!"
    )

    st.write(
        "MS AI — metrologiya kitoblari "
        "asosida ma'lumot qidiruvchi "
        "aqlli yordamchi."
    )

    st.info(
        "Kitoblar bazasidan foydalanib, "
        "metrologiyaga oid savollaringizga "
        "javob qidiring."
    )

    st.markdown(
        """
        ### MS AI imkoniyatlari

        - Metrologiya bo‘yicha ma'lumot qidirish
        - PDF va Word kitoblardan foydalanish
        - Kitob nomi va sahifa raqamini ko‘rsatish
        - Matematik hisoblash
        - Tabiiy tilda suhbatlashish
        """
    )


# ==========================================
# 10. KUTUBXONA
# ==========================================

elif bolim == "Mening kutubxonam":

    st.header(
        "📚 Mening kutubxonam"
    )

    # ADMIN KITOB YUKLAYDI
    if st.session_state.is_admin:

        st.success(
            "Admin paneli: kitob yuklash mumkin."
        )

        fayllar = st.file_uploader(
            "PDF yoki Word kitoblarni yuklang",
            type=["pdf", "docx"],
            accept_multiple_files=True
        )

        if fayllar:

            for fayl in fayllar:

                fayl_nomi = Path(
                    fayl.name
                ).name

                manzil = (
                    KUTUBXONA / fayl_nomi
                )

                try:

                    # Supabase'da oldin mavjudmi?
                    mavjud = (
                        supabase.table("materials")
                        .select("id")
                        .eq(
                            "file_name",
                            fayl_nomi
                        )
                        .limit(1)
                        .execute()
                    )

                    if mavjud.data:

                        st.info(
                            f"{fayl_nomi} "
                            "bazada avval saqlangan."
                        )

                        continue

                    # Faylni vaqtincha saqlash
                    manzil.write_bytes(
                        fayl.getbuffer()
                    )

                    # Kitob matnini ajratish
                    parchalar = matnni_ol(
                        manzil
                    )

                    if not parchalar:

                        st.warning(
                            f"{fayl_nomi} ichidan "
                            "matn topilmadi."
                        )

                        continue

                    yozuvlar = []

                    for raqam, parcha in enumerate(
                        parchalar,
                        start=1
                    ):

                        yozuvlar.append({
                            "title": (
                                f"{fayl_nomi} "
                                f"— {raqam}"
                            ),
                            "content": parcha["matn"],
                            "file_name": fayl_nomi,
                            "page_number": (
                                parcha["sahifa"]
                            )
                        })

                    # Supabase'ga yozish
                    # Katta kitoblarni bo'lib yuborish
                    for i in range(
                        0,
                        len(yozuvlar),
                        100
                    ):

                        guruh = yozuvlar[
                            i:i + 100
                        ]

                        (
                            supabase.table("materials")
                            .insert(guruh)
                            .execute()
                        )

                    st.success(
                        f"{fayl_nomi} "
                        "Supabase'ga saqlandi!"
                    )

                except Exception as e:

                    st.error(
                        f"{fayl_nomi} saqlanmadi."
                    )

                    st.caption(
                        str(e)
                    )

                finally:

                    # Serverdagi vaqtinchalik faylni o'chirish
                    if manzil.exists():
                        manzil.unlink()

    else:

        st.info(
            "Kitob yuklash faqat administrator "
            "uchun ochiq."
        )


    # SUPABASE'DAGI KITOBLAR
    st.divider()

    st.subheader(
        "📖 Saqlangan kitoblar"
    )

    try:

        kitoblar = (
            supabase.table("materials")
            .select("file_name")
            .limit(2000)
            .execute()
        )

        nomlar = sorted({
            x["file_name"]
            for x in kitoblar.data
            if x.get("file_name")
        })

        if nomlar:

            for nom in nomlar:
                st.write("📄", nom)

        else:

            st.warning(
                "Hozircha Supabase bazasida "
                "kitob mavjud emas."
            )

    except Exception:

        st.error(
            "Kitoblar ro‘yxatini olishda "
            "xatolik yuz berdi."
        )


# ==========================================
# 11. MS AI BILAN SUHBAT
# ==========================================

elif bolim == "MS AI bilan suhbat":

    st.header(
        "💬 Metrologiyadan savol bering"
    )

    savol = st.text_area(
        "Savolingizni yozing",
        placeholder=(
            "Masalan: Metrologiya nima?"
        )
    )

    if st.button(
        "Javob qidirish"
    ):

        if savol.strip():

            with st.spinner(
                "Supabase kitoblaridan "
                "ma'lumot qidirilmoqda..."
            ):

                try:

                    topilmalar = javob_qidir(
                        savol
                    )

                except Exception as e:

                    st.error(
                        "Ma'lumot qidirishda "
                        "xatolik yuz berdi."
                    )

                    st.caption(
                        str(e)
                    )

                    topilmalar = []

            if topilmalar:

                st.success(
                    f"{len(topilmalar)} ta "
                    "mos ma'lumot topildi."
                )

                for i, topilma in enumerate(
                    topilmalar,
                    start=1
                ):

                    st.markdown(
                        f"### {i}. "
                        f"{topilma['file_name']}"
                    )

                    sahifa = topilma.get(
                        "page_number"
                    )

                    if sahifa is not None:

                        st.caption(
                            f"Manba: "
                            f"{topilma['file_name']}, "
                            f"{sahifa}-sahifa"
                        )

                    else:

                        st.caption(
                            "Manba: Word hujjati. "
                            "Aniq sahifa raqami mavjud emas."
                        )

                    st.write(
                        topilma["content"][:1200]
                    )

                    st.divider()

            else:

                st.warning(
                    "Bu savolga mos ma'lumot "
                    "Supabase bazasidan topilmadi."
                )

        else:

            st.warning(
                "Avval savol yozing!"
            )


# ==========================================
# 12. SAHIFA OXIRI
# ==========================================

st.divider()

st.caption(
    "MS AI | Metrologiya bilimlar bazasi"
)
