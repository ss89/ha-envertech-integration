"""Tests for the OpenEVT API module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.openevt.api import (
    check_supervisor_addon,
    fetch_inverter_status,
    parse_inverter_status,
)


class TestParseInverterStatus:
    """Tests for parse_inverter_status."""

    def test_parse_valid_data(self, mock_inverter_data):
        """Test parsing valid inverter data."""
        result = parse_inverter_status(mock_inverter_data)
        assert result is not None
        assert result["InverterId"] == "31583078"
        assert "Module1" in result
        assert "Module2" in result
        assert result["Module1"]["InputVoltageDC"] == 23.64

    def test_parse_none_input(self):
        """Test that None input returns None."""
        result = parse_inverter_status(None)
        assert result is None

    def test_parse_empty_dict(self):
        """Test that empty dict returns None."""
        result = parse_inverter_status({})
        assert result is None

    def test_parse_missing_inverter_id(self, mock_inverter_data_no_id):
        """Test that missing InverterId returns None."""
        result = parse_inverter_status(mock_inverter_data_no_id)
        assert result is None

    def test_parse_missing_modules(self):
        """Test that missing modules still works."""
        data = {"InverterId": "12345"}
        result = parse_inverter_status(data)
        assert result is not None
        assert result["InverterId"] == "12345"
        assert result["Module1"] == {}
        assert result["Module2"] == {}


class TestFetchInverterStatus:
    """Tests for fetch_inverter_status."""

    @pytest.mark.asyncio
    async def test_fetch_success(self, hass, mock_inverter_data):
        """Test successful fetch."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_inverter_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch(
            "custom_components.openevt.api.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await fetch_inverter_status(hass, "http://openevt:9090/inverter")

        assert result == mock_inverter_data

    @pytest.mark.asyncio
    async def test_fetch_non_200(self, hass):
        """Test non-200 response returns None."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch(
            "custom_components.openevt.api.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await fetch_inverter_status(hass, "http://openevt:9090/inverter")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_exception(self, hass):
        """Test connection error returns None."""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection failed")
        hass.data["aiohttp_client"] = {}

        with patch(
            "custom_components.openevt.api.async_get_clientsession",
            return_value=mock_session,
        ):
            result = await fetch_inverter_status(hass, "http://openevt:9090/inverter")

        assert result is None


class TestCheckSupervisorAddon:
    """Tests for check_supervisor_addon."""

    @pytest.mark.asyncio
    async def test_check_success(self, hass, mock_supervisor_response):
        """Test successful addon detection."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_supervisor_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch.dict(
            "os.environ",
            {"SUPERVISOR": "http://supervisor", "SUPERVISOR_TOKEN": "test-token"},
        ):
            with patch(
                "custom_components.openevt.api.async_get_clientsession",
                return_value=mock_session,
            ):
                result = await check_supervisor_addon(hass)

        assert result is not None
        assert result["hostname"] == "openevt"
        assert result["state"] == "started"

    @pytest.mark.asyncio
    async def test_check_no_token(self, hass):
        """Test that missing token returns None."""
        with patch.dict("os.environ", {"SUPERVISOR": "http://supervisor"}, clear=True):
            with patch(
                "custom_components.openevt.api.async_get_clientsession"
            ) as mock_session:
                result = await check_supervisor_addon(hass)

        assert result is None
        mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_addon_not_started(self, hass, mock_supervisor_not_started):
        """Test addon not started returns None."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_supervisor_not_started)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch.dict(
            "os.environ",
            {"SUPERVISOR": "http://supervisor", "SUPERVISOR_TOKEN": "test-token"},
        ):
            with patch(
                "custom_components.openevt.api.async_get_clientsession",
                return_value=mock_session,
            ):
                result = await check_supervisor_addon(hass)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_addon_not_found(self, hass):
        """Test 404 response returns None."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch.dict(
            "os.environ",
            {"SUPERVISOR": "http://supervisor", "SUPERVISOR_TOKEN": "test-token"},
        ):
            with patch(
                "custom_components.openevt.api.async_get_clientsession",
                return_value=mock_session,
            ):
                result = await check_supervisor_addon(hass)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_bare_ip_scheme(self, hass, mock_supervisor_response):
        """Test bare IP address gets http:// prepended."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_supervisor_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch.dict(
            "os.environ",
            {"SUPERVISOR": "172.30.32.2", "SUPERVISOR_TOKEN": "test-token"},
        ):
            with patch(
                "custom_components.openevt.api.async_get_clientsession",
                return_value=mock_session,
            ):
                result = await check_supervisor_addon(hass)

        assert result is not None
        # Verify the URL had http:// prepended
        call_url = mock_session.get.call_args[0][0]
        assert call_url.startswith("http://172.30.32.2")

    @pytest.mark.asyncio
    async def test_check_all_slugs_fail(self, hass):
        """Test that trying all slugs and failing returns None."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        hass.data["aiohttp_client"] = {}

        with patch.dict(
            "os.environ",
            {"SUPERVISOR": "http://supervisor", "SUPERVISOR_TOKEN": "test-token"},
        ):
            with patch(
                "custom_components.openevt.api.async_get_clientsession",
                return_value=mock_session,
            ):
                result = await check_supervisor_addon(hass)

        assert result is None
        # Should have tried both slugs
        assert mock_session.get.call_count == 2
