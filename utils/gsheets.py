import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 👇 Thay link Google Sheets của bạn vào đây
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ThOEMd2B0q6BrW8h441eGxw5lXgr8FtTIwrDO_fKXGM/edit"

# Kết nối tới Google Sheets
def connect_gs(sheet_name):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        "./service_account.json", scopes=scopes
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
    return sheet

def load_sheet(sheet_name):
    sheet = connect_gs(sheet_name)
    data = sheet.get_all_values()
    if not data:
        return pd.DataFrame()
    headers = data[0]
    rows = data[1:]
    return pd.DataFrame(rows, columns=headers)

# Ghi đè DataFrame vào sheet
def save_sheet(sheet_name, df: pd.DataFrame):
    sheet = connect_gs(sheet_name)
    sheet.clear()
    if not df.empty:
        sheet.update([df.columns.values.tolist()] + df.values.tolist())