import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import BotCommandScopeChat, BotCommandScopeDefault

from bot.config.settings import BOT_TOKEN, GEMINI_KEY, SUPABASE_URL, ADMIN_IDS
from bot.database.supabase_client import get_supabase
from bot.handlers.start import start
from bot.handlers.admin import (
    cmd_guardar, cmd_inventario, cmd_eliminar, cmd_editar,
    cmd_activar, cmd_desactivar, cmd_stats, cmd_tienda,
    cmd_borrartodo, cmd_status, cmd_ayuda, cmd_confirmar,
    cmd_editar_sug, cmd_cancelar, manejar_foto_admin,
)
from bot.handlers.client import manejar_mensaje, manejar_foto

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def post_init(app: Application):
    commands_global = [
        ("start", "Iniciar / Vincular tienda"),
        ("ayuda", "Ayuda"),
    ]
    await app.bot.set_my_commands(
        commands_global,
        scope=BotCommandScopeDefault()
    )

    commands_admin = [
        ("start", "Panel de administración"),
        ("guardar", "Guardar producto"),
        ("inventario", "Ver inventario"),
        ("eliminar", "Eliminar producto"),
        ("editar", "Editar producto"),
        ("activar", "Activar producto"),
        ("desactivar", "Desactivar producto"),
        ("stats", "Estadísticas"),
        ("tienda", "Nombre de tienda"),
        ("borrartodo", "Vaciar inventario"),
        ("status", "Estado del sistema"),
        ("ayuda", "Ayuda"),
    ]
    for admin_id in ADMIN_IDS:
        await app.bot.set_my_commands(
            commands_admin,
            scope=BotCommandScopeChat(chat_id=admin_id)
        )

    try:
        db = get_supabase()
        db.table("tiendas").select("count", count="exact").limit(0).execute()
        print("✓ Conexión Supabase establecida correctamente")
        app.bot_data["supabase_ok"] = True
    except Exception as e:
        print(f"✗ Error de conexión Supabase: {e}")
        app.bot_data["supabase_ok"] = False


def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("ERROR CRÍTICO: Faltan BOT_TOKEN o GEMINI_KEY en .env")
        return

    if not SUPABASE_URL:
        print("ERROR CRÍTICO: Falta SUPABASE_URL en .env. "
              "Agrega SUPABASE_URL y SUPABASE_KEY para usar la base de datos.")
        return

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))

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
        ("status", cmd_status),
        ("ayuda", cmd_ayuda),
        ("confirmar", cmd_confirmar),
        ("editar_sug", cmd_editar_sug),
        ("cancelar", cmd_cancelar),
    ]
    for cmd, handler in admin_commands:
        app.add_handler(CommandHandler(cmd, handler))

    if ADMIN_IDS:
        app.add_handler(MessageHandler(
            filters.PHOTO & filters.User(ADMIN_IDS),
            manejar_foto_admin
        ))

    app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("Bot Multi-Tienda iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
