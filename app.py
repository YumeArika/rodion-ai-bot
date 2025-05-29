import os
import json
from flask import Flask, request
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Инициализация OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Подготовка доступа к Google Sheets через GOOGLE_CREDS
creds_json = os.getenv("GOOGLE_CREDS")
if not creds_json:
    raise ValueError("GOOGLE_CREDS переменная окружения не найдена")

with open("creds.json", "w") as f:
    f.write(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

spreadsheet_url = os.getenv("SPREADSHEET_URL")
spreadsheet = client.open_by_url(spreadsheet_url)
worksheet = spreadsheet.worksheet("Память")

@app.route("/webhook", methods=["POST"])
def index():
    if request.method == "POST":
        user_input = request.json.get("text", "")
        if not user_input:
            return {"error": "No input text provided"}, 400

        prompt = f"Пользователь написал: {user_input}\nОтветь ему как мотивационный помощник:"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            reply = response.choices[0].message["content"].strip()

            # Сохраняем диалог в Google Таблицу
            worksheet.append_row([user_input, reply])

            return {"reply": reply}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)