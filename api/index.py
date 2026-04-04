import os
import json
import requests
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler

P1SMS_API_KEY = os.environ.get("P1SMS_API_KEY")
AMO_TOKEN = os.environ.get("AMO_TOKEN")
AMO_DOMAIN = os.environ.get("AMO_DOMAIN", "kazafkz.amocrm.ru")

def get_phone_by_lead_id(lead_id):
    headers = {"Authorization": f"Bearer {AMO_TOKEN}"}
    url = f"https://{AMO_DOMAIN}/api/v4/leads/{lead_id}?with=contacts"
    r = requests.get(url, headers=headers)
    print(f"LEAD RESPONSE: {r.status_code} {r.text[:500]}")
    if r.status_code != 200:
        return None
    data = r.json()
    contacts = data.get("_embedded", {}).get("contacts", []) or []
    if not contacts:
        return None
    contact_id = contacts[0]["id"]
    print(f"CONTACT ID: {contact_id}")
    url2 = f"https://{AMO_DOMAIN}/api/v4/contacts/{contact_id}"
    r2 = requests.get(url2, headers=headers)
    print(f"CONTACT DETAIL: {r2.status_code} {r2.text[:500]}")
    if r2.status_code != 200:
        return None
    contact = r2.json()
    for field in contact.get("custom_fields_values", []) or []:
        if field.get("field_code") == "PHONE":
            values = field.get("values", [])
            if values:
                return values[0].get("value")
    return None

def send_sms(phone: str, text: str):
    digits = ''.join(filter(str.isdigit, phone))
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    payload = {
        "apiKey": P1SMS_API_KEY,
        "sms": [{
            "channel": "char",
            "sender": "VIRTA",
            "phone": digits,
            "text": text,
            "tag": "spasibo3"
        }]
    }
    response = requests.post(
        "https://admin.p1sms.kz/apiSms/create",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"P1SMS RESPONSE: {response.text}")
    return response.json()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        flat = parse_qs(body)
        lead_id = None
        for key, values in flat.items():
            if "leads" in key and key.endswith("[id]"):
                lead_id = values[0]
                break
        print(f"LEAD ID: {lead_id}")
        if lead_id:
            phone = get_phone_by_lead_id(lead_id)
            print(f"PHONE: {phone}")
            if phone:
                text = "Большое спасибо! Ждем ваш отзыв: https://share.google/R07PQVBPZPRHzZ8bK"
                send_sms(phone, text)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
