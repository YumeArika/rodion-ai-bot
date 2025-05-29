
from flask import Flask, request
import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
gc = gspread.authorize(creds)

sheet_id = os.getenv("SHEET_ID")
if not sheet_id:
    raise ValueError("SHEET_ID не найден в .env")

worksheet_name = os.getenv("GOOGLE_SHEET_TAB", "Память")
sheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)

@app.route("/")
def index():
    return "Бот успешно запущен!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
