from supabase import Client
from erp.adapter import buscar_cliente, buscar_producto, get_cliente_detalle, get_precio_producto
from app_db.adapter import guardar_borrador

def tool_buscar_cliente(supabase: Client, query: str) -> dict:
    resultados = buscar_cliente(supabase, query)
    if not resultados:
        return {"encontrados": [], "mensaje": f"No encontré clientes con '{query}'"}
    return {"encontrados": resultados}

def tool_buscar_producto(supabase: Client, query: str) -> dict:
    resultados = buscar_producto(supabase, query)
    if not resultados:
        return {"encontrados": [], "mensaje": f"No encontré productos con '{query}'"}
    return {"encontrados": resultados}

def tool_get_precio(supabase: Client, producto_id: int, lista_precios_id: int) -> dict:
    precio = get_precio_producto(supabase, producto_id, lista_precios_id)
    if precio is None:
        return {"precio": None, "mensaje": "No encontré precio para ese producto en esa lista"}
    return {"precio": precio}

def tool_guardar_borrador(supabase: Client, vendedor_id: int, cliente_id: int, items: list, notas: str = None) -> dict:
    borrador = guardar_borrador(supabase, vendedor_id, cliente_id, items, notas)
    return {"borrador_id": borrador["id"], "mensaje": "Borrador guardado correctamente"}