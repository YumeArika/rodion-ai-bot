from flask import Flask, request
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# Загружаем переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GOOGLE_SHEET_TAB = os.environ.get("GOOGLE_SHEET_TAB", "Память")

# Настройка OpenAI клиента
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# Настройка Google Sheets
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file("creds.json", scopes=scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_TAB)
except Exception as e:
    sheet = None
    print(f"[ERROR] Не удалось подключиться к Google Sheets: {e}")

# Главная страница
@app.route('/')
def index():
    return "Rodion AI Bot is running!"

# Обработка входящих сообщений Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print(f"[INFO] Получены данные: {data}")

        if "message" in data and "text" in data["message"]:
            user_message = data["message"]["text"]
            user_id = data["message"]["chat"]["id"]
            print(f"[INFO] Сообщение от пользователя {user_id}: {user_message}")

            # Получаем ответ от OpenAI
            response = client_ai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_message}]
            )
            bot_reply = response.choices[0].message.content.strip()
            print(f"[INFO] Ответ от бота: {bot_reply}")

            # Отправляем ответ пользователю
            send_message(user_id, bot_reply)

            # Записываем в таблицу
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, str(user_id), user_message, bot_reply])
                print("[INFO] Диалог записан в Google Таблицу")
            else:
                print("[WARNING] Таблица не подключена, запись невозможна")

        return "OK", 200
    except Exception as e:
        print(f"[ERROR] Ошибка в webhook: {e}")
        return "Internal Server Error", 500

# Отправка сообщения в Telegram
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        r = requests.post(url, json=payload)
        print(f"[INFO] Отправлен ответ: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке сообщения: {e}")

if __name__ == '__main__':
    app.run(debug=True)

