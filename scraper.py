import os
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Service Account Credentials Load
# Local testing ke liye serviceAccountKey.json ka path dein
if os.path.exists("serviceAccountKey.json"):
    cred = credentials.Certificate("serviceAccountKey.json")
else:
    # GitHub Actions ke liye Environment Variable use hoga
    firebase_config = json.loads(os.environ.get("FIREBASE_SERVICE_ACCOUNT"))
    cred = credentials.Certificate(firebase_config)

firebase_admin.initialize_app(cred)
db = firestore.client()

def fetch_and_upload_prompts():
    target_url = "https://faymas.in"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(target_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "html.parser")
        
        # Site ke structure ke according prompt cards locate karna
        # (Website HTML structure ke anusar selectors adjust ho sakte hain)
        items = soup.find_all("div", class_="card") or soup.find_all("article")
        
        uploaded_count = 0
        batch = db.batch()

        for item in items:
            if uploaded_count >= 10:
                break

            # Prompt Text & Image extraction
            prompt_elem = item.find("p") or item.find("h2") or item.find("h3")
            img_elem = item.find("img")

            prompt_text = prompt_elem.get_text(strip=True) if prompt_elem else None
            img_url = img_elem["src"] if img_elem and "src" in img_elem.attrs else ""

            if prompt_text:
                doc_ref = db.collection("prompts").document()
                batch.set(doc_ref, {
                    "prompt": prompt_text,
                    "imageUrl": img_url,
                    "category": "Trending AI",
                    "createdAt": firestore.SERVER_TIMESTAMP
                })
                uploaded_count += 1

        if uploaded_count > 0:
            batch.commit()
            print(f"Successfully auto-uploaded {uploaded_count} prompts from Faymas.in!")
        else:
            print("No new prompts found.")

    except Exception as e:
        print(f"Error while scraping: {str(e)}")

if __name__ == "__main__":
    fetch_and_upload_prompts()