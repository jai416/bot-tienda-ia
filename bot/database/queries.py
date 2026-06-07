from bot.database.supabase_client import get_supabase


# ── TIENDAS ──────────────────────────────────────

def crear_tienda(owner_id: int, nombre_tienda: str = "Mi Tienda", descripcion: str = ""):
    db = get_supabase()
    return db.table("tiendas").insert({
        "owner_id": owner_id,
        "nombre_tienda": nombre_tienda,
        "descripcion": descripcion
    }).execute()


def obtener_tienda_por_owner(owner_id: int):
    db = get_supabase()
    return db.table("tiendas").select("*").eq("owner_id", owner_id).maybe_single().execute()


def obtener_tienda_por_id(tienda_id: int):
    db = get_supabase()
    return db.table("tiendas").select("*").eq("id", tienda_id).maybe_single().execute()


def actualizar_tienda(tienda_id: int, datos: dict):
    db = get_supabase()
    return db.table("tiendas").update(datos).eq("id", tienda_id).execute()


# ── PRODUCTOS ────────────────────────────────────

def insertar_producto(tienda_id: int, datos: dict):
    db = get_supabase()
    datos["tienda_id"] = tienda_id
    return db.table("productos").insert(datos).execute()


def listar_productos(tienda_id: int):
    db = get_supabase()
    return db.table("productos").select("*").eq("tienda_id", tienda_id).order("id").execute()


def buscar_productos(tienda_id: int, terminos: list[str], limit: int = 15):
    db = get_supabase()
    condiciones = []
    for t in terminos:
        pat = f"%{t}%"
        condiciones.append(f"nombre.ilike.{pat}")
        condiciones.append(f"descripcion.ilike.{pat}")
        condiciones.append(f"categoria.ilike.{pat}")
    query = db.table("productos").select("*").eq("tienda_id", tienda_id).eq("disponible", True)
    for c in condiciones:
        query = query.or_(c)
    return query.limit(limit).execute()


def buscar_por_categoria(tienda_id: int, categoria: str, limit: int = 10):
    db = get_supabase()
    return db.table("productos").select("*").eq("tienda_id", tienda_id).eq("disponible", True).ilike("categoria", f"%{categoria}%").limit(limit).execute()


def obtener_producto(tienda_id: int, producto_id: int):
    db = get_supabase()
    return db.table("productos").select("*").eq("id", producto_id).eq("tienda_id", tienda_id).maybe_single().execute()


def actualizar_producto(tienda_id: int, producto_id: int, datos: dict):
    db = get_supabase()
    datos["fecha_actualizacion"] = "now()"
    return db.table("productos").update(datos).eq("id", producto_id).eq("tienda_id", tienda_id).execute()


def eliminar_producto(tienda_id: int, producto_id: int):
    db = get_supabase()
    return db.table("productos").delete().eq("id", producto_id).eq("tienda_id", tienda_id).execute()


# ── CLIENTES ─────────────────────────────────────

def registrar_cliente(cliente_id: int, tienda_id: int, username: str = "", primer_nombre: str = ""):
    db = get_supabase()
    return db.table("clientes").upsert({
        "cliente_id": cliente_id,
        "tienda_id": tienda_id,
        "username": username,
        "primer_nombre": primer_nombre
    }, on_conflict="cliente_id,tienda_id").execute()


def obtener_tienda_de_cliente(cliente_id: int):
    db = get_supabase()
    return db.table("clientes").select("tienda_id").eq("cliente_id", cliente_id).maybe_single().execute()


# ── CONSULTAS / ESTADÍSTICAS ─────────────────────

def registrar_consulta(tienda_id: int, cliente_id: int | None, consulta: str, respuesta: str, productos_ids: list, hubo_resultado: bool):
    db = get_supabase()
    return db.table("consultas").insert({
        "tienda_id": tienda_id,
        "cliente_id": cliente_id,
        "consulta": consulta,
        "respuesta": respuesta,
        "productos_consultados": productos_ids,
        "hubo_resultado": hubo_resultado
    }).execute()


def obtener_estadisticas(tienda_id: int):
    db = get_supabase()
    return db.table("estadisticas").select("*").eq("tienda_id", tienda_id).maybe_single().execute()


def upsert_estadisticas(tienda_id: int, datos: dict):
    db = get_supabase()
    existing = obtener_estadisticas(tienda_id)
    if existing.data:
        return db.table("estadisticas").update(datos).eq("tienda_id", tienda_id).execute()
    datos["tienda_id"] = tienda_id
    return db.table("estadisticas").insert(datos).execute()
