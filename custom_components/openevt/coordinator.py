"""Data update coordinator for the OpenEVT integration."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
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
        self.response_time_ms: float = 0.0
        self.last_contact: datetime | None = None
        self.request_retries: int = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all inverter endpoints."""
        result: dict[str, Any] = {}
        any_failure = False
        start_time = time.monotonic()

        for url in self._urls:
            try:
                raw_data = await fetch_inverter_status(self.hass, url)
                parsed = parse_inverter_status(raw_data)

                if parsed:
                    inverter_id = str(parsed.get("InverterId", ""))
                    if not inverter_id:
                        continue
                    result[inverter_id] = parsed
                    _LOGGER.debug("Fetched data for %s", inverter_id)
                else:
                    _LOGGER.debug("No valid data from %s (inverter may be unavailable)", url)
            except Exception as exc:
                any_failure = True
                _LOGGER.debug("Failed to update %s: %s", url, exc)
                continue

        elapsed_ms = (time.monotonic() - start_time) * 1000
        self.response_time_ms = round(elapsed_ms, 2)
        self.last_contact = datetime.now() if result else None
        self.request_retries = 0 if result else self.request_retries + 1

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
    ) -> tuple[set[str], set[str]]:
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
