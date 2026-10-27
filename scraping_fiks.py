from apify_client import ApifyClient
import pandas as pd
import os
from dotenv import load_dotenv

# Initialize the ApifyClient with your API token
load_dotenv()
token = os.getenv("APIFY_API_TOKEN")
if not token:
    raise ValueError("APIFY_API_TOKEN belum diatur. Isi file .env terlebih dahulu.")
client = ApifyClient(token)
# Prepare the Actor input
run_input = {
    "filter:blue_verified": False,
    "filter:consumer_video": False,
    "filter:has_engagement": False,
    "filter:hashtags": False,
    "filter:images": False,
    "filter:links": False,
    "filter:media": False,
    "filter:mentions": False,
    "filter:native_video": False,
    "filter:nativeretweets": False,
    "filter:news": False,
    "filter:pro_video": False,
    "filter:quote": False,
    "filter:replies": False,
    "filter:safe": False,
    "filter:spaces": False,
    "filter:twimg": False,
    "filter:videos": False,
    "filter:vine": False,
    "from": "elonmusk",
    "include:nativeretweets": False,
    "lang": "in",
    "maxItems": 300,
    "searchTerms": [
        "Aktivis Pati",
        "Pemblokiran Rekening Aktivis Pati",
        "Demo Pati"
    ]
}


    # Run the Actor and wait for it to finish
run = client.actor("CJdippxWmn9uRfooo").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)

items = []

dataset_id = (
    run.get("defaultDatasetId")
    if isinstance(run, dict)
    else getattr(run, "default_dataset_id", None)
)

if dataset_id:
    items = list(client.dataset(dataset_id).iterate_items())

    print("Dataset ID:", dataset_id)
    print("Jumlah data:", len(items))

    if items:
        import pandas as pd

        df = pd.DataFrame(items)
        df.to_csv(
            "hasil_scraping.csv",
            index=False,
            encoding="utf-8-sig"
        )
        print("Hasil disimpan ke hasil_scraping.csv")
    else:
        print("Dataset kosong. Periksa output dan log actor.")
else:
    print("Dataset ID tidak ditemukan.")
