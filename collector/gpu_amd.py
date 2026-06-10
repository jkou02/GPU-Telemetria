import os
import glob
import subprocess
import re
from typing import Optional


class AMDGPU:
    """Backend para GPUs AMD usando sysfs (amdgpu), pyrsmi o rocm-smi."""

    AMD_VENDOR_ID = "0x1002"

    def __init__(self):
        self._available = False
        self._card_path = None
        self._method = None  # "sysfs", "pyrsmi", "rocm_smi"

    def is_available(self) -> bool:
        if self._available:
            return True

        # 1. Intentar sysfs (siempre disponible con driver amdgpu)
        if self._detect_sysfs():
            self._method = "sysfs"
            self._available = True
            return True

        # 2. Intentar pyrsmi
        if self._detect_pyrsmi():
            self._method = "pyrsmi"
            self._available = True
            return True

        # 3. Intentar rocm-smi
        if self._detect_rocm_smi():
            self._method = "rocm_smi"
            self._available = True
            return True

        return False

    def _detect_sysfs(self) -> bool:
        """Detecta GPU AMD via sysfs (driver amdgpu del kernel)."""
        cards = glob.glob("/sys/class/drm/card[0-9]*/device/vendor")
        for vendor_path in cards:
            try:
                with open(vendor_path, "r") as f:
                    vendor = f.read().strip()
                    if vendor == self.AMD_VENDOR_ID:
                        card_dir = os.path.dirname(vendor_path)
                        busy_path = os.path.join(card_dir, "gpu_busy_percent")
                        if os.path.exists(busy_path):
                            self._card_path = card_dir
                            return True
            except (IOError, OSError):
                continue
        return False

    def _detect_pyrsmi(self) -> bool:
        """Detecta si pyrsmi está disponible."""
        try:
            from pyrsmi import gpuvm

            gpuvm.smi_initialize()
            count = gpuvm.smi_get_device_count()
            return count > 0
        except Exception:
            return False

    def _detect_rocm_smi(self) -> bool:
        """Detecta si rocm-smi está disponible."""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showid"],
                capture_output=True,
                text=True,
                timeout=5,
            )
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
        """Obtiene métricas via sysfs (driver amdgpu)."""
        try:
            # Nombre del GPU
            name = "AMD GPU"
            # Intentar obtener nombre del card
            card_name = self._read_sysfs("product_name")
            if card_name:
                name = f"AMD {card_name}"
            else:
                # Intentar desde lspcm
                try:
                    import subprocess as sp

                    result = sp.run(
                        ["lspci", "-v", "-s", self._get_pci_slot()],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    for line in result.stdout.splitlines():
                        if "VGA" in line or "Display" in line:
                            # Extraer nombre después de ": "
                            parts = line.split(": ", 1)
                            if len(parts) > 1:
                                name = f"AMD {parts[1].split(' (')[0]}"
                                break
                except Exception:
                    pass

            # Utilización GPU (%)
            gpu_util = 0.0
            busy = self._read_sysfs("gpu_busy_percent")
            if busy:
                try:
                    gpu_util = float(busy)
                except ValueError:
                    pass

            # VRAM total y usada (bytes)
            vram_total = 0
            vram_used = 0
            total_str = self._read_sysfs("mem_info_vram_total")
            used_str = self._read_sysfs("mem_info_vram_used")
            if total_str:
                try:
                    vram_total = int(total_str)
                except ValueError:
                    pass
            if used_str:
                try:
                    vram_used = int(used_str)
                except ValueError:
                    pass

            # Temperatura (hwmon)
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
                "memory_total": vram_total,
                "memory_used": vram_used,
                "memory_percent": (vram_used / vram_total) * 100
                if vram_total > 0
                else 0,
                "gpu_util": gpu_util,
            }
        except Exception:
            return None

    def _get_pci_slot(self) -> str:
        """Obtiene el slot PCI de la GPU."""
        if not self._card_path:
            return ""
        try:
            # El symlink device apunta al PCI slot
            device_path = os.path.join(self._card_path, "device")
            real_path = os.path.realpath(device_path)
            # Extraer: 0000:07:00.0
            return os.path.basename(real_path)
        except Exception:
            return ""

    def _get_stats_pyrsmi(self) -> Optional[dict]:
        """Obtiene métricas usando pyrsmi."""
        try:
            from pyrsmi import gpuvm

            gpu_id = 0
            name = gpuvm.smi_get_device_name(gpu_id)
            temp = gpuvm.smi_get_temp(gpu_id)
            vram_total = gpuvm.smi_get_mem_region_total(gpu_id, "vram")
            vram_used = gpuvm.smi_get_mem_region_used(gpu_id, "vram")
            gpu_util = gpuvm.smi_get_gpu_use(gpu_id)

            return {
                "name": name,
                "temperature": temp,
                "memory_total": vram_total,
                "memory_used": vram_used,
                "memory_percent": (vram_used / vram_total) * 100
                if vram_total > 0
                else 0,
                "gpu_util": gpu_util,
            }
        except Exception:
            return None

    def _get_stats_rocm_smi(self) -> Optional[dict]:
        """Obtiene métricas parseando rocm-smi."""
        try:
            # Obtener nombre
            name_result = subprocess.run(
                ["rocm-smi", "--showproductname"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            name = "AMD GPU"
            for line in name_result.stdout.splitlines():
                if "Card" in line or "GPU" in line:
                    name = line.split(":")[-1].strip()
                    break

            # Obtener temperatura
            temp_result = subprocess.run(
                ["rocm-smi", "-t"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            temp = 0.0
            for line in temp_result.stdout.splitlines():
                match = re.search(r"(\d+\.?\d*)\s*c", line.lower())
                if match:
                    temp = float(match.group(1))
                    break

            # Obtener uso de VRAM
            mem_result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            vram_total = 0
            vram_used = 0
            for line in mem_result.stdout.splitlines():
                if "Total Memory" in line or "total" in line.lower():
                    match = re.search(r"(\d+)", line)
                    if match:
                        vram_total = int(match.group(1))
                elif "Used Memory" in line or "used" in line.lower():
                    match = re.search(r"(\d+)", line)
                    if match:
                        vram_used = int(match.group(1))

            # Obtener uso de GPU
            util_result = subprocess.run(
                ["rocm-smi", "-u"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            gpu_util = 0.0
            for line in util_result.stdout.splitlines():
                match = re.search(r"(\d+\.?\d*)\s*%", line)
                if match:
                    gpu_util = float(match.group(1))
                    break

            return {
                "name": name,
                "temperature": temp,
                "memory_total": vram_total,
                "memory_used": vram_used,
                "memory_percent": (vram_used / vram_total) * 100
                if vram_total > 0
                else 0,
                "gpu_util": gpu_util,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def get_gpu_stats(self) -> Optional[dict]:
        if not self._available:
            if not self.is_available():
                return None

        if self._method == "sysfs":
            return self._get_stats_sysfs()
        elif self._method == "pyrsmi":
            return self._get_stats_pyrsmi()
        elif self._method == "rocm_smi":
            return self._get_stats_rocm_smi()
        return None
