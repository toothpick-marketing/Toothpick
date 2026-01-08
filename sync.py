import os
import json
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account

MERCHANT_ID = '5693326724'
PROXY_URL = "https://script.google.com/macros/s/AKfycbxxJ_JFEpRZvzdZDPhohHup8rjhGTSFIfRsPVlCSps0zzJ77i26lNB8C_cM0xcjaNoY/exec"

def fetch_links(url):
    try:
        res = requests.get(f"{PROXY_URL}?url={url}", timeout=60)
        return [l for l in res.text.split(',') if len(l) > 10]
    except:
        return []

def run_automated_sync():
    print("🤖 Starting FULL AUTOMATION Crawl...")
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_links = {'EG': [], 'AE': []}
    
    # أتمتة: فحص أول 5 صفحات من المنتجات تلقائياً لكل دولة
    for country in ['EG', 'AE']:
        base = f"https://{country.lower()}.toothpick.com/{'ar' if country=='EG' else 'en'}/products"
        for page in range(1, 6):
            p_url = f"{base}?page={page}"
            found = fetch_links(p_url)
            all_links[country].extend(found)
        
        all_links[country] = list(set(all_links[country]))
        print(f"✅ Found {len(all_links[country])} products for {country} WITHOUT manual work!")

    # تحويل الروابط إلى منتجات في Google
    entries = []
    for country, links in all_links.items():
        for idx, link in enumerate(links):
            title = link.split('/')[-1].replace('-', ' ').title()
            entries.append({
                'batchId': len(entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': f"{country.lower()}_{idx}",
                    'title': title,
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png",
                    'contentLanguage': 'ar' if country == 'EG' else 'en',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'availability': 'in stock',
                    'condition': 'new',
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'AED'}
                }
            })

    if entries:
        # إرسال البيانات على دفعات
        for i in range(0, len(entries), 100):
            batch = entries[i:i+100]
            service.products().custombatch(body={'entries': batch}).execute()
        print(f"🏁 DONE! Total Synced: {len(entries)} products.")

if __name__ == "__main__":
    run_automated_sync()
