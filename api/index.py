import os
import json
import requests
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler

P1SMS_API_KEY = os.environ.get("P1SMS_API_KEY")
P1SMS_SENDER = os.environ.get("P1SMS_SENDER", "SMS")

def send_sms(phone: str, text: str):
    phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
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

def extract_phones(data):
    phones = []
    for key, values in data.items():
        if "phone" in key.lower():
            for v in values:
                if v and len(v) >= 10:
                    phones.append(v)
    return phones

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        
        # Парсим form-urlencoded от amoCRM
        data = parse_qs(body)
        
        phones = extract_phones(data)
        
        if phones:
            for phone in phones[:1]:  # Отправляем только первому
                text = "Ваша заявка принята. Менеджер свяжется с вами в ближайшее время."
                send_sms(phone, text)
            self.send_response(200)
        else:
            self.send_response(200)  # Возвращаем 200 чтобы amoCRM не отключал хук
        
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
