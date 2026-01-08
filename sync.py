import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
# استخدمنا الروابط الجديدة التي أعطاها لك المبرمج
NEW_SITEMAPS = {
    'EG': 'https://eg.toothpick.com/sitemaps/last',
    'AE': 'https://ae.toothpick.com/sitemaps/last'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/xml,text/xml,*/*'
}

def get_links_from_last_sitemap(url):
    print(f"🔗 Accessing New Sitemap: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            # استخراج الروابط من وسوم <loc>
            links = [loc.text for loc in soup.find_all('loc')]
            return links
        else:
            return []
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return []

def run_automated_sync():
    print("🚀 Starting Toothpick Automated Sync (Sitemap-Last Mode)...")
    
    # Auth
    try:
        service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        service = build('content', 'v2.1', credentials=creds)
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    all_entries = []
    
    for country, url in NEW_SITEMAPS.items():
        links = get_links_from_last_sitemap(url)
        print(f"🎯 Found {len(links)} products for {country}.")

        for idx, link in enumerate(links[:250]): # سحب أول 250 منتج لكل دولة
            # استخراج اسم المنتج من الرابط بطريقة ذكية
            product_slug = link.split('/')[-1].replace('-', ' ').title()
            
            entry = {
                'batchId': len(all_entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': f"{country.lower()}_{idx}_{idx}",
                    'title': f"{product_slug} | Toothpick Dental",
                    'contentLanguage': 'ar' if country == 'EG' else 'en',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png", # سيتم تحسينها لاحقاً
                    'availability': 'in stock',
                    'condition': 'new',
                    'brand': 'Toothpick',
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'AED'}
                }
            }
            all_entries.append(entry)

    if all_entries:
        print(f"🚀 Pushing {len(all_entries)} products to Merchant Center API...")
        service.products().custombatch(body={'entries': all_entries}).execute()
        print("✅ Sync Successfully Sent!")
    else:
        print("❌ No products found. We might need to check the link content manually.")

if __name__ == "__main__":
    run_automated_sync()
