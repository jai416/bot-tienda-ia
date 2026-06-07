from bot.database.queries import (
    insertar_producto,
    listar_productos as db_listar,
    buscar_productos as db_buscar,
    buscar_por_categoria,
    obtener_producto as db_obtener,
    actualizar_producto as db_actualizar,
    eliminar_producto as db_eliminar,
)


def crear_producto(tienda_id: int, datos: dict) -> dict | None:
    result = insertar_producto(tienda_id, datos)
    return result.data[0] if result.data else None


def listar_productos(tienda_id: int) -> list:
    result = db_listar(tienda_id)
    return result.data if result.data else []


def buscar_productos(tienda_id: int, terminos: list[str], limit: int = 15) -> list:
    result = db_buscar(tienda_id, terminos, limit)
    return result.data if result.data else []


def buscar_similares(tienda_id: int, categoria: str, limit: int = 10) -> list:
    result = buscar_por_categoria(tienda_id, categoria, limit)
    return result.data if result.data else []


def obtener_producto(tienda_id: int, producto_id: int) -> dict | None:
    result = db_obtener(tienda_id, producto_id)
    return result.data


def actualizar_producto(tienda_id: int, producto_id: int, datos: dict) -> dict | None:
    result = db_actualizar(tienda_id, producto_id, datos)
    return result.data[0] if result.data else None


def activar_producto(tienda_id: int, producto_id: int) -> dict | None:
    return actualizar_producto(tienda_id, producto_id, {"disponible": True})


def desactivar_producto(tienda_id: int, producto_id: int) -> dict | None:
    return actualizar_producto(tienda_id, producto_id, {"disponible": False})


def eliminar_producto(tienda_id: int, producto_id: int) -> bool:
    result = db_eliminar(tienda_id, producto_id)
    return len(result.data) > 0
