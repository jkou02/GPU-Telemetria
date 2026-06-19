# PLAN MULTI-PC — GPU-Telemetria

Plan de actualización del sistema para soportar múltiples PCs monitoreadas desde
un único bot de Telegram, usando PostgreSQL como base de datos central compartida
vía Tailscale.

---

## 1. Objetivo

El sistema actual monitorea **1 sola PC**: el bot de Telegram y la recolección de
métricas corren en el mismo proceso (`main.py`), almacenando los datos en SQLite
local.

Se migrará a una arquitectura **multi-PC** donde:

- Varias PCs ejecutan un **agente recolector** (`agent.py`) que envía métricas a
  una base de datos PostgreSQL central.
- Un **bot de Telegram** (`main.py`) lee de PostgreSQL y responde comandos,
  pudiendo consultar métricas de cualquier PC registrada.
- **SQLite se elimina completamente**. PostgreSQL es la única base de datos.
- La conectividad entre PCs se resuelve con **Tailscale** (infraestructura, no
  código).

El modo 1 PC sigue siendo posible: misma PC ejecuta `agent.py` + `main.py`,
ambos apuntando al mismo PostgreSQL.

---

## 2. Arquitectura objetivo

```
┌──────────────────────────────────────────────────┐
│                Servidor Central                    │
│  ┌────────────┐    ┌───────────────────────────┐  │
│  │  main.py   │───▶│        PostgreSQL          │  │
│  │  (bot)     │◀───│   Tabla: telemetry         │  │
│  └────────────┘    │   (hostname TEXT NOT NULL)  │  │
│                    └───────────────────────────┘  │
│                              ▲                     │
└──────────────────────────────┼─────────────────────┘
                               │ Tailscale
          ┌────────────────────┼────────────────────┐
          │                    │                     │
          ▼                    ▼                     ▼
   ┌────────────┐       ┌────────────┐       ┌────────────┐
   │  agent.py  │       │  agent.py  │       │  agent.py  │
   │  PC-A      │       │  PC-B      │       │  PC-C      │
   │  (nvidia)  │       │  (amd)     │       │  (intel)   │
   └────────────┘       └────────────┘       └────────────┘
```

### Componentes

| Componente | Rol | Dependencias |
|---|---|---|
| `main.py` | Bot de Telegram. Responde comandos leyendo de PostgreSQL. | `python-telegram-bot`, `psycopg2-binary` |
| `agent.py` | Recolector de métricas. Lee CPU/GPU/RAM local y escribe en PostgreSQL. | `psutil`, `psycopg2-binary`, backend GPU |
| PostgreSQL | Base de datos central compartida. | Ninguna de código (infraestructura) |
| Tailscale | Red mesh VPN para conectar agentes con el servidor. | Ninguna de código (infraestructura) |

### Modos de operación

- **Modo 1 PC**: `agent.py` y `main.py` en la misma máquina, ambos apuntando al
  mismo PostgreSQL (local o remoto). Equivalente funcional al sistema actual pero
  sobre PostgreSQL.
- **Modo N PCs**: Un servidor central con PostgreSQL + `main.py`. Cada PC
  monitoreada ejecuta `agent.py` con su propio `HOSTNAME`.

---

## 3. Archivos a modificar/crear

| Archivo | Acción | Descripción |
|---|---|---|
| `config.py` | Modificar | Eliminar `DB_PATH`. Añadir `DATABASE_URL` (requerido) y `HOSTNAME` (default: `socket.gethostname()`). |
| `database/repository.py` | Reescribir | Eliminar SQLite. Solo PostgreSQL con `psycopg2`. Tabla `telemetry` incluye campo `hostname TEXT NOT NULL`. Migración automática desde SQLite viejo. |
| `bot/handlers.py` | Modificar | Comandos aceptan argumento opcional `[hostname]`. Sin argumento: usar `HOSTNAME` de la PC local. Añadir comando `/pcs`. |
| `bot/formatter.py` | Modificar | Mostrar `hostname` en `/status`, `/history`, `/gpu_info`. Nuevo: `format_pc_list()`. |
| `bot/alerts.py` | Modificar | Iterar sobre todos los `hostname` en BD. Para cada uno, obtener último registro y evaluar umbrales. Ya no recolecta métricas (eso lo hace `agent.py`). |
| `main.py` | Modificar | Eliminar recolección de métricas del job de alertas. Adaptar job para multi-PC. |
| `agent.py` | **Nuevo** | Bucle: recolectar métricas → `insert_telemetry()` → dormir `CHECK_INTERVAL_MIN * 60`. Sin dependencia de Telegram. |
| `.env.example` | Modificar | Quitar `DB_PATH`. Añadir `DATABASE_URL` y `HOSTNAME`. |
| `requirements.txt` | Modificar | Añadir `psycopg2-binary`. |

---

## 4. Nueva tabla de base de datos

Esquema PostgreSQL objetivo:

```sql
CREATE TABLE IF NOT EXISTS telemetry (
    id            SERIAL PRIMARY KEY,
    hostname      TEXT NOT NULL,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cpu_temp      REAL,
    ram_total     BIGINT,
    ram_used      BIGINT,
    ram_percent   REAL,
    gpu_name      TEXT,
    gpu_temp      REAL,
    vram_total    BIGINT,
    vram_used     BIGINT,
    vram_percent  REAL,
    gpu_util      REAL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_hostname ON telemetry (hostname);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry (timestamp DESC);
```

Cambios respecto al esquema SQLite actual:

- `id`: `SERIAL` en vez de `INTEGER PRIMARY KEY AUTOINCREMENT`.
- `hostname TEXT NOT NULL`: **nuevo campo obligatorio**.
- `timestamp`: `TIMESTAMPTZ` con `DEFAULT NOW()` en vez de `TEXT` con
  `datetime('now', 'localtime')`.
- `ram_*` y `vram_*`: `BIGINT` en vez de `INTEGER`.
- Índices sobre `hostname` y `timestamp` para consultas frecuentes.

---

## 5. Migración de datos existentes

El proceso de migración es **automático** y se ejecuta al iniciar el sistema
por primera vez tras la actualización.

### Flujo

1. Al iniciar, verificar si existe `data/telemetry.db`.
2. Si **no existe**: continuar normalmente (solo PostgreSQL).
3. Si **existe**:
   - Leer todos los registros de la tabla `telemetry` en SQLite.
   - Insertarlos en PostgreSQL con `hostname = HOSTNAME` (valor de la variable
     de entorno configurada en esa PC).
   - Renombrar `data/telemetry.db` → `data/telemetry.db.migrated`.
   - Registrar en log: `"Migrados X registros como '{HOSTNAME}'"`.
4. Ejecuciones siguientes: el archivo `.migrated` no se procesa. Solo
   PostgreSQL.

### Consideraciones

- La migración ocurre **una sola vez por PC**. Si se ejecuta en el servidor y
  en cada agente, solo la PC donde exista `data/telemetry.db` migrará datos.
- Los timestamps de SQLite son `TEXT` con formato `YYYY-MM-DD HH:MM:SS` local.
  Se convierten a `TIMESTAMPTZ` asumiendo la zona horaria local de la máquina
  que ejecuta la migración.
- Si PostgreSQL ya tiene registros con el mismo `hostname`, la migración no
  deduplica. Esto es aceptable porque la migración ocurre una sola vez y en un
  sistema que antes era mono-PC.

---

## 6. Variables de entorno (`.env` final)

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sí | — | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | Sí | — | Chat ID donde el bot envía alertas |
| `DATABASE_URL` | Sí | — | URL de conexión PostgreSQL. Formato: `postgresql://user:pass@host:5432/dbname` |
| `HOSTNAME` | No (agent.py) / Sí (útil) | `socket.gethostname()` | Identificador único de la PC. Usado en comandos y alertas. |
| `CHECK_INTERVAL_MIN` | No | `5` | Intervalo en minutos entre recolecciones del agente |
| `ALERT_CPU_TEMP` | No | `75` | Umbral de temperatura CPU (°C) |
| `ALERT_GPU_TEMP` | No | `80` | Umbral de temperatura GPU (°C) |
| `ALERT_RAM_PCT` | No | `90` | Umbral de uso de RAM (%) |
| `ALERT_VRAM_PCT` | No | `90` | Umbral de uso de VRAM (%) |
| `GPU_BACKEND` | No | `""` (auto) | Backend GPU: `nvidia`, `amd`, `intel`. Vacío = auto-detectar. |

**Nota sobre `DATABASE_URL`**: incluye credenciales. No se hardcodea. En
producción usar Tailscale IP o hostname de la máquina con PostgreSQL.

---

## 7. Comandos de Telegram (comportamiento final)

| Comando | Comportamiento |
|---|---|
| `/status [pc]` | Estado actual del sistema. Si se especifica PC, muestra el último registro de esa PC. Si no, usa `HOSTNAME` de la máquina local (útil en modo 1 PC). |
| `/history [pc]` | Últimos 5 registros. Filtrable por PC. Sin argumento: `HOSTNAME` local. |
| `/gpu_info [pc]` | Información detallada de GPU del último registro. Filtrable por PC. |
| `/alertas` | Umbrales de alerta configurados (sin cambios). |
| `/pcs` | **Nuevo**. Lista todas las PCs registradas en la BD (hostnames únicos con timestamp del último registro). |

El argumento `[pc]` es opcional en `/status`, `/history` y `/gpu_info`. Cuando
se omite, el bot usa `HOSTNAME` de su propia configuración como default.

---

## 8. Dependencias nuevas

### Código

| Dependencia | Uso |
|---|---|
| `psycopg2-binary` | Driver PostgreSQL para Python. Reemplaza a `sqlite3` (stdlib). |

`requirements.txt` actualizado:

```
psutil
python-telegram-bot[job-queue]>=20.0
python-dotenv
psycopg2-binary

# Backends de GPU (instalar el que necesites)
# nvidia-ml-py    # NVIDIA
# pyrsmi          # AMD (requiere ROCm instalado)
# intel-gpu-tools # Intel (requiere intel-gpu-tools instalado)
```

### Infraestructura

| Componente | Rol |
|---|---|
| **Tailscale** | VPN mesh para conectar agentes con el servidor PostgreSQL. Todas las PCs deben estar en la misma tailnet. |
| **PostgreSQL** | Base de datos central. Instalada en el servidor que ejecuta `main.py`. |

---

## 9. Instrucciones de despliegue

### 9.1. Servidor central (PostgreSQL + bot)

1. **Instalar PostgreSQL** en el servidor:
   ```bash
   sudo apt install postgresql
   sudo -u postgres createuser gpu_telemetry -P
   sudo -u postgres createdb gpu_telemetry -O gpu_telemetry
   ```

2. **Configurar Tailscale** en el servidor y en cada PC agente. Obtener la IP
   de Tailscale del servidor (`tailscale ip -4`).

3. **Clonar el repositorio** en el servidor:
   ```bash
   git clone <repo> /opt/gpu-telemetria
   cd /opt/gpu-telemetria
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configurar `.env`** en el servidor:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF
   TELEGRAM_CHAT_ID=123456789
   DATABASE_URL=postgresql://gpu_telemetry:password@localhost:5432/gpu_telemetry
   HOSTNAME=servidor
   ```

5. **Ejecutar el bot**:
   ```bash
   python main.py
   ```
   O instalar como servicio systemd (ver README.md).

6. **Ejecutar el agente** (si se quiere monitorear el propio servidor):
   ```bash
   python agent.py
   ```

### 9.2. Cada PC agente

1. **Instalar Tailscale** y conectarla a la misma tailnet.

2. **Clonar el repositorio** e instalar dependencias (igual que arriba).

3. **Configurar `.env`** con `DATABASE_URL` apuntando a la IP de Tailscale del
   servidor:
   ```env
   DATABASE_URL=postgresql://gpu_telemetry:password@100.64.0.1:5432/gpu_telemetry
   HOSTNAME=pc-estacion-trabajo
   ```
   El resto de variables no son necesarias en agentes puros, pero no hacen daño.

4. **Ejecutar el agente**:
   ```bash
   python agent.py
   ```
   Opcional: instalar como servicio systemd.

### 9.3. Verificación

- En Telegram, enviar `/pcs` para ver las PCs registradas.
- Enviar `/status pc-estacion-trabajo` para ver el estado de una PC remota.
- Esperar a que se dispare una alerta multi-PC.

---

## 10. Notas de implementación

### `agent.py` — estructura esperada

```python
import time
from config import CHECK_INTERVAL_MIN, HOSTNAME
from collector.system import get_system_stats
from collector.gpu import get_gpu_stats
from database.repository import init_db, insert_telemetry, migrate_from_sqlite

def main():
    init_db()
    migrate_from_sqlite()
    while True:
        system = get_system_stats()
        gpu = get_gpu_stats()
        insert_telemetry(system, gpu)
        time.sleep(CHECK_INTERVAL_MIN * 60)

if __name__ == "__main__":
    main()
```

### `database/repository.py` — cambios clave

- `_get_connection()` usa `psycopg2.connect(DATABASE_URL)`.
- `init_db()` ejecuta `CREATE TABLE IF NOT EXISTS` con el esquema PostgreSQL.
- `insert_telemetry()` incluye `hostname=HOSTNAME` en el INSERT.
- `get_recent_entries(limit, hostname=None)` acepta filtro opcional por hostname.
- Nueva función `get_distinct_hostnames()` para el comando `/pcs`.
- Nueva función `migrate_from_sqlite()` que implementa la migración automática.

### `bot/alerts.py` — nuevo flujo

1. Obtener todos los `hostname` distintos de la BD.
2. Para cada uno, obtener el último registro.
3. Evaluar umbrales sobre ese registro.
4. Si se dispara una alerta, incluir el `hostname` en el mensaje.

### `bot/handlers.py` — extracción de argumento

```python
args = context.args
hostname = args[0] if args else HOSTNAME
```

Los comandos que aceptan `[pc]` extraen el argumento de `context.args` y lo
pasan al formatter/repository.

---

*Documento generado como referencia de implementación. No reemplaza decisiones
de arquitectura que surjan durante el desarrollo.*
