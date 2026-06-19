import pytest
from unittest.mock import patch, MagicMock

from bot.alerts import check_and_alert
from config import TELEGRAM_CHAT_ID


@pytest.fixture
def entry_below_thresholds():
    return {
        "cpu_temp": 45.0,
        "gpu_temp": 55.0,
        "ram_percent": 50.0,
        "vram_percent": 30.0,
    }


@pytest.fixture
def entry_above_all():
    return {
        "cpu_temp": 85.0,
        "gpu_temp": 90.0,
        "ram_percent": 95.0,
        "vram_percent": 95.0,
    }


@pytest.fixture
def entry_none_values():
    return {
        "cpu_temp": None,
        "gpu_temp": None,
        "ram_percent": None,
        "vram_percent": None,
    }


@pytest.mark.asyncio
async def test_no_hostnames(mock_bot_context):
    with patch("bot.alerts.get_hostnames", return_value=[]):
        await check_and_alert(mock_bot_context)
        mock_bot_context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_below_thresholds(mock_bot_context, entry_below_thresholds):
    with patch("bot.alerts.get_hostnames", return_value=["servidor"]):
        with patch("bot.alerts.get_latest_entry", return_value=entry_below_thresholds):
            await check_and_alert(mock_bot_context)
            mock_bot_context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_above_all_thresholds(mock_bot_context, entry_above_all):
    with patch("bot.alerts.get_hostnames", return_value=["servidor"]):
        with patch("bot.alerts.get_latest_entry", return_value=entry_above_all):
            await check_and_alert(mock_bot_context)

            mock_bot_context.bot.send_message.assert_called_once()
            call_args = mock_bot_context.bot.send_message.call_args
            assert call_args[1]["chat_id"] == TELEGRAM_CHAT_ID
            assert "ALERTA — servidor" in call_args[1]["text"]
            assert "CPU temp" in call_args[1]["text"]
            assert "GPU temp" in call_args[1]["text"]
            assert "RAM" in call_args[1]["text"]
            assert "VRAM" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_none_values_no_alert(mock_bot_context, entry_none_values):
    with patch("bot.alerts.get_hostnames", return_value=["servidor"]):
        with patch("bot.alerts.get_latest_entry", return_value=entry_none_values):
            await check_and_alert(mock_bot_context)
            mock_bot_context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_multiple_hostnames(mock_bot_context, entry_above_all, entry_below_thresholds):
    def mock_get_latest(hostname):
        if hostname == "servidor":
            return entry_above_all
        if hostname == "laptop":
            return entry_below_thresholds
        return None

    with patch("bot.alerts.get_hostnames", return_value=["laptop", "servidor"]):
        with patch("bot.alerts.get_latest_entry", side_effect=mock_get_latest):
            await check_and_alert(mock_bot_context)

            # Solo servidor debe disparar alerta
            mock_bot_context.bot.send_message.assert_called_once()
            assert "servidor" in mock_bot_context.bot.send_message.call_args[1]["text"]


@pytest.mark.asyncio
async def test_no_entry_for_hostname(mock_bot_context):
    with patch("bot.alerts.get_hostnames", return_value=["desconocido"]):
        with patch("bot.alerts.get_latest_entry", return_value=None):
            await check_and_alert(mock_bot_context)
            mock_bot_context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_only_cpu_triggered(mock_bot_context):
    entry = {
        "cpu_temp": 80.0,
        "gpu_temp": 50.0,
        "ram_percent": 50.0,
        "vram_percent": 30.0,
    }
    with patch("bot.alerts.get_hostnames", return_value=["servidor"]):
        with patch("bot.alerts.get_latest_entry", return_value=entry):
            await check_and_alert(mock_bot_context)

            mock_bot_context.bot.send_message.assert_called_once()
            text = mock_bot_context.bot.send_message.call_args[1]["text"]
            assert "CPU temp" in text
            assert "GPU temp" not in text
            assert "RAM" not in text
            assert "VRAM" not in text
