from datetime import datetime

from bot.database.supabase_client import get_supabase

NOW = datetime.utcnow().isoformat()


# ── TIENDAS ──────────────────────────────────────

def crear_tienda(owner_id: int, nombre_tienda: str = "Mi Tienda", descripcion: str = ""):
    db = get_supabase()
    result = db.table("tiendas").insert({
        "owner_id": owner_id,
        "nombre_tienda": nombre_tienda,
        "descripcion": descripcion
    }).execute()
    return result.data[0] if result.data else None


def obtener_tienda_por_owner(owner_id: int) -> dict | None:
    db = get_supabase()
    result = db.table("tiendas").select("*").eq("owner_id", owner_id).maybe_single().execute()
    return result.data


def obtener_tienda_por_id(tienda_id: int) -> dict | None:
    db = get_supabase()
    result = db.table("tiendas").select("*").eq("id", tienda_id).maybe_single().execute()
    return result.data


def actualizar_tienda(tienda_id: int, datos: dict) -> dict | None:
    db = get_supabase()
    result = db.table("tiendas").update(datos).eq("id", tienda_id).execute()
    return result.data[0] if result.data else None


# ── PRODUCTOS ────────────────────────────────────

def insertar_producto(tienda_id: int, datos: dict) -> dict | None:
    db = get_supabase()
    datos["tienda_id"] = tienda_id
    result = db.table("productos").insert(datos).execute()
    return result.data[0] if result.data else None


def listar_productos(tienda_id: int) -> list:
    db = get_supabase()
    result = db.table("productos").select("*").eq("tienda_id", tienda_id).order("id").execute()
    return result.data if result.data else []


def buscar_productos(tienda_id: int, terminos: list[str], limit: int = 15) -> list:
    db = get_supabase()
    query = db.table("productos").select("*").eq("tienda_id", tienda_id).eq("disponible", True)
    for t in terminos:
        pat = f"%{t}%"
        query = query.or_(f"nombre.ilike.{pat},descripcion.ilike.{pat},categoria.ilike.{pat}")
    result = query.limit(limit).execute()
    return result.data if result.data else []


def buscar_por_categoria(tienda_id: int, categoria: str, limit: int = 10) -> list:
    db = get_supabase()
    result = db.table("productos").select("*").eq("tienda_id", tienda_id).eq("disponible", True).ilike("categoria", f"%{categoria}%").limit(limit).execute()
    return result.data if result.data else []


def obtener_producto(tienda_id: int, producto_id: int) -> dict | None:
    db = get_supabase()
    result = db.table("productos").select("*").eq("id", producto_id).eq("tienda_id", tienda_id).maybe_single().execute()
    return result.data


def actualizar_producto(tienda_id: int, producto_id: int, datos: dict) -> dict | None:
    db = get_supabase()
    datos["fecha_actualizacion"] = NOW
    result = db.table("productos").update(datos).eq("id", producto_id).eq("tienda_id", tienda_id).execute()
    return result.data[0] if result.data else None


def activar_producto(tienda_id: int, producto_id: int) -> dict | None:
    return actualizar_producto(tienda_id, producto_id, {"disponible": True})


def desactivar_producto(tienda_id: int, producto_id: int) -> dict | None:
    return actualizar_producto(tienda_id, producto_id, {"disponible": False})


def eliminar_producto(tienda_id: int, producto_id: int) -> bool:
    db = get_supabase()
    result = db.table("productos").delete().eq("id", producto_id).eq("tienda_id", tienda_id).execute()
    return len(result.data) > 0


# ── CLIENTES ─────────────────────────────────────

def registrar_cliente(cliente_id: int, tienda_id: int, username: str = "", primer_nombre: str = "") -> dict | None:
    db = get_supabase()
    result = db.table("clientes").upsert({
        "cliente_id": cliente_id,
        "tienda_id": tienda_id,
        "username": username,
        "primer_nombre": primer_nombre
    }, on_conflict="cliente_id,tienda_id").execute()
    return result.data[0] if result.data else None


def obtener_tienda_de_cliente(cliente_id: int) -> dict | None:
    db = get_supabase()
    result = db.table("clientes").select("tienda_id").eq("cliente_id", cliente_id).maybe_single().execute()
    return result.data


# ── CONSULTAS / ESTADÍSTICAS ─────────────────────

def registrar_consulta(tienda_id: int, cliente_id: int | None, consulta: str, respuesta: str, productos_ids: list, hubo_resultado: bool):
    db = get_supabase()
    db.table("consultas").insert({
        "tienda_id": tienda_id,
        "cliente_id": cliente_id,
        "consulta": consulta,
        "respuesta": respuesta,
        "productos_consultados": productos_ids,
        "hubo_resultado": hubo_resultado
    }).execute()


def obtener_estadisticas(tienda_id: int) -> dict | None:
    db = get_supabase()
    result = db.table("estadisticas").select("*").eq("tienda_id", tienda_id).maybe_single().execute()
    return result.data


def upsert_estadisticas(tienda_id: int, datos: dict):
    db = get_supabase()
    existing = obtener_estadisticas(tienda_id)
    if existing:
        db.table("estadisticas").update(datos).eq("tienda_id", tienda_id).execute()
    else:
        datos["tienda_id"] = tienda_id
        db.table("estadisticas").insert(datos).execute()
