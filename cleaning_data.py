import ast
import html
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("hasil_scraping.csv")
OUTPUT_FILE = Path("hasil_cleaning.csv")


LANG_DIPERTAHANKAN = {"id", "in"} 
HAPUS_ANGKA = True

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

# Stopword umum Bahasa Indonesia. Kata negasi dipertahankan untuk analisis sentimen.
STOPWORDS = set("""
yang dan di ke dari ini itu untuk dengan pada adalah akan bukan jangan belum
tak tanpa kurang saya kamu dia mereka kita kami anda aku nya pun lah kah si sang
para atau tetapi tapi juga karena agar jika maka dalam sebagai oleh terhadap
setelah sebelum saat bisa dapat sudah lebih sangat hanya saja ada menjadi suatu
seorang sebuah sih dong deh kok nih tuh kan yah lho loh nah mah toh via aja gitu
gini banget yaudah oke eh oh hehe wkwk
""".split())
STOPWORDS -= {"tidak", "bukan", "jangan", "belum", "tak", "tanpa", "kurang"}

URL_RE = re.compile(r"(?:https?://|www\.)\S+|\b(?:pic\.(?:x|twitter)\.com|t\.co)/\S+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
MENTION_RE = re.compile(r"@\w+")
SPASI_RE = re.compile(r"\s+")


def rapikan_teks(teks):
    """Jadikan setiap posting satu baris agar tabel CSV tidak berantakan."""
    if pd.isna(teks):
        return ""
    teks = html.unescape(str(teks))
    teks = unicodedata.normalize("NFKC", teks)
    teks = "".join(c for c in teks if unicodedata.category(c) not in {"Cc", "Cf"} or c in "\n\t")
    return SPASI_RE.sub(" ", teks).strip()


def bersihkan_teks(teks):
    """Lowercase, hapus URL/email/mention, simbol dan angka, lalu normalkan slang."""
    teks = rapikan_teks(teks).lower()
    teks = URL_RE.sub(" ", teks)
    teks = EMAIL_RE.sub(" ", teks)
    teks = MENTION_RE.sub(" ", teks)
    teks = re.sub(r"^\s*rt\s+", " ", teks)
    teks = re.sub(r"[^a-z\s]" if HAPUS_ANGKA else r"[^a-z0-9\s]", " ", teks)
    teks = SPASI_RE.sub(" ", teks).strip()
    teks = " ".join(SLANG.get(kata, kata) for kata in teks.split())
    return SPASI_RE.sub(" ", teks).strip()


def hapus_stopword(teks):
    return " ".join(kata for kata in teks.split()
                    if kata not in STOPWORDS and len(kata) > 1)


def ambil_author(nilai, kunci):
    try:
        return ast.literal_eval(nilai).get(kunci, "") if isinstance(nilai, str) else ""
    except (ValueError, SyntaxError, AttributeError):
        return ""


def main():
    if not INPUT_FILE.exists():
        sys.exit(f"File {INPUT_FILE} tidak ditemukan. Letakkan di folder yang sama dengan script.")

    data = pd.read_csv(INPUT_FILE, encoding="utf-8-sig", low_memory=False, dtype={"id": "string"})
    jumlah_awal = len(data)

    if "text" not in data.columns or "id" not in data.columns:
        sys.exit("Data scraping harus memiliki kolom 'id' dan 'text'.")

    # Ambil hanya posting berbahasa Indonesia dan hilangkan ID duplikat.
    data["text_asli"] = data["text"].map(rapikan_teks)
    data = data[data["lang"].isin(LANG_DIPERTAHANKAN)].copy()
    data = data.drop_duplicates(subset="id", keep="first")
    data = data[data["text_asli"].ne("")].copy()

    data["text_bersih"] = data["text_asli"].map(bersihkan_teks)
    data["text_stopword"] = data["text_bersih"].map(hapus_stopword)

    # Stemming memakai Sastrawi jika sudah terpasang.
    try:
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
        stemmer = StemmerFactory().create_stemmer()
        data["text_stemmed"] = data["text_stopword"].map(stemmer.stem)
        status_stemming = "Sastrawi aktif"
    except ImportError:
        # Tidak mengubah kata jika Sastrawi belum terpasang; hindari stemming palsu.
        data["text_stemmed"] = data["text_stopword"]
        status_stemming = "Sastrawi belum terpasang; kolom stemming sama dengan teks tanpa stopword"

    # Hapus hasil yang kosong setelah proses cleaning.
    data = data[data["text_bersih"].ne("") & data["text_stopword"].ne("")].copy()

    data["username"] = data["author"].map(lambda x: ambil_author(x, "userName"))
    data["nama_akun"] = data["author"].map(lambda x: ambil_author(x, "name"))
    data["createdAt"] = pd.to_datetime(
        data["createdAt"], format="%a %b %d %H:%M:%S %z %Y",
        errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    kolom = [
        "id", "url", "createdAt", "username", "nama_akun",
        "text_asli", "text_bersih", "text_stopword", "text_stemmed",
        "retweetCount", "replyCount", "likeCount", "quoteCount",
        "viewCount", "bookmarkCount", "lang", "isReply", "isQuote"
    ]
    kolom_ada = [k for k in kolom if k in data.columns]
    data = data[kolom_ada]
    data = data.dropna(subset=["id", "url", "createdAt", "username", "text_bersih"])
    data = data[data["username"].astype(str).str.strip().ne("")]
    data = data.drop_duplicates(subset="text_bersih", keep="first").reset_index(drop=True)

    data.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("CLEANING DATA SELESAI")
    print(f"Data awal       : {jumlah_awal}")
    print(f"Data akhir      : {len(data)}")
    print(f"Kolom akhir     : {len(data.columns)}")
    print(f"Stemming        : {status_stemming}")
    print(f"File tersimpan  : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
