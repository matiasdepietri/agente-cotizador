from pydantic import BaseModel
from typing import Optional

class Cliente(BaseModel):
    id: int
    nombre: str
    cuit: Optional[str] = None
    condicion_iva: str
    lista_precios_id: int
    condicion_pago: Optional[str] = None
    moneda: str
    email: Optional[str] = None
    rating: str

class Producto(BaseModel):
    id: int
    nombre: str
    unidad_medida: str

class ItemBorrador(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: float
    precio_unitario: float
    descuento: float = 0.0
    subtotal: float

class BorradorCotizacion(BaseModel):
    id: Optional[int] = None
    vendedor_id: int
    cliente: Cliente
    items: list[ItemBorrador] = []
    notas: Optional[str] = None
    moneda: str
    condicion_pago: Optional[str] = None
    subtotal: float = 0.0
    impuestos: float = 0.0
    total: float = 0.0