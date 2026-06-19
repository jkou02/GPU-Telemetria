from bot.formatter import (
    format_status,
    format_history,
    format_alertas,
    format_gpu_info,
    format_pc_list,
    _fmt_bytes,
    _fmt_uptime,
)


class TestFmtBytes:
    def test_bytes(self):
        assert _fmt_bytes(0) == "0.0 B"
        assert _fmt_bytes(512) == "512.0 B"
        assert _fmt_bytes(1023) == "1023.0 B"

    def test_kilobytes(self):
        assert "1.0 KB" in _fmt_bytes(1024)

    def test_megabytes(self):
        result = _fmt_bytes(1024 * 1024)
        assert "1.0 MB" in result

    def test_gigabytes(self):
        result = _fmt_bytes(1024 * 1024 * 1024)
        assert "1.0 GB" in result

    def test_terabytes(self):
        result = _fmt_bytes(1024 * 1024 * 1024 * 1024)
        assert "1.0 TB" in result

    def test_none(self):
        assert _fmt_bytes(None) == "N/A"


class TestFmtUptime:
    def test_minutes_only(self):
        assert _fmt_uptime(120) == "0h 2m"

    def test_hours_and_minutes(self):
        assert _fmt_uptime(3661) == "1h 1m"

    def test_days(self):
        assert _fmt_uptime(90061) == "1d 1h 1m"

    def test_none(self):
        assert _fmt_uptime(None) == "N/A"


class TestFormatStatus:
    def test_with_gpu_and_hostname(self, sample_system, sample_gpu):
        msg = format_status(sample_system, sample_gpu, hostname="servidor")
        assert "Estado del Sistema — servidor" in msg
        assert "CPU" in msg
        assert "45.5 C" in msg
        assert "50.0%" in msg
        assert "NVIDIA GeForce RTX 3060" in msg
        assert "65.0 C" in msg
        assert "33.3%" in msg
        assert "45.0%" in msg
        assert "Uptime:" in msg
        assert "1h 1m" in msg

    def test_without_hostname(self, sample_system, sample_gpu):
        msg = format_status(sample_system, sample_gpu)
        assert "Estado del Sistema" in msg
        assert "servidor" not in msg  # sin hostname no debe aparecer

    def test_without_gpu(self, sample_system):
        msg = format_status(sample_system, None)
        assert "No detectada" in msg

    def test_cpu_temp_none(self, sample_system):
        sample_system["cpu_temp"] = None
        msg = format_status(sample_system, None)
        assert "N/A" in msg

    def test_uptime_none(self, sample_system):
        sample_system["uptime_seconds"] = None
        msg = format_status(sample_system, None)
        assert "N/A" in msg.split("*Uptime:*")[1]


class TestFormatHistory:
    def test_with_entries(self, sample_entries):
        msg = format_history(sample_entries)
        assert "Ultimos registros" in msg
        assert "servidor" in msg
        assert "CPU 46C" in msg or "CPU 45C" in msg
        assert "GPU 65.0C" in msg

    def test_with_entries_and_hostname(self, sample_entries):
        msg = format_history(sample_entries, hostname="servidor")
        assert "Ultimos registros" in msg

    def test_empty(self):
        msg = format_history([])
        assert "No hay registros" in msg

    def test_empty_with_hostname(self):
        msg = format_history([], hostname="laptop")
        assert "No hay registros para 'laptop'" in msg

    def test_null_values(self, sample_entries):
        msg = format_history(sample_entries)
        # El tercer registro tiene valores None
        assert "Ultimos registros" in msg


class TestFormatAlertas:
    def test_format(self):
        msg = format_alertas()
        assert "Umbrales configurados" in msg
        assert "CPU temp" in msg
        assert "GPU temp" in msg
        assert "RAM" in msg
        assert "VRAM" in msg


class TestFormatGpuInfo:
    def test_with_gpu_and_hostname(self, sample_gpu):
        msg = format_gpu_info(sample_gpu, hostname="servidor")
        assert "Información detallada de GPU — servidor" in msg
        assert "NVIDIA GeForce RTX 3060" in msg
        assert "65.0 C" in msg
        assert "33.3%" in msg
        assert "45.0%" in msg
        assert "Umbrales de alerta" in msg

    def test_without_hostname(self, sample_gpu):
        msg = format_gpu_info(sample_gpu)
        assert "Información detallada de GPU" in msg
        assert "servidor" not in msg

    def test_without_gpu(self):
        msg = format_gpu_info(None, hostname="laptop")
        assert "Información detallada de GPU — laptop" in msg
        assert "No se detectó GPU activa" in msg

    def test_temperature_icons(self, sample_gpu):
        sample_gpu["temperature"] = 85.0
        msg = format_gpu_info(sample_gpu)
        assert "🔴" in msg

        sample_gpu["temperature"] = 65.0
        msg = format_gpu_info(sample_gpu)
        assert "🟡" in msg

        sample_gpu["temperature"] = 35.0
        msg = format_gpu_info(sample_gpu)
        assert "🟢" in msg


class TestFormatPcList:
    def test_with_hostnames(self):
        msg = format_pc_list(["servidor", "laptop", "pc-juegos"])
        assert "PCs registradas" in msg
        assert "servidor" in msg
        assert "laptop" in msg
        assert "pc-juegos" in msg
        assert "/status" in msg

    def test_empty(self):
        msg = format_pc_list([])
        assert "No hay PCs registradas" in msg
