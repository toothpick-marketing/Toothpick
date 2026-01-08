import os
import json
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account

MERCHANT_ID = '5693326724'
PROXY_URL = "https://script.google.com/macros/s/AKfycbwjEHPiqlg_8glVXp9CcE_q4ole9NKSQCtdVdkDbacFMA9T1whKKWAg8eC7RQuYm0pV/exec"

# صفحات المنتجات الرئيسية التي سنبدأ منها الزحف
STORE_PAGES = {
    'EG': 'https://eg.toothpick.com/ar/products',
    'AE': 'https://ae.toothpick.com/en/products'
}

def get_automated_links(start_url):
    print(f"🕵️ Automated Crawling via Google: {start_url}")
    try:
        response = requests.get(f"{PROXY_URL}?url={start_url}", timeout=60)
        if response.status_code == 200 and response.text:
            links = response.text.split(',')
            # تصفية الروابط لضمان الجودة
            unique_links = list(set([l for l in links if '/products/' in l]))
            return unique_links
        return []
    except:
        return []

def run_automated_sync():
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    for country, start_url in STORE_PAGES.items():
        links = get_automated_links(start_url)
        print(f"🚀 Found {len(links)} products automatically for {country}!")

        for idx, link in enumerate(links):
            product_id = f"{country.lower()}_{idx}"
            title = link.split('/')[-1].replace('-', ' ').title()
            
            all_entries.append({
                'batchId': len(all_entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': product_id,
                    'title': f"{title} | Toothpick",
                    'contentLanguage': 'ar' if country == 'EG' else 'en',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png", # سنحدث الصور لاحقاً
                    'availability': 'in stock',
                    'condition': 'new',
                    'brand': 'Toothpick',
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'AED'}
                }
            })

    if all_entries:
        # إرسال البيانات على دفعات (Batches) لتجنب ضغط الـ API
        service.products().custombatch(body={'entries': all_entries}).execute()
        print(f"✅ Full Automation Success: {len(all_entries)} products synced!")

if __name__ == "__main__":
    run_automated_sync()
