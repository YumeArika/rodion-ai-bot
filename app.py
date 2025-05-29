import os
import json
import openai
import gspread
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
spreadsheet_url = os.getenv("GOOGLE_SPREADSHEET_URL")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = os.getenv("GOOGLE_CREDS")
client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope))
spreadsheet = client.open_by_url(spreadsheet_url)

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        message = data.get("message", {}).get("text", "")
        chat_id = data.get("message", {}).get("chat", {}).get("id")

        if not message or not chat_id:
            return "No message or chat_id", 400

        # Пример генерации ответа
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        answer = response.choices[0].message["content"]

        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
