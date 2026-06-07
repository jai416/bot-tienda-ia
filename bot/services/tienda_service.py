from bot.database.queries import (
    crear_tienda as db_crear_tienda,
    obtener_tienda_por_owner,
    obtener_tienda_por_id,
    actualizar_tienda,
)


def obtener_o_crear_tienda(owner_id: int) -> dict:
    tienda = obtener_tienda_por_owner(owner_id)
    if tienda.data:
        return tienda.data
    result = db_crear_tienda(owner_id)
    return result.data[0] if result.data else None


def obtener_tienda(tienda_id: int) -> dict | None:
    result = obtener_tienda_por_id(tienda_id)
    return result.data


def actualizar_nombre_tienda(tienda_id: int, nombre: str) -> dict | None:
    result = actualizar_tienda(tienda_id, {"nombre_tienda": nombre})
    return result.data[0] if result.data else None


def actualizar_descripcion_tienda(tienda_id: int, descripcion: str) -> dict | None:
    result = actualizar_tienda(tienda_id, {"descripcion": descripcion})
    return result.data[0] if result.data else None
