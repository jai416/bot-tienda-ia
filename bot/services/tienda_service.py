from bot.database.queries import (
    crear_tienda as db_crear_tienda,
    obtener_tienda_por_owner,
    obtener_tienda_por_id,
    actualizar_tienda,
)


def obtener_o_crear_tienda(owner_id: int) -> dict | None:
    tienda = obtener_tienda_por_owner(owner_id)
    if tienda:
        return tienda
    return db_crear_tienda(owner_id)


def obtener_tienda(tienda_id: int) -> dict | None:
    return obtener_tienda_por_id(tienda_id)


def actualizar_nombre_tienda(tienda_id: int, nombre: str) -> dict | None:
    return actualizar_tienda(tienda_id, {"nombre_tienda": nombre})
