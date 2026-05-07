from dotenv import load_dotenv
from openai import OpenAI
from supabase import Client
from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    tool_buscar_cliente, tool_buscar_producto, tool_get_precio,
    tool_guardar_borrador, tool_confirmar_envio,
    tool_get_borradores_cliente, tool_actualizar_borrador,
    tool_ver_cotizaciones_cliente, tool_ver_mis_cotizaciones,
)
import json

load_dotenv()
openai_client = OpenAI()

TOOLS_DEFINICION = [
    {
        "type": "function",
        "function": {
            "name": "buscar_cliente",
            "description": "Busca clientes por nombre en el sistema",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nombre o parte del nombre del cliente"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_producto",
            "description": "Busca productos por nombre en el sistema",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nombre o parte del nombre del producto"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_precio",
            "description": "Obtiene el precio de un producto según la lista de precios del cliente",
            "parameters": {
                "type": "object",
                "properties": {
                    "producto_id": {"type": "integer", "description": "ID del producto"},
                    "lista_precios_id": {"type": "integer", "description": "ID de la lista de precios"}
                },
                "required": ["producto_id", "lista_precios_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_borrador",
            "description": "Guarda el borrador de la cotización cuando el vendedor confirma los datos",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendedor_id": {"type": "integer", "description": "ID del vendedor"},
                    "cliente_id": {"type": "integer", "description": "ID del cliente"},
                    "items": {"type": "array", "description": "Lista de productos con cantidades y precios", "items": {"type": "object"}},
                    "notas": {"type": "string", "description": "Notas opcionales"}
                },
                "required": ["vendedor_id", "cliente_id", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirmar_envio",
            "description": "Confirma y envía la cotización al cliente. SOLO llamar cuando el vendedor dé confirmación explícita de envío.",
            "parameters": {
                "type": "object",
                "properties": {
                    "borrador_id": {"type": "integer", "description": "ID del borrador a confirmar"}
                },
                "required": ["borrador_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_borradores_cliente",
            "description": "Busca borradores pendientes para un cliente. Usarlo antes de guardar uno nuevo para ver si ya existe uno para ese cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "integer", "description": "ID del cliente"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_borrador",
            "description": "Actualiza los ítems de un borrador existente en lugar de crear uno nuevo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "borrador_id": {"type": "integer", "description": "ID del borrador a actualizar"},
                    "items": {"type": "array", "description": "Lista completa y actualizada de productos", "items": {"type": "object"}},
                    "notas": {"type": "string", "description": "Notas opcionales"}
                },
                "required": ["borrador_id", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_cotizaciones_cliente",
            "description": "Muestra el historial de cotizaciones de un cliente específico",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "integer", "description": "ID del cliente"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_mis_cotizaciones",
            "description": "Muestra todas las cotizaciones del vendedor activo",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]

TOOLS_CON_VENDEDOR = {"confirmar_envio", "get_borradores_cliente", "ver_mis_cotizaciones"}

TOOL_MAP = {
    "buscar_cliente":         tool_buscar_cliente,
    "buscar_producto":        tool_buscar_producto,
    "get_precio":             tool_get_precio,
    "guardar_borrador":       tool_guardar_borrador,
    "confirmar_envio":        tool_confirmar_envio,
    "get_borradores_cliente": tool_get_borradores_cliente,
    "actualizar_borrador":    tool_actualizar_borrador,
    "ver_cotizaciones_cliente": tool_ver_cotizaciones_cliente,
    "ver_mis_cotizaciones":     tool_ver_mis_cotizaciones,
}


def ejecutar_tool(nombre: str, argumentos: dict, supabase: Client, vendedor_id: int = 1) -> str:
    fn = TOOL_MAP.get(nombre)
    if fn is None:
        return json.dumps({"error": f"Tool '{nombre}' no existe"})
    if nombre in TOOLS_CON_VENDEDOR:
        resultado = fn(supabase, vendedor_id=vendedor_id, **argumentos)
    else:
        resultado = fn(supabase, **argumentos)
    return json.dumps(resultado)


def chat(mensaje: str, historial: list, supabase: Client, vendedor_id: int = 1) -> tuple[str, list]:
    system_message = {"role": "system", "content": SYSTEM_PROMPT + f"\n\nEl vendedor activo tiene ID: {vendedor_id}."}
    historial.append({"role": "user", "content": mensaje})

    try:
        while True:
            respuesta = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_message] + historial,
                tools=TOOLS_DEFINICION,
                tool_choice="auto",
                timeout=20,
            )

            mensaje_respuesta = respuesta.choices[0].message

            if not mensaje_respuesta.tool_calls:
                historial.append({"role": "assistant", "content": mensaje_respuesta.content})
                return mensaje_respuesta.content, historial

            historial.append(mensaje_respuesta)
            for tool_call in mensaje_respuesta.tool_calls:
                nombre = tool_call.function.name
                argumentos = json.loads(tool_call.function.arguments)
                resultado = ejecutar_tool(nombre, argumentos, supabase, vendedor_id)
                historial.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": resultado,
                })

    except Exception as e:
        mensaje_error = "Hubo un problema de conexión. Por favor repetí el pedido."
        historial.append({"role": "assistant", "content": mensaje_error})
        return mensaje_error, historial