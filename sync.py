import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
# انسخ الرابط الذي حصلت عليه من جوجل وضعه هنا
PROXY_URL = "https://script.google.com/macros/s/AKfycbxB7yvR7g0U0uzWIP949btjiPIVkq2UP9R7bBqv5U6heFDrvx2hQA5OsqfoiI7nx6-j/exec"

NEW_SITEMAPS = {
    'EG': 'https://eg.toothpick.com/sitemaps/last',
    'AE': 'https://ae.toothpick.com/sitemaps/last'
}

def get_via_proxy(target_url):
    print(f"📡 Requesting via Google Proxy: {target_url}")
    try:
        # نحن نطلب من جوجل أن يطلب هو الرابط من موقعك
        response = requests.get(f"{PROXY_URL}?url={target_url}", timeout=40)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            links = [loc.text for loc in soup.find_all('loc')]
            return links
        else:
            print(f"❌ Proxy Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Proxy Error: {e}")
        return []

def run_automated_sync():
    print("🚀 Starting Toothpick Stealth Sync (Proxy Mode)...")
    
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    for country, url in NEW_SITEMAPS.items():
        links = get_via_proxy(url)
        print(f"🎯 Total products found for {country}: {len(links)}")

        for idx, link in enumerate(links[:200]):
            product_id = f"{country.lower()}_{idx}"
            product_slug = link.split('/')[-1].replace('-', ' ').title()
            
            entry = {
                'batchId': len(all_entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': product_id,
                    'title': f"{product_slug} | Toothpick",
                    'contentLanguage': 'ar' if country == 'EG' else 'en',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png",
                    'availability': 'in stock',
                    'condition': 'new',
                    'brand': 'Toothpick',
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'AED'}
                }
            }
            all_entries.append(entry)

    if all_entries:
        service.products().custombatch(body={'entries': all_entries}).execute()
        print(f"✅ Success! Sent {len(all_entries)} products via Google Proxy.")

if __name__ == "__main__":
    run_automated_sync()
