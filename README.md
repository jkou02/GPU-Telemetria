# GPU-Telemetria

Sistema de telemetría de GPU con bot de Telegram. Soporta 1 o N PCs,
almacenando métricas en PostgreSQL y notificando alertas por Telegram.

## Arquitectura

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  PC 1    │     │  PC 2    │     │  PC N    │
│ agent.py │     │ agent.py │     │ agent.py │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────┬───────┴────────┬───────┘
              │                │
         PostgreSQL ◄──── main.py ────► Telegram Bot
           (central)         │
                          Usuarios
```

Dos componentes:

| Componente | Descripción |
|-----------|-------------|
| `main.py` | Bot de Telegram que responde comandos y envía alertas periódicas |
| `agent.py` | Recolector de métricas que corre en cada PC y escribe en PostgreSQL |

En modo 1 PC, ambos componentes corren en la misma máquina. En modo multi-PC,
`agent.py` se despliega en cada máquina cliente y apunta al PostgreSQL central
(accesible vía Tailscale).

## Requisitos

- **Python** >= 3.10
- **PostgreSQL** (local o remoto; se recomienda Tailscale para acceso multi-PC)
- **Tailscale** (solo para multi-PC)
- Dependencias Python principales:
  - `psutil`
  - `python-telegram-bot`
  - `python-dotenv`
  - `psycopg2-binary`
- Backends de GPU (opcionales, instalar según hardware):
  - `nvidia-ml-py` — NVIDIA
  - `pyrsmi` — AMD (requiere ROCm instalado)
  - `intel-gpu-tools` — Intel (requiere `intel-gpu-tools` del sistema)
- Bot de Telegram (crear con [@BotFather](https://t.me/botfather))

## Instalación

```bash
git clone https://github.com/usuario/GPU-Telemetria.git
cd GPU-Telemetria
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID y HOSTNAME
```

> Instalá el backend de GPU que corresponda, por ejemplo:
> ```bash
> pip install nvidia-ml-py    # NVIDIA
> pip install pyrsmi          # AMD (requiere ROCm)
> ```

### Crear la base de datos PostgreSQL

```bash
sudo -u postgres createdb telemetria
```

Las tablas se crean automáticamente al iniciar `agent.py` o `main.py`.

## Configuración (.env)

| Variable | Requerido | Default | Descripción |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sí | — | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | Sí | — | Chat ID donde el bot envía alertas |
| `DATABASE_URL` | Sí | — | URL de PostgreSQL: `postgresql://user:pass@host:5432/telemetria` |
| `HOSTNAME` | No | `hostname` del sistema | Identificador de esta máquina |
| `ALERT_CPU_TEMP` | No | `75` | Umbral de temperatura CPU (°C) |
| `ALERT_GPU_TEMP` | No | `80` | Umbral de temperatura GPU (°C) |
| `ALERT_RAM_PCT` | No | `90` | Umbral de uso de RAM (%) |
| `ALERT_VRAM_PCT` | No | `90` | Umbral de uso de VRAM (%) |
| `CHECK_INTERVAL_MIN` | No | `5` | Intervalo entre chequeos (minutos) |
| `GPU_BACKEND` | No | Vacío (auto) | Backend GPU: `nvidia`, `amd`, `intel` |

### Obtener TELEGRAM_CHAT_ID

1. Iniciar chat con tu bot en Telegram.
2. Enviar un mensaje cualquiera.
3. Visitar `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. El `chat.id` aparece en la respuesta JSON.

### Soporte multi-vendor GPU

El sistema detecta automáticamente el tipo de GPU. Orden de detección:
NVIDIA → AMD → Intel.

| Vendor | Método | Dependencia |
|---|---|---|
| **NVIDIA** | `pynvml` | `pip install nvidia-ml-py` |
| **AMD** | sysfs (`amdgpu`) | Driver `amdgpu` + `pip install pyrsmi` |
| **Intel** | sysfs (`i915`) | Driver `i915` + `intel-gpu-tools` |

Forzar backend: definir `GPU_BACKEND=nvidia`, `GPU_BACKEND=amd` o `GPU_BACKEND=intel` en `.env`.

## Uso

### Modo 1 PC

Ejecutar ambos componentes en la misma máquina:

```bash
python agent.py &   # Recolector de métricas (segundo plano)
python main.py      # Bot de Telegram (primer plano)
```

### Modo multi-PC (con Tailscale)

1. En el **servidor central** (donde está PostgreSQL):
   ```bash
   python main.py &      # Bot de Telegram
   python agent.py &     # Opcional: recolecta métricas del propio servidor
   ```

2. En cada **PC adicional**:
   - Asegurate de que Tailscale esté activo y la PC alcance el servidor PostgreSQL.
   - Configurá `DATABASE_URL` con la IP de Tailscale del servidor y un `HOSTNAME` único.
   ```bash
   python agent.py
   ```

## Comandos de Telegram

| Comando | Descripción |
|---|---|
| `/status [pc]` | Estado actual: CPU, RAM, GPU, uptime |
| `/gpu_info [pc]` | Detalle de GPU con barras visuales de uso |
| `/history [pc]` | Últimos 5 registros |
| `/alertas` | Umbrales de alerta configurados |
| `/pcs` | Lista de PCs registradas |

El argumento `[pc]` es opcional. Si se omite, se usa el `HOSTNAME` del agente
que esté corriendo en la misma máquina que el bot (o el definido en `.env`).

## Tests

El proyecto incluye 84 tests unitarios y de integración que cubren:

| Módulo | Archivo | Tests |
|---|---|---|
| Formateo de mensajes | `tests/test_formatter.py` | 21 |
| Repositorio (unitario) | `tests/test_repository.py` | 5 |
| Repositorio (integración PostgreSQL) | `tests/test_repository_integration.py` | 6 |
| Sistema de alertas | `tests/test_alerts.py` | 7 |
| Recolección del sistema | `tests/test_collector.py` | 9 |
| Handlers de Telegram | `tests/test_handlers.py` | 11 |
| Backend NVIDIA | `tests/test_gpu_nvidia.py` | 7 |
| Backend AMD | `tests/test_gpu_amd.py` | 5 |
| Backend Intel | `tests/test_gpu_intel.py` | 6 |

**Requisitos:** PostgreSQL accesible (los tests de integración usan la BD real configurada en `.env` y limpian sus datos automáticamente).

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## Despliegue con systemd

Crear las unidades en `~/.config/systemd/user/`. Ajustar rutas de
`WorkingDirectory` y `ExecStart` según tu entorno.

### gpu-telemetria-bot.service (main.py)

```ini
[Unit]
Description=GPU-Telemetria Bot
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/ruta/al/proyecto/GPU-Telemetria
ExecStart=/ruta/al/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### gpu-telemetria-agent.service (agent.py)

```ini
[Unit]
Description=GPU-Telemetria Agent
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/ruta/al/proyecto/GPU-Telemetria
ExecStart=/ruta/al/venv/bin/python agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Activar e iniciar:

```bash
systemctl --user daemon-reload
systemctl --user enable gpu-telemetria-bot gpu-telemetria-agent
systemctl --user start gpu-telemetria-bot gpu-telemetria-agent
```

Verificar estado:

```bash
systemctl --user status gpu-telemetria-bot gpu-telemetria-agent
```

Ver logs:

```bash
journalctl --user -u gpu-telemetria-bot -f
journalctl --user -u gpu-telemetria-agent -f
```

> En modo multi-PC, desplegá solo `gpu-telemetria-agent.service` en las PCs
> clientes, y ambos servicios en el servidor central.

## Migración desde SQLite

Si usabas una versión anterior basada en SQLite, la migración es automática:

- Al iniciar `agent.py` o `main.py` con `DATABASE_URL` configurado, el sistema
  busca `data/telemetry.db`.
- Si existe, migra los registros a PostgreSQL usando el `HOSTNAME` actual.
- El archivo SQLite se renombra a `data/telemetry.db.migrated`.

No requiere pasos manuales.

## Licencia

MIT — ver archivo [LICENSE](LICENSE).
