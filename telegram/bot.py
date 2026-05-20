import httpx
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def enviar_mensaje(telegram_id: int, texto: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        respuesta = httpx.post(url, json={
            "chat_id": telegram_id,
            "text": texto,
            "parse_mode": "HTML",
        }, timeout=10)
        return respuesta.status_code == 200
    except Exception as e:
        print(f"Error al enviar mensaje Telegram: {e}")
        return False
    
def enviar_documento(telegram_id: int, pdf_bytes: bytes, filename: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        respuesta = httpx.post(url, data={
            "chat_id": telegram_id,
        }, files={
            "document": (filename, pdf_bytes, "application/pdf"),
        }, timeout=30)
        return respuesta.status_code == 200
    except Exception as e:
        print(f"Error al enviar documento Telegram: {e}")
        return False