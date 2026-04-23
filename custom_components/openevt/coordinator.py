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
        self._known_inverter_ids: set[str] = set()
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all inverter endpoints."""
        result: dict[str, Any] = {}
        any_failure = False

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
                any_failure = True
                _LOGGER.debug("Failed to update %s: %s", url, exc)
                continue

        self.data = result

        if not result and any_failure:
            raise UpdateFailed("Failed to fetch data from any endpoint")

        return result

    @property
    def inverter_ids(self) -> set[str]:
        """Return the set of known inverter IDs from the latest data."""
        return set(self.data.keys())

    def async_update_list(
        self,
        async_add_entities: Any,
        async_remove_entities: Any | None = None,
    ) -> None:
        """Notify sensor platform of new/removed inverters.

        Compares known inverter IDs against current data and returns
        the sets of new and stale inverter IDs for the sensor platform
        to act on.
        """
        current_ids = set(self.data.keys())
        known_ids = set(self._known_inverter_ids)

        new_ids = current_ids - known_ids
        stale_ids = known_ids - current_ids

        if new_ids or stale_ids:
            _LOGGER.info(
                "Inverter list changed: +%s, -%s (current: %s)",
                new_ids,
                stale_ids,
                current_ids,
            )

        self._known_inverter_ids = current_ids
        return new_ids, stale_ids
