"""API client for the OpenEVT integration."""

from __future__ import annotations

import logging
import os
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import SUPERVISOR_ADDON_SLUG, SUPERVISOR_ADDON_PORT

_LOGGER = logging.getLogger(__name__)


async def check_supervisor_addon(hass: HomeAssistant) -> dict[str, Any] | None:
    """Check if the OpenEVT Supervisor add-on is installed and running.

    Returns addon info dict with hostname, options, state, or None if not available.
    """
    api_host = os.environ.get("SUPERVISOR", "http://supervisor")
    token = os.environ.get("SUPERVISOR_TOKEN", "")

    if not api_host or not token:
        _LOGGER.debug("Supervisor API not available (missing env vars)")
        return None

    session = async_get_clientsession(hass)
    timeout = ClientTimeout(total=5)

    try:
        url = f"{api_host}/addons/{SUPERVISOR_ADDON_SLUG}/info"
        headers = {"Authorization": f"Bearer {token}"}

        async with session.get(url, headers=headers, timeout=timeout) as resp:
            if resp.status != 200:
                _LOGGER.debug(
                    "Addon %s not found (status %d)", SUPERVISOR_ADDON_SLUG, resp.status
                )
                return None
            data = await resp.json()
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to check addon %s: %s", SUPERVISOR_ADDON_SLUG, exc)
        return None

    # Handle both old and new Supervisor API response formats
    addon = data.get("data") or data

    state = addon.get("state")
    hostname = addon.get("hostname")
    options = addon.get("options", {})

    if state != "started" or not hostname:
        _LOGGER.debug(
            "Addon %s not ready (state=%s, hostname=%s)",
            SUPERVISOR_ADDON_SLUG,
            state,
            hostname,
        )
        return None

    return {
        "hostname": hostname,
        "options": options,
        "state": state,
    }


async def fetch_inverter_status(hass: HomeAssistant, url: str) -> dict[str, Any] | None:
    """Fetch inverter status from the OpenEVT endpoint.

    Args:
        hass: Home Assistant instance.
        url: Full URL to the /inverter endpoint (e.g. http://openevt:9090/inverter).

    Returns:
        Parsed JSON response dict, or None on failure.
    """
    session = async_get_clientsession(hass)
    timeout = ClientTimeout(total=10)

    try:
        async with session.get(url, timeout=timeout) as resp:
            if resp.status != 200:
                _LOGGER.debug("Inverter endpoint returned status %d", resp.status)
                return None
            return await resp.json()
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("Failed to fetch inverter status from %s: %s", url, exc)
        return None


def parse_inverter_status(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Parse the raw JSON response into a structured dict.

    Returns the parsed dict with InverterId, Module1, Module2 keys,
    or None if data is invalid.
    """
    if not data:
        return None

    inverter_id = data.get("InverterId")
    if not inverter_id:
        _LOGGER.debug("Missing InverterId in inverter response")
        return None

    return {
        "InverterId": str(inverter_id),
        "Module1": data.get("Module1", {}),
        "Module2": data.get("Module2", {}),
    }
