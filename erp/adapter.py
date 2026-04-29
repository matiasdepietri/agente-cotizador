from supabase import Client
from rapidfuzz import process, fuzz

def buscar_cliente(supabase: Client, query: str) -> list[dict]:
    todos = (
        supabase
        .schema("erp")
        .from_("clientes")
        .select("id, nombre, lista_precios_id")
        .execute()
    ).data

    nombres = [c["nombre"] for c in todos]
    query_norm = query.lower().strip()
    nombres_norm = [n.lower() for n in nombres]
    matches = process.extract(query_norm, nombres_norm, scorer=fuzz.WRatio, limit=5, score_cutoff=40)
    ids_encontrados = {nombres[i] for _, _, i in matches}
    return [c for c in todos if c["nombre"] in ids_encontrados]

def buscar_producto(supabase: Client, query: str) -> list[dict]:
    todos = (
        supabase
        .schema("erp")
        .from_("productos")
        .select("id, nombre, unidad_medida")
        .execute()
    ).data

    nombres = [p["nombre"] for p in todos]
    matches = process.extract(query, nombres, scorer=fuzz.WRatio, limit=5, score_cutoff=60)
    ids_encontrados = {match[0] for match in matches}
    return [p for p in todos if p["nombre"] in ids_encontrados]

def get_cliente_detalle(supabase: Client, cliente_id: int) -> dict | None:
    resultado = (
        supabase
        .schema("erp")
        .from_("clientes")
        .select("id, nombre, cuit, condicion_iva, lista_precios_id, condicion_pago, moneda, email, rating")
        .eq("id", cliente_id)
        .execute()
    )
    if resultado.data:
        return resultado.data[0]
    return None

def get_precio_producto(supabase: Client, producto_id: int, lista_precios_id: int) -> float | None:
    resultado = (
        supabase
        .schema("erp")
        .from_("precios_por_producto")
        .select("precio_unitario")
        .eq("producto_id", producto_id)
        .eq("lista_precios_id", lista_precios_id)
        .execute()
    )
    if resultado.data:
        return float(resultado.data[0]["precio_unitario"])
    return None