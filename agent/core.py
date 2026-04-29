from openai import OpenAI
from supabase import Client
from agent.prompts import SYSTEM_PROMPT
from agent.tools import tool_buscar_cliente, tool_buscar_producto, tool_get_precio, tool_guardar_borrador
import json

def get_openai_client():
    from dotenv import load_dotenv
    load_dotenv()
    return OpenAI()

TOOLS_DEFINICION = [
    {
        "type": "function",
        "function": {
            "name": "buscar_cliente",
            "description": "Busca clientes por nombre en el sistema",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nombre o parte del nombre del cliente a buscar"
                    }
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
                    "query": {
                        "type": "string",
                        "description": "Nombre o parte del nombre del producto a buscar"
                    }
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
                    "producto_id": {
                        "type": "integer",
                        "description": "ID del producto"
                    },
                    "lista_precios_id": {
                        "type": "integer",
                        "description": "ID de la lista de precios del cliente"
                    }
                },
                "required": ["producto_id", "lista_precios_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_borrador",
            "description": "Guarda el borrador de la cotización en el sistema cuando el vendedor confirma los datos",
            "parameters": {
                "type": "object",
                "properties": {
                    "vendedor_id": {
                        "type": "integer",
                        "description": "ID del vendedor"
                    },
                    "cliente_id": {
                        "type": "integer",
                        "description": "ID del cliente"
                    },
                    "items": {
                        "type": "array",
                        "description": "Lista de productos con cantidades y precios",
                        "items": {
                            "type": "object"
                        }
                    },
                    "notas": {
                        "type": "string",
                        "description": "Notas opcionales de la cotización"
                    }
                },
                "required": ["vendedor_id", "cliente_id", "items"]
            }
        }
    }
]

def ejecutar_tool(nombre: str, argumentos: dict, supabase: Client) -> str:
    if nombre == "buscar_cliente":
        resultado = tool_buscar_cliente(supabase, **argumentos)
    elif nombre == "buscar_producto":
        resultado = tool_buscar_producto(supabase, **argumentos)
    elif nombre == "get_precio":
        resultado = tool_get_precio(supabase, **argumentos)
    elif nombre == "guardar_borrador":
        resultado = tool_guardar_borrador(supabase, **argumentos)
    else:
        resultado = {"error": f"Tool '{nombre}' no existe"}
    return json.dumps(resultado)


def chat(mensaje: str, historial: list, supabase: Client, vendedor_id: int = 1) -> tuple[str, list]:
    historial.append({"role": "user", "content": mensaje})

    while True:
        respuesta = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT + f"\n\nEl vendedor activo tiene ID: {vendedor_id}. Usá siempre este ID cuando llames a guardar_borrador."}] + historial,
            tools=TOOLS_DEFINICION,
            tool_choice="auto"
        )

        mensaje_respuesta = respuesta.choices[0].message

        if mensaje_respuesta.tool_calls:
            historial.append(mensaje_respuesta)
            for tool_call in mensaje_respuesta.tool_calls:
                nombre = tool_call.function.name
                argumentos = json.loads(tool_call.function.arguments)
                resultado = ejecutar_tool(nombre, argumentos, supabase)
                historial.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": resultado
                })
        else:
            historial.append({"role": "assistant", "content": mensaje_respuesta.content})
            return mensaje_respuesta.content, historial