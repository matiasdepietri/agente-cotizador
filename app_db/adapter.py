from supabase import Client
from datetime import datetime, timedelta, timezone

def guardar_borrador(supabase: Client, vendedor_id: int, cliente_id: int, items: list, notas: str = None) -> dict:
    data = {
        "vendedor_id": vendedor_id,
        "cliente_id": cliente_id,
        "items": items,
        "notas": notas
    }
    resultado = (
        supabase
        .schema("app")
        .from_("cotizaciones_borrador")
        .insert(data)
        .execute()
    )
    return resultado.data[0]

def get_borrador(supabase: Client, borrador_id: int) -> dict | None:
    resultado = (
        supabase
        .schema("app")
        .from_("cotizaciones_borrador")
        .select("*")
        .eq("id", borrador_id)
        .execute()
    )
    if resultado.data:
        return resultado.data[0]
    return None

def borrar_borrador(supabase: Client, borrador_id: int) -> None:
    supabase.schema("app").from_("cotizaciones_borrador").delete().eq("id", borrador_id).execute()


def calcular_bucket(total: float, rating: str) -> str:
    if total > 2_000_000 or rating == "estrategico":
        return "A"
    if total > 500_000 or rating == "normal":
        return "B"
    return "C"


def crear_seguimiento(supabase: Client, cotizacion_id: int, vendedor_id: int, total: float, rating: str) -> dict:
    bucket = calcular_bucket(total, rating)
    dias_primer_recordatorio = {"A": 1, "B": 3, "C": 7}
    primer_recordatorio = datetime.now(timezone.utc) + timedelta(days=dias_primer_recordatorio[bucket])

    resultado = (
        supabase
        .schema("app")
        .from_("cotizaciones_seguimiento")
        .insert({
            "cotizacion_id": cotizacion_id,
            "vendedor_id": vendedor_id,
            "bucket_urgencia": bucket,
            "proximo_recordatorio_at": primer_recordatorio.isoformat(),
            "estado_seguimiento": "activo",
        })
        .execute()
    )
    return resultado.data[0]

def get_borradores_por_cliente(supabase: Client, vendedor_id: int, cliente_id: int) -> list[dict]:
    resultado = (
        supabase
        .schema("app")
        .from_("cotizaciones_borrador")
        .select("id, items, notas, created_at")
        .eq("vendedor_id", vendedor_id)
        .eq("cliente_id", cliente_id)
        .execute()
    )
    return resultado.data


def actualizar_borrador(supabase: Client, borrador_id: int, items: list, notas: str = None) -> dict:
    data = {"items": items}
    if notas is not None:
        data["notas"] = notas
    resultado = (
        supabase
        .schema("app")
        .from_("cotizaciones_borrador")
        .update(data)
        .eq("id", borrador_id)
        .execute()
    )
    return resultado.data[0]