"""Config flow for the OpenEVT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
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
        self._urls: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        _LOGGER.info("Config flow: starting user step")

        if user_input is None:
            _LOGGER.info("Config flow: attempting addon auto-detection")
            addon_info = await check_supervisor_addon(self.hass)
            if addon_info:
                _LOGGER.info(
                    "Config flow: addon detected (hostname=%s, slug=%s)",
                    addon_info["hostname"],
                    addon_info.get("slug", "unknown"),
                )
                return await self._async_create_entry_from_addon(addon_info)

            _LOGGER.warning(
                "Config flow: addon auto-detection failed. "
                "Showing manual form. "
                "Ensure the OpenEVT addon is installed and running in Home Assistant Supervisor."
            )
            return self._show_manual_form()

        _LOGGER.info("Config flow: user submitted manual input")
        return await self._async_create_entry_from_manual(user_input)

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual configuration (shown after auto-discovery fails)."""
        _LOGGER.info("Config flow: manual step entered")
        if user_input is None:
            return self._show_manual_form()

        _LOGGER.info("Config flow: manual step submitted")
        return await self._async_create_entry_from_manual(user_input)

    async def _async_create_entry_from_addon(
        self, addon_info: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create entry from detected addon."""
        hostname = addon_info["hostname"]
        slug = addon_info.get("slug", "unknown")
        url = f"http://{hostname}:{SUPERVISOR_ADDON_PORT}/inverter"

        _LOGGER.info(
            "Config flow: creating entry from addon (slug=%s, hostname=%s, url=%s)",
            slug,
            hostname,
            url,
        )

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

        _LOGGER.info("Config flow: creating entry from manual input (urls=%s)", urls)

        if not urls:
            _LOGGER.warning("Config flow: empty URL provided")
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

    def _show_manual_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        """Show the manual configuration form."""
        _LOGGER.debug("Config flow: showing manual form")
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: Any,
    ) -> OptionsFlow:
        """Return the options flow."""
        return OpenEVTOptionsFlowHandler(config_entry)


class OpenEVTOptionsFlowHandler(OptionsFlow):
    """Handle OpenEVT options."""

    def __init__(self, config_entry: Any) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is None:
            current_url = "; ".join(self._config_entry.data.get("urls", []))
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            "url",
                            default=current_url,
                        ): str,
                    }
                ),
            )

        url_raw = user_input["url"]
        urls = [u.strip() for u in url_raw.split(";") if u.strip()]

        if not urls:
            current_url = "; ".join(self._config_entry.data.get("urls", []))
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required("url", default=current_url): str,
                    }
                ),
                errors={"url": "empty_url"},
            )

        self.hass.config_entries.async_update_entry(
            self._config_entry,
            data={"urls": urls},
        )
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)
        return self.async_create_entry(data={})
