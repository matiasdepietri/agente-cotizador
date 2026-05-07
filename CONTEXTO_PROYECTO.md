# CONTEXTO DEL PROYECTO — Agente Cotizador con IA

> Este archivo es el repositorio de contexto del proyecto. Se actualiza a medida que avanzamos. Pegarlo al inicio de cualquier chat nuevo para continuar sin perder contexto.

---

## SOBRE EL USUARIO

- Se llama Matias. Está aprendiendo a programar.
- **Hablale siempre en castellano argentino (vos).**
- El agente lo desarrolla él a mano, con guía paso a paso.
- Cuando hay que hacer un cambio: decile exactamente en qué archivo, en qué línea, qué poner.
- Si el archivo puede tener errores o está muy modificado, leerlo primero con la herramienta Read antes de dar instrucciones.
- Explicar cada línea nueva de código, especialmente conceptos nuevos (async, FK, decorator, etc.).
- No hacer las cosas por él — guiarlo para que las haga.
- Si se equivoca al copiar/pegar, ayudarlo a debuggear paso a paso.
- Cuando hay opciones, decirle cuál elegirías y por qué.
- Respuestas cortas en conversación, más largas cuando se enseña algo nuevo.
- No usar bullet points en exceso. Prosa cuando sea posible.
- **Siempre que vayas a dar instrucciones sobre un archivo existente, leerlo primero con Read para ver el estado real.**

---

## QUÉ ESTAMOS CONSTRUYENDO

Un agente conversacional con IA que ayuda a vendedores a armar cotizaciones. El vendedor le habla en lenguaje natural ("cotización para Acme: 5 caños 2 pulgadas"), el agente:

1. Matchea cliente y productos contra una base de datos (matching difuso con rapidfuzz)
2. Calcula precios automáticamente según la lista de precios asignada al cliente
3. Arma un borrador
4. Pide **confirmación humana** al vendedor antes de enviar
5. Registra la cotización en el ERP
6. Genera PDF y manda mail al cliente
7. Hace seguimiento con recordatorios automáticos al vendedor por Telegram según urgencia (A/B/C)
8. Cuando el cliente acepta → crea Orden de Venta y cierra el seguimiento

**Reglas duras:**
- El vendedor SIEMPRE tiene que confirmar antes de enviar al cliente.
- El agente NUNCA marca una cotización como confirmada sin OK del vendedor.
- Plata = humano en el loop.

**Destino del producto:** se vende a empresas como producto terminado. Tiene que ser de calidad profesional y seguro.

---

## STACK TECNOLÓGICO

- **LLM**: OpenAI (gpt-4o-mini en desarrollo, gpt-4o en producción)
- **Framework del agente**: OpenAI SDK directo + Function Calling (sin LangChain, sin Assistants API)
- **Backend**: FastAPI (pendiente)
- **DB**: Supabase (PostgreSQL)
- **Lenguaje**: Python 3.11+
- **Notificaciones**: Telegram Bot API (via httpx, sin librería extra)
- **Canal inicial**: terminal (después Telegram conversacional, WhatsApp)

### Librerías instaladas (via pyproject.toml)
`openai`, `instructor`, `pydantic`, `fastapi`, `uvicorn`, `supabase`, `python-dotenv`, `rapidfuzz`, `loguru`, `httpx`, `weasyprint`, `resend`, `apscheduler`

---

## ARQUITECTURA CLAVE

- **Capa de canal** (web/Telegram/WhatsApp) intercambiable. El core del agente recibe siempre `{vendedor_id, mensaje}`.
- **Adapter ERP** (`erp/adapter.py`) — hoy habla con Supabase schema `erp`, mañana con Finnegans real. Reemplazable sin tocar el agente.
- **Capa operativa** (`app_db/adapter.py`) — habla con Supabase schema `app` (seguimiento, borradores, recordatorios).
- El agente **NUNCA** toca SQL directo. Siempre va a través de los adapters.
- Las tools del LLM son funciones de negocio, NUNCA operaciones SQL crudas.

---

## SUPABASE — CONFIGURACIÓN

- **Project ID**: `ruxuusenpzshwzogyyyx`
- **URL**: `https://ruxuusenpzshwzogyyyx.supabase.co`
- **Key usada**: `service_role` ✅ (ya cambiada)
- **RLS**: deshabilitado en todas las tablas (acceso vía service_role key desde Python)
- **Schemas expuestos en API**: `erp`, `app`, `public`
- **Permisos otorgados** (ejecutar si aparece "permission denied"):
  ```sql
  GRANT USAGE ON SCHEMA erp TO service_role;
  GRANT ALL ON ALL TABLES IN SCHEMA erp TO service_role;
  GRANT USAGE ON ALL SEQUENCES IN SCHEMA erp TO service_role;
  GRANT USAGE ON SCHEMA app TO service_role;
  GRANT ALL ON ALL TABLES IN SCHEMA app TO service_role;
  GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO service_role;
  ```

---

## MODELO DE DATOS EN SUPABASE

### Schema `erp` (simula Finnegans — será reemplazado en el futuro)

#### `erp.vendedores`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| nombre | TEXT NOT NULL | |
| email | TEXT UNIQUE NOT NULL | |
| telefono | TEXT | |
| jefe_id | BIGINT FK → vendedores(id) | jerarquía para escalado |
| activo | BOOLEAN DEFAULT TRUE | |
| telegram_id | BIGINT | ✅ agregado — para mandar recordatorios por Telegram |
| created_at / updated_at | TIMESTAMPTZ | auto |

Sembrados: 10 vendedores (incluye 2 jefes). Vendedor id=1 es Matias Depietri Salvat.

#### `erp.listas_precios`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| nombre | TEXT UNIQUE NOT NULL | |
| moneda | TEXT DEFAULT 'ARS' | |
| vigente_desde | DATE | |
| vigente_hasta | DATE | |
| activa | BOOLEAN DEFAULT TRUE | |

Sembradas: 4 listas — Minorista (1), Mayorista (2), Distribuidor (3), Exportación USD (4)

#### `erp.clientes`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| nombre | TEXT NOT NULL | |
| cuit | TEXT UNIQUE | |
| condicion_iva | TEXT | responsable_inscripto / monotributista / exento / consumidor_final / no_responsable |
| lista_precios_id | BIGINT FK → listas_precios(id) | |
| condicion_pago | TEXT | |
| moneda | TEXT DEFAULT 'ARS' | |
| vendedor_asignado_id | BIGINT FK → vendedores(id) | |
| email | TEXT | |
| rating | TEXT DEFAULT 'normal' | estrategico / normal / esporadico |
| activo | BOOLEAN DEFAULT TRUE | |

Sembrados: 44 clientes con variaciones para testear fuzzy match (mayúsculas, tildes, nombres similares)

#### `erp.productos`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| sku | TEXT UNIQUE NOT NULL | |
| nombre | TEXT NOT NULL | |
| descripcion | TEXT | |
| unidad_medida | TEXT DEFAULT 'un' | un / kg / m / m2 / m3 / l |
| iva_aplicable | NUMERIC(5,2) DEFAULT 21.00 | |
| activo | BOOLEAN DEFAULT TRUE | |

Sembrados: 65 productos (rubro ferretería industrial — caños, codos, válvulas, bridas, tornillería, etc.)

#### `erp.precios_por_producto`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| lista_precios_id | BIGINT FK → listas_precios(id) | |
| producto_id | BIGINT FK → productos(id) | |
| precio_unitario | NUMERIC(15,2) | |
| UNIQUE | (lista_precios_id, producto_id) | |

Sembrados: 260 precios (65 productos × 4 listas)

#### `erp.cotizaciones`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| numero | TEXT UNIQUE NOT NULL | formato: COT-2026-0001 |
| fecha_emision | DATE DEFAULT CURRENT_DATE | |
| vendedor_id | BIGINT FK → vendedores(id) | |
| cliente_id | BIGINT FK → clientes(id) | |
| estado | TEXT DEFAULT 'enviada' | enviada / confirmada / perdida / vencida / anulada |
| validez_hasta | DATE | |
| moneda | TEXT | |
| condicion_pago | TEXT | |
| subtotal | NUMERIC(15,2) | |
| impuestos | NUMERIC(15,2) | |
| total | NUMERIC(15,2) | |
| notas | TEXT | |
| version | INT DEFAULT 1 | |
| cotizacion_padre_id | BIGINT FK → cotizaciones(id) | para versionado |

Se llena cuando el vendedor confirma el envío via `confirmar_cotizacion`.

#### `erp.cotizaciones_items`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| cotizacion_id | BIGINT FK → cotizaciones(id) ON DELETE CASCADE | |
| producto_id | BIGINT FK → productos(id) | |
| cantidad | NUMERIC(15,3) | |
| precio_unitario | NUMERIC(15,2) | |
| descuento | NUMERIC(5,2) DEFAULT 0 | % |
| iva_aplicable | NUMERIC(5,2) | snapshot del IVA al cotizar |
| orden | INT DEFAULT 1 | |

---

### Schema `app` (operativo, vive solo en este sistema)

#### `app.cotizaciones_borrador`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| vendedor_id | BIGINT NOT NULL | referencia lógica al ERP, no FK |
| cliente_id | BIGINT | nullable mientras no se resolvió |
| notas | TEXT | |
| moneda | TEXT | |
| condicion_pago | TEXT | |
| items | JSONB DEFAULT '[]' | ítems flexibles mientras se arma |
| conversation_state | JSONB | contexto de la charla con el agente |

#### `app.cotizaciones_seguimiento`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| cotizacion_id | BIGINT UNIQUE | referencia a erp.cotizaciones(id) |
| vendedor_id | BIGINT | denormalizado para queries rápidas |
| bucket_urgencia | CHAR(1) | A / B / C |
| proximo_recordatorio_at | TIMESTAMPTZ | cuándo mandar el próximo recordatorio |
| ultimo_recordatorio_at | TIMESTAMPTZ | cuándo fue el último |
| recordatorios_enviados | INT DEFAULT 0 | |
| recordatorios_ignorados | INT DEFAULT 0 | |
| escalado_jefe | BOOLEAN DEFAULT FALSE | |
| estado_seguimiento | TEXT DEFAULT 'activo' | activo / cerrado_confirmada / cerrado_perdida / cerrado_vencida |
| notas_vendedor | TEXT | |
| created_at / updated_at | TIMESTAMPTZ | auto |

#### `app.motivos_perdida`
Sembrados: precio, plazo_entrega, competencia, sin_respuesta, postergado, otro

#### `app.configuracion`
Sembrados:
- `validez_dias_default` = 15
- `descuento_max_vendedor` = 10 (% sin aprobación)
- `buckets_urgencia` = `{"A":{"monto_min":2000000,"dias":[1,3,5,7]},"B":{"monto_min":500000,"dias":[3,7,14]},"C":{"monto_min":0,"dias":[7,14]}}`
- `recordatorios_max_antes_escalar` = `{"A":3,"B":2,"C":2}`

---

## BUCKETS DE URGENCIA

Se calcula con dos ejes, se toma el más alto:

| Eje monto | Eje cliente | Bucket |
|---|---|---|
| > $2M | rating estratégico | A |
| > $500K | rating normal | B |
| resto | rating esporádico | C |

Cadencia de recordatorios:
- **A**: días 1, 3, 5, 7 → escala al jefe si ignora 3
- **B**: días 3, 7, 14 → escala si ignora 2
- **C**: días 7, 14 → escala si ignora 2

---

## ESTRUCTURA DE ARCHIVOS ACTUAL

```
Agente Cotizador/
├── main.py                  # Loop conversacional de prueba (temporario, reemplazar con FastAPI)
├── config.py                # Carga configuración desde app.configuracion (no usado aún)
├── pyproject.toml           # Dependencias del proyecto
├── .env                     # OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN
├── .gitignore               # Ignora .env, __pycache__, .venv
├── CONTEXTO_PROYECTO.md     # Este archivo
├── agent/
│   ├── __init__.py
│   ├── core.py              # Loop conversacional con OpenAI + TOOL_MAP + chat()
│   ├── tools.py             # 7 funciones-tool que el agente puede llamar
│   └── prompts.py           # System prompt del agente
├── erp/
│   ├── __init__.py
│   └── adapter.py           # Funciones para leer/escribir en schema erp de Supabase
├── app_db/
│   ├── __init__.py
│   └── adapter.py           # Funciones para leer/escribir en schema app de Supabase
├── telegram/
│   ├── __init__.py
│   └── bot.py               # enviar_mensaje() — manda mensajes al vendedor via Telegram Bot API
└── models/
    └── schemas.py           # Modelos Pydantic: Cliente, Producto, ItemBorrador, BorradorCotizacion (no usado aún)
```

---

## FUNCIONES IMPLEMENTADAS

### `erp/adapter.py`
- `buscar_cliente(supabase, query)` — fuzzy match con rapidfuzz, score_cutoff=40
- `buscar_producto(supabase, query)` — fuzzy match con rapidfuzz, score_cutoff=60
- `get_cliente_detalle(supabase, cliente_id)` — ficha completa del cliente (rating, moneda, condicion_pago)
- `get_precio_producto(supabase, producto_id, lista_precios_id)` — precio según lista
- `generar_numero_cotizacion(supabase)` — lee el último COT-2026-NNNN y devuelve el siguiente
- `confirmar_cotizacion(supabase, vendedor_id, cliente_id, items, notas, moneda, condicion_pago)` — INSERT cabecera + INSERT items con try/except rollback. Calcula subtotal, IVA 21%, total. Validez 15 días.

### `app_db/adapter.py`
- `consolidar_items(items)` — mergea items duplicados por producto_id sumando cantidades y subtotales
- `guardar_borrador(supabase, vendedor_id, cliente_id, items, notas)` — insert en cotizaciones_borrador con consolidación
- `get_borrador(supabase, borrador_id)` — trae un borrador por ID
- `borrar_borrador(supabase, borrador_id)` — elimina el borrador después de confirmar
- `actualizar_borrador(supabase, borrador_id, items, notas)` — fetch items existentes de DB + merge con nuevos items + update. Evita perder items no mencionados.
- `get_borradores_por_cliente(supabase, vendedor_id, cliente_id)` — busca borradores activos para un cliente
- `calcular_bucket(total, rating)` — devuelve A, B o C según monto y rating del cliente
- `crear_seguimiento(supabase, cotizacion_id, vendedor_id, total, rating)` — INSERT en cotizaciones_seguimiento con bucket y primer recordatorio calculado

### `agent/tools.py` (7 tools)
- `tool_buscar_cliente` — wrapper con mensaje si no encuentra
- `tool_buscar_producto` — wrapper con mensaje si no encuentra
- `tool_get_precio` — wrapper de get_precio_producto
- `tool_guardar_borrador` — valida que vengan items antes de guardar
- `tool_confirmar_envio` — orquesta: get_borrador → get_cliente_detalle → confirmar_cotizacion → crear_seguimiento → borrar_borrador
- `tool_get_borradores_cliente` — verifica si ya existe un borrador para el cliente antes de crear uno nuevo
- `tool_actualizar_borrador` — valida items y actualiza el borrador existente

### `agent/core.py`
- Cliente OpenAI creado una sola vez a nivel de módulo
- `TOOL_MAP` — dict que mapea nombre → función (reemplaza if/elif)
- `TOOLS_CON_VENDEDOR` — set con tools que necesitan `vendedor_id` inyectado: `{"confirmar_envio", "get_borradores_cliente"}`
- `ejecutar_tool(nombre, argumentos, supabase, vendedor_id)` — dispatcher limpio
- `chat(mensaje, historial, supabase, vendedor_id=1)` — loop principal con timeout=20 y try/except para errores de red

### `telegram/bot.py`
- `enviar_mensaje(telegram_id, texto)` — POST a la Telegram Bot API via httpx. Devuelve True/False. Usa `parse_mode=HTML`.

---

## LO QUE FUNCIONA HOY

**Flujo completo de cotización end-to-end:**
1. El vendedor escribe en lenguaje natural
2. El agente busca cliente y productos con fuzzy match
3. Trae precios según la lista del cliente
4. Muestra resumen y pide confirmación explícita
5. Verifica si ya existe un borrador para ese cliente (`get_borradores_cliente`)
6. Guarda nuevo borrador o actualiza el existente (merge con DB, no reemplaza)
7. Pregunta si quiere enviarlo
8. Si confirma: crea cotización en ERP (numero COT-2026-XXXX), registra seguimiento con bucket A/B/C, borra el borrador

**Items consolidados:** si el mismo producto aparece dos veces, se suman cantidades y subtotales automáticamente, tanto al guardar como al actualizar.

**Robustez:** timeout de 20s en llamadas a OpenAI, manejo de errores con mensaje amigable al usuario, rollback de cotización si falla el insert de items.

---

## LO QUE FALTA HACER (en orden)

### ✅ Bot de Telegram (recordatorios) — COMPLETADO
- [x] Crear `telegram/bot.py` con `enviar_mensaje()`
- [x] Agregar `TELEGRAM_BOT_TOKEN` al `.env`
- [x] Agregar columna `telegram_id` a `erp.vendedores`
- [x] Testear que `enviar_mensaje()` funciona
- [x] Escribir `scheduler/cron.py` — cron con apscheduler que corre cada hora, busca cotizaciones vencidas en `app.cotizaciones_seguimiento` y manda recordatorio al vendedor por Telegram
- [x] Función `get_cotizaciones_para_recordar()` en `app_db/adapter.py`
- [x] Función `actualizar_tras_recordatorio()` en `app_db/adapter.py`

### Fase 1 — Completar MVP
- [ ] **FastAPI** — reemplazar el `main.py` de prueba por un servidor real con rutas HTTP. Hacerlo cuando haya una interfaz real para conectar (Telegram conversacional, web).
- [ ] **Autenticación de vendedores** — sacar el `vendedor_id=1` hardcodeado. Necesario antes de que lo usen varios vendedores.

### Fase 2.5 — Consulta de historial
- [ ] `get_cotizaciones_cliente(supabase, cliente_id)` en `erp/adapter.py`
- [ ] `get_cotizaciones_vendedor(supabase, vendedor_id)` en `erp/adapter.py`
- [ ] `tool_ver_cotizaciones_cliente` y `tool_ver_mis_cotizaciones` en `agent/tools.py`
- [ ] Agregarlas a `TOOLS_DEFINICION` en `agent/core.py`
- Nota: hacerlo DESPUÉS de que haya cotizaciones confirmadas en la DB

### Fase 2 — Seguimiento avanzado
- [ ] `marcar_confirmada(cotizacion_id)` → crea Orden de Venta en ERP
- [ ] `marcar_perdida(cotizacion_id, motivo)` → cierra el seguimiento

### Deuda técnica menor
- [ ] Usar `models/schemas.py` Pydantic (actualmente no importado en ningún lado)
- [ ] Usar `config.py` en `calcular_bucket` en lugar de valores hardcodeados
- [ ] Mover cálculo de subtotal del LLM a Python

### Fases 4-9 (más adelante)
- PDF con weasyprint + envío por mail con resend al confirmar
- Telegram conversacional (vendedor le escribe al bot y responde) — requiere FastAPI + webhook
  - Cuando esté implementado: agregar lógica de escalado al jefe si `recordatorios_enviados >= recordatorios_max_antes_escalar`. Hoy no se puede detectar si el vendedor ignora un recordatorio porque no hay canal de respuesta. Con Telegram conversacional el vendedor puede responder y el agente puede trackear la inacción.
- WhatsApp Business
- Memoria por vendedor/cliente/producto
- Link interactivo para el cliente
- Tracking de aperturas
- Versionado y negociación
- Análisis y reportes
- Adaptadores para otros ERPs y CRM

---

## ENTORNO DE DESARROLLO

- Editor: VSCode
- Python: 3.14 (instalado en la máquina, aunque el proyecto pide >=3.11)
- Entorno virtual: `.venv` dentro de la carpeta del proyecto
- Para activar el entorno: `source .venv/bin/activate`
- Para correr el agente: `python3 main.py`
- Cowork activo: tiene acceso a la carpeta del proyecto para leer archivos en tiempo real
