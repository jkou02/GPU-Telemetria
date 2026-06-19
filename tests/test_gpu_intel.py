from unittest.mock import patch, mock_open
import os

from collector.gpu_intel import IntelGPU


class TestIntelGPU:
    def test_is_available_sysfs(self):
        vendor_content = "0x8086\n"

        def mock_open_side_effect(path, mode="r"):
            if "vendor" in str(path):
                return mock_open(read_data=vendor_content).return_value
            raise FileNotFoundError

        def mock_exists(path):
            if "gt_cur_freq_mhz" in str(path):
                return True
            return False

        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch("collector.gpu_intel.glob.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: (
                    ["/sys/class/drm/card0/device/vendor"]
                    if "vendor" in pattern
                    else []
                )
                with patch.object(os.path, "exists", side_effect=mock_exists):
                    with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=False):
                        gpu = IntelGPU()
                        assert gpu.is_available() is True
                        assert gpu._card_path is not None

    def test_is_available_no_intel_vendor(self):
        vendor_content = "0x10de\n"

        with patch("builtins.open", mock_open(read_data=vendor_content)):
            with patch("collector.gpu_intel.glob.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: (
                    ["/sys/class/drm/card0/device/vendor"]
                    if "vendor" in pattern
                    else []
                )
                with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=False):
                    gpu = IntelGPU()
                    assert gpu.is_available() is False

    def test_is_available_no_cards(self):
        with patch("collector.gpu_intel.glob.glob", return_value=[]):
            with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=False):
                gpu = IntelGPU()
                assert gpu.is_available() is False

    def test_is_available_fallback_intel_gpu_top(self):
        vendor_content = "0x8086\n"

        with patch("builtins.open", mock_open(read_data=vendor_content)):
            with patch("collector.gpu_intel.glob.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: (
                    ["/sys/class/drm/card0/device/vendor"]
                    if "vendor" in pattern
                    else []
                )
                with patch.object(os.path, "exists", return_value=False):
                    with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=True):
                        gpu = IntelGPU()
                        assert gpu.is_available() is True

    def test_get_stats_not_available(self):
        with patch("collector.gpu_intel.glob.glob", return_value=[]):
            with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=False):
                gpu = IntelGPU()
                stats = gpu.get_gpu_stats()
                assert stats is None

    def test_get_stats_sysfs_format(self):
        vendor_content = "0x8086\n"

        mock_files = {
            "/sys/class/drm/card0/device/gt_cur_freq_mhz": "300\n",
            "/sys/class/drm/card0/device/gt_max_freq_mhz": "1000\n",
            "/sys/class/drm/card0/device/gt_name": "AlderLake-S GT1\n",
            "/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input": "42000\n",
        }

        def mock_open_side_effect(path, mode="r"):
            path_str = str(path)
            if "vendor" in path_str:
                return mock_open(read_data=vendor_content).return_value
            if "meminfo" in path_str:
                return mock_open(
                    read_data="MemTotal: 16384000 kB\nMemAvailable: 8192000 kB\n"
                ).return_value
            for mock_path, content in mock_files.items():
                if path_str == mock_path:
                    return mock_open(read_data=content).return_value
            raise FileNotFoundError

        def mock_glob_side_effect(pattern):
            if "vendor" in pattern:
                return ["/sys/class/drm/card0/device/vendor"]
            if "hwmon" in pattern:
                return ["/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input"]
            return []

        def mock_exists(path):
            if "gt_cur_freq_mhz" in str(path):
                return True
            return False

        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch("collector.gpu_intel.glob.glob") as mock_glob:
                mock_glob.side_effect = mock_glob_side_effect
                with patch.object(os.path, "exists", side_effect=mock_exists):
                    with patch.object(IntelGPU, "_check_intel_gpu_top", return_value=False):
                        gpu = IntelGPU()
                        stats = gpu.get_gpu_stats()

                        assert stats is not None
                        assert "Intel" in stats["name"]
                        assert stats["temperature"] == 42.0
                        assert stats["gpu_util"] == 30.0
                        assert stats["memory_percent"] >= 0
