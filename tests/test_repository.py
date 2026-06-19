from database.repository import row_to_stats


class TestRowToStats:
    def test_full_row(self, sample_row):
        system, gpu = row_to_stats(sample_row)

        assert system is not None
        assert system["cpu_temp"] == 45.5
        assert system["ram"]["total"] == 17179869184
        assert system["ram"]["used"] == 8589934592
        assert system["ram"]["percent"] == 50.0
        assert system["uptime_seconds"] == 3661

        assert gpu is not None
        assert gpu["name"] == "NVIDIA GeForce RTX 3060"
        assert gpu["temperature"] == 65.0
        assert gpu["memory_total"] == 12884901888
        assert gpu["memory_used"] == 4294967296
        assert gpu["memory_percent"] == 33.3
        assert gpu["gpu_util"] == 45.0

    def test_none_row(self):
        system, gpu = row_to_stats(None)
        assert system is None
        assert gpu is None

    def test_row_without_gpu(self, sample_row_no_gpu):
        system, gpu = row_to_stats(sample_row_no_gpu)

        assert system is not None
        assert system["cpu_temp"] == 55.0
        assert system["ram"]["total"] == 8589934592
        assert system["uptime_seconds"] is None

        assert gpu is None

    def test_row_with_none_values(self):
        row = {
            "cpu_temp": None,
            "ram_total": None,
            "ram_used": None,
            "ram_percent": None,
            "gpu_name": "Some GPU",
            "gpu_temp": None,
            "vram_total": None,
            "vram_used": None,
            "vram_percent": None,
            "gpu_util": None,
        }
        system, gpu = row_to_stats(row)

        assert system["cpu_temp"] is None
        assert system["ram"]["total"] is None
        assert gpu is not None
        assert gpu["name"] == "Some GPU"
        assert gpu["temperature"] is None

    def test_missing_keys(self):
        """row_to_stats debe manejar filas que no tienen ciertas keys."""
        row = {"cpu_temp": 30.0}
        system, gpu = row_to_stats(row)

        assert system["cpu_temp"] == 30.0
        assert system["ram"]["total"] is None
        assert system["ram"]["used"] is None
        assert system["ram"]["percent"] is None
        assert gpu is None
