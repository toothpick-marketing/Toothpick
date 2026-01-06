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

def run_automated_sync():
    print("🚀 Starting Direct API Automation Sync...")
    
    # Auth via GitHub Secrets
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    
    for country, sitemap_url in STORES.items():
        print(f"🔍 Scanning {country} catalog via Sitemap...")
        try:
            response = requests.get(sitemap_url, timeout=30)
            soup = BeautifulSoup(response.content, 'xml')
            # Find all product links
            links = [loc.text for loc in soup.find_all('loc') if '/products/' in loc.text]
            print(f"✅ Found {len(links)} products in {country}.")

            for idx, link in enumerate(links[:100]): # Start with 100 products per store
                # Generate unique ID for each product
                product_id = f"{country.lower()}_{idx}"
                
                # Format product for Content API
                entry = {
                    'batchId': len(all_entries),
                    'merchantId': MERCHANT_ID,
                    'method': 'insert',
                    'product': {
                        'offerId': product_id,
                        'title': f"Toothpick Product {idx}", # Logic to fetch title from link can be added
                        'contentLanguage': 'ar',
                        'targetCountry': country,
                        'feedLabel': country,
                        'channel': 'online',
                        'link': link,
                        'availability': 'in stock',
                        'condition': 'new',
                        'googleProductCategory': '505312'
                    }
                }
                all_entries.append(entry)
        except Exception as e:
            print(f"❌ Error scanning {country}: {e}")

    # Final Upload
    if all_entries:
        print(f"🚀 Syncing {len(all_entries)} products directly via API...")
        service.products().custombatch(body={'entries': all_entries}).execute()
        print("✅ Success! Check Merchant Center in a few minutes.")

if __name__ == "__main__":
    run_automated_sync()
