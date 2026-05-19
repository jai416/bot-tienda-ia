import os
import logging
import io
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from PIL import Image

# 1. Configurar los registros de consola (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()

# 2. Leer las Variables de Entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]

# 3. Inicializar el cliente de Gemini
client = genai.Client(api_key=GEMINI_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_bienvenida = (
        "👋 ¡Hola! Bienvenido a nuestro Asistente Virtual Inteligente 🤖🚀\n\n"
        "Estoy aquí para ayudarte las 24 horas del día. Gracias a mi IA, puedo:\n"
        "📦 Darte el catálogo actual y precios de la tienda.\n"
        "📸 Reconocer productos si me mandas una foto.\n"
        "💡 Responder tus dudas sobre envíos o métodos de pago.\n\n"
        "👉 ¡Escríbeme tu duda o envíame la foto de lo que buscas de la tienda!"
    )
    await update.message.reply_text(texto_bienvenida)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto_recibido = update.message.text.strip()

    # 🔐 ZONA DE ADMINISTRADORES
    if user_id in ADMIN_IDS:
        
        # COMANDO 1: Guardar producto nuevo
        if texto_recibido.startswith("/guardar"):
            nueva_info = texto_recibido.replace("/guardar", "").strip()
            if not nueva_info:
                await update.message.reply_text("❌ Escribe algo válido. Ejemplo: `/guardar Zapatos Adidas, precio $40`")
                return
            with open("inventario.txt", "a", encoding="utf-8") as f:
                f.write(f"- {nueva_info}\n")
            await update.message.reply_text("📥 ¡Entendido jefe! Ya guardé ese producto.")
            return

        # COMANDO 2: Ver inventario numerado para poder eliminar
        if texto_recibido == "/inventario":
            try:
                with open("inventario.txt", "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                if not lineas:
                    await update.message.reply_text("📭 El inventario está vacío.")
                    return
                
                texto_lista = "📦 **Inventario Actual (Modo Admin):**\n\n"
                for i, linea in enumerate(lineas, 1):
                    # Limpiamos el guión inicial para mostrarlo bonito
                    prod = linea.replace("- ", "").strip()
                    texto_lista += f"{i}. {prod}\n"
                texto_lista += "\n👉 Para eliminar uno, usa: `/eliminar [número]`. Ejemplo: `/eliminar 2`"
                await update.message.reply_text(texto_lista)
                return
            except FileNotFoundError:
                await update.message.reply_text("📭 No hay productos registrados aún.")
                return

        # COMANDO 3: Eliminar un producto específico por su número
        if texto_recibido.startswith("/eliminar"):
            partes = texto_recibido.split()
            if len(partes) < 2 or not partes[1].isdigit():
                await update.message.reply_text("❌ Uso correcto: `/eliminar [número]`. Ejemplo: `/eliminar 3`")
                return
            
            num_a_borrar = int(partes[1])
            try:
                with open("inventario.txt", "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                
                if num_a_borrar < 1 or num_a_borrar > len(lineas):
                    await update.message.reply_text(f"❌ Número inválido. El inventario solo tiene {len(lineas)} productos.")
                    return
                
                # Sacamos la línea correspondiente (restamos 1 porque Python cuenta desde 0)
                eliminado = lineas.pop(num_a_borrar - 1)
                
                # Volvemos a escribir el archivo con las líneas que quedaron
                with open("inventario.txt", "w", encoding="utf-8") as f:
                    f.writelines(lineas)
                    
                await update.message.reply_text(f"🗑️ ¡Listo! Eliminado el producto:\n\"{eliminado.replace('- ', '').strip()}\"")
                return
            except FileNotFoundError:
                await update.message.reply_text("❌ No hay inventario creado todavía.")
                return

        # COMANDO 4: Resetear todo el inventario de un golpe
        if texto_recibido == "/borrartodo":
            if os.path.exists("inventario.txt"):
                os.remove("inventario.txt")
            await update.message.reply_text("💥 ¡Inventario completamente vaciado! El bot vuelve a estar de fábrica.")
            return

    # 👥 ZONA DE CLIENTES (Consultas normales a Gemini)
    try:
        with open("inventario.txt", "r", encoding="utf-8") as f:
            contexto_productos = f.read()
    except FileNotFoundError:
        contexto_productos = "No hay productos registrados en la tienda actualmente."

    instrucciones_ia = (
        "Eres el asistente virtual inteligente de nuestra tienda. Tu objetivo es atender a los clientes.\n"
        f"Aquí tienes el catálogo e inventario actualizado de la tienda:\n{contexto_productos}\n\n"
        "Reglas de oro:\n"
        "1. Responde siempre de manera amable, educada y profesional.\n"
        "2. Básate estrictamente en el inventario provisto. Si te preguntan por algo que NO está listado, "
        "di cortésmente que de momento no está disponible pero que pueden consultar más adelante."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto_recibido,
            config=types.GenerateContentConfig(system_instruction=instrucciones_ia)
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error en Gemini Texto: {e}")
        await update.message.reply_text("Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar escribirlo de otra forma?")

async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las imágenes que envían los clientes (Multimodal)"""
    foto_archivo = await update.message.photo[-1].get_file()
    foto_bytes = await foto_archivo.download_as_bytearray()
    imagen_pil = Image.open(io.BytesIO(foto_bytes))
    texto_usuario = update.message.caption or "¿Qué producto es este y qué detalles tiene según la tienda?"

    try:
        with open("inventario.txt", "r", encoding="utf-8") as f:
            contexto_productos = f.read()
    except FileNotFoundError:
        contexto_productos = "No hay productos registrados en la tienda actualmente."

    instrucciones_ia = (
        "Eres el asistente virtual de nuestra tienda. Analiza visualmente la foto enviada por el cliente "
        "y compárala con el inventario de nuestra tienda para identificar si lo tenemos y darle precio/detalles.\n"
        f"Inventario real de la tienda:\n{contexto_productos}"
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen_pil, texto_usuario],
            config=types.GenerateContentConfig(system_instruction=instrucciones_ia)
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error en Gemini Foto: {e}")
        await update.message.reply_text("Veo la imagen, pero no pude procesarla de momento.")

def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("❌ ERROR CRÍTICO: Faltan variables de entorno.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))

    print("🤖 Bot Inteligente con Panel de Control en marcha...")
    app.run_polling()

if __name__ == '__main__':
    main()
