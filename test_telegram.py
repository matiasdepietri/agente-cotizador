from dotenv import load_dotenv
import os
from supabase import create_client
from telegram.bot import enviar_mensaje

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

resultado = supabase.schema("erp").from_("vendedores").select("telegram_id, nombre").eq("id", 1).execute()
vendedor = resultado.data[0]

print(f"Mandando mensaje a {vendedor['nombre']} (telegram_id: {vendedor['telegram_id']})")

exito = enviar_mensaje(vendedor["telegram_id"], "🤖 Test del agente cotizador. ¡Telegram funciona!")
print("Enviado:", exito)