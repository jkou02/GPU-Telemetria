# GPU-Telemetria

Monitoreo de CPU, RAM y GPU (NVIDIA, AMD, Intel) con almacenamiento local en SQLite y
notificaciones vía Telegram.

## Requisitos

- Linux con drivers de GPU instalados:
  - **NVIDIA**: driver NVIDIA + `nvidia-ml-py` (`pip install nvidia-ml-py`)
  - **AMD**: driver `amdgpu` del kernel (automático en la mayoría de distribuciones)
  - **Intel**: driver `i915` del kernel (automático en la mayoría de distribuciones)
- Python >= 3.10
- Bot de Telegram (crear con [@BotFather](https://t.me/botfather))

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Copiar y editar:

```bash
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot (de @BotFather) |
| `TELEGRAM_CHAT_ID` | Tu chat ID de Telegram |
| `ALERT_CPU_TEMP` | Umbral de temp. CPU (°C) |
| `ALERT_GPU_TEMP` | Umbral de temp. GPU (°C) |
| `ALERT_RAM_PCT` | Umbral de uso de RAM (%) |
| `ALERT_VRAM_PCT` | Umbral de uso de VRAM (%) |
| `CHECK_INTERVAL_MIN` | Intervalo entre chequeos (min) |
| `DB_PATH` | Ruta a la base SQLite |
| `GPU_BACKEND` | Backend GPU: `nvidia`, `amd`, `intel` (vacío = auto-detectar) |

### Obtener TELEGRAM_CHAT_ID

1. Iniciar chat con tu bot
2. Enviar un mensaje cualquiera
3. Visitar `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. El `chat.id` aparece en la respuesta JSON

### Soporte multi-vendor GPU

El sistema detecta automáticamente el tipo de GPU instalada:

| Vendor | Método de detección | Dependencias |
|--------|---------------------|--------------|
| **NVIDIA** | `pynvml` | `pip install nvidia-ml-py` |
| **AMD** | sysfs (`amdgpu`) | Driver `amdgpu` del kernel |
| **Intel** | sysfs (`i915`) | Driver `i915` del kernel |

**Auto-detección:** NVIDIA → AMD → Intel

**Forzar backend específico:**

```bash
GPU_BACKEND=nvidia python main.py
GPU_BACKEND=amd python main.py
GPU_BACKEND=intel python main.py
```

## Uso

### Ejecución manual (pruebas)

```bash
python main.py
```

El bot arranca en primer plano. Sirve para probar que funciona antes de
instalarlo como servicio. Comandos disponibles una vez corriendo:

- `/status` — estado actual del sistema
- `/gpu_info` — información detallada de la GPU detectada
- `/history` — últimos 5 registros de la base de datos
- `/alertas` — umbrales configurados

### Servicio systemd (automático)

Para que el bot arranque solo al iniciar sesión y se reinicie si falla,
creá un servicio de systemd por usuario.

1. Crear el archivo de unidad:

```bash
mkdir -p ~/.config/systemd/user
```

```ini
# ~/.config/systemd/user/gpu-telemetria.service
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

Ajustá `WorkingDirectory` y `ExecStart` a las rutas reales de tu equipo.

2. Activar e iniciar:

```bash
systemctl --user daemon-reload
systemctl --user enable gpu-telemetria
systemctl --user start gpu-telemetria
```

3. Verificar que esté corriendo:

```bash
systemctl --user status gpu-telemetria
```

4. Ver logs:

```bash
journalctl --user -u gpu-telemetria -f
```

5. Detener o reiniciar:

```bash
systemctl --user stop gpu-telemetria
systemctl --user restart gpu-telemetria
```
