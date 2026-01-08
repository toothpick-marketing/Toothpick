import os
import json
import pandas as pd
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Configuration ---
MERCHANT_ID = '5693326724'
# رابط ملف الـ CSV الخاص بـ Google Sheet (بصيغة التصدير)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1vfg1AP6ufzDEYmFX3YOZo2r74jpfjmyUB9969YJ-SLg/export?format=csv&gid=0"

def run_automated_sync():
    print("🚀 Starting Sync from Google Sheets...")
    
    # 1. قراءة البيانات من جوجل شيت مباشرة
    try:
        df = pd.read_csv(SHEET_URL)
        print(f"✅ Successfully read {len(df)} products from Sheets.")
    except Exception as e:
        print(f"❌ Error reading Sheet: {e}")
        return

    # 2. إعداد الاتصال بـ Google Merchant API
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('content', 'v2.1', credentials=creds)

    all_entries = []
    for _, row in df.iterrows():
        entry = {
            'batchId': len(all_entries),
            'merchantId': MERCHANT_ID,
            'method': 'insert',
            'product': {
                'offerId': str(row['id']),
                'title': str(row['title']),
                'description': str(row['description']),
                'link': str(row['link']),
                'imageLink': str(row['image_link']),
                'contentLanguage': 'ar' if row['country_code'] == 'EG' else 'en',
                'targetCountry': str(row['country_code']),
                'feedLabel': str(row['country_code']),
                'channel': 'online',
                'availability': 'in stock',
                'condition': 'new',
                'brand': str(row['brand']),
                'price': {'value': str(row['sale_price']), 'currency': str(row['currency'])}
            }
        }
        all_entries.append(entry)

    # 3. إرسال البيانات
    if all_entries:
        # إرسال على دفعات كل دفعة 100 منتج
        for i in range(0, len(all_entries), 100):
            batch = all_entries[i:i+100]
            service.products().custombatch(body={'entries': batch}).execute()
        print(f"🏁 DONE! Total {len(all_entries)} products synced to Merchant Center.")

if __name__ == "__main__":
    run_automated_sync()
