#!/usr/bin/env python3
"""
Script para probar la conexión a Supabase.

Uso:
    python test_conexion.py

Verifica:
    - Que SUPABASE_URL y SUPABASE_KEY existen en .env
    - Que la conexión TCP funciona
    - Que las tablas del esquema existen
    - Devuelve diagnóstico claro
"""

import sys
from bot.config.settings import SUPABASE_URL, SUPABASE_KEY
from bot.database.supabase_client import get_supabase


def test():
    print("=" * 50)
    print("  DIAGNÓSTICO DE CONEXIÓN SUPABASE")
    print("=" * 50)

    ok = True

    # 1. Variables de entorno
    print("\n[1/4] Variables de entorno:")
    url_ok = bool(SUPABASE_URL)
    key_ok = bool(SUPABASE_KEY)
    print(f"  SUPABASE_URL:  {'✓' if url_ok else '✗'} {SUPABASE_URL[:30] + '...' if url_ok else 'VACÍA'}")
    print(f"  SUPABASE_KEY:  {'✓' if key_ok else '✗'} {SUPABASE_KEY[:30] + '...' if key_ok else 'VACÍA'}")
    if not url_ok or not key_ok:
        print("\n  ❌ Faltan credenciales. Revisa tu archivo .env")
        ok = False

    # 2. Cliente Supabase
    print("\n[2/4] Creando cliente Supabase...")
    try:
        db = get_supabase()
        print("  ✓ Cliente creado correctamente")
    except Exception as e:
        print(f"  ✗ Error al crear cliente: {e}")
        ok = False

    if not ok:
        print("\n❌ Diagnóstico fallido. Revisa las credenciales en .env")
        sys.exit(1)

    # 3. Query de prueba
    print("\n[3/4] Probando consulta a tabla 'tiendas'...")
    try:
        result = db.table("tiendas").select("count", count="exact").limit(0).execute()
        count = result.count if hasattr(result, 'count') else 'N/A'
        print(f"  ✓ Conexión exitosa | count: {count}")
    except Exception as e:
        print(f"  ✗ Error en consulta: {e}")
        ok = False

    if not ok:
        print("\n❌ Diagnóstico fallido. Revisa la URL y KEY de Supabase.")
        sys.exit(1)

    # 4. Verificar tablas
    print("\n[4/4] Verificando tablas del esquema...")
    tablas = ["tiendas", "productos", "clientes", "consultas", "estadisticas"]
    todas_ok = True
    for table in tablas:
        try:
            db.table(table).select("count", count="exact").limit(0).execute()
            print(f"  ✓ Tabla '{table}' existe")
        except Exception:
            print(f"  ✗ Tabla '{table}' NO existe — ejecuta el SQL de esquema_supabase.sql")
            todas_ok = False

    print()
    print("=" * 50)
    if todas_ok:
        print("  ✅ DIAGNÓSTICO COMPLETADO — TODO OK")
    else:
        print("  ⚠️  Algunas tablas faltan. Ejecuta el esquema SQL.")
    print("=" * 50)


if __name__ == "__main__":
    test()
