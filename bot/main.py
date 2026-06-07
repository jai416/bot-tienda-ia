import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.config.settings import BOT_TOKEN, GEMINI_KEY, SUPABASE_URL, ADMIN_IDS
from bot.handlers.start import start
from bot.handlers.admin import (
    cmd_guardar, cmd_inventario, cmd_eliminar, cmd_editar,
    cmd_activar, cmd_desactivar, cmd_stats, cmd_tienda,
    cmd_borrartodo, cmd_ayuda, cmd_confirmar, cmd_editar_sug,
    cmd_cancelar, manejar_foto_admin,
)
from bot.handlers.client import manejar_mensaje, manejar_foto

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("ERROR CRÍTICO: Faltan BOT_TOKEN o GEMINI_KEY en .env")
        return

    if not SUPABASE_URL:
        print("ERROR CRÍTICO: Falta SUPABASE_URL en .env. "
              "Agrega SUPABASE_URL y SUPABASE_KEY para usar la base de datos.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Comando /start
    app.add_handler(CommandHandler("start", start))

    # Comandos de administración
    admin_commands = [
        ("guardar", cmd_guardar),
        ("inventario", cmd_inventario),
        ("eliminar", cmd_eliminar),
        ("editar", cmd_editar),
        ("activar", cmd_activar),
        ("desactivar", cmd_desactivar),
        ("stats", cmd_stats),
        ("tienda", cmd_tienda),
        ("borrartodo", cmd_borrartodo),
        ("ayuda", cmd_ayuda),
        ("confirmar", cmd_confirmar),
        ("editar_sug", cmd_editar_sug),
        ("cancelar", cmd_cancelar),
    ]
    for cmd, handler in admin_commands:
        app.add_handler(CommandHandler(cmd, handler))

    # Manejador de fotos para admin
    if ADMIN_IDS:
        app.add_handler(MessageHandler(
            filters.PHOTO & filters.User(ADMIN_IDS),
            manejar_foto_admin
        ))

    # Manejador de fotos para clientes
    app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))

    # Manejador de mensajes de texto para clientes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("Bot Multi-Tienda iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
