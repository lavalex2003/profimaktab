from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ProfiMaktabClient
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    DATA_CLIENT,
    DATA_PAYLOAD,
)
from .update import async_update_entry

_LOGGER = logging.getLogger(__name__)

SENSOR_PLATFORMS = ["sensor"]
BUTTON_PLATFORMS = ["button"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initial setup of ProfiMaktab."""
    _LOGGER.debug("ProfiMaktab: async_setup called")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("button_created", False)
    _LOGGER.info("ProfiMaktab: initial setup complete")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ProfiMaktab from a config entry."""
    _LOGGER.info(
        "ProfiMaktab: async_setup_entry for %s (ID: %s)",
        entry.title,
        entry.entry_id,
    )
    
    session = async_get_clientsession(hass)

    # 🔌 Runtime API client
    client = ProfiMaktabClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )
    _LOGGER.debug("ProfiMaktab: API client created for %s", entry.title)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_PAYLOAD: None,
    }

    # 📟 Сенсоры — для КАЖДОЙ записи
    _LOGGER.debug("ProfiMaktab: setting up sensors for %s", entry.title)
    await hass.config_entries.async_forward_entry_setups(
        entry, SENSOR_PLATFORMS
    )

    # 🔘 Глобальная кнопка — ТОЛЬКО ОДИН РАЗ
    if not hass.data[DOMAIN]["button_created"]:
        _LOGGER.info("ProfiMaktab: creating global update button")
        await hass.config_entries.async_forward_entry_setups(
            entry, BUTTON_PLATFORMS
        )
        hass.data[DOMAIN]["button_created"] = True
    else:
        _LOGGER.debug("ProfiMaktab: button already created, skipping")

    # 🔄 Автоматическое первичное обновление данных
    _LOGGER.debug("ProfiMaktab: starting initial data update for %s", entry.title)
    try:
        await async_update_entry(hass, entry)
        _LOGGER.info("ProfiMaktab: initial update successful for %s", entry.title)
    except Exception as err:
        _LOGGER.error(
            "ProfiMaktab: initial update FAILED for %s: %s",
            entry.title,
            err,
            exc_info=True,
        )
        # Продолжаем setup даже если update упал

    _LOGGER.info("ProfiMaktab: setup complete for %s", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload ProfiMaktab config entry."""
    _LOGGER.info("ProfiMaktab: unloading entry %s", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SENSOR_PLATFORMS
    )

    hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.debug("ProfiMaktab: entry %s unloaded", entry.title)
    return unload_ok
