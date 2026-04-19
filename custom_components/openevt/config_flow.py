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
        vol.Required("serial_numbers"): str,
    }
)


class OpenEVTConfigFlow(ConfigFlow, domain="openevt"):
    """Handle a config flow for OpenEVT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._addon_info: dict[str, Any] | None = None
        self._urls: list[str] = []
        self._serial_numbers: list[str] = []

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
        options = addon_info["options"]

        # Parse semicolon-separated addresses
        address_raw = options.get("address", "")
        addresses = [a.strip() for a in address_raw.split(";") if a.strip()]

        # Parse semicolon-separated serial numbers
        serial_raw = options.get("serial_number", "")
        serial_numbers = [s.strip() for s in serial_raw.split(";") if s.strip()]

        # Build URLs for each address
        urls = [f"http://{hostname}:{SUPERVISOR_ADDON_PORT}/inverter" for _ in addresses]

        # If no addresses provided, use a default URL
        if not urls:
            urls = [f"http://{hostname}:{SUPERVISOR_ADDON_PORT}/inverter"]

        # If no serial numbers provided, generate placeholders
        if not serial_numbers:
            serial_numbers = [f"inverter-{i+1}" for i in range(len(urls))]

        # Ensure serial numbers match URLs
        while len(serial_numbers) < len(urls):
            serial_numbers.append(f"inverter-{len(serial_numbers)+1}")

        self._urls = urls
        self._serial_numbers = serial_numbers

        title_parts = []
        for sn in serial_numbers:
            if sn and not sn.startswith("inverter-"):
                title_parts.append(sn)
        title = f"{DEFAULT_NAME}" + (f" ({', '.join(title_parts)})" if title_parts else "")

        await self.async_set_unique_id(serial_numbers[0])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={
                "urls": urls,
                "serial_numbers": serial_numbers,
            },
        )

    async def _async_create_entry_from_manual(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create entry from manual input."""
        url_raw = user_input["url"]
        urls = [u.strip() for u in url_raw.split(";") if u.strip()]

        serial_raw = user_input["serial_numbers"]
        serial_numbers = [s.strip() for s in serial_raw.split(";") if s.strip()]

        if not urls:
            return self._show_manual_form(errors={"url": "empty_url"})

        if not serial_numbers:
            return self._show_manual_form(errors={"serial_numbers": "empty_serial"})

        # Ensure serial numbers match URLs
        while len(serial_numbers) < len(urls):
            serial_numbers.append(f"inverter-{len(serial_numbers)+1}")

        self._urls = urls
        self._serial_numbers = serial_numbers

        title_parts = [sn for sn in serial_numbers if sn and not sn.startswith("inverter-")]
        title = f"{DEFAULT_NAME}" + (f" ({', '.join(title_parts)})" if title_parts else DEFAULT_NAME)

        await self.async_set_unique_id(serial_numbers[0])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={
                "urls": urls,
                "serial_numbers": serial_numbers,
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

        serial_raw = user_input["serial_numbers"]
        serial_numbers = [s.strip() for s in serial_raw.split(";") if s.strip()]

        if not urls:
            return self._show_reconfigure_form(errors={"url": "empty_url"})

        if not serial_numbers:
            return self._show_reconfigure_form(errors={"serial_numbers": "empty_serial"})

        # Ensure serial numbers match URLs
        while len(serial_numbers) < len(urls):
            serial_numbers.append(f"inverter-{len(serial_numbers)+1}")

        title_parts = [sn for sn in serial_numbers if sn and not sn.startswith("inverter-")]
        title = f"{DEFAULT_NAME}" + (f" ({', '.join(title_parts)})" if title_parts else DEFAULT_NAME)

        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(),
            data_updates={
                "urls": urls,
                "serial_numbers": serial_numbers,
            },
            title=title,
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
