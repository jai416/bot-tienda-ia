from bot.database.queries import (
    registrar_cliente as db_registrar,
    obtener_tienda_de_cliente,
)


def registrar_o_actualizar(cliente_id: int, tienda_id: int, username: str = "", primer_nombre: str = "") -> dict | None:
    result = db_registrar(cliente_id, tienda_id, username, primer_nombre)
    return result.data[0] if result.data else None


def obtener_tienda_asociada(cliente_id: int) -> int | None:
    result = obtener_tienda_de_cliente(cliente_id)
    if result.data:
        return result.data["tienda_id"]
    return None
