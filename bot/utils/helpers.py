from bot.config.settings import ADMIN_IDS


def es_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def formatear_producto(p: dict) -> str:
    nombre = p.get("nombre", "Sin nombre")
    precio = p.get("precio", "N/A")
    desc = p.get("descripcion", "")
    cat = p.get("categoria", "")
    color = p.get("color", "")
    talla = p.get("talla", "")
    stock = p.get("stock", 0)
    disponible = p.get("disponible", True)

    estado = "✅ Disponible" if disponible else "❌ No disponible"
    linea = f"🆔 #{p['id']} | {nombre} | 💰 ${precio}"
    if desc:
        linea += f"\n   📝 {desc}"
    if cat:
        linea += f"\n   📂 {cat}"
    if color or talla:
        linea += f"\n   🎨 {color} | {talla}"
    linea += f"\n   📦 Stock: {stock} | {estado}"
    return linea


def formatear_lista(productos: list[dict]) -> str:
    if not productos:
        return "📭 No hay productos registrados."
    lineas = ["📦 **Inventario:**\n"]
    for p in productos:
        lineas.append(formatear_producto(p))
        lineas.append("")
    return "\n".join(lineas)


def parsear_guardado(texto: str) -> dict:
    partes = [p.strip() for p in texto.split("|")]
    datos = {
        "nombre": "",
        "descripcion": "",
        "precio": 0,
        "categoria": "",
        "color": "",
        "talla": "",
        "stock": 0,
        "etiquetas": []
    }

    if partes:
        datos["nombre"] = partes[0]

    for p in partes[1:]:
        if p.lower().startswith("$"):
            try:
                datos["precio"] = float(p.replace("$", "").replace(",", "."))
            except ValueError:
                pass
        elif p.lower().startswith("precio"):
            try:
                datos["precio"] = float(p.split()[-1].replace("$", "").replace(",", "."))
            except ValueError:
                pass
        elif p.lower().startswith("cat") or p.lower().startswith("categor"):
            datos["categoria"] = p.split(":", 1)[-1].strip() if ":" in p else p.split()[-1]
        elif p.lower().startswith("color") or p.lower().startswith("col"):
            datos["color"] = p.split(":", 1)[-1].strip() if ":" in p else p.split()[-1]
        elif p.lower().startswith("talla") or p.lower().startswith("t"):
            datos["talla"] = p.split(":", 1)[-1].strip() if ":" in p else p.split()[-1]
        elif p.lower().startswith("stock") or p.lower().startswith("s"):
            try:
                datos["stock"] = int(p.split(":", 1)[-1].strip() if ":" in p else p.split()[-1])
            except ValueError:
                pass
        elif p.lower().startswith("desc") or p.lower().startswith("d"):
            datos["descripcion"] = p.split(":", 1)[-1].strip() if ":" in p else p.split(" ", 1)[-1]

    return datos
