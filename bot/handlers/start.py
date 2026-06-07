import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config.settings import ADMIN_IDS
from bot.services.cliente_service import registrar_o_actualizar, obtener_tienda_asociada
from bot.services.tienda_service import obtener_o_crear_tienda
from bot.utils.helpers import es_admin


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if args and args[0].isdigit():
        tienda_id = int(args[0])
        username = update.effective_user.username or ""
        nombre = update.effective_user.first_name or ""
        registrar_o_actualizar(user_id, tienda_id, username, nombre)
        context.user_data["tienda_id"] = tienda_id
        await update.message.reply_text(
            f"👋 ¡Bienvenido {nombre}! Has sido vinculado a la tienda correctamente.\n"
            "Ahora puedes preguntarme sobre los productos disponibles."
        )
        return

    if es_admin(user_id):
        tienda = obtener_o_crear_tienda(user_id)
        if tienda:
            context.user_data["tienda_id"] = tienda["id"]
        texto = (
            "👋 **Panel de Administración**\n\n"
            "Comandos disponibles:\n"
            "📦 `/guardar nombre | $precio | cat:Categoría | color:Rojo | talla:M | stock:10`\n"
            "📋 `/inventario` - Ver todos los productos\n"
            "🗑️ `/eliminar ID` - Eliminar producto\n"
            "✏️ `/editar ID campo valor` - Editar producto\n"
            "✅ `/activar ID` - Activar producto\n"
            "❌ `/desactivar ID` - Desactivar producto\n"
            "📊 `/stats` - Estadísticas de la tienda\n"
            "🏪 `/tienda Nombre` - Cambiar nombre de tienda\n"
            "📸 Envía una foto para agregar producto con IA\n\n"
            "❓ `/ayuda` - Mostrar esta ayuda"
        )
        await update.message.reply_text(texto)
    else:
        tienda_id = obtener_tienda_asociada(user_id)
        if tienda_id:
            context.user_data["tienda_id"] = tienda_id
            await update.message.reply_text(
                "👋 ¡Bienvenido de nuevo! Puedes preguntarme sobre los productos disponibles."
            )
        else:
            await update.message.reply_text(
                "👋 ¡Hola! Soy el asistente virtual de la tienda.\n\n"
                "Para comenzar, necesitas usar el enlace especial que te proporcionó la tienda.\n"
                "Ejemplo: t.me/TuBot?start=ID_DE_TIENDA\n\n"
                "Si ya tienes tu enlace, haz clic en él para empezar."
            )
