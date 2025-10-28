import requests
import time
from flask import Flask
import threading
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# להריץ את Flask בת'רד נפרד
threading.Thread(target=run_flask).start()

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# ...שאר הקוד של הבוט שלך

# === פרטים אישיים שלך ===
TOKEN = "8307413253:AAH0SxaykxklOMRXJmZQKYd1iaUzoI-rhLY"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzQ9G_6HYwwqIvSV1T7nvUMAmwKuuJvDlnLH67HQaEiEOMi2UgE7Wxm7w7d6jIlwJDtGw/exec"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

CATEGORIES = [
    "סופר משותף", "סופר דירה", "אישי", "טבק", "תרבות",
    "אוכל בחוץ", "אחרי מפעל", "דלק מוקי", "לק ג'ל", "בורקס", "תספורות"
]

def get_updates(offset=None):
    url = BASE_URL + "/getUpdates"
    params = {"timeout": 100, "offset": offset}
    r = requests.get(url, params=params)
    return r.json()

def send_message(chat_id, text, reply_markup=None):
    url = BASE_URL + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(url, json=data)

def main():
    offset = None
    state = {}
    while True:
        updates = get_updates(offset)
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message:
                    continue
                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                # התחלה
                if text == "/start" or chat_id not in state:
                    state[chat_id] = {"step": "action"}
                    keyboard = {"keyboard": [["➕ הוספת הוצאה", "📊 בדיקת סטטוס תקציב"]],
                                "one_time_keyboard": True}
                    send_message(chat_id, "שלום! מה תרצה לעשות?", reply_markup=keyboard)

                elif state[chat_id]["step"] == "action":
                    if "הוספת הוצאה" in text:
                        state[chat_id]["step"] = "category"
                        keyboard = {"keyboard": [[c] for c in CATEGORIES], "one_time_keyboard": True}
                        send_message(chat_id, "בחר קטגוריה:", reply_markup=keyboard)
                    elif "סטטוס תקציב" in text:
                        r = requests.post(SCRIPT_URL, json={"action": "report"})
                        if r.status_code == 200:
                            report = r.json().get("report", {})
                            msg = "📊 סטטוס תקציב לחודש האחרון:\n"
                            for cat, total in report.items():
                                msg += f"{cat}: {total} ₪\n"
                            send_message(chat_id, msg)
                        else:
                            send_message(chat_id, "❌ שגיאה בשליפת הנתונים.")
                        state.pop(chat_id)

                elif state[chat_id]["step"] == "category":
                    state[chat_id]["category"] = text
                    state[chat_id]["step"] = "amount"
                    send_message(chat_id, "הכנס סכום (מספר בלבד):")

                elif state[chat_id]["step"] == "amount":
                    amount = text
                    data = {
                        "user": message["from"].get("username", message["from"].get("first_name", "לא ידוע")),
                        "category": state[chat_id]["category"],
                        "amount": amount
                    }
                    r = requests.post(SCRIPT_URL, json=data)
                    if r.status_code == 200:
                        send_message(chat_id, "✅ ההוצאה נשמרה בהצלחה!")
                    else:
                        send_message(chat_id, "❌ שגיאה בשליחה לגליון.")
                    state.pop(chat_id)

        time.sleep(1)

if __name__ == "__main__":
    main()
