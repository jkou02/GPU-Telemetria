import sys
import os
from unittest.mock import MagicMock, AsyncMock

import pytest

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_system():
    return {
        "cpu_temp": 45.5,
        "ram": {
            "total": 17179869184,  # 16 GB
            "used": 8589934592,    # 8 GB
            "percent": 50.0,
        },
        "uptime_seconds": 3661.0,  # 1h 1m 1s
    }


@pytest.fixture
def sample_gpu():
    return {
        "name": "NVIDIA GeForce RTX 3060",
        "temperature": 65.0,
        "memory_total": 12884901888,  # 12 GB
        "memory_used": 4294967296,    # 4 GB
        "memory_percent": 33.3,
        "gpu_util": 45.0,
    }


@pytest.fixture
def sample_row():
    return {
        "id": 1,
        "hostname": "servidor",
        "timestamp": "2026-06-19 06:00:00+00",
        "cpu_temp": 45.5,
        "ram_total": 17179869184,
        "ram_used": 8589934592,
        "ram_percent": 50.0,
        "gpu_name": "NVIDIA GeForce RTX 3060",
        "gpu_temp": 65.0,
        "vram_total": 12884901888,
        "vram_used": 4294967296,
        "vram_percent": 33.3,
        "gpu_util": 45.0,
        "uptime_seconds": 3661,
    }


@pytest.fixture
def sample_row_no_gpu():
    return {
        "id": 2,
        "hostname": "laptop",
        "timestamp": "2026-06-18 22:00:00+00",
        "cpu_temp": 55.0,
        "ram_total": 8589934592,
        "ram_used": 6442450944,
        "ram_percent": 75.0,
        "gpu_name": None,
        "gpu_temp": None,
        "vram_total": None,
        "vram_used": None,
        "vram_percent": None,
        "gpu_util": None,
        "uptime_seconds": None,
    }


@pytest.fixture
def sample_entries(sample_row):
    return [
        sample_row,
        {
            **sample_row,
            "id": 2,
            "timestamp": "2026-06-19 05:55:00+00",
            "cpu_temp": 50.0,
            "ram_percent": 60.0,
            "gpu_temp": 70.0,
            "vram_percent": 40.0,
        },
        {
            **sample_row,
            "id": 3,
            "timestamp": "2026-06-19 05:50:00+00",
            "cpu_temp": None,
            "ram_percent": None,
            "gpu_temp": None,
            "vram_percent": None,
        },
    ]


@pytest.fixture
def mock_bot_context():
    """Mock del context de Telegram con send_message asíncrono."""
    ctx = MagicMock()
    ctx.bot.send_message = AsyncMock()
    return ctx
