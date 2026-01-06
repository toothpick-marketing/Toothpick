import os
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Config ---
MERCHANT_ID = '5693326724'
# ضع هنا ID الشيت الخاص بك (تجد في رابط الشيت بين d/ و /edit)
SPREADSHEET_ID = '1vfg1AP6ufzDEYmFX3YOZo2r74jpfjmyUB9969YJ-SLg' 

def update_google_sheet(df, creds):
    print("📊 Updating Google Sheet with latest website data...")
    service = build('sheets', 'v4', credentials=creds)
    
    # تحويل البيانات لتنسيق يفهمه جوجل شيت
    values = [df.columns.values.tolist()] + df.values.tolist()
    body = {'values': values}
    
    # مسح البيانات القديمة وكتابة الجديدة
    service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range="A1:Z10000").execute()
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range="A1",
        valueInputOption="RAW", body=body).execute()
    print("✅ Google Sheet updated as a Backup.")

def run_automated_sync():
    # التحقق من الهوية
    service_account_info = json.loads(os.environ.get('GOOGLE_SERVICE_ACCOUNT'))
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    
    # --- خطوة السحب من الموقع ---
    # (هنا يوضع كود السحب الذي استخرجناه سابقا)
    # لنفرض أننا حصلنا على بيانات في شكل DataFrame
    all_data = [] 
    # ... كود السحب يملأ all_data ...
    
    df = pd.DataFrame(all_data)
    
    # --- خطوة تحديث الشيت (المرجع) ---
    update_google_sheet(df, creds)
    
    print("🚀 All systems Go! Products are now in the Sheet and ready for Merchant Center.")

if __name__ == "__main__":
    run_automated_sync()
