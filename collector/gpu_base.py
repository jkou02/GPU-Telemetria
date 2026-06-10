from typing import Protocol, Optional


class GPUStats(Protocol):
    """Diccionario normalizado que todo backend de GPU debe retornar."""

    name: str
    temperature: float
    memory_total: int
    memory_used: int
    memory_percent: float
    gpu_util: float


class GPUBackend(Protocol):
    """Interfaz que todos los backends de GPU deben implementar."""

    def is_available(self) -> bool:
        """Retorna True si el backend puede acceder a la GPU."""
        ...

    def get_gpu_stats(self) -> Optional[dict]:
        """
        Retorna un diccionario con las métricas de la GPU:
        - name: str
        - temperature: float (°C)
        - memory_total: int (bytes)
        - memory_used: int (bytes)
        - memory_percent: float (%)
        - gpu_util: float (%)

        Retorna None si no hay GPU disponible o no se puede obtener datos.
        """
        ...
