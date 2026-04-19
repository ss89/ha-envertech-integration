"""Data update coordinator for the OpenEVT integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import fetch_inverter_status, parse_inverter_status
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OpenEVTCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Envertech inverter data via the OpenEVT API."""

    def __init__(
        self,
        hass: HomeAssistant,
        urls: list[str],
        serial_numbers: list[str],
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="openevt",
            update_interval=asyncio.timedelta(seconds=UPDATE_INTERVAL),
            # Coordinator centralizes updates; sensors are read-only
            parallel_updates=0,
        )
        self._urls = urls
        self._serial_numbers = serial_numbers
        # Map serial numbers to their inverter data
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all inverter endpoints."""
        result: dict[str, Any] = {}

        for i, url in enumerate(self._urls):
            serial = self._serial_numbers[i] if i < len(self._serial_numbers) else f"inverter-{i+1}"

            try:
                raw_data = await fetch_inverter_status(self.hass, url)
                parsed = parse_inverter_status(raw_data)

                if parsed:
                    result[serial] = parsed
                    _LOGGER.debug("Fetched data for %s: %s", serial, parsed.get("InverterId"))
                else:
                    _LOGGER.debug("No valid data from %s", url)
            except Exception as exc:
                _LOGGER.debug("Failed to update %s: %s", serial, exc)
                raise UpdateFailed(f"Failed to fetch data from {url}: {exc}") from exc

        if not result:
            raise UpdateFailed("No inverter data received from any endpoint")

        self.data = result
        return result
