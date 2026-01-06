import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
STORES = {
    'EG': 'https://eg.toothpick.com/sitemap.xml',
    'SA': 'https://sa.toothpick.com/sitemap.xml'
}

def get_deep_product_links(sitemap_url):
    print(f"🌐 Deep Scanning Index: {sitemap_url}")
    all_product_links = []
    try:
        response = requests.get(sitemap_url, timeout=30)
        soup = BeautifulSoup(response.content, 'xml')
        
        # البحث عن كل الروابط داخل الفهرس
        locs = [loc.text for loc in soup.find_all('loc')]
        
        for loc in locs:
            if 'products' in loc and '.xml' in loc:
                print(f"  📂 Entering Sub-Sitemap: {loc}")
                sub_res = requests.get(loc, timeout=30)
                sub_soup = BeautifulSoup(sub_res.content, 'xml')
                all_product_links += [l.text for l in sub_soup.find_all('loc')]
            elif '/products/' in loc:
                all_product_links.append(loc)
                
    except Exception as e:
        print(f"⚠️ Error scanning {sitemap_url}: {e}")
    return list(set(all_product_links))

def run_automated_sync():
    print("🚀 Starting Toothpick Advanced Crawler...")
    
    # Auth
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    
    for country, url in STORES.items():
        links = get_deep_product_links(url)
        print(f"✅ Success! Found {len(links)} actual products for {country}.")

        # رفع أول 50 منتج كعينة للتأكد من نجاح الرفع الفعلي
        for idx, link in enumerate(links[:50]):
            product_id = f"{country.lower()}_{idx}"
            # استخراج براند تقريبي من الرابط
            brand = link.split('/')[-1].split('-')[0].replace('__', ' ').capitalize()
            
            entry = {
                'batchId': len(all_entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': product_id,
                    'title': brand + " - Toothpick Dental Product", 
                    'contentLanguage': 'ar',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png", # سيتم تحسينها لجلب صورة المنتج لاحقاً
                    'availability': 'in stock',
                    'condition': 'new',
                    'brand': brand,
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'SAR'}
                }
            }
            all_entries.append(entry)

    if all_entries:
        print(f"🚀 Pushing {len(all_entries)} discovered products to Google...")
        service.products().custombatch(body={'entries': all_entries}).execute()
        print("✅ Finished! Products are now syncing with Google API.")

if __name__ == "__main__":
    run_automated_sync()
