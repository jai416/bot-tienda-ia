from bot.database.queries import obtener_estadisticas, upsert_estadisticas


def get_estadisticas(tienda_id: int) -> dict | None:
    return obtener_estadisticas(tienda_id)


def incrementar_consultas(tienda_id: int, hubo_resultado: bool):
    stats = obtener_estadisticas(tienda_id)
    if stats:
        total = (stats.get("total_consultas") or 0) + 1
        sin_resultado = (stats.get("busquedas_sin_resultado") or 0) + (0 if hubo_resultado else 1)
    else:
        total = 1
        sin_resultado = 0 if hubo_resultado else 1
    upsert_estadisticas(tienda_id, {
        "total_consultas": total,
        "busquedas_sin_resultado": sin_resultado,
    })
