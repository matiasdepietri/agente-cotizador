from supabase import Client

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