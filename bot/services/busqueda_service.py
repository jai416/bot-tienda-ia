import re

from bot.database.queries import buscar_productos, buscar_por_categoria


STOPWORDS = {
    "tienen", "tiene", "hay", "algún", "alguna", "un", "una",
    "unos", "unas", "el", "la", "los", "las", "lo", "que",
    "de", "en", "por", "para", "con", "sin", "es", "son",
    "busco", "buscando", "quisiera", "me", "pueden", "podrian",
    "venden", "vende", "oferta", "ofertas", "algo", "todo",
    "como", "cual", "cuales", "precio", "precios", "caro",
    "barato", "cuesta", "valen", "vale", "cuestan",
}

RECOMENDACION_KEYWORDS = {
    "recomienda", "recomiendas", "recomendación", "recomendaciones",
    "sugiere", "sugieres", "sugerencia", "opinión", "opinion",
    "mejor", "cual", "cuál", "elegante", "moderno", "moda",
    "fancy", "conviene", "qué tal", "que tal", "qué opinas",
    "que opinas", "está de moda", "novedades", "nuevo",
    "nuevos", "lanzamiento", "tendencia",
}


def tokenizar_consulta(texto: str) -> list[str]:
    limpio = re.sub(r"[^\w\s]", " ", texto.lower())
    return [t for t in limpio.split() if t not in STOPWORDS and len(t) > 1]


def es_consulta_compleja(texto: str) -> bool:
    texto_lower = texto.lower()
    for kw in RECOMENDACION_KEYWORDS:
        if kw in texto_lower:
            return True
    return False


def buscar(tienda_id: int, consulta: str) -> dict:
    terminos = tokenizar_consulta(consulta)

    if not terminos:
        return {"resultados": [], "alternativas": [], "hubo_resultado": False}

    resultados = buscar_productos(tienda_id, terminos)
    hubo_resultado = len(resultados) > 0

    alternativas = []
    if not hubo_resultado:
        for t in terminos:
            alt = buscar_por_categoria(tienda_id, t)
            if alt:
                alternativas.extend(alt)
                break

    return {
        "resultados": resultados,
        "alternativas": alternativas,
        "hubo_resultado": hubo_resultado
    }
