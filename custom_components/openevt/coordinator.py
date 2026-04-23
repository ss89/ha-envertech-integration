"""Data update coordinator for the OpenEVT integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_inverter_status, parse_inverter_status
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OpenEVTCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Envertech inverter data via the OpenEVT API."""

    parallel_updates = 0

    def __init__(
        self,
        hass: HomeAssistant,
        urls: list[str],
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="openevt",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self._urls = urls
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all inverter endpoints."""
        result: dict[str, Any] = {}

        for url in self._urls:
            try:
                raw_data = await fetch_inverter_status(self.hass, url)
                parsed = parse_inverter_status(raw_data)

                if parsed:
                    inverter_id = parsed.get("InverterId")
                    result[inverter_id] = parsed
                    _LOGGER.debug("Fetched data for %s: %s", inverter_id, parsed.get("InverterId"))
                else:
                    _LOGGER.debug("No valid data from %s (inverter may be unavailable)", url)
            except Exception as exc:
                _LOGGER.debug("Failed to update %s: %s", url, exc)
                raise UpdateFailed(f"Failed to fetch data from {url}: {exc}") from exc

        # Inverter may be powered off or in standby — return empty data
        # so sensors show as unavailable instead of crashing
        if not result:
            _LOGGER.debug("No inverter data received from any endpoint (inverter may be unavailable)")
            self.data = {}
            return {}

        self.data = result
        return result
