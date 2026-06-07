from bot.database.queries import registrar_cliente, obtener_tienda_de_cliente


def registrar_o_actualizar(cliente_id: int, tienda_id: int, username: str = "", primer_nombre: str = "") -> dict | None:
    return registrar_cliente(cliente_id, tienda_id, username, primer_nombre)


def obtener_tienda_asociada(cliente_id: int) -> int | None:
    tienda = obtener_tienda_de_cliente(cliente_id)
    if tienda:
        return tienda["tienda_id"]
    return None
