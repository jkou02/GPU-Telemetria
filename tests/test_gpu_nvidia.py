from unittest.mock import patch, MagicMock
from collector.gpu_nvidia import NvidiaGPU


class FakeNVMLError(Exception):
    """Excepción falsa para simular NVMLError en tests."""
    pass


class TestNvidiaGPU:
    def test_is_available_with_gpu(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlDeviceGetCount.return_value = 1
                gpu = NvidiaGPU()
                assert gpu.is_available() is True
                mock_pynvml.nvmlInit.assert_called_once()

    def test_is_available_no_gpu(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlDeviceGetCount.return_value = 0
                gpu = NvidiaGPU()
                assert gpu.is_available() is False

    def test_is_available_pynvml_not_installed(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", False):
            gpu = NvidiaGPU()
            assert gpu.is_available() is False

    def test_is_available_nvml_error(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlInit.side_effect = FakeNVMLError
                gpu = NvidiaGPU()
                assert gpu.is_available() is False

    def test_get_gpu_stats_returns_dict(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlDeviceGetCount.return_value = 1
                mock_pynvml.nvmlDeviceGetName.return_value = "NVIDIA GeForce RTX 4090"
                mock_pynvml.nvmlDeviceGetTemperature.return_value = 65
                mock_mem = MagicMock()
                mock_mem.total = 25769803776
                mock_mem.used = 8589934592
                mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem
                mock_util = MagicMock()
                mock_util.gpu = 80
                mock_pynvml.nvmlDeviceGetUtilizationRates.return_value = mock_util
                mock_pynvml.NVML_TEMPERATURE_GPU = 0

                gpu = NvidiaGPU()
                stats = gpu.get_gpu_stats()

                assert stats is not None
                assert stats["name"] == "NVIDIA GeForce RTX 4090"
                assert stats["temperature"] == 65
                assert stats["memory_total"] == 25769803776
                assert stats["memory_used"] == 8589934592
                assert stats["gpu_util"] == 80
                assert 30 < stats["memory_percent"] < 35

    def test_get_gpu_stats_not_initialized_returns_none(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlDeviceGetCount.return_value = 0
                gpu = NvidiaGPU()
                stats = gpu.get_gpu_stats()
                assert stats is None

    def test_get_gpu_stats_error_returns_none(self):
        with patch("collector.gpu_nvidia.PYNVML_AVAILABLE", True):
            with patch("collector.gpu_nvidia.pynvml") as mock_pynvml:
                mock_pynvml.NVMLError = FakeNVMLError
                mock_pynvml.nvmlDeviceGetCount.return_value = 1
                mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = FakeNVMLError
                gpu = NvidiaGPU()
                stats = gpu.get_gpu_stats()
                assert stats is None
