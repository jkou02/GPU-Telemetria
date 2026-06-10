from typing import Optional

try:
    import pynvml

    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False


class NvidiaGPU:
    """Backend para GPUs NVIDIA usando pynvml."""

    def __init__(self):
        self._initialized = False

    def is_available(self) -> bool:
        if not PYNVML_AVAILABLE:
            return False
        try:
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            self._initialized = True
            return count > 0
        except pynvml.NVMLError:
            return False

    def get_gpu_stats(self) -> Optional[dict]:
        if not self._initialized:
            if not self.is_available():
                return None

        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)

            return {
                "name": name,
                "temperature": temp,
                "memory_total": mem_info.total,
                "memory_used": mem_info.used,
                "memory_percent": (mem_info.used / mem_info.total) * 100,
                "gpu_util": util.gpu,
            }
        except pynvml.NVMLError:
            return None
