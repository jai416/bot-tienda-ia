import os
import io
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from PIL import Image

# --- CONFIGURACIÓN ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

# !!! AQUÍ PON TU ID DE TELEGRAM !!!
ADMIN_ID =6988595915 

# Configurar el cliente moderno de Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
MODELO_IA = 'gemini-2.5-flash'  # Usamos la versión estable y rápida

ARCHIVO_CONOCIMIENTO = "base_conocimiento.txt"

# --- CORE: GESTIÓN DE LA MEMORIA DEL BOT ---
def leer_base_conocimiento():
    if not os.path.exists(ARCHIVO_CONOCIMIENTO) or os.stat(ARCHIVO_CONOCIMIENTO).st_size == 0:
        return "La tienda actualmente no tiene productos registrados en el inventario."
    with open(ARCHIVO_CONOCIMIENTO, 'r', encoding='utf-8') as f:
        return f.read()

def actualizar_memoria(nueva_informacion):
    memoria_vieja = leer_base_conocimiento()
    
    prompt_consolidacion = (
        f"Eres un sistema experto en gestión de inventarios.\n"
        f"Aquí tienes el catálogo actual de la tienda:\n{memoria_vieja}\n\n"
        f"El dueño acaba de aportar estos nuevos datos:\n{nueva_informacion}\n\n"
        f"Tu tarea es fusionar ambas informaciones. Devuelve un único catálogo consolidado, "
        f"perfectamente adelantado y estructurado por categorías, eliminando duplicados y aplicando las correcciones. "
        f"Sé directo, solo devuelve el catálogo limpio."
    )
    
    respuesta = client.models.generate_content(
        model=MODELO_IA,
        contents=prompt_consolidacion,
    )
    
    with open(ARCHIVO_CONOCIMIENTO, 'w', encoding='utf-8') as f:
        f.write(respuesta.text)
    return respuesta.text

# --- COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy el asistente virtual inteligente de la tienda.\n"
        "Pregúntame lo que quieras sobre ropa, tenis, precios o tallas disponibles."
    )

# --- PROCESAR ENTRADAS DEL ADMIN ---
async def entrenar_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    
    texto_admin = update.message.caption if update.message.caption else update.message.text
    info_para_guardar = ""

    if update.message.photo:
        foto_id = update.message.photo[-1].file_id
        archivo_foto = await context.bot.get_file(foto_id)
        bytes_foto = await archivo_foto.download_as_bytearray()
        imagen_pil = Image.open(io.BytesIO(bytes_foto))
        
        prompt_vision = (
            f"Analiza detalladamente esta imagen de un producto que el dueño va a subir a su tienda. "
            f"Describe qué artículo es, su estilo, color y marca si es visible. "
            f"El dueño agregó este comentario: '{texto_admin if texto_admin else 'Sin comentarios'}'. "
            f"Extrae y unifica toda la información relevante para el inventario."
        )
        
        respuesta_ia = client.models.generate_content(
            model=MODELO_IA,
            contents=[imagen_pil, prompt_vision]
        )
        info_para_guardar = respuesta_ia.text
    else:
        info_para_guardar = texto_admin

    catalogo_nuevo = actualizar_memoria(info_para_guardar)
    await update.message.reply_text(
        f"🧠 *¡Catálogo Actualizado, Jefe!* Inventario actual:\n\n{catalogo_nuevo}",
        parse_mode="Markdown"
    )

# --- PROCESAR CONSULTAS DEL CLIENTE ---
async def atender_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    
    pregunta_cliente = update.message.text
    conocimiento_actual = leer_base_conocimiento()
    
    prompt_cliente = (
        f"Eres el asistente virtual interactivo de una tienda en Cuba.\n"
        f"Tu misión es atender al cliente con el inventario real de la tienda.\n\n"
        f"--- INVENTARIO REAL ACTUALIZADO ---\n{conocimiento_actual}\n-----------------------------------\n\n"
        f"Reglas estrictas:\n"
        f"1. Responde basándote únicamente en el inventario real provisto arriba.\n"
        f"2. Si no hay stock, dilo con amabilidad y sugiere algo similar si aplica.\n"
        f"3. Usa un tono amigable, natural y cubano sutil (asere, bro), pero mantén el respeto.\n"
        f"4. Si quiere comprar, indícale que puede pagar por Transfermóvil, MLC o Zelle.\n\n"
        f"Pregunta del cliente: '{pregunta_cliente}'"
    )
    
    try:
        respuesta_ia = client.models.generate_content(
            model=MODELO_IA,
            contents=prompt_cliente
        )
        await update.message.reply_text(respuesta_ia.text)
        
        # Notificar al dueño por detrás
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👀 *Cliente preguntando:*\n💬 {pregunta_cliente}"
        )
    except Exception as e:
        await update.message.reply_text("Disculpa el bache, asere. ¿Me repites la pregunta?")
        print(f"Error en Gemini: {e}")

async def manejador_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await entrenar_bot(update, context)
    else:
        if update.message.text:
            await atender_cliente(update, context)

if __name__ == '__main__':
    print("🚀 Iniciando el Bot Inteligente Multimodal...")
    
    # Si estás en producción en la nube, corre limpio. 
    # Si estás en local con VPN, forzamos a usar el entorno del sistema.
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, manejador_principal))
    
    app.run_polling()
