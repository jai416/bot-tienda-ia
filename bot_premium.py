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

# Cargar archivo .env local si existe (para tus pruebas en PC)
load_dotenv()

# 2. Leer las Variables de Entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# Leer los IDs de administradores (ej: "123456,789101") y convertirlos en lista de números
admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]

# 3. Inicializar el cliente de la Inteligencia Artificial de Google
client = genai.Client(api_key=GEMINI_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el saludo inicial cuando un usuario escribe /start"""
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
    """Maneja los mensajes de texto entrantes"""
    user_id = update.effective_user.id
    texto_recibido = update.message.text

    # 🔐 CASO 1: Es un Administrador intentando registrar un producto
    if user_id in ADMIN_IDS and texto_recibido.startswith("/guardar"):
        nueva_info = texto_recibido.replace("/guardar", "").strip()
        if not nueva_info:
            await update.message.reply_text("❌ Por favor, escribe algo válido. Ejemplo: `/guardar Zapatos Adidas, talla 41, precio $40`")
            return

        # Guardar la nueva línea en el archivo de memoria
        with open("inventario.txt", "a", encoding="utf-8") as f:
            f.write(f"- {nueva_info}\n")
            
        await update.message.reply_text("📥 ¡Entendido jefe! Ya guardé ese producto en mi memoria.")
        return

    # 👥 CASO 2: Cliente consultando al Bot (o admin haciendo pregunta común)
    # Intentar leer los productos memorizados
    try:
        with open("inventario.txt", "r", encoding="utf-8") as f:
            contexto_productos = f.read()
    except FileNotFoundError:
        contexto_productos = "No hay productos registrados en la tienda actualmente."

    # Instrucciones fijas que moldean la personalidad de la IA
    instrucciones_ia = (
        "Eres el asistente virtual inteligente de nuestra tienda. Tu objetivo es atender a los clientes.\n"
        f"Aquí tienes el catálogo e inventario actualizado de la tienda:\n{contexto_productos}\n\n"
        "Reglas de oro:\n"
        "1. Responde siempre de manera amable, educada y profesional.\n"
        "2. Básate estrictamente en el inventario provisto. Si te preguntan por algo que NO está listado, "
        "di cortésmente que de momento no está disponible pero que pueden consultar más adelante."
    )

    try:
        # Llamada oficial a Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto_recibido,
            config=types.GenerateContentConfig(
                system_instruction=instrucciones_ia
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error en Gemini Texto: {e}")
        await update.message.reply_text("Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentar escribirlo de otra forma?")

async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las imágenes que envían los clientes (Multimodal)"""
    # Descargar la foto enviada en la mayor calidad posible
    foto_archivo = await update.message.photo[-1].get_file()
    foto_bytes = await foto_archivo.download_as_bytearray()
    
    # Convertirla a un formato que entienda Gemini usando la librería Pillow
    imagen_pil = Image.open(io.BytesIO(foto_bytes))
    
    # Si el cliente escribió texto junto con la foto, lo capturamos. Si no, usamos una pregunta genérica
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
        # Gemini analiza tanto la imagen de PIL como el texto en un solo viaje
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen_pil, texto_usuario],
            config=types.GenerateContentConfig(
                system_instruction=instrucciones_ia
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Error en Gemini Foto: {e}")
        await update.message.reply_text("Veo la imagen, pero no pude procesarla correctamente con mi sistema de visión. ¿Me dices el nombre del producto por texto?")

def main():
    if not BOT_TOKEN or not GEMINI_KEY:
        print("❌ ERROR CRÍTICO: Faltan variables de entorno básicas para arrancar.")
        return

    # Iniciar la aplicación del bot de Telegram
    app = Application.builder().token(BOT_TOKEN).build()

    # Registrar las funciones encargadas de escuchar los eventos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))

    print("🤖 Bot Inteligente Protegido en marcha con éxito...")
    app.run_polling()

if __name__ == '__main__':
    main()
