"""Tests for the OpenEVT coordinator."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.openevt.coordinator import OpenEVTCoordinator


class TestCoordinatorInit:
    """Tests for coordinator initialization."""

    def test_init(self, hass):
        """Test coordinator initialization."""
        urls = ["http://openevt:9090/inverter"]
        coord = OpenEVTCoordinator(hass, urls)

        assert coord._urls == urls
        assert coord.data == {}
        assert coord._known_inverter_ids == set()
        assert coord.inverter_ids == set()


class TestCoordinatorUpdate:
    """Tests for coordinator data updates."""

    @pytest.mark.asyncio
    async def test_update_success(self, hass, mock_inverter_data):
        """Test successful data update."""
        urls = ["http://openevt:9090/inverter"]
        coord = OpenEVTCoordinator(hass, urls)

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_inverter_data
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                result = await coord._async_update_data()

        assert "31583078" in result
        assert result["31583078"]["InverterId"] == "31583078"
        assert coord.data == result
        assert coord.last_update_success is True

    @pytest.mark.asyncio
    async def test_update_all_fail(self, hass):
        """Test UpdateFailed when all endpoints fail."""
        urls = ["http://openevt:9090/inverter"]
        coord = OpenEVTCoordinator(hass, urls)

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Connection failed")
            with pytest.raises(UpdateFailed):
                await coord._async_update_data()

    @pytest.mark.asyncio
    async def test_update_partial_failure(self, hass, mock_inverter_data):
        """Test partial failure: one URL fails, one succeeds."""
        urls = [
            "http://openevt1:9090/inverter",
            "http://openevt2:9090/inverter",
        ]
        coord = OpenEVTCoordinator(hass, urls)

        call_count = 0

        async def mock_fetch(h, url):
            nonlocal call_count
            call_count += 1
            if "openevt1" in url:
                raise Exception("Connection failed")
            return mock_inverter_data

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
            side_effect=mock_fetch,
        ):
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                result = await coord._async_update_data()

        assert "31583078" in result
        assert coord.last_update_success is True
    @pytest.mark.asyncio
    async def test_update_invalid_data(self, hass):
        """Test that invalid data is skipped."""
        urls = ["http://openevt:9090/inverter"]
        coord = OpenEVTCoordinator(hass, urls)

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = None
            result = await coord._async_update_data()

        assert result == {}
        assert coord.last_update_success is True

    @pytest.mark.asyncio
    async def test_update_invalid_data_with_failure(self, hass):
        """Test UpdateFailed when data is invalid AND an exception occurred."""
        urls = ["http://openevt:9090/inverter"]
        coord = OpenEVTCoordinator(hass, urls)

        async def mock_fetch_fail(h, _url):
            raise Exception("Connection failed")

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
            side_effect=mock_fetch_fail,
        ):
            with pytest.raises(UpdateFailed):
                await coord._async_update_data()

class TestCoordinatorInverterIds:
    """Tests for inverter_ids tracking."""

    @pytest.mark.asyncio
    async def test_inverter_ids_empty(self, hass):
        """Test empty inverter_ids when no data."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])
        assert coord.inverter_ids == set()

    @pytest.mark.asyncio
    async def test_inverter_ids_populated(self, hass, mock_inverter_data):
        """Test inverter_ids after successful update."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_inverter_data
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                await coord._async_update_data()

        assert coord.inverter_ids == {"31583078"}


class TestCoordinatorAsyncUpdateList:
    """Tests for async_update_list dynamic entity management."""

    @pytest.mark.asyncio
    async def test_new_inverter(self, hass, mock_inverter_data):
        """Test detecting a new inverter."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_inverter_data
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                await coord._async_update_data()

        new_ids, stale_ids = coord.async_update_list(None, None)
        assert new_ids == {"31583078"}
        assert stale_ids == set()

    @pytest.mark.asyncio
    async def test_stale_inverter(self, hass, mock_inverter_data):
        """Test detecting a stale inverter."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])

        # First update: inverter present
        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_inverter_data
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                await coord._async_update_data()

        # Mark as known
        coord.async_update_list(None, None)

        # Second update: inverter gone
        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = None
            await coord._async_update_data()

        new_ids, stale_ids = coord.async_update_list(None, None)
        assert new_ids == set()
        assert stale_ids == {"31583078"}

    @pytest.mark.asyncio
    async def test_no_change(self, hass, mock_inverter_data):
        """Test no change in inverter list."""
        coord = OpenEVTCoordinator(hass, ["http://openevt:9090/inverter"])

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_inverter_data
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                return_value=mock_inverter_data,
            ):
                await coord._async_update_data()

        # First call marks as known
        coord.async_update_list(None, None)
        # Second call: same data
        new_ids, stale_ids = coord.async_update_list(None, None)
        assert new_ids == set()
        assert stale_ids == set()

    @pytest.mark.asyncio
    async def test_multiple_inverters(self, hass):
        """Test tracking multiple inverters."""
        data1 = {
            "InverterId": "111111",
            "Module1": {"InputVoltageDC": 23.0},
            "Module2": {"InputVoltageDC": 24.0},
        }
        data2 = {
            "InverterId": "222222",
            "Module1": {"InputVoltageDC": 25.0},
            "Module2": {"InputVoltageDC": 26.0},
        }

        urls = [
            "http://openevt1:9090/inverter",
            "http://openevt2:9090/inverter",
        ]
        coord = OpenEVTCoordinator(hass, urls)

        async def mock_fetch(h, url):
            if "openevt1" in url:
                return data1
            return data2

        with patch(
            "custom_components.openevt.coordinator.fetch_inverter_status",
            new_callable=AsyncMock,
            side_effect=mock_fetch,
        ):
            with patch(
                "custom_components.openevt.coordinator.parse_inverter_status",
                side_effect=lambda d: d,
            ):
                await coord._async_update_data()

        new_ids, stale_ids = coord.async_update_list(None, None)
        assert new_ids == {"111111", "222222"}
        assert stale_ids == set()
