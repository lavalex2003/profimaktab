from __future__ import annotations

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

SENSOR_PLATFORMS = ["sensor"]
BUTTON_PLATFORMS = ["button"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initial setup of ProfiMaktab."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("button_created", False)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ProfiMaktab from a config entry."""
    session = async_get_clientsession(hass)

    # 🔌 Runtime API client
    client = ProfiMaktabClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_PAYLOAD: None,
    }

    # 📟 Сенсоры — для КАЖДОЙ записи
    await hass.config_entries.async_forward_entry_setups(
        entry, SENSOR_PLATFORMS
    )

    # 🔘 Глобальная кнопка — ТОЛЬКО ОДИН РАЗ
    if not hass.data[DOMAIN]["button_created"]:
        await hass.config_entries.async_forward_entry_setups(
            entry, BUTTON_PLATFORMS
        )
        hass.data[DOMAIN]["button_created"] = True

    # 🔄 Автоматическое первичное обновление данных
    # (асинхронно, чтобы не блокировать setup)
    hass.async_create_task(async_update_entry(hass, entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload ProfiMaktab config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SENSOR_PLATFORMS
    )

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
