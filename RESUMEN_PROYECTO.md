# 📋 Resumen del Proyecto — GPU-Telemetria

## 1. Resumen Ejecutivo

### Propósito

GPU-Telemetria es un sistema de monitoreo de hardware (CPU, RAM, GPU) que recolecta métricas en tiempo real y las expone a través de un bot de Telegram. Resuelve la necesidad de supervisar el estado térmico y de uso de una o múltiples PCs de forma remota, con alertas automáticas cuando se superan umbrales configurables.

### Arquitectura

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

Dos componentes independientes:

| Componente | Archivo | Función |
|---|---|---|
| **Agente recolector** | `agent.py` | Recolecta métricas de CPU/GPU/RAM local y escribe en PostgreSQL |
| **Bot de Telegram** | `main.py` | Responde comandos (`/status`, `/history`, `/gpu_info`, `/pcs`, `/alertas`) y envía alertas periódicas |

En modo 1 PC ambos corren en la misma máquina. En modo multi-PC, cada máquina ejecuta `agent.py` y apunta a un PostgreSQL central vía Tailscale.

### Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python >= 3.10 |
| Base de datos | PostgreSQL (con migración automática desde SQLite) |
| Driver BD | `psycopg2-binary` |
| Bot | `python-telegram-bot` (con job-queue para alertas) |
| Métricas del sistema | `psutil` |
| Configuración | `python-dotenv` (.env) |
| GPU NVIDIA | `pynvml` (`nvidia-ml-py`) |
| GPU AMD | sysfs (`amdgpu`), `pyrsmi`, `rocm-smi` |
| GPU Intel | sysfs (`i915`), `intel_gpu_top` |
| Tests | `pytest`, `pytest-mock`, `pytest-asyncio` |
| Despliegue | systemd (servicios de usuario) |
| Red multi-PC | Tailscale (infraestructura) |

### Estado Actual

- ✅ Migración de SQLite a PostgreSQL completada.
- ✅ Soporte multi-PC funcional (N PCs → 1 PostgreSQL → 1 bot).
- ✅ Soporte multi-vendor GPU (NVIDIA, AMD, Intel) con auto-detección.
- ✅ 84 tests (unitarios y de integración) pasando.
- ✅ Documentación completa (README, PLAN_MULTI_PC, AGENTS).
- ✅ Despliegue con systemd documentado.
- ⚠️ Sin CI/CD automatizado.
- ⚠️ Sin linters ni formatters configurados.
- ⚠️ Sin lock file de dependencias.
- ⚠️ Uso de `print()` en lugar de `logging`.

---

## 2. 🏆 Fortalezas del Proyecto

1. **Arquitectura limpia y desacoplada**: Separación clara entre `collector/`, `database/`, `bot/` y los puntos de entrada (`main.py`, `agent.py`). Cada capa tiene una responsabilidad definida.

2. **Multi-vendor GPU con auto-detección**: Soporta NVIDIA, AMD e Intel con un protocolo común (`GPUBackend`). El usuario no necesita configurar nada si tiene hardware estándar.

3. **Múltiples estrategias por vendor**: AMD tiene tres backends (sysfs, pyrsmi, rocm-smi) con fallback automático. Intel tiene sysfs + `intel_gpu_top`. Esto maximiza compatibilidad.

4. **Diseño extensible**: La interfaz `GPUBackend` (Protocol) permite agregar nuevos vendors o estrategias sin modificar el código existente.

5. **Modo 1 PC y N PCs con el mismo código**: Sin flags ni modos especiales. La diferencia es puramente operativa (dónde se ejecuta cada componente).

6. **Migración automática desde SQLite**: Los usuarios de versiones anteriores no pierden datos. La migración es transparente y se ejecuta una sola vez.

7. **Suite de tests sólida**: 84 tests que cubren formatters, handlers, alertas, repositorio (unitario e integración), y los tres backends de GPU.

8. **Documentación completa**: README con instalación, configuración, uso, despliegue con systemd y soporte multi-PC. PLAN_MULTI_PC documenta decisiones de arquitectura.

9. **Configuración vía .env**: Todas las variables sensibles y ajustables están externalizadas. `.env.example` sirve como referencia.

10. **Alertas multi-PC**: El sistema de alertas itera sobre todos los hostnames registrados, no solo la máquina local.

---

## 3. 🎯 Plan de Mejoras por Prioridad

### Prioridad Alta 🔴

#### 1. CI/CD con GitHub Actions

**Descripción**: Configurar un pipeline automático que corra los tests en cada push y pull request.

**Importancia**: Detecta errores de integración temprano, asegura que los cambios no rompan funcionalidad existente, y permite integración continua sin depender de que el desarrollador corra tests manualmente.

**Pasos para completar**:

- **Planificación**:
  - Definir matriz de versiones de Python a soportar (mínimo 3.10).
  - Los tests de integración requieren PostgreSQL — decidir si usar un servicio de GitHub Actions o migrar a testcontainers (ver mejora #10).

- **Ejecución**:
  1. Crear `.github/workflows/test.yml`.
  2. Configurar trigger en `push` y `pull_request` a `main`.
  3. Definir job con `ubuntu-latest`.
  4. Steps: checkout, setup Python, instalar dependencias (`requirements.txt` + `requirements-dev.txt`), configurar PostgreSQL (servicio), correr `pytest`.

- **Pruebas**:
  - Verificar que el workflow se ejecuta en un PR de prueba.
  - Confirmar que los 84 tests pasan en CI.
  - Validar que un test que falla rompe el build.

---

#### 2. Linters y Formatters (ruff + mypy)

**Descripción**: Incorporar `ruff` (linting + formateo) y `mypy` (type checking) al proyecto.

**Importancia**: Mantiene consistencia de estilo, detecta errores de tipos y bugs potenciales antes del review, y establece un estándar de calidad para contribuciones futuras.

**Pasos para completar**:

- **Planificación**:
  - `ruff` reemplaza `flake8`, `isort`, `black` — una sola herramienta.
  - Decidir nivel de exigencia de `mypy` (empezar con configuración básica, no strict).

- **Ejecución**:
  1. Agregar `ruff` y `mypy` a `requirements-dev.txt`.
  2. Crear configuración en `pyproject.toml` (secciones `[tool.ruff]` y `[tool.mypy]`).
  3. Ejecutar `ruff check .` y `ruff format .` para ver el estado actual.
  4. Corregir errores o agregar excepciones justificadas.
  5. Ejecutar `mypy .` y agregar tipos donde falten de forma gradual.

- **Pruebas**:
  - Integrar ambos en CI (ver mejora #1): `ruff check .`, `ruff format --check .`, `mypy .`.
  - Verificar que el código actual pasa (o definir un plan de corrección gradual).

---

#### 3. Lock File de Dependencias

**Descripción**: Generar un archivo de versiones exactas de todas las dependencias (directas y transitivas).

**Importancia**: Garantiza reproducibilidad de builds. Evita el problema "funciona en mi máquina" cuando una dependencia nueva rompe algo en producción. Esencial para CI confiable.

**Pasos para completar**:

- **Planificación**:
  - Opciones: `pip-tools` (`pip-compile`), `Poetry`, `uv`, o `pip freeze`.
  - Recomendación: `pip-tools` por simplicidad — no cambia el flujo actual de `requirements.txt`.

- **Ejecución**:
  1. Instalar `pip-tools`: `pip install pip-tools`.
  2. Renombrar `requirements.txt` a `requirements.in` (dependencias directas).
  3. Ejecutar `pip-compile requirements.in -o requirements.txt`.
  4. Ejecutar `pip-compile requirements-dev.in -o requirements-dev.txt`.
  5. Documentar en README: `pip-compile` para actualizar, `pip-sync` para instalar.

- **Pruebas**:
  - Verificar que `pip install -r requirements.txt` funciona en un venv limpio.
  - Confirmar que CI usa el lock file.

---

#### 4. Sistema de Logging

**Descripción**: Reemplazar `print()` por el módulo `logging` estándar de Python con niveles apropiados.

**Importancia**: Permite controlar verbosidad sin modificar código, habilita rotación de logs, integración con systemd/journald, y preparación para sistemas de monitoreo centralizado.

**Pasos para completar**:

- **Planificación**:
  - Identificar todos los `print()` actuales: `agent.py` (3), `database/repository.py` (1).
  - Definir niveles: `INFO` para operaciones normales, `WARNING` para errores recuperables, `ERROR` para fallos.
  - Configurar formato con timestamp y hostname.

- **Ejecución**:
  1. Crear módulo `logging_config.py` o configurar logging en `config.py`.
  2. Formato: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
  3. Reemplazar `print()` en `agent.py` por `logger.info()` / `logger.error()`.
  4. Reemplazar `print()` en `repository.py` (migración SQLite) por `logger.info()`.
  5. Agregar `logging.getLogger(__name__)` en cada módulo.

- **Pruebas**:
  - Ejecutar `agent.py` y verificar que los logs aparecen con formato correcto.
  - Probar con variable de entorno `LOG_LEVEL=DEBUG` para validar control de verbosidad.
  - Confirmar que tests siguen pasando.

---

### Prioridad Media 🟡

#### 5. Pool de Conexiones a BD

**Descripción**: Usar `psycopg2.pool.ThreadedConnectionPool` o context managers para reutilizar conexiones en lugar de abrir/cerrar en cada operación.

**Importancia**: Cada función en `repository.py` abre y cierra una conexión nueva. Bajo carga (múltiples PCs escribiendo frecuentemente), esto genera overhead innecesario. Un pool reduce latencia y uso de recursos del servidor PostgreSQL.

**Pasos para completar**:

- **Planificación**:
  - Evaluar si `agent.py` (un solo hilo) necesita pool o si basta con una conexión persistente.
  - Para `main.py` (bot con job-queue asíncrono), un pool es más relevante.
  - Considerar context managers (`with get_connection() as conn`) para asegurar cierre.

- **Ejecución**:
  1. Crear función `_get_pool()` en `repository.py` que inicialice un pool perezoso.
  2. Reemplazar `_get_connection()` para obtener del pool.
  3. Agregar método `_release_connection()` o usar context managers.
  4. Cerrar pool en shutdown graceful (ver mejora #7).

- **Pruebas**:
  - Ejecutar tests de integración — deben seguir pasando.
  - Medir tiempo de respuesta de `insert_telemetry()` antes y después.
  - Simular carga con múltiples inserciones concurrentes.

---

#### 6. Validación de Configuración al Inicio

**Descripción**: Verificar que las variables de entorno críticas están presentes y son válidas antes de iniciar la aplicación.

**Importancia**: Actualmente, si falta `DATABASE_URL` o `TELEGRAM_BOT_TOKEN`, el error ocurre en runtime cuando ya se intentó conectar. Fallar rápido con un mensaje claro ahorra tiempo de debugging.

**Pasos para completar**:

- **Planificación**:
  - Variables requeridas para `main.py`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DATABASE_URL`.
  - Variables requeridas para `agent.py`: `DATABASE_URL`.
  - Validar formatos: `DATABASE_URL` debe empezar con `postgresql://`, `TELEGRAM_CHAT_ID` debe ser numérico.

- **Ejecución**:
  1. Crear función `validate_config(required_vars: list[str])` en `config.py`.
  2. Lanzar `SystemExit` con mensaje claro si falta alguna variable.
  3. Llamar al inicio de `main()` en `main.py` y `agent.py`.
  4. Incluir en el mensaje qué variables faltan y un ejemplo de formato.

- **Pruebas**:
  - Ejecutar sin `.env` y verificar mensaje de error claro.
  - Ejecutar con `DATABASE_URL` inválido y verificar que falla antes de conectar.
  - Confirmar que con configuración válida arranca normalmente.

---

#### 7. Manejo de Señales en agent.py

**Descripción**: Capturar `SIGINT` y `SIGTERM` para realizar un shutdown graceful del agente.

**Importancia**: Actualmente `agent.py` corre un `while True` sin manejo de señales. Al detener el servicio (systemctl stop, Ctrl+C), puede interrumpir una inserción en BD. Un shutdown graceful asegura que las conexiones se cierren correctamente y los datos no se pierdan.

**Pasos para completar**:

- **Planificación**:
  - Señales a capturar: `SIGINT` (Ctrl+C), `SIGTERM` (systemctl stop).
  - Acciones: cerrar conexión BD (si es persistente), log de shutdown, salir con código 0.
  - Usar `signal.signal()` o un flag `_running = True` que el bucle verifica.

- **Ejecución**:
  1. Importar `signal` y `sys`.
  2. Definir flag `_running = True` a nivel de módulo.
  3. Registrar handler: `signal.signal(signal.SIGTERM, _shutdown)`.
  4. Handler setea `_running = False` y hace log.
  5. Cambiar `while True` por `while _running`.
  6. Agregar `time.sleep()` con intervalos cortos para responder rápido a señales.

- **Pruebas**:
  - Ejecutar `agent.py` y enviar `kill -TERM <pid>`. Verificar que termina limpiamente.
  - Verificar que Ctrl+C funciona sin traceback.
  - Confirmar que systemd reporta estado "deactivated" limpio.

---

#### 8. Versiones de Dependencias

**Descripción**: Fijar versiones mínimas en `requirements.txt` para todas las dependencias.

**Importancia**: Actualmente `psutil`, `python-dotenv` y `psycopg2-binary` no tienen versión mínima. Un breaking change en una dependencia puede romper la aplicación sin previo aviso. Fijar versiones mínimas hace los builds predecibles.

**Pasos para completar**:

- **Planificación**:
  - Revisar versiones instaladas actualmente en el entorno de desarrollo.
  - Consultar changelogs de cada dependencia para identificar versiones estables conocidas.
  - Decidir estrategia: `>=` (mínimo) vs `~=` (compatible con).

- **Ejecución**:
  1. Ejecutar `pip freeze` en el entorno actual para ver versiones.
  2. Actualizar `requirements.txt`:
     ```
     psutil>=5.9
     python-telegram-bot[job-queue]>=20.0
     python-dotenv>=1.0
     psycopg2-binary>=2.9
     ```
  3. Actualizar `requirements-dev.txt` con versiones mínimas de pytest y plugins.
  4. Probar instalación desde cero en un venv limpio.

- **Pruebas**:
  - Crear venv nuevo, instalar desde `requirements.txt`, correr tests.
  - Verificar que no hay warnings de compatibilidad.

---

### Prioridad Baja 🟢

#### 9. Refactor de gpu_amd.py

**Descripción**: Separar las tres estrategias de detección de AMD (sysfs, pyrsmi, rocm-smi) en clases independientes que implementen `GPUBackend`.

**Importancia**: `gpu_amd.py` tiene 301 líneas con lógica de tres métodos mezclada. Separar en clases reduce complejidad ciclomática, facilita testing individual de cada backend, y sigue el patrón ya usado para NVIDIA e Intel.

**Pasos para completar**:

- **Planificación**:
  - Crear tres clases: `AMDSysfsBackend`, `AMDPyrsmiBackend`, `AMDRocmSmiBackend`.
  - Cada una implementa `is_available()` y `get_gpu_stats()`.
  - Crear `AMDGPU` como dispatcher que prueba cada backend en orden.

- **Ejecución**:
  1. Crear archivo `collector/gpu_amd_sysfs.py` con `AMDSysfsBackend`.
  2. Crear archivo `collector/gpu_amd_pyrsmi.py` con `AMDPyrsmiBackend`.
  3. Crear archivo `collector/gpu_amd_rocm.py` with `AMDRocmSmiBackend`.
  4. Simplificar `gpu_amd.py` para que sea un dispatcher.
  5. Actualizar tests para cubrir cada clase por separado.

- **Pruebas**:
  - Los tests existentes de `test_gpu_amd.py` deben seguir pasando.
  - Agregar tests unitarios para cada backend individual.
  - Verificar que la auto-detección sigue el mismo orden (sysfs → pyrsmi → rocm-smi).

---

#### 10. Tests de Integración con testcontainers

**Descripción**: Usar `testcontainers-postgresql` para levantar un PostgreSQL efímero en Docker durante los tests de integración.

**Importancia**: Los tests de integración actuales requieren un PostgreSQL real configurado en `.env`. Esto complica CI y el setup de nuevos desarrolladores. Con testcontainers, cada test suite levanta su propia BD aislada.

**Pasos para completar**:

- **Planificación**:
  - Requiere Docker disponible en el entorno de desarrollo y CI.
  - El fixture debe crear y destruir el contenedor por sesión de tests.
  - Migrar `test_repository_integration.py` para usar el contenedor.

- **Ejecución**:
  1. Agregar `testcontainers[postgresql]` a `requirements-dev.txt`.
  2. Crear fixture en `conftest.py` que levante un contenedor PostgreSQL.
  3. Configurar `DATABASE_URL` dinámicamente desde el contenedor.
  4. Migrar tests de `test_repository_integration.py` para usar el fixture.
  5. Actualizar CI para incluir Docker.

- **Pruebas**:
  - Ejecutar `pytest tests/test_repository_integration.py -v` sin PostgreSQL local.
  - Verificar que el contenedor se levanta y destruye correctamente.
  - Confirmar que tests son aislados (sin datos residuales).

---

#### 11. Dockerfile y docker-compose

**Descripción**: Containerizar la aplicación para facilitar despliegue y desarrollo.

**Importancia**: Elimina la necesidad de instalar Python, dependencias y PostgreSQL manualmente. Un `docker-compose up` levanta todo el stack. Útil para CI, desarrollo y producción.

**Pasos para completar**:

- **Planificación**:
  - Dockerfile multi-stage: builder (instala deps) + runtime (imagen mínima).
  - docker-compose: servicio `bot` (main.py), servicio `agent` (agent.py), servicio `postgres`.
  - Variables de entorno vía `.env` o `env_file` en compose.

- **Ejecución**:
  1. Crear `Dockerfile` con Python 3.10-slim como base.
  2. Multi-stage: instalar deps en builder, copiar solo lo necesario al runtime.
  3. Crear `docker-compose.yml` con tres servicios.
  4. Crear `docker-compose.dev.yml` con volúmenes para desarrollo.
  5. Documentar uso en README.

- **Pruebas**:
  - `docker-compose up` debe levantar bot + agent + postgres.
  - Verificar que el bot responde comandos.
  - Verificar que el agente inserta datos.

---

#### 12. Type Hints Completos

**Descripción**: Agregar tipos de retorno y parámetros a todas las funciones públicas.

**Importancia**: Mejora el soporte de IDE (autocompletado, detección de errores), sirve como documentación inline, y permite usar `mypy` para verificación estática de tipos.

**Pasos para completar**:

- **Planificación**:
  - Empezar por módulos estables: `config.py`, `collector/system.py`, `bot/formatter.py`.
  - Usar `Optional`, `dict[str, Any]` donde aplique.
  - No buscar strict mode desde el inicio — ser gradual.

- **Ejecución**:
  1. Configurar `mypy` en `pyproject.toml` con `check_untyped_defs = True`.
  2. Agregar tipos a `config.py` (variables de módulo).
  3. Agregar tipos a `collector/system.py` (retorno de funciones).
  4. Agregar tipos a `database/repository.py` (parámetros y retornos).
  5. Agregar tipos a `bot/formatter.py` y `bot/handlers.py`.
  6. Ejecutar `mypy .` y corregir errores.

- **Pruebas**:
  - `mypy .` debe pasar sin errores.
  - Tests deben seguir pasando.
  - Verificar en IDE que el autocompletado mejora.

---

## 4. ✅ Conclusión

### Estado General

GPU-Telemetria es un proyecto **funcional y bien estructurado** que ya resuelve su problema principal: monitoreo multi-PC con alertas por Telegram. La arquitectura es limpia, la suite de tests es sólida (84 tests), y la documentación es completa.

Las mejoras identificadas son de **ingeniería y madurez del proyecto**, no de funcionalidad básica. El sistema funciona correctamente en su estado actual.

### Próximos Pasos Recomendados

| Orden | Mejora | Esfuerzo estimado |
|---|---|---|
| 1 | CI/CD con GitHub Actions | 1-2 horas |
| 2 | Versiones de dependencias | 30 min |
| 3 | Validación de configuración | 1 hora |
| 4 | Sistema de logging | 1-2 horas |
| 5 | Linters y formatters (ruff + mypy) | 2-3 horas (incluye correcciones) |
| 6 | Lock file de dependencias | 30 min |
| 7 | Manejo de señales en agent.py | 1 hora |
| 8 | Pool de conexiones a BD | 2-3 horas |
| 9 | Type hints completos | 3-4 horas (gradual) |
| 10 | Refactor de gpu_amd.py | 2-3 horas |
| 11 | Tests con testcontainers | 2-3 horas |
| 12 | Dockerfile y docker-compose | 3-4 horas |

**Total estimado**: ~20-30 horas de trabajo distribuidas en mejoras incrementales.

### Recomendación

Empezar por **CI/CD + versiones de dependencias + validación de configuración**. Esas tres mejoras juntas establecen una base de calidad sobre la cual las demás mejoras se pueden implementar con mayor confianza y menor riesgo de regressión.
