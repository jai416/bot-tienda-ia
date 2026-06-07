# AUDITORÍA TÉCNICA: bot_tienda_ia

## Sistema SaaS Multi-Tienda para Telegram + Gemini + Supabase

---

## 1. VISIÓN GENERAL

### Proyecto Original
- **Archivo único**: `bot_premium.py` (183 líneas monolíticas)
- **Persistencia**: `inventario.txt` (archivo local)
- **Escalabilidad**: 1 tienda, 1 admin
- **Gemini**: Recibía el catálogo COMPLETO en cada consulta
- **Multi-tienda**: No soportado

### Proyecto Evolucionado
- **Arquitectura**: Modular, 20+ archivos organizados en 8 módulos
- **Persistencia**: Supabase (PostgreSQL cloud)
- **Escalabilidad**: Cientos de tiendas, miles de productos
- **Gemini**: RAG controlado, solo recibe productos relevantes
- **Multi-tienda**: Completo aislamiento por `tienda_id`

---

## 2. ESTRUCTURA DEL PROYECTO

```
bot_tienda_ia/
├── bot/
│   ├── __init__.py
│   ├── main.py                     # Entry point del bot
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Variables de entorno
│   ├── database/
│   │   ├── __init__.py
│   │   ├── supabase_client.py      # Cliente Supabase singleton
│   │   └── queries.py              # Queries SQL parametrizadas
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Dataclasses tipadas
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py                # /start + deep linking
│   │   ├── admin.py                # CRUD administración
│   │   └── client.py               # Consultas de clientes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tienda_service.py       # Lógica de tiendas
│   │   ├── producto_service.py     # CRUD de productos
│   │   ├── cliente_service.py      # Gestión de clientes
│   │   ├── busqueda_service.py     # Motor de búsqueda RAG
│   │   └── estadisticas_service.py # Estadísticas
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── gemini_client.py        # Wrapper Gemini controlado
│   │   └── prompts.py              # Instrucciones del sistema
│   └── utils/
│       ├── __init__.py
│       └── helpers.py              # Funciones auxiliares
├── migrate_inventario.py           # Script de migración
├── .env                            # Variables de entorno
├── .gitignore
├── requirements.txt
└── AUDITORIA.md
```

### Propósito de cada archivo

| Archivo | Responsabilidad |
|---|---|
| `bot/main.py` | Construye la aplicación, registra handlers, inicia polling |
| `bot/config/settings.py` | Carga todas las variables de entorno (nada hardcodeado) |
| `bot/database/supabase_client.py` | Singleton del cliente Supabase |
| `bot/database/queries.py` | Todas las consultas SQL parametrizadas |
| `bot/models/schemas.py` | Tipos de datos (Tienda, Producto, Cliente, Consulta) |
| `bot/handlers/start.py` | Comando /start, deep linking, panel admin |
| `bot/handlers/admin.py` | Comandos de administración + carga inteligente con foto |
| `bot/handlers/client.py` | Atención al cliente con búsqueda RAG |
| `bot/services/tienda_service.py` | Crear/obtener/actualizar tiendas |
| `bot/services/producto_service.py` | CRUD de productos con filtro tienda_id |
| `bot/services/cliente_service.py` | Registrar/obtener clientes por tienda |
| `bot/services/busqueda_service.py` | Tokenizar consultas, buscar en Supabase, RAG |
| `bot/services/estadisticas_service.py` | Registrar y consultar estadísticas |
| `bot/ai/gemini_client.py` | Wrapper seguro con temperature=0.1 |
| `bot/ai/prompts.py` | Instrucciones fijas anti-alucinaciones |
| `bot/utils/helpers.py` | Validación admin, formateo, parseo |

---

## 3. ARQUITECTURA RAG (RETRIEVAL AUGMENTED GENERATION)

### Flujo obligatorio para cada consulta de cliente

```
CLIENTE: "¿Tienen zapatos negros?"
              │
              ▼
    ┌─────────────────────────┐
    │  handlers/client.py     │
    │  1. Obtiene tienda_id   │
    │     (user_data o DB)    │
    └─────────┬───────────────┘
              │
              ▼
    ┌──────────────────────────────────────────┐
    │ services/busqueda_service.py             │
    │                                          │
    │ 1. Tokenizar: "tienen zapatos negros"    │
    │    → tokens = ["zapatos", "negros"]      │
    │    (stopwords eliminadas)                │
    │                                          │
    │ 2. Buscar en Supabase:                   │
    │    SELECT * FROM productos               │
    │    WHERE tienda_id = X                   │
    │    AND disponible = true                 │
    │    AND (nombre ILIKE '%zapatos%'         │
    │         OR descripcion ILIKE '%zapatos%' │
    │         OR categoria ILIKE '%zapatos%')  │
    │    AND (color ILIKE '%negro%'            │
    │         OR etiquetas @> '{negro}')       │
    │    LIMIT 15                              │
    │                                          │
    │ 3. ¿Hay resultados?                      │
    │    ├── Sí → pasar a Gemini               │
    │    └── No → buscar alternativas          │
    │          (misma categoría)               │
    │          ├── Sí → Gemini con alternativas│
    │          └── No → respuesta directa      │
    │                SIN Gemini                │
    │                                          │
    │ 4. Registrar consulta en estadísticas    │
    └─────────┬────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────────────┐
    │ ai/gemini_client.py                      │
    │                                          │
    ● temperature = 0.1 (mínima creatividad)   │
    ● System instruction FIJA:                 │
    │ "Usa exclusivamente los datos            │
    │  proporcionados. No inventes nada."      │
    ● Recibe SOLO productos relevantes (≤15)   │
    ● NUNCA recibe el catálogo completo        │
    └─────────┬────────────────────────────────┘
              │
              ▼
    RESPUESTA: "Sí, tenemos zapatos negros.
    Tenemos el modelo X en talla 42 a $40
    y el modelo Y en talla 40 a $38.
    ¿Te interesa alguno?"
```

### Lo que Gemini NUNCA hace

- ❌ Decidir qué productos existen
- ❌ Inventar precios, stock, promociones
- ❌ Recibir el catálogo completo
- ❌ Actuar como base de datos
- ❌ Almacenar información

### Lo que Supabase SIEMPRE hace

- ✅ Es la fuente de verdad de productos
- ✅ Responde con datos reales
- ✅ Filtra por tienda_id
- ✅ Garantiza aislamiento entre tiendas

---

## 4. ESQUEMA DE BASE DE DATOS

### Relaciones

```
tiendas (1) ──── (N) productos
tiendas (1) ──── (N) clientes
tiendas (1) ──── (N) consultas
tiendas (1) ──── (1) estadisticas
```

### Tablas

**tiendas**
| Campo | Tipo | Descripción |
|---|---|---|
| id | BIGSERIAL | PK |
| owner_id | BIGINT UNIQUE | ID de Telegram del admin |
| nombre_tienda | TEXT | Nombre configurable |
| descripcion | TEXT | Descripción de la tienda |
| activo | BOOLEAN | Si la tienda está activa |
| fecha_creacion | TIMESTAMPTZ | Auto |

**productos**
| Campo | Tipo | Descripción |
|---|---|---|
| id | BIGSERIAL | PK |
| tienda_id | BIGINT FK | Tienda a la que pertenece |
| nombre | TEXT | Nombre del producto |
| descripcion | TEXT | Descripción |
| precio | NUMERIC(10,2) | Precio en USD |
| categoria | TEXT | Categoría |
| color | TEXT | Color |
| talla | TEXT | Talla |
| stock | INTEGER | Stock disponible |
| disponible | BOOLEAN | Si está activo para venta |
| etiquetas | TEXT[] | Array de etiquetas |
| imagen_url | TEXT | URL de la imagen |
| fecha_creacion | TIMESTAMPTZ | Auto |
| fecha_actualizacion | TIMESTAMPTZ | Auto |

**clientes**
| Campo | Tipo | Descripción |
|---|---|---|
| id | BIGSERIAL | PK |
| cliente_id | BIGINT | ID de Telegram del cliente |
| tienda_id | BIGINT FK | Tienda asociada |
| username | TEXT | @username |
| primer_nombre | TEXT | Nombre en Telegram |
| primera_vez | TIMESTAMPTZ | Fecha de primer ingreso |

### Índices

- `idx_productos_tienda`: Búsqueda rápida por tienda
- `idx_productos_categoria`: Filtrado por categoría
- `idx_productos_busqueda`: Búsqueda de texto completo en español (tsvector)
- `idx_clientes_telegram`: Búsqueda de cliente por Telegram ID
- `idx_consultas_tienda`: Estadísticas por tienda

---

## 5. SISTEMA DE DEEP LINKING (ENLACES ÚNICOS)

### Cómo funciona

```
El admin comparte: t.me/MiBot?start=5

El cliente hace clic y abre el bot.
El bot recibe: /start 5

Flujo:
1. Bot extrae "5" como tienda_id
2. Inserta/actualiza: clientes(cliente_id=USER, tienda_id=5)
3. Guarda tienda_id=5 en context.user_data
4. A partir de ese momento, TODAS las consultas
   del cliente usan tienda_id=5
```

### Seguridad

- El cliente solo puede consultar productos de su tienda asociada
- Si no tiene tienda asociada, el bot le pide el enlace
- El admin ve SOLO sus propios productos

---

## 6. COMANDOS DEL ADMIN

| Comando | Descripción |
|---|---|
| `/start` | Panel de administración |
| `/guardar nombre \| $precio \| cat:Cat \| color:Col \| talla:T \| stock:N` | Agregar producto |
| `/inventario` | Listar todos los productos |
| `/eliminar ID` | Eliminar producto por ID |
| `/editar ID campo valor` | Editar campo de producto |
| `/activar ID` | Marcar producto como disponible |
| `/desactivar ID` | Marcar producto como no disponible |
| `/stats` | Estadísticas de la tienda |
| `/tienda Nombre` | Cambiar nombre de la tienda |
| `/borrartodo` | Eliminar todos los productos |
| `/ayuda` | Mostrar ayuda |
| Enviar foto | IA sugiere producto, admin confirma/edita |
| `/confirmar` | Guardar producto sugerido por IA |
| `/editar_sug campo valor` | Editar campo de sugerencia IA |
| `/cancelar` | Cancelar sugerencia IA |

---

## 7. VARIABLES DE ENTORNO

```env
BOT_TOKEN=          # Token del bot de Telegram
GEMINI_KEY=         # API key de Gemini
ADMIN_IDS=          # IDs de Telegram separados por coma
SUPABASE_URL=       # URL del proyecto Supabase
SUPABASE_KEY=       # Service role key de Supabase
```

**Nada está hardcodeado. Todo se lee desde .env mediante `os.getenv()`.**

---

## 8. DECISIONES TÉCNICAS

| Decisión | Alternativa | Motivo |
|---|---|---|
| BIGSERIAL como PK | UUID | 4x más rápido en índices, menos espacio |
| BIGINT para IDs Telegram | VARCHAR | Los IDs de Telegram ya son enteros |
| TEXT[] para etiquetas | Tabla separada | Consultas más rápidas, menos JOINs |
| tsvector en productos | Elasticsearch | Sin servicio adicional, Railway no lo incluye gratis |
| Sin SQLAlchemy | ORM completo | supabase client es suficiente, más ligero |
| context.user_data | Redis | Sin dependencias extra, Railway no ofrece Redis gratis |
| temperature=0.1 | Default | Minimiza alucinaciones |
| ILIKE + tsvector | Solo tsvector | Captura búsquedas parciales |

---

## 9. GUÍA DE DESPLIEGUE

### 9.1 Supabase

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Ir a SQL Editor
3. Pegar y ejecutar el contenido de `esquema_supabase.sql`
4. Copiar `Project URL` a `SUPABASE_URL` en `.env`
5. Copiar `service_role key` a `SUPABASE_KEY` en `.env`

### 9.2 Railway

1. Conectar repositorio a Railway
2. Agregar variables de entorno en Railway Dashboard:

   ```
   BOT_TOKEN=...
   GEMINI_KEY=...
   ADMIN_IDS=...
   SUPABASE_URL=...
   SUPABASE_KEY=...
   ```

3. Comando de inicio: `python -m bot.main`

### 9.3 Local (desarrollo)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

---

## 10. PLAN DE MONETIZACIÓN FUTURA

El sistema está preparado para:

1. **Límites por plan**:
   - Gratis: 50 productos, 500 consultas/mes
   - Pro: 500 productos, 10,000 consultas/mes
   - Enterprise: Ilimitado

2. **Campos adicionales en `tiendas`** (sin migración):
   - `plan TEXT DEFAULT 'gratis'`
   - `limite_productos INTEGER DEFAULT 50`
   - `limite_consultas INTEGER DEFAULT 500`
   - `proximo_pago TIMESTAMPTZ`

3. **Control en `busqueda_service.py`**:
   - Verificar límite antes de procesar consulta
   - Bloquear si excede el plan

4. **Escalabilidad horizontal**:
   - Railway auto-escala
   - Supabase maneja miles de consultas concurrentes
   - Gemini 2.5 Flash es económico (~$0.15/1M tokens)

---

## 11. CHECKLIST DE VERIFICACIÓN

- [ ] `SUPABASE_URL` y `SUPABASE_KEY` configurados en `.env`
- [ ] `ADMIN_IDS` configurados en `.env`
- [ ] Esquema SQL ejecutado en Supabase
- [ ] `python -m bot.main` inicia sin errores
- [ ] `/start` responde correctamente
- [ ] Admin puede agregar producto con `/guardar`
- [ ] Admin puede listar con `/inventario`
- [ ] Admin puede eliminar con `/eliminar`
- [ ] Admin puede editar con `/editar`
- [ ] Cliente puede consultar con enlace deep link
- [ ] Productos de tienda A no aparecen en tienda B
- [ ] Gemini no alucina productos
- [ ] Foto con IA sugiere producto correctamente

---

## 12. MANTENIMIENTO

### Diario
- Revisar logs del bot en Railway
- Verificar consumo de tokens Gemini

### Semanal
- Revisar estadísticas de tiendas
- Verificar espacio en Supabase

### Mensual
- Evaluar límites de planes gratuitos
- Actualizar dependencias si es necesario

---

*Documento generado como parte de la auditoría técnica y evolución arquitectónica del proyecto bot_tienda_ia. Junio 2026.*
