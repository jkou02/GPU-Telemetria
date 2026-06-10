import os
import glob
import subprocess
import re
from typing import Optional


class IntelGPU:
    """Backend para GPUs Intel usando sysfs o intel_gpu_top como fallback."""

    def __init__(self):
        self._available = False
        self._card_path = None

    def is_available(self) -> bool:
        # Buscar tarjetas Intel en /sys/class/drm/
        cards = glob.glob("/sys/class/drm/card[0-9]*/device/vendor")
        for vendor_path in cards:
            try:
                with open(vendor_path, "r") as f:
                    vendor = f.read().strip()
                    # Intel vendor ID: 0x8086
                    if vendor == "0x8086":
                        card_dir = os.path.dirname(vendor_path)
                        # Verificar que tenga archivos de frecuencia del GPU
                        if os.path.exists(os.path.join(card_dir, "gt_cur_freq_mhz")):
                            self._card_path = card_dir
                            self._available = True
                            return True
            except (IOError, OSError):
                continue

        # Fallback: intel_gpu_top
        if self._check_intel_gpu_top():
            self._available = True
            return True

        return False

    def _check_intel_gpu_top(self) -> bool:
        """Verifica si intel_gpu_top está disponible."""
        try:
            result = subprocess.run(
                ["intel_gpu_top", "-J", "-s", "1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # intel_gpu_top retorna 0 si funciona
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _read_sysfs(self, filename: str) -> Optional[str]:
        """Lee un archivo de sysfs."""
        if not self._card_path:
            return None
        filepath = os.path.join(self._card_path, filename)
        try:
            with open(filepath, "r") as f:
                return f.read().strip()
        except (IOError, OSError):
            return None

    def _get_stats_sysfs(self) -> Optional[dict]:
        """Obtiene métricas de sysfs (i915)."""
        try:
            # Nombre del GPU
            name = "Intel GPU"
            name_file = self._read_sysfs("gt_name")
            if name_file:
                name = f"Intel {name_file}"

            # Frecuencia actual (MHz) - usar como proxy de utilization
            cur_freq = self._read_sysfs("gt_cur_freq_mhz")
            max_freq = self._read_sysfs("gt_max_freq_mhz")
            gpu_util = 0.0
            if cur_freq and max_freq:
                try:
                    cur = int(cur_freq)
                    mx = int(max_freq)
                    if mx > 0:
                        gpu_util = (cur / mx) * 100
                except ValueError:
                    pass

            # VRAM: intel GPUs comparten RAM del sistema
            # Usar /proc/meminfo como referencia
            mem_total = 0
            mem_used = 0
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_total = int(line.split()[1]) * 1024  # kB a bytes
                        elif line.startswith("MemAvailable:"):
                            mem_available = int(line.split()[1]) * 1024
                            mem_used = mem_total - mem_available
            except (IOError, OSError):
                pass

            # Temperatura: buscar en hwmon
            temp = 0.0
            hwmon_dirs = glob.glob(
                os.path.join(self._card_path, "hwmon/hwmon*/temp1_input")
            )
            for temp_path in hwmon_dirs:
                try:
                    with open(temp_path, "r") as f:
                        temp_raw = int(f.read().strip())
                        temp = temp_raw / 1000.0  # miligrados a grados
                        break
                except (IOError, OSError, ValueError):
                    continue

            return {
                "name": name,
                "temperature": temp,
                "memory_total": mem_total,
                "memory_used": mem_used,
                "memory_percent": (mem_used / mem_total) * 100 if mem_total > 0 else 0,
                "gpu_util": gpu_util,
            }
        except Exception:
            return None

    def _get_stats_intel_gpu_top(self) -> Optional[dict]:
        """Obtiene métricas parseando intel_gpu_top."""
        try:
            result = subprocess.run(
                ["intel_gpu_top", "-J", "-s", "1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None

            # intel_gpu_top produce JSON, parsearlo
            import json

            # Leer solo la primera línea JSON válida
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        data = json.loads(line)
                        return {
                            "name": "Intel GPU",
                            "temperature": 0.0,  # intel_gpu_top no provee temp
                            "memory_total": 0,
                            "memory_used": 0,
                            "memory_percent": 0.0,
                            "gpu_util": data.get("engines", {}).get("rcs0", 0.0),
                        }
                    except json.JSONDecodeError:
                        continue
            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def get_gpu_stats(self) -> Optional[dict]:
        if not self._available:
            if not self.is_available():
                return None

        if self._card_path:
            return self._get_stats_sysfs()
        return self._get_stats_intel_gpu_top()
