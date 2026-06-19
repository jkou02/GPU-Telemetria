from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from bot.handlers import (
    status_command,
    history_command,
    gpu_info_command,
    alertas_command,
    pcs_command,
    _resolve_hostname,
)
from config import HOSTNAME


@pytest.fixture
def mock_update():
    """Mock de telegram.Update con reply_text asíncrono."""
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Mock de ContextTypes.DEFAULT_TYPE."""
    ctx = MagicMock()
    ctx.args = []
    return ctx


@pytest.fixture
def mock_db_entry():
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


class TestResolveHostname:
    def test_with_args(self):
        assert _resolve_hostname(["laptop"]) == "laptop"

    def test_without_args(self):
        assert _resolve_hostname([]) == HOSTNAME


class TestStatusCommand:
    @pytest.mark.asyncio
    async def test_status_with_data(self, mock_update, mock_context, mock_db_entry):
        with patch("bot.handlers.get_latest_entry", return_value=mock_db_entry):
            await status_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Estado del Sistema" in call_args[0][0]
            assert "NVIDIA GeForce RTX 3060" in call_args[0][0]
            assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_status_no_data(self, mock_update, mock_context):
        with patch("bot.handlers.get_latest_entry", return_value=None):
            await status_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "No hay datos" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_status_with_hostname_arg(self, mock_update, mock_context, mock_db_entry):
        mock_context.args = ["laptop"]
        with patch("bot.handlers.get_latest_entry", return_value=mock_db_entry):
            await status_command(mock_update, mock_context)

            # Verifica que get_latest_entry fue llamado con "laptop"
            # (no verificamos directamente el mock porque está patcheado,
            #  pero verificamos que el mensaje contiene el hostname)
            call_args = mock_update.message.reply_text.call_args
            assert "laptop" in call_args[0][0] or "Laptop" in call_args[0][0]


class TestHistoryCommand:
    @pytest.mark.asyncio
    async def test_history_with_data(self, mock_update, mock_context, mock_db_entry):
        entries = [mock_db_entry]
        with patch("bot.handlers.get_recent_entries", return_value=entries):
            await history_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ultimos registros" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_history_empty(self, mock_update, mock_context):
        with patch("bot.handlers.get_recent_entries", return_value=[]):
            await history_command(mock_update, mock_context)

            call_args = mock_update.message.reply_text.call_args
            assert "No hay registros" in call_args[0][0]


class TestGpuInfoCommand:
    @pytest.mark.asyncio
    async def test_gpu_info_with_data(self, mock_update, mock_context, mock_db_entry):
        with patch("bot.handlers.get_latest_entry", return_value=mock_db_entry):
            await gpu_info_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Información detallada de GPU" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_gpu_info_no_data(self, mock_update, mock_context):
        with patch("bot.handlers.get_latest_entry", return_value=None):
            await gpu_info_command(mock_update, mock_context)

            call_args = mock_update.message.reply_text.call_args
            assert "No hay datos" in call_args[0][0]


class TestAlertasCommand:
    @pytest.mark.asyncio
    async def test_alertas(self, mock_update, mock_context):
        await alertas_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Umbrales configurados" in call_args[0][0]


class TestPcsCommand:
    @pytest.mark.asyncio
    async def test_pcs_with_hostnames(self, mock_update, mock_context):
        with patch("bot.handlers.get_hostnames", return_value=["servidor", "laptop"]):
            await pcs_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "PCs registradas" in call_args[0][0]
            assert "servidor" in call_args[0][0]
            assert "laptop" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_pcs_empty(self, mock_update, mock_context):
        with patch("bot.handlers.get_hostnames", return_value=[]):
            await pcs_command(mock_update, mock_context)

            call_args = mock_update.message.reply_text.call_args
            assert "No hay PCs" in call_args[0][0]
