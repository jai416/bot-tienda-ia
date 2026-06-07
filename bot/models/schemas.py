from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Tienda:
    id: int
    owner_id: int
    nombre_tienda: str
    descripcion: str
    activo: bool
    fecha_creacion: datetime


@dataclass
class Producto:
    id: int
    tienda_id: int
    nombre: str
    descripcion: str
    precio: Decimal
    categoria: str
    color: str
    talla: str
    stock: int
    disponible: bool
    etiquetas: list
    imagen_url: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime


@dataclass
class Cliente:
    id: int
    cliente_id: int
    tienda_id: int
    username: str
    primer_nombre: str
    primera_vez: datetime


@dataclass
class Consulta:
    id: int
    tienda_id: int
    cliente_id: Optional[int]
    consulta: str
    respuesta: Optional[str]
    productos_consultados: list
    hubo_resultado: bool
    fecha_creacion: datetime
