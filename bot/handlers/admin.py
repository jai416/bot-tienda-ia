from telegram import Update
from telegram.ext import ContextTypes
from google import genai
from google.genai import types

from bot.config.settings import GEMINI_KEY
from bot.database.supabase_client import get_supabase
from bot.database.queries import (
    insertar_producto, listar_productos, obtener_producto,
    actualizar_producto, activar_producto, desactivar_producto,
    eliminar_producto, obtener_estadisticas,
)
from bot.services.tienda_service import obtener_o_crear_tienda, actualizar_nombre_tienda
from bot.ai.gemini_client import sugerir_desde_foto
from bot.utils.helpers import formatear_producto, formatear_lista, parsear_guardado

_gemini_client = genai.Client(api_key=GEMINI_KEY)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_status = "✅ Bot funcionando"

    try:
        _gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents="ping",
            config=types.GenerateContentConfig(temperature=0)
        )
        gemini_status = "✅ Gemini conectado"
    except Exception:
        gemini_status = "❌ Gemini NO responde"

    supabase_ok = context.application.bot_data.get("supabase_ok")
    if supabase_ok:
        supabase_status = "✅ Supabase conectada"
    else:
        supabase_status = "❌ Supabase NO disponible"

    texto = (
        "📊 **Estado del Sistema**\n\n"
        f"🤖 Bot: {bot_status}\n"
        f"🧠 Gemini: {gemini_status}\n"
        f"🗄️ Supabase: {supabase_status}\n\n"
        "Si ves alguna ❌, contacta al desarrollador."
    )
    await update.message.reply_text(texto)


async def _supabase_ok(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.application.bot_data.get("supabase_ok", False)


async def cmd_guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text(
            "🔧 Estamos teniendo problemas técnicos con nuestros servidores.\n"
            "Nuestro equipo ya está trabajando para solucionarlo.\n"
            "Por favor, intenta de nuevo más tarde. 🙏"
        )
        return
    user_id = update.effective_user.id
    texto = update.message.text.replace("/guardar", "", 1).strip()

    if not texto:
        await update.message.reply_text(
            "❌ Uso: `/guardar Nombre | $precio | cat:Categoría | color:Rojo | talla:M | stock:10`"
        )
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    datos = parsear_guardado(texto)
    if not datos["nombre"]:
        await update.message.reply_text("❌ Debes especificar al menos el nombre del producto.")
        return

    prod = insertar_producto(tienda["id"], datos)
    if prod:
        await update.message.reply_text(f"✅ Producto guardado:\n{formatear_producto(prod)}")
    else:
        await update.message.reply_text("❌ Error al guardar el producto.")


async def cmd_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text(
            "🔧 Estamos teniendo problemas técnicos con nuestros servidores.\n"
            "Nuestro equipo ya está trabajando para solucionarlo. 🙏"
        )
        return
    user_id = update.effective_user.id
    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    productos = listar_productos(tienda["id"])
    if not productos:
        await update.message.reply_text("📭 El inventario está vacío.")
        return

    texto = formatear_lista(productos)
    texto += "\n\n👉 Para eliminar: `/eliminar ID`\n👉 Para editar: `/editar ID campo valor`"
    await update.message.reply_text(texto)


async def cmd_eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    partes = update.message.text.split()
    if len(partes) < 2 or not partes[1].isdigit():
        await update.message.reply_text("❌ Uso: `/eliminar ID`")
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    producto_id = int(partes[1])
    prod = obtener_producto(tienda["id"], producto_id)
    if not prod:
        await update.message.reply_text("❌ Producto no encontrado.")
        return

    eliminar_producto(tienda["id"], producto_id)
    await update.message.reply_text(f"🗑️ Producto eliminado: {prod['nombre']}")


async def cmd_editar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    partes = update.message.text.split(maxsplit=3)
    if len(partes) < 4:
        await update.message.reply_text(
            "❌ Uso: `/editar ID campo valor`\n"
            "Campos: nombre, descripcion, precio, categoria, color, talla, stock"
        )
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    producto_id = int(partes[1])
    campo = partes[2].lower()
    valor = partes[3]

    mapa_campos = {
        "nombre": "nombre",
        "descripcion": "descripcion",
        "precio": "precio",
        "categoria": "categoria",
        "color": "color",
        "talla": "talla",
        "stock": "stock",
    }

    if campo not in mapa_campos:
        await update.message.reply_text(f"❌ Campo inválido. Válidos: {', '.join(mapa_campos.keys())}")
        return

    db_campo = mapa_campos[campo]
    valor_convertido = valor
    if db_campo == "precio":
        try:
            valor_convertido = float(valor.replace("$", "").replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Precio inválido.")
            return
    elif db_campo == "stock":
        try:
            valor_convertido = int(valor)
        except ValueError:
            await update.message.reply_text("❌ Stock inválido.")
            return

    prod = actualizar_producto(tienda["id"], producto_id, {db_campo: valor_convertido})
    if prod:
        await update.message.reply_text(f"✅ Producto actualizado:\n{formatear_producto(prod)}")
    else:
        await update.message.reply_text("❌ Producto no encontrado.")


async def cmd_activar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    partes = update.message.text.split()
    if len(partes) < 2 or not partes[1].isdigit():
        await update.message.reply_text("❌ Uso: `/activar ID`")
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    prod = activar_producto(tienda["id"], int(partes[1]))
    if prod:
        await update.message.reply_text(f"✅ Producto activado: {prod['nombre']}")
    else:
        await update.message.reply_text("❌ Producto no encontrado.")


async def cmd_desactivar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    partes = update.message.text.split()
    if len(partes) < 2 or not partes[1].isdigit():
        await update.message.reply_text("❌ Uso: `/desactivar ID`")
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    prod = desactivar_producto(tienda["id"], int(partes[1]))
    if prod:
        await update.message.reply_text(f"⛔ Producto desactivado: {prod['nombre']}")
    else:
        await update.message.reply_text("❌ Producto no encontrado.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    stats = obtener_estadisticas(tienda["id"])
    productos = listar_productos(tienda["id"])
    total_productos = len(productos)
    activos = sum(1 for p in productos if p.get("disponible"))

    texto = f"📊 **Estadísticas de {tienda['nombre_tienda']}**\n\n"
    texto += f"🏪 Tienda ID: {tienda['id']}\n"
    texto += f"📦 Total productos: {total_productos}\n"
    texto += f"✅ Productos activos: {activos}\n"
    texto += f"❌ Productos inactivos: {total_productos - activos}\n"

    if stats:
        texto += f"💬 Total consultas: {stats.get('total_consultas', 0)}\n"
        texto += f"🔍 Búsquedas sin resultado: {stats.get('busquedas_sin_resultado', 0)}\n"

    await update.message.reply_text(texto)


async def cmd_tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    nombre = update.message.text.replace("/tienda", "", 1).strip()

    if not nombre:
        await update.message.reply_text("❌ Uso: `/tienda Nombre de mi tienda`")
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    actualizar_nombre_tienda(tienda["id"], nombre)
    await update.message.reply_text(f"✅ Nombre de tienda actualizado: {nombre}")


async def cmd_borrartodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    productos = listar_productos(tienda["id"])
    for p in productos:
        eliminar_producto(tienda["id"], p["id"])

    await update.message.reply_text("💥 ¡Todos los productos han sido eliminados!")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📚 **Ayuda de comandos**\n\n"
        "📦 `/guardar nombre | $precio | cat:Cat | color:Col | talla:T | stock:N`\n"
        "📋 `/inventario` - Ver productos\n"
        "🗑️ `/eliminar ID` - Eliminar producto\n"
        "✏️ `/editar ID campo valor` - Editar producto\n"
        "✅ `/activar ID` - Activar producto\n"
        "❌ `/desactivar ID` - Desactivar producto\n"
        "📊 `/stats` - Estadísticas\n"
        "🏪 `/tienda Nombre` - Cambiar nombre\n"
        "💥 `/borrartodo` - Vaciar inventario\n"
        "📸 Envía una foto para agregar con IA\n\n"
        "❓ `/ayuda` - Esta ayuda"
    )
    await update.message.reply_text(texto)


async def manejar_foto_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    await update.message.reply_text("🔍 Analizando imagen con IA...")

    foto_archivo = await update.message.photo[-1].get_file()
    foto_bytes = await foto_archivo.download_as_bytearray()

    sugerencia = sugerir_desde_foto(foto_bytes)
    if not sugerencia:
        await update.message.reply_text("❌ No pude analizar la imagen. Intenta de nuevo.")
        return

    context.user_data["sugerencia_producto"] = sugerencia
    texto = (
        "🤖 **Sugerencia de producto:**\n\n"
        f"📛 Nombre: {sugerencia.get('nombre', 'N/A')}\n"
        f"📝 Descripción: {sugerencia.get('descripcion', 'N/A')}\n"
        f"💰 Precio: ${sugerencia.get('precio', 0)}\n"
        f"📂 Categoría: {sugerencia.get('categoria', 'N/A')}\n"
        f"🎨 Color: {sugerencia.get('color', 'N/A')}\n"
        f"📏 Talla: {sugerencia.get('talla', 'N/A')}\n"
        f"🏷️ Etiquetas: {', '.join(sugerencia.get('etiquetas', []))}\n\n"
        "Comandos:\n"
        "✅ `/confirmar` - Guardar producto\n"
        "✏️ `/editar_sug campo valor` - Editar campo\n"
        "❌ `/cancelar` - Cancelar"
    )
    await update.message.reply_text(texto)


async def cmd_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _supabase_ok(context):
        await update.message.reply_text("🔧 Error de conexión. Intenta más tarde. 🙏")
        return
    user_id = update.effective_user.id
    sugerencia = context.user_data.get("sugerencia_producto")
    if not sugerencia:
        await update.message.reply_text("❌ No hay ninguna sugerencia pendiente. Envía una foto primero.")
        return

    tienda = obtener_o_crear_tienda(user_id)
    if not tienda:
        await update.message.reply_text("❌ No se pudo obtener tu tienda.")
        return

    prod = insertar_producto(tienda["id"], sugerencia)
    if prod:
        await update.message.reply_text(f"✅ Producto guardado:\n{formatear_producto(prod)}")
        context.user_data.pop("sugerencia_producto", None)
    else:
        await update.message.reply_text("❌ Error al guardar el producto.")


async def cmd_editar_sug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sugerencia = context.user_data.get("sugerencia_producto")
    if not sugerencia:
        await update.message.reply_text("❌ No hay ninguna sugerencia pendiente.")
        return

    partes = update.message.text.split(maxsplit=2)
    if len(partes) < 3:
        await update.message.reply_text("❌ Uso: `/editar_sug campo valor`")
        return

    campo = partes[1].lower()
    valor = partes[2]

    mapa = {
        "nombre": "nombre",
        "descripcion": "descripcion",
        "precio": "precio",
        "categoria": "categoria",
        "color": "color",
        "talla": "talla",
        "etiquetas": "etiquetas",
    }

    if campo not in mapa:
        await update.message.reply_text(f"❌ Campo inválido: {', '.join(mapa.keys())}")
        return

    db_campo = mapa[campo]
    if db_campo == "precio":
        try:
            valor = float(valor.replace("$", "").replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Precio inválido.")
            return
    elif db_campo == "etiquetas":
        valor = [v.strip() for v in valor.split(",")]

    sugerencia[db_campo] = valor
    context.user_data["sugerencia_producto"] = sugerencia
    await update.message.reply_text(f"✅ Campo '{campo}' actualizado a: {valor}")


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("sugerencia_producto", None)
    await update.message.reply_text("❌ Sugerencia cancelada.")
