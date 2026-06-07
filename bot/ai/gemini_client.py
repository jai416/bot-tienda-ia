import json
import logging
import io

from google import genai
from google.genai import types
from PIL import Image

from bot.config.settings import GEMINI_KEY
from bot.ai.prompts import SYSTEM_INSTRUCTION, PHOTO_ANALYSIS_INSTRUCTION, PHOTO_SUGGEST_INSTRUCTION

client = genai.Client(api_key=GEMINI_KEY)
MODEL = "gemini-2.5-flash"


def generar_respuesta(consulta: str, productos_contexto: list[dict]) -> str:
    if not productos_contexto:
        return "Lo siento, actualmente no tenemos productos disponibles que coincidan con tu búsqueda."

    contexto = _formatear_productos(productos_contexto)
    prompt = f"{contexto}\n\n---\nPregunta del cliente: {consulta}"

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Error en Gemini: {e}")
        return "Lo siento, tuve un problema procesando tu consulta. ¿Podrías intentar de nuevo?"


def analizar_imagen(imagen_bytes: bytes, productos_contexto: list[dict]) -> str:
    contexto = _formatear_productos(productos_contexto)
    prompt = f"{contexto}\n\n---\nEl cliente envió esta foto. ¿Qué producto es?"

    try:
        imagen_pil = Image.open(io.BytesIO(imagen_bytes))
        response = client.models.generate_content(
            model=MODEL,
            contents=[imagen_pil, prompt],
            config=types.GenerateContentConfig(
                system_instruction=PHOTO_ANALYSIS_INSTRUCTION,
                temperature=0.1
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Error en Gemini foto: {e}")
        return "Veo la imagen, pero no pude procesarla de momento."


def sugerir_desde_foto(imagen_bytes: bytes) -> dict | None:
    try:
        imagen_pil = Image.open(io.BytesIO(imagen_bytes))
        response = client.models.generate_content(
            model=MODEL,
            contents=[imagen_pil, "Analiza esta imagen y sugiere datos del producto en JSON."],
            config=types.GenerateContentConfig(
                system_instruction=PHOTO_SUGGEST_INSTRUCTION,
                temperature=0.2
            )
        )
        texto = response.text.strip()
        texto = texto.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(texto)
    except Exception as e:
        logging.error(f"Error al sugerir desde foto: {e}")
        return None


def _formatear_productos(productos: list[dict]) -> str:
    lineas = ["PRODUCTOS DISPONIBLES EN LA TIENDA:"]
    for p in productos:
        nombre = p.get("nombre", "Sin nombre")
        precio = p.get("precio", "N/A")
        desc = p.get("descripcion", "")
        cat = p.get("categoria", "")
        color = p.get("color", "")
        talla = p.get("talla", "")
        stock = p.get("stock", "N/A")
        etiquetas = p.get("etiquetas", [])
        etiq_str = ", ".join(etiquetas) if etiquetas else ""
        linea = f"- {nombre} | Precio: ${precio}"
        if desc:
            linea += f" | {desc}"
        if cat:
            linea += f" | Categoría: {cat}"
        if color:
            linea += f" | Color: {color}"
        if talla:
            linea += f" | Talla: {talla}"
        if stock:
            linea += f" | Stock: {stock}"
        if etiq_str:
            linea += f" | Etiquetas: {etiq_str}"
        lineas.append(linea)
    return "\n".join(lineas)
