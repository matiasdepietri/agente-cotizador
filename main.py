from dotenv import load_dotenv
import os
from supabase import create_client
from agent.core import chat

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

historial = []

print("Agente listo. Escribí tu pedido (Ctrl+C para salir)\n")

while True:
    mensaje = input("Vos: ")
    respuesta, historial = chat(mensaje, historial, supabase)
    print(f"\nAgente: {respuesta}\n")