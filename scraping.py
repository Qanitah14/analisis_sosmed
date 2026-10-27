import requests
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import quote

KEYWORDS = [
    '"Pak Botok" Pati',
    '"Supriyono" "Bank Mandiri"',
    '"rekening diblokir" "Pak Botok"',
    '"rekening dibekukan" Pati',
]

hasil = []
headers = {
    "User-Agent": "Mozilla/5.0"
}

for keyword in KEYWORDS:
    print(f"Mencari: {keyword}")

    url = (
        "https://news.google.com/rss/search?q="
        + quote(keyword)
        + "&hl=id&gl=ID&ceid=ID:id"
    )

    try:
        response = requests.get(
            url, headers=headers, timeout=20
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            hasil.append({
                "keyword": keyword,
                "judul": item.findtext("title", ""),
                "tanggal": item.findtext("pubDate", ""),
                "tautan": item.findtext("link", ""),
                "sumber": item.findtext("source", ""),
            })

    except Exception as error:
        print(f"Gagal mengambil data: {error}")

df = pd.DataFrame(hasil)

if not df.empty:
    df = df.drop_duplicates(subset=["tautan"])
    df.to_csv(
        "hasil_pencarian_kasus.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print(f"\nTotal hasil: {len(df)}")
    print("Data tersimpan di hasil_pencarian_kasus.csv")
else:
    print("\nBelum ditemukan hasil.")
    print("Coba variasi kata kunci lain.")
