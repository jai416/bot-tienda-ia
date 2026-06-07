import re

from bot.services.producto_service import buscar_productos, buscar_similares
from bot.database.queries import registrar_consulta


def tokenizar_consulta(texto: str) -> list[str]:
    limpio = re.sub(r"[^\w\s]", " ", texto.lower())
    tokens = limpio.split()
    stopwords = {"tienen", "tiene", "hay", "algún", "alguna", "un", "una",
                 "unos", "unas", "el", "la", "los", "las", "lo", "que",
                 "de", "en", "por", "para", "con", "sin", "es", "son",
                 "busco", "buscando", "quisiera", "me", "pueden", "podrian",
                 "venden", "vende", "oferta", "ofertas", "algo", "todo",
                 "como", "cual", "cuales", "precio", "precios", "caro",
                 "barato", "cuesta", "valen", "vale", "cuestan"}
    return [t for t in tokens if t not in stopwords and len(t) > 1]


def buscar(tienda_id: int, consulta: str) -> dict:
    terminos = tokenizar_consulta(consulta)

    if not terminos:
        return {"resultados": [], "alternativas": [], "hubo_resultado": False}

    resultados = buscar_productos(tienda_id, terminos)
    hubo_resultado = len(resultados) > 0

    alternativas = []
    if not hubo_resultado:
        for t in terminos:
            alt = buscar_similares(tienda_id, t)
            if alt:
                alternativas.extend(alt)
                break

    return {
        "resultados": resultados,
        "alternativas": alternativas,
        "hubo_resultado": hubo_resultado
    }


def registrar_consulta_stats(tienda_id: int, cliente_id: int | None, consulta: str, respuesta: str, productos_ids: list, hubo_resultado: bool):
    registrar_consulta(tienda_id, cliente_id, consulta, respuesta, productos_ids, hubo_resultado)
