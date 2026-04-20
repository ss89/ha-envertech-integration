"""Config flow for the OpenEVT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback

from .api import check_supervisor_addon
from .const import DEFAULT_NAME, SUPERVISOR_ADDON_PORT

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("url"): str,
    }
)


class OpenEVTConfigFlow(ConfigFlow, domain="openevt"):
    """Handle a config flow for OpenEVT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._addon_info: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            # Try to auto-detect the addon
            addon_info = await check_supervisor_addon(self.hass)
            if addon_info:
                return await self._async_create_entry_from_addon(addon_info)
            # Auto-discovery failed — show manual form as fallback
            # (supervisor may not be available on HA Core)
            return self._show_manual_form()

        return self._async_create_entry_from_manual(user_input)

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual configuration (shown after auto-discovery fails)."""
        if user_input is None:
            return self._show_manual_form()

        return self._async_create_entry_from_manual(user_input)

    async def _async_create_entry_from_addon(
        self, addon_info: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create entry from detected addon."""
        hostname = addon_info["hostname"]
        url = f"http://{hostname}:{SUPERVISOR_ADDON_PORT}/inverter"

        self._urls = [url]

        title = DEFAULT_NAME

        await self.async_set_unique_id(url)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={
                "urls": [url],
            },
        )

    async def _async_create_entry_from_manual(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create entry from manual input."""
        url_raw = user_input["url"]
        urls = [u.strip() for u in url_raw.split(";") if u.strip()]

        if not urls:
            return self._show_manual_form(errors={"url": "empty_url"})

        self._urls = urls

        title = DEFAULT_NAME

        await self.async_set_unique_id(urls[0])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={
                "urls": urls,
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        if user_input is None:
            return self._show_reconfigure_form()

        return self._async_update_entry(user_input)

    def _show_reconfigure_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show the reconfiguration form."""
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors or {},
        )

    def _async_update_entry(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Update the existing config entry."""
        url_raw = user_input["url"]
        urls = [u.strip() for u in url_raw.split(";") if u.strip()]

        if not urls:
            return self._show_reconfigure_form(errors={"url": "empty_url"})

        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(),
            data_updates={"urls": urls},
        )

    def _show_manual_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show the manual configuration form."""
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: Any,
    ) -> None:
        """No options flow supported."""
        return None
