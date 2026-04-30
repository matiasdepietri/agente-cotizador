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
7. Hace seguimiento con recordatorios al vendedor según urgencia (A/B/C)
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
- **Backend**: FastAPI
- **DB**: Supabase (PostgreSQL)
- **Lenguaje**: Python 3.11+
- **Canal inicial**: web simple (después Telegram, WhatsApp)

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
- **Key usada**: `service_role` (pendiente de cambiar — ver sección de deuda técnica)
- **RLS**: deshabilitado en todas las tablas (acceso vía service_role key desde Python)
- **Schemas expuestos en API**: `erp`, `app`, `public`
- **Permisos otorgados al rol `anon`**:
  - `GRANT USAGE ON SCHEMA erp TO anon`
  - `GRANT SELECT ON ALL TABLES IN SCHEMA erp TO anon`
  - `GRANT USAGE ON SCHEMA app TO anon`
  - `GRANT SELECT ON ALL TABLES IN SCHEMA app TO anon`
  - `GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO anon`
  - `GRANT USAGE ON ALL SEQUENCES IN SCHEMA app TO anon`

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
| jefe_id | BIGINT FK → vendedores(id) | jerarquía |
| activo | BOOLEAN DEFAULT TRUE | |
| created_at / updated_at | TIMESTAMPTZ | auto |

Sembrados: 10 vendedores (incluye 2 jefes)

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

**Actualmente vacía** — se llena cuando el vendedor confirma el envío.

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

**Actualmente vacía.**

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

Tiene registros de prueba (se pueden limpiar).

#### `app.cotizaciones_seguimiento`
| columna | tipo | detalle |
|---|---|---|
| id | BIGSERIAL PK | |
| cotizacion_id | BIGINT UNIQUE | referencia a erp.cotizaciones(id) |
| vendedor_id | BIGINT | denormalizado para queries rápidas |
| bucket_urgencia | CHAR(1) | A / B / C |
| proximo_recordatorio_at | TIMESTAMPTZ | |
| ultimo_recordatorio_at | TIMESTAMPTZ | |
| recordatorios_enviados | INT DEFAULT 0 | |
| recordatorios_ignorados | INT DEFAULT 0 | |
| escalado_jefe | BOOLEAN DEFAULT FALSE | |
| estado_seguimiento | TEXT DEFAULT 'activo' | activo / cerrado_confirmada / cerrado_perdida / cerrado_vencida |

**Actualmente vacía.**

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
├── main.py                  # Loop conversacional de prueba (temporario)
├── config.py                # Carga configuración desde app.configuracion
├── pyproject.toml           # Dependencias del proyecto
├── .env                     # OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
├── .gitignore               # Ignora .env, __pycache__, .venv
├── CONTEXTO_PROYECTO.md     # Este archivo
├── agent/
│   ├── __init__.py
│   ├── core.py              # Loop conversacional con OpenAI + ejecutar_tool + chat()
│   ├── tools.py             # Funciones-tool que el agente puede llamar
│   └── prompts.py           # System prompt del agente
├── erp/
│   ├── __init__.py
│   └── adapter.py           # Funciones para leer del schema erp de Supabase
├── app_db/
│   ├── __init__.py
│   └── adapter.py           # Funciones para leer/escribir en schema app de Supabase
└── models/
    └── schemas.py           # Modelos Pydantic: Cliente, Producto, ItemBorrador, BorradorCotizacion
```

---

## FUNCIONES IMPLEMENTADAS

### `erp/adapter.py`
- `buscar_cliente(supabase, query)` — fuzzy match con rapidfuzz, score_cutoff=40
- `buscar_producto(supabase, query)` — fuzzy match con rapidfuzz, score_cutoff=60
- `get_cliente_detalle(supabase, cliente_id)` — ficha completa del cliente
- `get_precio_producto(supabase, producto_id, lista_precios_id)` — precio según lista

### `app_db/adapter.py`
- `guardar_borrador(supabase, vendedor_id, cliente_id, items, notas)` — insert en cotizaciones_borrador
- `get_borrador(supabase, borrador_id)` — trae un borrador por ID

### `config.py`
- `get_configuracion(supabase)` — devuelve dict con todos los parámetros de app.configuracion

### `agent/tools.py`
- `tool_buscar_cliente` — wrapper de buscar_cliente con mensaje si no encuentra
- `tool_buscar_producto` — wrapper de buscar_producto con mensaje si no encuentra
- `tool_get_precio` — wrapper de get_precio_producto
- `tool_guardar_borrador` — wrapper de guardar_borrador

### `agent/core.py`
- `TOOLS_DEFINICION` — lista con las 4 tools definidas para OpenAI (buscar_cliente, buscar_producto, get_precio, guardar_borrador)
- `ejecutar_tool(nombre, argumentos, supabase)` — dispatcher que ejecuta la tool correcta
- `chat(mensaje, historial, supabase, vendedor_id=1)` — loop principal conversacional

---

## LO QUE FUNCIONA HOY

El flujo completo de armado de borrador funciona end-to-end:
1. El vendedor escribe en lenguaje natural
2. El agente busca cliente y productos con fuzzy match
3. Trae precios según la lista del cliente
4. Muestra el borrador y pide confirmación
5. Cuando el vendedor confirma, guarda en `app.cotizaciones_borrador`

Probado con: `"cotización para ACME S.A.: 5 bridas acero 2 pulgadas"`

---

## LO QUE FALTA HACER (en orden)

### Inmediato — deuda técnica
- [ ] Cambiar `SUPABASE_KEY` en `.env` de `anon` a `service_role` (seguridad crítica para producto de calidad)

### Fase 1 — completar MVP

- [ ] **`confirmar_envio`** — el paso más importante:
  1. Tomar el borrador de `app.cotizaciones_borrador`
  2. Generar número de cotización (formato `COT-2026-0001`)
  3. INSERT en `erp.cotizaciones` (cabecera)
  4. INSERT en `erp.cotizaciones_items` (una fila por producto)
  5. Calcular bucket de urgencia (monto + rating del cliente)
  6. INSERT en `app.cotizaciones_seguimiento`
  7. Generar PDF con weasyprint
  8. Mandar mail al cliente con resend
  9. Cerrar/borrar el borrador
  - Importante: pasos 3 y 4 deben ser atómicos (todo o nada)

- [ ] **FastAPI** — reemplazar el `main.py` de prueba por un servidor real con rutas HTTP
- [ ] **Autenticación de vendedores** — hoy el `vendedor_id=1` está hardcodeado

### Fase 2 — Seguimiento
- [ ] Cron con apscheduler que revisa `app.cotizaciones_seguimiento` 2x/día
- [ ] Envía recordatorios al vendedor según bucket y cadencia
- [ ] Escala al jefe si supera el máximo de recordatorios ignorados
- [ ] `marcar_confirmada(cotizacion_id)` → crea Orden de Venta en ERP
- [ ] `marcar_perdida(cotizacion_id, motivo)` → cierra el seguimiento

### Fase 2.5 — Consulta de historial (agregar después de confirmar_envio)
- [ ] `get_cotizaciones_cliente(supabase, cliente_id)` en `erp/adapter.py` — trae cotizaciones confirmadas de un cliente
- [ ] `get_cotizaciones_vendedor(supabase, vendedor_id)` en `erp/adapter.py` — trae cotizaciones del vendedor activo
- [ ] `tool_ver_cotizaciones_cliente` y `tool_ver_mis_cotizaciones` en `agent/tools.py`
- [ ] Agregarlas a `TOOLS_DEFINICION` en `agent/core.py`
- Nota: hacerlo DESPUÉS de confirmar_envio, porque antes `erp.cotizaciones` está vacía

### Fase 3 — Validaciones y aprobaciones
- [ ] Chequeo de descuento máximo por vendedor (10% sin aprobación)
- [ ] Workflow de aprobación si supera el límite
- [ ] Validar cliente activo, producto activo, precio disponible

### Fases 4-9 (más adelante)
- Memoria por vendedor/cliente/producto
- Multi-canal (WhatsApp, voz)
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
