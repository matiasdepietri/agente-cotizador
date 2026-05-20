from supabase import Client
from weasyprint import HTML
from datetime import date, datetime
import os
import base64

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo-nikron-new.svg")

def _fmt2(n) -> str:
    try:
        val = float(n or 0)
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"

def _fmt_date(d) -> str:
    if not d:
        return "-"
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    try:
        return datetime.strptime(str(d), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(d)

def _get_logo_base64() -> str:
    try:
        with open(LOGO_PATH, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/svg+xml;base64,{data}"
    except Exception:
        return ""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Cotización {numero}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: Arial, sans-serif; font-size: 11px; color: #1a1a1a; line-height: 1.4; }}
        #pedido {{ max-width: 800px; margin: 0 auto; padding: 28px 28px 180px 28px; }}
        .ped-header {{ display: grid; grid-template-columns: 1fr 60px 1fr; gap: 0; align-items: stretch; border: 2px solid #000; margin-bottom: 2px; }}
        .ped-logo-block {{ padding: 10px 10px 10px 14px; }}
        .ped-logo-block img {{ width: 110px; display: block; }}
        .ped-logo-block .company-name {{ font-size: 11px; font-weight: 400; margin-top: 8px; margin-bottom: 2px; }}
        .ped-logo-block .company-address {{ font-size: 10px; line-height: 1.5; margin-top: 2px; }}
        .ped-header-center {{ display: flex; flex-direction: column; align-items: center; justify-content: space-between; border-left: 2px solid #000; border-right: 2px solid #000; padding: 10px 4px; }}
        .ped-type-stamp {{ display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 36px; line-height: 1; }}
        .resp-inscripto {{ font-size: 8px; text-align: center; line-height: 1.3; }}
        .ped-doc-info {{ padding: 10px 14px 10px 10px; }}
        .ped-doc-title {{ font-size: 13px; font-weight: 900; margin-bottom: 8px; letter-spacing: -0.5px; }}
        .ped-doc-field {{ display: flex; align-items: baseline; margin-bottom: 4px; }}
        .ped-doc-field label {{ font-weight: 900; white-space: nowrap; margin-right: 6px; min-width: 80px; }}
        .ped-doc-field span {{ flex: 1; }}
        .ped-client-box {{ border: 2px solid #000; padding: 6px 10px 6px 14px; margin-bottom: 2px; font-size: 11px; }}
        .ped-client-row {{ display: flex; gap: 20px; align-items: baseline; }}
        .ped-client-row .field {{ display: flex; align-items: baseline; gap: 5px; }}
        .ped-client-row .field strong {{ font-weight: 900; white-space: nowrap; }}
        .ped-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; margin-top: 4px; }}
        .ped-table thead {{ border: 2px solid #000; background: #C0C0C0; }}
        .ped-table thead th {{ background: #C0C0C0; padding: 5px 6px; font-size: 11px; font-weight: 900; text-align: left; }}
        .ped-table thead th.text-right {{ text-align: right; }}
        .ped-table thead th.text-center {{ text-align: center; }}
        .ped-table tbody td {{ padding: 4px 6px; font-size: 10px; vertical-align: top; border-bottom: 1px solid #eee; }}
        .text-right {{ text-align: right; }}
        .text-center {{ text-align: center; }}
        .ped-footer {{ position: fixed; bottom: 28px; left: 28px; right: 28px; border-top: 2px solid #000; padding-top: 6px; font-size: 10.5px; }}
        .son-line {{ font-style: italic; margin-bottom: 6px; margin-top: 4px; }}
        .totals-block {{ border: 2px solid #000; margin-bottom: 6px; padding: 5px 16px 5px 8px; display: flex; flex-direction: column; align-items: flex-end; gap: 3px; }}
        .totals-line {{ display: flex; gap: 16px; font-size: 11px; justify-content: flex-end; white-space: nowrap; }}
        .totals-line span:first-child {{ min-width: 80px; text-align: right; }}
        .totals-line span:last-child {{ min-width: 120px; text-align: right; }}
        .totals-final {{ font-weight: 900; border-top: 1px solid #000; padding-top: 3px; margin-top: 1px; }}
        .vb-row {{ display: flex; gap: 10px; margin-top: 10px; }}
        .vb-box {{ flex: 1; border: 2px solid #000; padding: 6px 8px; min-height: 50px; font-size: 10px; font-weight: 900; }}
    </style>
</head>
<body>
<div id="pedido">
    <div class="ped-header">
        <div class="ped-logo-block">
            <img src="{logo_src}" alt="NIKRON">
            <div class="company-name">(completar con Razón Social)</div>
            <div class="company-address">(completar con Domicilio)</div>
        </div>
        <div class="ped-header-center">
            <div class="ped-type-stamp">C</div>
            <div class="resp-inscripto">(completar<br>Cond. IVA)</div>
        </div>
        <div class="ped-doc-info">
            <div class="ped-doc-title">Cotización</div>
            <div class="ped-doc-field"><label>Número:</label><span>{numero}</span></div>
            <div class="ped-doc-field"><label>Fecha:</label><span>{fecha_emision}</span></div>
            <div class="ped-doc-field"><label>Válida hasta:</label><span>{validez_hasta}</span></div>
            <div class="ped-doc-field"><label>C.U.I.T.:</label><span>(completar con CUIT)</span></div>
        </div>
    </div>
    <div class="ped-client-box">
        <div class="ped-client-row">
            <div class="field"><strong>Sr. (es):</strong> {cliente_nombre}</div>
            <div class="field"><strong>CUIT:</strong> {cliente_cuit}</div>
        </div>
    </div>
    <div class="ped-client-box">
        <div class="ped-client-row">
            <div class="field"><strong>Cond. de Pago:</strong> {condicion_pago}</div>
            <div class="field"><strong>Condición IVA:</strong> {cliente_condicion_iva}</div>
            <div class="field"><strong>Moneda:</strong> {moneda}</div>
        </div>
    </div>
    <table class="ped-table">
        <thead>
            <tr>
                <th>Artículo</th>
                <th class="text-right">Cantidad</th>
                <th>Unidad</th>
                <th class="text-right">Precio Unit.</th>
                <th class="text-center">% Desc.</th>
                <th class="text-right">Subtotal</th>
            </tr>
        </thead>
        <tbody>{items_rows}</tbody>
    </table>
    <div class="ped-footer">
        <div class="son-line"><i>Cotización en curso. Precios, condiciones comerciales y disponibilidad sujetos a confirmación con su agente comercial.</i></div>
        <div class="totals-block">
            <div class="totals-line"><span>Subtotal:</span><span>$ {subtotal}</span></div>
            <div class="totals-line"><span>IVA (21%):</span><span>$ {impuestos}</span></div>
            <div class="totals-line totals-final"><span>Total:</span><span>$ {total}</span></div>
        </div>
        <div class="vb-row">
            <div class="vb-box">Vendedor</div>
            <div class="vb-box">Aprobación</div>
            <div class="vb-box">Cliente</div>
        </div>
    </div>
</div>
</body>
</html>"""

def generar_pdf(supabase: Client, cotizacion_id: int) -> bytes:
    cot = supabase.schema("erp").from_("cotizaciones").select(
        "numero, fecha_emision, validez_hasta, moneda, condicion_pago, subtotal, impuestos, total, notas, cliente_id"
    ).eq("id", cotizacion_id).execute().data[0]

    cliente = supabase.schema("erp").from_("clientes").select(
        "nombre, cuit, condicion_iva, condicion_pago"
    ).eq("id", cot["cliente_id"]).execute().data[0]

    items = supabase.schema("erp").from_("cotizaciones_items").select(
        "orden, cantidad, precio_unitario, descuento, productos(nombre, unidad_medida)"
    ).eq("cotizacion_id", cotizacion_id).order("orden").execute().data

    items_rows = ""
    for item in items:
        producto = item["productos"]
        desc = item["descuento"] or 0
        subtotal_item = item["cantidad"] * item["precio_unitario"] * (1 - desc / 100)
        items_rows += f"""
        <tr>
            <td>{producto['nombre']}</td>
            <td class="text-right">{_fmt2(item['cantidad'])}</td>
            <td>{producto['unidad_medida']}</td>
            <td class="text-right">{_fmt2(item['precio_unitario'])}</td>
            <td class="text-center">{int(desc)}%</td>
            <td class="text-right">{_fmt2(subtotal_item)}</td>
        </tr>"""

    html = HTML_TEMPLATE.format(
        logo_src=_get_logo_base64(),
        numero=cot["numero"],
        fecha_emision=_fmt_date(cot["fecha_emision"]),
        validez_hasta=_fmt_date(cot["validez_hasta"]),
        cliente_nombre=cliente["nombre"],
        cliente_cuit=cliente.get("cuit") or "-",
        cliente_condicion_iva=cliente.get("condicion_iva", "-").replace("_", " ").title(),
        condicion_pago=cot.get("condicion_pago") or cliente.get("condicion_pago") or "-",
        moneda=cot.get("moneda") or "ARS",
        subtotal=_fmt2(cot["subtotal"]),
        impuestos=_fmt2(cot["impuestos"]),
        total=_fmt2(cot["total"]),
        items_rows=items_rows,
    )

    return HTML(string=html, base_url=os.path.dirname(os.path.abspath(__file__))).write_pdf()