import os
from typing import Optional

from .gpu_nvidia import NvidiaGPU
from .gpu_amd import AMDGPU
from .gpu_intel import IntelGPU

# Mapeo de nombres de backend a clases
_BACKENDS = {
    "nvidia": NvidiaGPU,
    "amd": AMDGPU,
    "intel": IntelGPU,
}

# Instancia cache del backend detectado
_backend_instance = None
_backend_name = None


def _detect_backend():
    """Detecta el backend de GPU disponible."""
    global _backend_instance, _backend_name

    # Si se fuerza un backend desde config, usarlo
    forced = os.getenv("GPU_BACKEND", "").strip().lower()
    if forced and forced in _BACKENDS:
        instance = _BACKENDS[forced]()
        if instance.is_available():
            _backend_instance = instance
            _backend_name = forced
            return
        # Si el forzado no está disponible, continuar con auto-detección

    # Auto-detección: NVIDIA → AMD → Intel
    for name, cls in _BACKENDS.items():
        instance = cls()
        if instance.is_available():
            _backend_instance = instance
            _backend_name = name
            return

    _backend_instance = None
    _backend_name = None


def get_gpu_stats() -> Optional[dict]:
    """
    Retorna métricas de la GPU usando el backend disponible.

    Auto-detecta NVIDIA, AMD o Intel. Se puede forzar con la
    variable de entorno GPU_BACKEND=nvidia|amd|intel.

    Retorna None si no hay GPU disponible.
    """
    global _backend_instance, _backend_name

    if _backend_instance is None and _backend_name is None:
        _detect_backend()

    if _backend_instance is None:
        return None

    return _backend_instance.get_gpu_stats()


def get_gpu_backend_name() -> Optional[str]:
    """Retorna el nombre del backend detectado (nvidia, amd, intel) o None."""
    if _backend_name is None:
        _detect_backend()
    return _backend_name
