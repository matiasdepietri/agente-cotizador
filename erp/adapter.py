from supabase import Client
from rapidfuzz import process, fuzz
from datetime import date, timedelta

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

def generar_numero_cotizacion(supabase: Client) -> str:
    resultado = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .select("numero")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    if not resultado.data:
        return "COT-2026-0001"
    ultimo = resultado.data[0]["numero"]
    partes = ultimo.split("-")
    siguiente = int(partes[2]) + 1
    return f"COT-2026-{siguiente:04d}"

def confirmar_cotizacion(supabase: Client, vendedor_id: int, cliente_id: int, items: list, notas: str = None, moneda: str = "ARS", condicion_pago: str = None) -> dict:
    subtotal = sum(item["subtotal"] for item in items)
    impuestos = subtotal * 0.21
    total = subtotal + impuestos

    numero = generar_numero_cotizacion(supabase)
    validez = date.today() + timedelta(days=15)

    cabecera_result = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .insert({
            "numero": numero,
            "vendedor_id": vendedor_id,
            "cliente_id": cliente_id,
            "estado": "enviada",
            "validez_hasta": str(validez),
            "moneda": moneda,
            "condicion_pago": condicion_pago,
            "subtotal": round(subtotal, 2),
            "impuestos": round(impuestos, 2),
            "total": round(total, 2),
            "notas": notas,
        })
        .execute()
    )
    cotizacion = cabecera_result.data[0]
    cotizacion_id = cotizacion["id"]

    try:
        items_data = []
        for i, item in enumerate(items):
            items_data.append({
                "cotizacion_id": cotizacion_id,
                "producto_id": item["producto_id"],
                "cantidad": item["cantidad"],
                "precio_unitario": item["precio_unitario"],
                "descuento": item.get("descuento", 0),
                "iva_aplicable": 21.00,
                "orden": i + 1,
            })
        supabase.schema("erp").from_("cotizaciones_items").insert(items_data).execute()
    except Exception as e:
        supabase.schema("erp").from_("cotizaciones").delete().eq("id", cotizacion_id).execute()
        raise Exception(f"Error al insertar ítems, se revirtió la cabecera: {e}")

    return {
        "cotizacion_id": cotizacion_id,
        "numero": numero,
        "subtotal": subtotal,
        "impuestos": impuestos,
        "total": total,
    }

def get_cotizaciones_cliente(supabase: Client, cliente_id: int) -> list[dict]:
    resultado = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .select("id, numero, fecha_emision, estado, total, moneda, validez_hasta, clientes(nombre)")
        .eq("cliente_id", cliente_id)
        .order("id", desc=True)
        .execute()
    )
    return resultado.data

def get_cotizaciones_vendedor(supabase: Client, vendedor_id: int) -> list[dict]:
    resultado = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .select("id, numero, fecha_emision, estado, total, moneda, cliente_id, clientes(nombre)")
        .eq("vendedor_id", vendedor_id)
        .order("id", desc=True)
        .execute()
    )
    return resultado.data

def marcar_cotizacion_confirmada(supabase: Client, cotizacion_id: int) -> dict:
    resultado = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .update({"estado": "confirmada"})
        .eq("id", cotizacion_id)
        .execute()
    )
    return resultado.data[0]

def marcar_cotizacion_perdida(supabase: Client, cotizacion_id: int) -> dict:
    resultado = (
        supabase
        .schema("erp")
        .from_("cotizaciones")
        .update({"estado": "perdida"})
        .eq("id", cotizacion_id)
        .execute()
    )
    return resultado.data[0]