from unittest.mock import patch, MagicMock, PropertyMock

from collector.system import get_system_stats, get_cpu_temperature, get_ram_usage, get_uptime_seconds


class TestCpuTemperature:
    def test_coretemp_detected(self):
        mock_sensor = MagicMock()
        mock_sensor.current = 45.5
        mock_temps = {"coretemp": [mock_sensor]}

        with patch("collector.system.psutil.sensors_temperatures", return_value=mock_temps):
            temp = get_cpu_temperature()
            assert temp == 45.5

    def test_k10temp_detected(self):
        mock_sensor = MagicMock()
        mock_sensor.current = 55.0
        mock_temps = {"k10temp": [mock_sensor]}

        with patch("collector.system.psutil.sensors_temperatures", return_value=mock_temps):
            temp = get_cpu_temperature()
            assert temp == 55.0

    def test_zenpower_detected(self):
        mock_sensor = MagicMock()
        mock_sensor.current = 60.0
        mock_temps = {"zenpmp": [mock_sensor]}

        with patch("collector.system.psutil.sensors_temperatures", return_value=mock_temps):
            temp = get_cpu_temperature()
            assert temp == 60.0

    def test_no_sensor(self):
        with patch("collector.system.psutil.sensors_temperatures", return_value={}):
            temp = get_cpu_temperature()
            assert temp is None

    def test_unknown_sensor_key(self):
        mock_sensor = MagicMock()
        mock_temps = {"unknown_key": [mock_sensor]}

        with patch("collector.system.psutil.sensors_temperatures", return_value=mock_temps):
            temp = get_cpu_temperature()
            assert temp is None


class TestRamUsage:
    def test_ram_usage(self):
        mock_mem = MagicMock()
        mock_mem.total = 17179869184
        mock_mem.available = 8589934592
        mock_mem.percent = 50.0
        mock_mem.used = 8589934592

        with patch("collector.system.psutil.virtual_memory", return_value=mock_mem):
            ram = get_ram_usage()
            assert ram["total"] == 17179869184
            assert ram["available"] == 8589934592
            assert ram["percent"] == 50.0
            assert ram["used"] == 8589934592


class TestUptime:
    def test_uptime_calculation(self):
        with patch("collector.system.time.time", return_value=10000.0):
            with patch("collector.system.psutil.boot_time", return_value=5000.0):
                uptime = get_uptime_seconds()
                assert uptime == 5000.0


class TestGetSystemStats:
    def test_get_system_stats(self):
        mock_sensor = MagicMock()
        mock_sensor.current = 45.5
        mock_temps = {"coretemp": [mock_sensor]}

        mock_mem = MagicMock()
        mock_mem.total = 17179869184
        mock_mem.available = 8589934592
        mock_mem.percent = 50.0
        mock_mem.used = 8589934592

        with patch("collector.system.psutil.sensors_temperatures", return_value=mock_temps):
            with patch("collector.system.psutil.virtual_memory", return_value=mock_mem):
                with patch("collector.system.time.time", return_value=10000.0):
                    with patch("collector.system.psutil.boot_time", return_value=5000.0):
                        stats = get_system_stats()

        assert stats["cpu_temp"] == 45.5
        assert stats["ram"]["total"] == 17179869184
        assert stats["ram"]["used"] == 8589934592
        assert stats["ram"]["percent"] == 50.0
        assert stats["uptime_seconds"] == 5000.0

    def test_no_cpu_sensor(self):
        mock_mem = MagicMock()
        mock_mem.total = 17179869184
        mock_mem.available = 8589934592
        mock_mem.percent = 50.0
        mock_mem.used = 8589934592

        with patch("collector.system.psutil.sensors_temperatures", return_value={}):
            with patch("collector.system.psutil.virtual_memory", return_value=mock_mem):
                with patch("collector.system.time.time", return_value=10000.0):
                    with patch("collector.system.psutil.boot_time", return_value=5000.0):
                        stats = get_system_stats()

        assert stats["cpu_temp"] is None
        assert stats["ram"]["total"] == 17179869184
