import json
import os
import requests
from http.server import BaseHTTPRequestHandler

P1SMS_API_KEY = os.environ.get("P1SMS_API_KEY")
P1SMS_SENDER = os.environ.get("P1SMS_SENDER", "SMS")

def send_sms(phone: str, text: str):
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if phone.startswith("8"):
        phone = "7" + phone[1:]
    
    payload = {
        "apiKey": P1SMS_API_KEY,
        "sms": [{
            "channel": "char",
            "sender": P1SMS_SENDER,
            "phone": phone,
            "text": text
        }]
    }
    response = requests.post(
        "https://admin.p1sms.kz/apiSms/create",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        
        try:
            data = json.loads(body)
        except:
            data = {}

        # Достаём телефон и имя контакта из webhook amoCRM
        leads = data.get("leads", {})
        contacts = data.get("contacts", {})
        
        phone = None
        name = "Клиент"

        # Берём первый контакт
        for contact in contacts.get("update", contacts.get("add", [])):
            for field in contact.get("custom_fields", []):
                if field.get("code") == "PHONE":
                    values = field.get("values", [])
                    if values:
                        phone = values[0].get("value")
                        break
            name = contact.get("name", "Клиент")
            break

        # Берём статус сделки
        status_name = ""
        for lead in leads.get("status", leads.get("add", [])):
            status_name = lead.get("status_id", "")
            break

        if phone:
            text = f"{name}, ваша заявка принята. Менеджер свяжется с вами в ближайшее время."
            send_sms(phone, text)
            self.send_response(200)
        else:
            self.send_response(400)
        
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "amo-sms-bot running"}).encode())
