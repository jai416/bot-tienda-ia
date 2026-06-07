from bot.database.queries import (
    obtener_estadisticas,
    upsert_estadisticas,
)


def get_estadisticas(tienda_id: int) -> dict | None:
    result = obtener_estadisticas(tienda_id)
    return result.data


def incrementar_consultas(tienda_id: int, hubo_resultado: bool):
    stats = obtener_estadisticas(tienda_id)
    if stats.data:
        datos = stats.data
        total = (datos.get("total_consultas") or 0) + 1
        sin_resultado = (datos.get("busquedas_sin_resultado") or 0) + (0 if hubo_resultado else 1)
        upsert_estadisticas(tienda_id, {
            "total_consultas": total,
            "busquedas_sin_resultado": sin_resultado
        })
    else:
        upsert_estadisticas(tienda_id, {
            "total_consultas": 1,
            "busquedas_sin_resultado": 0 if hubo_resultado else 1
        })
