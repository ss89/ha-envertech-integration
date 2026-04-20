"""API client for the OpenEVT integration."""

from __future__ import annotations

import logging
import os
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import SUPERVISOR_ADDON_PORT, SUPERVISOR_ADDON_SLUGS

_LOGGER = logging.getLogger(__name__)


async def check_supervisor_addon(
    hass: HomeAssistant,
) -> dict[str, Any] | None:
    """Check if the OpenEVT Supervisor add-on is installed and running.

    Returns addon info dict with hostname, options, state on success,
    or None if the addon is not available.
    """
    api_host = os.environ.get("SUPERVISOR", "http://supervisor")
    token = os.environ.get("SUPERVISOR_TOKEN", "")

    _LOGGER.warning(
        "Supervisor check: api_host=%s, token_present=%s",
        api_host,
        bool(token),
    )

    if not api_host or not token:
        _LOGGER.warning(
            "Supervisor check: not available (api_host=%s, token_present=%s). "
            "This integration requires HA OS or HA Container.",
            api_host,
            bool(token),
        )
        return None

    session = async_get_clientsession(hass)
    timeout = ClientTimeout(total=5)

    # Try each known slug variant in order
    for slug in SUPERVISOR_ADDON_SLUGS:
        _LOGGER.warning("Supervisor check: trying slug '%s'", slug)
        try:
            url = f"{api_host}/addons/{slug}/info"
            headers = {"Authorization": f"Bearer {token}"}

            _LOGGER.warning("Supervisor check: GET %s", url)
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                _LOGGER.warning(
                    "Supervisor check: status %d for slug '%s'",
                    resp.status,
                    slug,
                )
                if resp.status != 200:
                    _LOGGER.warning(
                        "Supervisor check: addon %s not found (status %d). "
                        "If your addon slug differs, update SUPERVISOR_ADDON_SLUGS.",
                        slug,
                        resp.status,
                    )
                    continue
                data = await resp.json()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning(
                "Supervisor check: failed for slug '%s': %s. "
                "Ensure HA OS/Container is used and the addon is installed.",
                slug,
                exc,
            )
            continue

        # Handle both old and new Supervisor API response formats
        addon = data.get("data") or data

        state = addon.get("state")
        hostname = addon.get("hostname")
        options = addon.get("options", {})

        _LOGGER.warning(
            "Supervisor check: slug '%s' found (state=%s, hostname=%s)",
            slug,
            state,
            hostname,
        )

        if state != "started" or not hostname:
            _LOGGER.warning(
                "Supervisor check: addon %s not ready (state=%s, hostname=%s). "
                "Ensure the addon is running.",
                slug,
                state,
                hostname,
            )
            continue

        _LOGGER.info(
            "Supervisor check: addon '%s' ready (hostname=%s, state=%s)",
            slug,
            hostname,
            state,
        )
        return {
            "hostname": hostname,
            "options": options,
            "state": state,
            "slug": slug,
        }

    _LOGGER.warning(
        "Supervisor check: no addon found with any known slug (%s). "
        "Check the addon slug in HA Supervisor settings.",
        SUPERVISOR_ADDON_SLUGS,
    )
    return None


async def fetch_inverter_status(hass: HomeAssistant, url: str) -> dict[str, Any] | None:
    """Fetch inverter status from the OpenEVT endpoint.

    Args:
        hass: Home Assistant instance.
        url: Full URL to the /inverter endpoint (e.g. http://openevt:9090/inverter).

    Returns:
        Parsed JSON response dict, or None on failure.
    """
    _LOGGER.debug("Fetching inverter status from %s", url)
    session = async_get_clientsession(hass)
    timeout = ClientTimeout(total=10)

    try:
        async with session.get(url, timeout=timeout) as resp:
            _LOGGER.debug("Inverter endpoint status: %d", resp.status)
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
        _LOGGER.debug("parse_inverter_status: no data provided")
        return None

    inverter_id = data.get("InverterId")
    if not inverter_id:
        _LOGGER.debug("parse_inverter_status: missing InverterId")
        return None

    _LOGGER.debug("parse_inverter_status: InverterId=%s", inverter_id)
    return {
        "InverterId": str(inverter_id),
        "Module1": data.get("Module1", {}),
        "Module2": data.get("Module2", {}),
    }
