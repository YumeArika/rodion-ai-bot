import os
import openai
import gspread
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet("Память")

def get_last_prompt():
    data = sheet.get_all_values()
    if len(data) >= 1:
        return data[-1][0]
    return "Привет! Давай начнем."

def save_to_sheet(prompt, response):
    sheet.append_row([prompt, response])

def generate_response(prompt):
    messages = [
        {"role": "system", "content": "Ты внимательный, поддерживающий ИИ-помощник Родиону, архитектору интерьеров. Отвечай доброжелательно и по делу."},
        {"role": "user", "content": prompt}
    ]
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return completion.choices[0].message['content'].strip()

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        r = requests.post(url, json=payload)
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке сообщения: {e}")

@app.route('/webhook', methods=["POST"])
def webhook():
    data = request.get_json()
    print("[INFO] Получены данные:", data)

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        prompt = data["message"]["text"]

        print(f"[INFO] Сообщение от пользователя {chat_id}: {prompt}")

        try:
            response = generate_response(prompt)
            save_to_sheet(prompt, response)
            send_message(chat_id, response)
        except Exception as e:
            print("[ERROR] Ошибка в webhook:", e)
            send_message(chat_id, "Произошла ошибка. Попробуй позже.")

    return "ok"

@app.route('/')
def index():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(debug=True)
