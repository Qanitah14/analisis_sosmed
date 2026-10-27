import ast
import html
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


# Nama file input dan output
INPUT_FILE = Path("hasil_scraping.csv")
OUTPUT_FILE = Path("hasil_cleaning_tweet.csv")

# Bahasa yang dipertahankan
LANG_DIPERTAHANKAN = {"id", "in"}
# Daftar kata tidak baku dan bentuk standarnya
SLANG = {
    "gak": "tidak", "ga": "tidak", "gk": "tidak", "nggak": "tidak",
    "ngga": "tidak", "enggak": "tidak", "engga": "tidak", "tdk": "tidak",
    "blm": "belum", "gue": "saya", "gua": "saya", "gw": "saya",
    "sy": "saya", "aku": "saya", "lu": "kamu", "lo": "kamu",
    "yg": "yang", "dgn": "dengan", "dg": "dengan", "utk": "untuk",
    "krn": "karena", "karna": "karena", "jg": "juga", "jga": "juga",
    "dr": "dari", "dri": "dari", "pd": "pada", "spt": "seperti",
    "kyk": "seperti", "kayak": "seperti", "tp": "tapi", "trs": "terus",
    "lg": "lagi", "bs": "bisa", "emg": "memang", "emang": "memang",
    "jd": "jadi", "dlm": "dalam", "sbg": "sebagai", "dll": "dan lain lain",
    "bnyk": "banyak", "byk": "banyak", "hrs": "harus",
    "skrg": "sekarang", "kmrn": "kemarin", "gmn": "bagaimana",
    "gimana": "bagaimana", "knp": "kenapa", "smua": "semua",
    "sdh": "sudah", "udh": "sudah", "udah": "sudah", "sj": "saja",
    "cm": "hanya", "cuma": "hanya", "ttp": "tetap", "kalo": "kalau",
    "klo": "kalau", "ntar": "nanti", "bener": "benar", "bnr": "benar",
    "bgt": "banget", "org": "orang", "pake": "pakai", "tau": "tahu",
    "liat": "lihat", "sbnrnya": "sebenarnya", "makasih": "terima kasih",
    "thx": "terima kasih", "trims": "terima kasih",
}

# Stopwords umum Bahasa Indonesia.
# Kata negasi dipertahankan karena penting untuk analisis sentimen.
STOPWORDS = set("""
yang dan di ke dari ini itu untuk dengan pada adalah akan bukan jangan belum
tak tanpa kurang saya kamu dia mereka kita kami anda aku nya pun lah kah si sang
para atau tetapi tapi juga karena agar jika maka dalam sebagai oleh terhadap
setelah sebelum saat bisa dapat sudah lebih sangat hanya saja ada menjadi suatu
seorang sebuah sih dong deh kok nih tuh kan yah lho loh nah mah toh via aja gitu
gini banget yaudah oke eh oh hehe wkwk
""".split())
STOPWORDS -= {"tidak", "bukan", "jangan", "belum", "tak", "tanpa", "kurang"}

URL_RE = re.compile(
    r"(?:https?://|www\.)\S+|\b(?:pic\.(?:x|twitter)\.com|t\.co)/\S+",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
MENTION_RE = re.compile(r"@\w+")
SPASI_RE = re.compile(r"\s+")


def rapikan_teks(teks):
    """Merapikan format teks dan mengubah baris baru menjadi spasi."""
    if pd.isna(teks):
        return ""

    teks = html.unescape(str(teks))
    teks = unicodedata.normalize("NFKC", teks)
    teks = "".join(
        karakter for karakter in teks
        if unicodedata.category(karakter) not in {"Cc", "Cf"}
        or karakter in "\n\t"
    )
    return SPASI_RE.sub(" ", teks).strip()


def bersihkan_teks(teks):
    """
    Tahap text cleaning:
    1. Mengubah teks menjadi huruf kecil.
    2. Menghapus URL dan alamat email.
    3. Menghapus mention dan penanda retweet.
    4. Menghapus angka, tanda baca, dan simbol.
    5. Mengganti kata slang dengan bentuk standar.
    6. Merapikan spasi berlebih.
    """
    teks = rapikan_teks(teks).lower()

    # Menghapus URL dan alamat email
    teks = URL_RE.sub(" ", teks)
    teks = EMAIL_RE.sub(" ", teks)

    # Menghapus mention dan penanda retweet
    teks = MENTION_RE.sub(" ", teks)
    teks = re.sub(r"^\s*rt\s+", " ", teks)

    # Menghapus angka, tanda baca, dan simbol
    teks = re.sub(r"[^a-z\s]", " ", teks)

    # Mengganti kata tidak baku menjadi bentuk standar
    teks = " ".join(SLANG.get(kata, kata) for kata in teks.split())

    # Menghapus spasi berlebih
    return SPASI_RE.sub(" ", teks).strip()


def hapus_stopword(teks):
    """Menghapus kata umum yang kurang informatif."""
    return " ".join(
        kata for kata in teks.split()
        if kata not in STOPWORDS and len(kata) > 1
    )


def ambil_author(nilai, kunci):
    """Mengambil informasi akun dari kolom author."""
    try:
        data_author = ast.literal_eval(nilai) if isinstance(nilai, str) else {}
        return data_author.get(kunci, "")
    except (ValueError, SyntaxError, AttributeError):
        return ""


def main():
    if not INPUT_FILE.exists():
        sys.exit(
            f"File {INPUT_FILE} tidak ditemukan. "
            "Letakkan file CSV di folder yang sama dengan script."
        )

    data = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
        low_memory=False,
        dtype={"id": "string"},
    )
    jumlah_awal = len(data)

    if "text" not in data.columns or "id" not in data.columns:
        sys.exit("Data scraping harus memiliki kolom 'id' dan 'text'.")

    # Menyiapkan teks asli, memilih bahasa Indonesia, dan menghapus ID duplikat.
    data["text_asli"] = data["text"].map(rapikan_teks)

    if "lang" in data.columns:
        data = data[data["lang"].isin(LANG_DIPERTAHANKAN)].copy()

    data = data.drop_duplicates(subset="id", keep="first")
    data = data[data["text_asli"].ne("")].copy()

    # Menerapkan text cleaning dan penghapusan stopwords.
    data["text_bersih"] = data["text_asli"].map(bersihkan_teks)
    data["text_stopword"] = data["text_bersih"].map(hapus_stopword)

    # Menghapus teks yang kosong setelah cleaning.
    data = data[
        data["text_bersih"].ne("") & data["text_stopword"].ne("")
    ].copy()

    # Mengambil informasi akun jika kolom author tersedia.
    if "author" in data.columns:
        data["username"] = data["author"].map(
            lambda nilai: ambil_author(nilai, "userName")
        )
        data["nama_akun"] = data["author"].map(
            lambda nilai: ambil_author(nilai, "name")
        )

    # Merapikan format tanggal jika kolom createdAt tersedia.
    if "createdAt" in data.columns:
        data["createdAt"] = pd.to_datetime(
            data["createdAt"],
            format="%a %b %d %H:%M:%S %z %Y",
            errors="coerce",
            utc=True,
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Belum ada stemming/Sastrawi pada tahap ini.
    # Kolom text_stemmed sengaja tidak dibuat.

    kolom = [
        "id", "url", "createdAt", "username", "nama_akun",
        "text_asli", "text_bersih", "text_stopword",
        "retweetCount", "replyCount", "likeCount", "quoteCount",
        "viewCount", "bookmarkCount", "lang", "isReply", "isQuote",
    ]
    kolom_ada = [kolom_nama for kolom_nama in kolom if kolom_nama in data.columns]
    data = data[kolom_ada]

    # Menghapus duplikasi berdasarkan teks yang sudah dibersihkan.
    if "text_bersih" in data.columns:
        data = data.drop_duplicates(
            subset="text_bersih", keep="first"
        ).reset_index(drop=True)

    data.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("TEXT CLEANING SELESAI")
    print(f"Data awal      : {jumlah_awal}")
    print(f"Data akhir     : {len(data)}")
    print(f"Jumlah kolom   : {len(data.columns)}")
    print("Tahap          : Text cleaning dan penghapusan stopwords")
    print("Stemming       : Belum dilakukan")
    print(f"File tersimpan : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
