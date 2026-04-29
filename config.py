from supabase import Client

def get_configuracion(supabase: Client) -> dict:
    resultado = (
        supabase
        .schema("app")
        .from_("configuracion")
        .select("clave, valor")
        .execute()
    )
    return {row["clave"]: row["valor"] for row in resultado.data}