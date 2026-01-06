import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
# حددنا هنا روابط "خرائط المنتجات" مباشرة لضمان الوصول للبيانات
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

def get_links_from_xml(url):
    print(f"🔗 Extracting links from: {url}")
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'xml')
        links = [loc.text for loc in soup.find_all('loc')]
        return links
    except Exception as e:
        print(f"⚠️ Error reading {url}: {e}")
        return []

def run_automated_sync():
    print("🚀 Starting Toothpick Direct-Sitemap Sync...")
    
    # Auth via GitHub Secrets
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    
    for country, sitemaps in PRODUCT_SITEMAPS.items():
        country_links = []
        for sitemap_url in sitemaps:
            country_links += get_links_from_xml(sitemap_url)
        
        print(f"✅ Found {len(country_links)} actual product links for {country}.")

        # رفع أول 100 منتج كدفعة أولى آمنة
        for idx, link in enumerate(country_links[:100]):
            product_id = f"{country.lower()}_{idx}"
            # منطق استخراج البراند من الرابط (Slug)
            slug = link.split('/')[-1]
            brand = slug.split('-')[0].replace('__', ' ').capitalize()
            
            entry = {
                'batchId': len(all_entries),
                'merchantId': MERCHANT_ID,
                'method': 'insert',
                'product': {
                    'offerId': product_id,
                    'title': f"{brand} - Toothpick Professional Care", 
                    'contentLanguage': 'ar',
                    'targetCountry': country,
                    'feedLabel': country,
                    'channel': 'online',
                    'link': link,
                    'imageLink': "https://toothpick.com/logo.png", # سيتم تحسينها لجلب صورة المنتج
                    'availability': 'in stock',
                    'condition': 'new',
                    'brand': brand,
                    'price': {'value': '100', 'currency': 'EGP' if country == 'EG' else 'SAR'}
                }
            }
            all_entries.append(entry)

    if all_entries:
        print(f"🚀 Pushing {len(all_entries)} discovered products to Merchant Center API...")
        service.products().custombatch(body={'entries': all_entries}).execute()
        print("✅ Success! Check your Merchant Center 'All Products' tab now.")

if __name__ == "__main__":
    run_automated_sync()
