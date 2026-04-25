"""Tests for the OpenEVT config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.openevt.config_flow import OpenEVTOptionsFlowHandler
from custom_components.openevt.const import DOMAIN


@pytest.fixture
def mock_check_supervisor_addon():
    """Mock check_supervisor_addon to return addon info."""
    with patch(
        "custom_components.openevt.config_flow.check_supervisor_addon",
        new_callable=AsyncMock,
        return_value={
            "hostname": "openevt",
            "options": {},
            "state": "started",
            "slug": "openevt",
        },
    ) as mock:
        yield mock


@pytest.fixture
def mock_check_supervisor_addon_not_found():
    """Mock check_supervisor_addon to return None."""
    with patch(
        "custom_components.openevt.config_flow.check_supervisor_addon",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock:
        yield mock


class TestOptionsFlow:
    """Tests for the options flow."""

    async def test_options_flow_shows_form(self, hass: HomeAssistant):
        """Test options flow shows form with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        handler = OpenEVTOptionsFlowHandler(entry)
        handler.hass = hass

        result = await handler.async_step_init()

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    async def test_options_flow_updates(self, hass: HomeAssistant):
        """Test options flow updates URLs."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        handler = OpenEVTOptionsFlowHandler(entry)
        handler.hass = hass

        result = await handler.async_step_init({"url": "http://openevt2:9090/inverter"})

        assert result["type"] == "create_entry"
        assert entry.data["urls"] == ["http://openevt2:9090/inverter"]

    async def test_options_flow_empty_url_error(self, hass: HomeAssistant):
        """Test empty URL in options flow."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"urls": ["http://openevt:9090/inverter"]},
        )
        entry.add_to_hass(hass)

        handler = OpenEVTOptionsFlowHandler(entry)
        handler.hass = hass

        result = await handler.async_step_init({"url": ""})

        assert result["type"] == "form"
        assert result["errors"] == {"url": "empty_url"}
