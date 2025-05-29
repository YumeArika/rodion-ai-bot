import os
import json
import requests
from flask import Flask, request
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Восстанавливаем credentials.json из переменной окружения
with open("credentials.json", "w") as f:
    f.write(os.getenv("CREDS_JSON"))

# Авторизация в Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(os.getenv("SHEET_ID")).worksheet("Память")

# OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Flask app
app = Flask(__name__)

def append_to_sheet(user_id, user_msg, bot_msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, str(user_id), user_msg, bot_msg])

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Ошибка отправки сообщения:", e)

def get_gpt_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Ошибка OpenAI:", e)
        return "Произошла ошибка при обращении к OpenAI."

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "no message", 400

    message = data["message"]
    chat_id = message["chat"]["id"]
    user_msg = message.get("text", "")

    bot_msg = get_gpt_response(user_msg)
    append_to_sheet(chat_id, user_msg, bot_msg)
    send_message(chat_id, bot_msg)

    return "ok", 200

@app.route('/')
def index():
    return "Bot is running."

if __name__ == "__main__":
    app.run()
