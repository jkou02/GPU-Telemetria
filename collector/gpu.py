import pynvml


def get_gpu_stats():
    try:
        pynvml.nvmlInit()
    except pynvml.NVMLError:
        return None

    device_count = pynvml.nvmlDeviceGetCount()
    if device_count == 0:
        return None

    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    name = pynvml.nvmlDeviceGetName(handle)
    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
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
