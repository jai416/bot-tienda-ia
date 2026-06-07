from telegram import Update
from telegram.ext import ContextTypes

from bot.database.queries import (
    buscar_productos,
    registrar_consulta,
)
from bot.services.cliente_service import obtener_tienda_asociada
from bot.services.busqueda_service import buscar, es_consulta_compleja, tokenizar_consulta
from bot.services.estadisticas_service import incrementar_consultas
from bot.ai.gemini_client import responder_consulta
from bot.utils.helpers import es_admin


def _formatear_resultados(productos: list[dict]) -> str:
    if not productos:
        return ""
    partes = [f"📦 **{len(productos)} producto(s) encontrado(s):**\n"]
    for p in productos:
        nombre = p.get("nombre", "Sin nombre")
        precio = p.get("precio", "N/A")
        desc = p.get("descripcion", "")
        cat = p.get("categoria", "")
        color = p.get("color", "")
        talla = p.get("talla", "")
        linea = f"\n• *{nombre}* — 💰 ${precio}"
        if desc:
            linea += f"\n  {desc}"
        if cat or color or talla:
            extra = " | ".join(filter(None, [cat, color, talla]))
            linea += f"\n  _{extra}_"
        partes.append(linea)
    return "\n".join(partes)


async def _check_supabase(context: ContextTypes.DEFAULT_TYPE, update: Update) -> bool:
    if not context.application.bot_data.get("supabase_ok", False):
        await update.message.reply_text(
            "🔧 Estamos teniendo problemas técnicos con nuestros servidores.\n"
            "Nuestro equipo ya está trabajando para solucionarlo.\n"
            "Por favor, intenta de nuevo más tarde. ¡Gracias por tu paciencia! 🙏"
        )
        return False
    return True


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if es_admin(user_id):
        return

    if not await _check_supabase(context, update):
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
    productos = resultado["resultados"] or resultado["alternativas"]
    hubo_resultado = resultado["hubo_resultado"]

    if not productos:
        respuesta = "Lo siento, actualmente no tenemos productos que coincidan con tu búsqueda."
    elif es_consulta_compleja(texto):
        respuesta = responder_consulta(texto, productos)
    else:
        respuesta = _formatear_resultados(productos)

    registrar_consulta(
        tienda_id, user_id, texto, respuesta,
        [p.get("id") for p in productos if p.get("id")],
        hubo_resultado
    )
    incrementar_consultas(tienda_id, bool(productos))

    await update.message.reply_text(respuesta)


async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if es_admin(user_id):
        return

    if not await _check_supabase(context, update):
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

    texto_usuario = update.message.caption or ""
    terminos = tokenizar_consulta(texto_usuario)

    if terminos:
        productos = buscar_productos(tienda_id, terminos)
    else:
        productos = []

    foto_archivo = await update.message.photo[-1].get_file()
    foto_bytes = await foto_archivo.download_as_bytearray()

    if productos:
        respuesta = responder_consulta(
            f"El cliente envió esta foto. {texto_usuario}",
            productos
        )
    else:
        respuesta = "Gracias por enviar la foto. No encontré productos similares en nuestro inventario actual."

    await update.message.reply_text(respuesta)
