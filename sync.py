import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
PRODUCT_SITEMAPS = {
    'EG': [
        'https://eg.toothpick.com/sitemap-products-1.xml',
        'https://eg.toothpick.com/sitemap-products-2.xml'
    ],
    'SA': [
        'https://sa.toothpick.com/sitemap-products-1.xml',
        'https://sa.toothpick.com/sitemap-products-2.xml'
    ]
}

# إضافة "هوية متصفح" لإجبار الموقع على إظهار البيانات
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

def get_links_from_xml(url):
    print(f"🔗 Attempting to read links from: {url}")
    try:
        # استخدام الـ HEADERS هنا هو المفتاح
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to access {url}. Status Code: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, 'xml')
        links = [loc.text for loc in soup.find_all('loc')]
        return links
    except Exception as e:
        print(f"⚠️ Connection Error on {url}: {e}")
        return []

def run_automated_sync():
    print("🚀 Starting Toothpick Advanced Crawler (V4 - Stealth Mode)...")
    
    # Auth via GitHub Secrets
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    
    for country, sitemaps in PRODUCT_SITEMAPS.items():
        country_links = []
        for sitemap_url in sitemaps:
            links = get_links_from_xml(sitemap_url)
            country_links += links
        
        print(f"🎯 Total products found for {country}: {len(country_links)}")

        if len(country_links) > 0:
            for idx, link in enumerate(country_links[:150]):
                product_id = f"{country.lower()}_{idx}"
                slug = link.split('/')[-1]
                brand = slug.split('-')[0].replace('__', ' ').capitalize()
                
                entry = {
                    'batchId': len(all_entries),
                    'merchantId': MERCHANT_ID,
                    'method': 'insert',
                    'product': {
                        'offerId': product_id,
                        'title': f"{brand} - Dental Supplies", 
                        'contentLanguage': 'ar',
                        'targetCountry': country,
                        'feedLabel': country,
                        'channel': 'online',
                        'link': link,
                        'imageLink': "https://toothpick.com/logo.png",
                        'availability': 'in stock',
                        'condition': 'new',
                        'brand': brand,
                        'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'SAR'}
                    }
                }
                all_entries.append(entry)

    if all_entries:
        print(f"🚀 Pushing {len(all_entries)} discovered products to API...")
        service.products().custombatch(body={'entries': all_entries}).execute()
        print("✅ Success! Sync complete.")
    else:
        print("❌ Still found 0 links. The site might be blocking GitHub's IP range.")

if __name__ == "__main__":
    run_automated_sync()
