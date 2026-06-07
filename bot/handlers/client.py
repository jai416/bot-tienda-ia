import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.cliente_service import obtener_tienda_asociada
from bot.services.busqueda_service import buscar, registrar_consulta_stats
from bot.services.estadisticas_service import incrementar_consultas
from bot.services.producto_service import listar_productos
from bot.ai.gemini_client import generar_respuesta, analizar_imagen
from bot.utils.helpers import es_admin


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if es_admin(user_id):
        return

    texto = update.message.text.strip()
    tienda_id = context.user_data.get("tienda_id")

    if not tienda_id:
        tienda_id = obtener_tienda_asociada(user_id)
        if tienda_id:
            context.user_data["tienda_id"] = tienda_id
        else:
            await update.message.reply_text(
                "🔗 No estás vinculado a ninguna tienda. "
                "Usa el enlace que te proporcionó la tienda para comenzar.\n"
                "Ejemplo: t.me/TuBot?start=ID"
            )
            return

    resultado = buscar(tienda_id, texto)

    if resultado["hubo_resultado"]:
        respuesta = generar_respuesta(texto, resultado["resultados"])
        productos_ids = [p.get("id") for p in resultado["resultados"] if p.get("id")]
    elif resultado["alternativas"]:
        respuesta = generar_respuesta(texto, resultado["alternativas"])
        productos_ids = [p.get("id") for p in resultado["alternativas"] if p.get("id")]
    else:
        respuesta = "Lo siento, actualmente no tenemos productos que coincidan con tu búsqueda."
        productos_ids = []

    registrar_consulta_stats(
        tienda_id, user_id, texto, respuesta,
        productos_ids, resultado["hubo_resultado"]
    )
    incrementar_consultas(tienda_id, resultado["hubo_resultado"])

    await update.message.reply_text(respuesta)


async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if es_admin(user_id):
        return

    tienda_id = context.user_data.get("tienda_id")
    if not tienda_id:
        tienda_id = obtener_tienda_asociada(user_id)
        if tienda_id:
            context.user_data["tienda_id"] = tienda_id
        else:
            await update.message.reply_text(
                "🔗 No estás vinculado a ninguna tienda. Usa tu enlace primero."
            )
            return

    productos = listar_productos(tienda_id)
    foto_archivo = await update.message.photo[-1].get_file()
    foto_bytes = await foto_archivo.download_as_bytearray()

    respuesta = analizar_imagen(foto_bytes, productos)
    await update.message.reply_text(respuesta)
