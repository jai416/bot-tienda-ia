"""
Script de migración: inventario.txt → Supabase

Uso:
    python migrate_inventario.py <owner_id>

Ejemplo:
    python migrate_inventario.py 111111

Lee inventario.txt, migra cada línea como producto
asociado al owner_id (admin dueño de la tienda).
Luego respalda inventario.txt como inventario_backup.txt
y elimina el archivo original.
"""

import os
import sys
import shutil
from bot.database.queries import insertar_producto
from bot.database.supabase_client import get_supabase
from bot.database.queries import crear_tienda, obtener_tienda_por_owner
from bot.config.settings import SUPABASE_URL, SUPABASE_KEY


def migrar(owner_id: int):
    if not os.path.exists("inventario.txt"):
        print("No existe inventario.txt. Nada que migrar.")
        return

    tienda = obtener_tienda_por_owner(owner_id)
    if not tienda.data:
        print(f"Creando tienda para owner_id={owner_id}...")
        result = crear_tienda(owner_id)
        tienda_id = result.data[0]["id"]
        print(f"Tienda creada con ID: {tienda_id}")
    else:
        tienda_id = tienda.data["id"]
        print(f"Tienda existente encontrada con ID: {tienda_id}")

    with open("inventario.txt", "r", encoding="utf-8") as f:
        lineas = f.readlines()

    migrados = 0
    for linea in lineas:
        texto = linea.replace("- ", "").strip()
        if not texto:
            continue

        datos = {
            "nombre": texto,
            "descripcion": "",
            "precio": 0,
            "categoria": "",
            "color": "",
            "talla": "",
            "stock": 0,
            "disponible": True,
            "etiquetas": [],
            "imagen_url": "",
        }
        insertar_producto(tienda_id, datos)
        migrados += 1

    backup = "inventario_backup.txt"
    shutil.copy2("inventario.txt", backup)
    os.remove("inventario.txt")

    print(f"Migración completada: {migrados} productos migrados.")
    print(f"Backup creado: {backup}")
    print(f"inventario.txt ha sido eliminido.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python migrate_inventario.py <owner_id>")
        print("Ejemplo: python migrate_inventario.py 111111")
        sys.exit(1)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Configura SUPABASE_URL y SUPABASE_KEY en .env primero.")
        sys.exit(1)

    owner_id = int(sys.argv[1])
    migrar(owner_id)
