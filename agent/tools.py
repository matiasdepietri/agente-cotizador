from supabase import Client
from erp.adapter import buscar_cliente, buscar_producto, get_cliente_detalle, get_precio_producto, confirmar_cotizacion
from app_db.adapter import guardar_borrador, get_borrador, crear_seguimiento, borrar_borrador, get_borradores_por_cliente, actualizar_borrador

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

def tool_guardar_borrador(supabase: Client, vendedor_id: int, cliente_id: int, items: list = None, notas: str = None) -> dict:
    if not items:
        return {"error": True, "mensaje": "Faltan los ítems. Buscá los productos y obtené los precios antes de guardar."}
    borrador = guardar_borrador(supabase, vendedor_id, cliente_id, items, notas)
    return {"borrador_id": borrador["id"], "mensaje": "Borrador guardado correctamente"}

def tool_confirmar_envio(supabase: Client, borrador_id: int, vendedor_id: int) -> dict:
    borrador = get_borrador(supabase, borrador_id)
    if not borrador:
        return {"error": True, "mensaje": f"No encontré el borrador con ID {borrador_id}"}

    cliente = get_cliente_detalle(supabase, borrador["cliente_id"])
    if not cliente:
        return {"error": True, "mensaje": "No se encontró el cliente del borrador"}

    try:
        cotizacion = confirmar_cotizacion(
            supabase,
            vendedor_id=vendedor_id,
            cliente_id=borrador["cliente_id"],
            items=borrador["items"],
            notas=borrador.get("notas"),
            moneda=cliente.get("moneda", "ARS"),
            condicion_pago=cliente.get("condicion_pago"),
        )
        seguimiento = crear_seguimiento(
            supabase,
            cotizacion_id=cotizacion["cotizacion_id"],
            vendedor_id=vendedor_id,
            total=cotizacion["total"],
            rating=cliente.get("rating", "normal"),
        )
        borrar_borrador(supabase, borrador_id)
        return {
            "numero": cotizacion["numero"],
            "total": cotizacion["total"],
            "bucket_urgencia": seguimiento["bucket_urgencia"],
            "mensaje": f"✓ Cotización {cotizacion['numero']} confirmada. Total: ${cotizacion['total']:,.2f}. Seguimiento bucket {seguimiento['bucket_urgencia']}.",
        }
    except Exception as e:
        return {"error": True, "mensaje": f"Error al confirmar: {str(e)}"}
    
def tool_get_borradores_cliente(supabase: Client, cliente_id: int, vendedor_id: int) -> dict:
    borradores = get_borradores_por_cliente(supabase, vendedor_id, cliente_id)
    if not borradores:
        return {"borradores": [], "mensaje": "No hay borradores pendientes para este cliente"}
    return {"borradores": borradores}


def tool_actualizar_borrador(supabase: Client, borrador_id: int, items: list = None, notas: str = None) -> dict:
    if not items:
        return {"error": True, "mensaje": "Faltan los ítems. Incluí la lista completa con producto_id, cantidad y precio_unitario de cada producto."}
    borrador = actualizar_borrador(supabase, borrador_id, items, notas)
    return {"borrador_id": borrador["id"], "mensaje": "Borrador actualizado correctamente"}

def tool_ver_cotizaciones_cliente(supabase: Client, cliente_id: int) -> dict:
    from erp.adapter import get_cotizaciones_cliente
    cotizaciones = get_cotizaciones_cliente(supabase, cliente_id)
    if not cotizaciones:
        return {"cotizaciones": [], "mensaje": "No encontré cotizaciones para ese cliente"}
    return {"cotizaciones": cotizaciones}

def tool_ver_mis_cotizaciones(supabase: Client, vendedor_id: int) -> dict:
    from erp.adapter import get_cotizaciones_vendedor
    cotizaciones = get_cotizaciones_vendedor(supabase, vendedor_id)
    if not cotizaciones:
        return {"cotizaciones": [], "mensaje": "No tenés cotizaciones registradas"}
    return {"cotizaciones": cotizaciones}