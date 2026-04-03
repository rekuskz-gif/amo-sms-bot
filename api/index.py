import os
import json
import requests
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler

P1SMS_API_KEY = os.environ.get("P1SMS_API_KEY")
P1SMS_SENDER = os.environ.get("P1SMS_SENDER", "SMS")

def send_sms(phone: str, text: str):
    digits = ''.join(filter(str.isdigit, phone))
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    payload = {
        "apiKey": P1SMS_API_KEY,
        "sms": [{
            "channel": "char",
            "sender": P1SMS_SENDER,
            "phone": digits,
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
        body = self.rfile.read(length).decode("utf-8")
        
        # Логируем что пришло от amoCRM
        print("=== BODY FROM AMOCRM ===")
        print(body[:2000])
        print("========================")
        
        flat = parse_qs(body)
        
        # Логируем все ключи
        print("=== KEYS ===")
        for key in flat.keys():
            print(f"{key} = {flat[key]}")
        print("============")
        
        # Ищем телефон среди всех значений
        phone = None
        for key, values in flat.items():
            for v in values:
                digits = ''.join(filter(str.isdigit, v))
                if 10 <= len(digits) <= 12:
                    phone = v
                    print(f"FOUND PHONE: {phone} in key: {key}")
                    break

        if phone:
            text = "Ваша заявка принята. Менеджер свяжется с вами в ближайшее время."
            result = send_sms(phone, text)
            print(f"P1SMS RESPONSE: {result}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "phone": phone}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
