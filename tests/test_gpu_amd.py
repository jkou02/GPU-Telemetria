from unittest.mock import patch, mock_open, MagicMock
import os

from collector.gpu_amd import AMDGPU


class TestAMDGPUSysfs:
    def test_is_available_sysfs(self):
        """Detecta GPU AMD via sysfs con vendor ID correcto."""
        vendor_content = "0x1002\n"

        def mock_open_side_effect(path, mode="r"):
            if "vendor" in str(path):
                return mock_open(read_data=vendor_content).return_value
            raise FileNotFoundError

        def mock_exists(path):
            if "gpu_busy_percent" in str(path):
                return True
            return False

        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch("collector.gpu_amd.glob.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: (
                    ["/sys/class/drm/card0/device/vendor"]
                    if "vendor" in pattern
                    else []
                )
                with patch.object(os.path, "exists", side_effect=mock_exists):
                    with patch.object(AMDGPU, "_detect_pyrsmi", return_value=False):
                        with patch.object(AMDGPU, "_detect_rocm_smi", return_value=False):
                            gpu = AMDGPU()
                            assert gpu.is_available() is True
                            assert gpu._method == "sysfs"

    def test_is_available_no_amd_vendor(self):
        """No detecta GPU si vendor no es AMD."""
        vendor_content = "0x10de\n"

        with patch("builtins.open", mock_open(read_data=vendor_content)):
            with patch("collector.gpu_amd.glob.glob") as mock_glob:
                mock_glob.side_effect = lambda pattern: (
                    ["/sys/class/drm/card0/device/vendor"]
                    if "vendor" in pattern
                    else []
                )
                with patch.object(AMDGPU, "_detect_pyrsmi", return_value=False):
                    with patch.object(AMDGPU, "_detect_rocm_smi", return_value=False):
                        gpu = AMDGPU()
                        assert gpu.is_available() is False

    def test_is_available_no_cards_at_all(self):
        with patch("collector.gpu_amd.glob.glob", return_value=[]):
            with patch.object(AMDGPU, "_detect_pyrsmi", return_value=False):
                with patch.object(AMDGPU, "_detect_rocm_smi", return_value=False):
                    gpu = AMDGPU()
                    assert gpu.is_available() is False


class TestAMDGPUStats:
    def test_get_stats_not_available(self):
        with patch("collector.gpu_amd.glob.glob", return_value=[]):
            with patch.object(AMDGPU, "_detect_pyrsmi", return_value=False):
                with patch.object(AMDGPU, "_detect_rocm_smi", return_value=False):
                    gpu = AMDGPU()
                    stats = gpu.get_gpu_stats()
                    assert stats is None

    def test_get_stats_sysfs_format(self):
        vendor_content = "0x1002\n"

        mock_files = {
            "/sys/class/drm/card0/device/gpu_busy_percent": "75\n",
            "/sys/class/drm/card0/device/mem_info_vram_total": "8589934592\n",
            "/sys/class/drm/card0/device/mem_info_vram_used": "4294967296\n",
            "/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input": "45000\n",
        }

        def mock_open_side_effect(path, mode="r"):
            path_str = str(path)
            if "vendor" in path_str:
                return mock_open(read_data=vendor_content).return_value
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
            if "gpu_busy_percent" in str(path):
                return True
            return False

        with patch("builtins.open", side_effect=mock_open_side_effect):
            with patch("collector.gpu_amd.glob.glob") as mock_glob:
                mock_glob.side_effect = mock_glob_side_effect
                with patch.object(os.path, "exists", side_effect=mock_exists):
                    with patch.object(AMDGPU, "_detect_pyrsmi", return_value=False):
                        with patch.object(AMDGPU, "_detect_rocm_smi", return_value=False):
                            gpu = AMDGPU()
                            stats = gpu.get_gpu_stats()

                            assert stats is not None
                            assert "name" in stats
                            assert "AMD" in stats["name"]
                            assert stats["temperature"] == 45.0
                            assert stats["memory_total"] == 8589934592
                            assert stats["memory_used"] == 4294967296
                            assert 45 < stats["memory_percent"] < 55
                            assert stats["gpu_util"] == 75.0
