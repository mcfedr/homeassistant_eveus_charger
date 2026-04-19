"""Tests for coordinator.py — data fetching and error handling."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from tests.conftest import SAMPLE_MAIN_DATA, SAMPLE_INIT_DATA


class FakeResponse:
    """Fake aiohttp response for testing."""
    def __init__(self, json_data=None, status=200, content_type="application/json"):
        self._json_data = json_data
        self.status = status
        self.headers = {"Content-Type": content_type}

    async def json(self):
        return self._json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.post = MagicMock()
    return session


@pytest.fixture
def coordinator(mock_config_entry):
    from custom_components.eveus_chargers.coordinator import EveusCoordinator
    coord = object.__new__(EveusCoordinator)
    coord.hass = MagicMock()
    coord.host = "10.2.0.135"
    coord.config_entry = mock_config_entry
    coord.device_name = "Eveus Pro"
    coord.device_name_slug = "eveus_pro"
    coord._mac = None
    coord.data = {}
    coord.logger = MagicMock()
    return coord


class TestAsyncUpdateData:
    @patch("custom_components.eveus_chargers.coordinator.async_get_clientsession")
    async def test_happy_path_merges_data(self, mock_get_session, coordinator, mock_session):
        mock_get_session.return_value = mock_session
        mock_session.post.side_effect = [
            FakeResponse(json_data=SAMPLE_INIT_DATA),
            FakeResponse(json_data=SAMPLE_MAIN_DATA),
        ]
        result = await coordinator._async_update_data()
        assert result["state"] == 1
        assert result["ESP_MAC"] == "C8:F0:9E:CB:02:D0"
        assert result["currentSet"] == 16

    @patch("custom_components.eveus_chargers.coordinator.async_get_clientsession")
    async def test_mac_extracted_from_init(self, mock_get_session, coordinator, mock_session):
        mock_get_session.return_value = mock_session
        mock_session.post.side_effect = [
            FakeResponse(json_data={"ESP_MAC": "AA:BB:CC:DD:EE:FF"}),
            FakeResponse(json_data={"state": 1}),
        ]
        await coordinator._async_update_data()
        assert coordinator._mac == "AA:BB:CC:DD:EE:FF"

    @patch("custom_components.eveus_chargers.coordinator.async_get_clientsession")
    async def test_init_failure_still_returns_main(self, mock_get_session, coordinator, mock_session):
        mock_get_session.return_value = mock_session

        class FailInit:
            """Context manager that raises on /init, succeeds on /main."""
            def __init__(self, url, **kwargs):
                self._url = url
            async def __aenter__(self):
                if "/init" in self._url:
                    raise ConnectionError("init failed")
                return FakeResponse(json_data={"state": 1})
            async def __aexit__(self, *args):
                pass

        mock_session.post = FailInit
        result = await coordinator._async_update_data()
        assert result["state"] == 1

    @patch("custom_components.eveus_chargers.coordinator.async_get_clientsession")
    async def test_main_failure_raises_update_failed(self, mock_get_session, coordinator, mock_session):
        from custom_components.eveus_chargers.coordinator import UpdateFailed
        mock_get_session.return_value = mock_session

        class FailMain:
            """Context manager that succeeds on /init, raises on /main."""
            def __init__(self, url, **kwargs):
                self._url = url
            async def __aenter__(self):
                if "/main" in self._url:
                    raise ConnectionError("main failed")
                return FakeResponse(json_data={})
            async def __aexit__(self, *args):
                pass

        mock_session.post = FailMain
        with pytest.raises(UpdateFailed, match="Error fetching /main"):
            await coordinator._async_update_data()

    @patch("custom_components.eveus_chargers.coordinator.async_get_clientsession")
    async def test_main_non_json_raises_update_failed(self, mock_get_session, coordinator, mock_session):
        from custom_components.eveus_chargers.coordinator import UpdateFailed
        mock_get_session.return_value = mock_session
        mock_session.post.side_effect = [
            FakeResponse(json_data={}),
            FakeResponse(json_data=None, content_type="text/html"),
        ]
        with pytest.raises(UpdateFailed, match="non-JSON"):
            await coordinator._async_update_data()


class TestDeviceInfo:
    def test_uses_mac_when_available(self, coordinator):
        coordinator._mac = "AA:BB:CC:DD:EE:FF"
        coordinator.data = {"fwVersion": "249"}
        info = coordinator.device_info
        assert ("eveus_chargers", "AA:BB:CC:DD:EE:FF") in info["identifiers"]

    def test_falls_back_to_entry_id(self, coordinator):
        coordinator._mac = None
        coordinator.data = {}
        info = coordinator.device_info
        assert ("eveus_chargers", "test_entry_123") in info["identifiers"]
