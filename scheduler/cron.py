from dotenv import load_dotenv
import os
from supabase import create_client
from apscheduler.schedulers.blocking import BlockingScheduler
from app_db.adapter import get_cotizaciones_para_recordar, actualizar_tras_recordatorio
from erp.adapter import get_cliente_detalle
from telegram.bot import enviar_mensaje

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def procesar_recordatorios():
    print("Revisando recordatorios...")
    pendientes = get_cotizaciones_para_recordar(supabase)
    print(f"Encontradas: {len(pendientes)} cotizaciones para recordar")

    for s in pendientes:
        vendedor_result = supabase.schema("erp").from_("vendedores").select("telegram_id, nombre").eq("id", s["vendedor_id"]).execute()
        vendedor = vendedor_result.data[0] if vendedor_result.data else None

        if not vendedor or not vendedor["telegram_id"]:
            print(f"Vendedor {s['vendedor_id']} sin telegram_id, salteando")
            continue

        texto = (
            f"🔔 Recordatorio de cotización\n"
            f"Cotización ID: {s['cotizacion_id']}\n"
            f"Urgencia: Bucket {s['bucket_urgencia']}\n"
            f"Recordatorios enviados: {s['recordatorios_enviados']}"
        )

        exito = enviar_mensaje(vendedor["telegram_id"], texto)

        if exito:
            actualizar_tras_recordatorio(supabase, s["id"], s["bucket_urgencia"], s["recordatorios_enviados"])
            print(f"Recordatorio enviado a {vendedor['nombre']}")
        else:
            print(f"Error al enviar a {vendedor['nombre']}")

scheduler = BlockingScheduler()
scheduler.add_job(procesar_recordatorios, "interval", hours=1)

print("Scheduler iniciado. Revisando cada hora.")
procesar_recordatorios()
scheduler.start()