from __future__ import annotations

import logging
from datetime import date

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import SIGNAL_DATA_UPDATED

from .api import ProfiMaktabApiError
from .const import DOMAIN, DATA_CLIENT, DATA_PAYLOAD
from .parser import parse_dairy

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the global update button ONCE."""

    # Создаём кнопку ТОЛЬКО для первого entry
    from .const import BUTTON_CREATED

    if hass.data[DOMAIN].get(BUTTON_CREATED):
        return

    hass.data[DOMAIN][BUTTON_CREATED] = True

    async_add_entities([ProfiMaktabGlobalUpdateButton(hass)])


class ProfiMaktabGlobalUpdateButton(ButtonEntity):
    """Global button to update ProfiMaktab data for all students."""

    _attr_name = "Update ProfiMaktab Data"
    _attr_unique_id = "profimaktab_update_all"
    _attr_icon = "mdi:update"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def async_press(self) -> None:
        _LOGGER.debug("ProfiMaktab: global update started")

        today = date.today().isoformat()

        for entry_id, entry_data in self._hass.data.get(DOMAIN, {}).items():
            if entry_id in ("button_created", "button_entity_created"):
                continue

            client = entry_data.get(DATA_CLIENT)
            if not client:
                continue

            try:
                config_entry = self._hass.config_entries.async_get_entry(entry_id)
                if not config_entry:
                    continue

                student_id = config_entry.data["student_id"]
                student_name = config_entry.data["student_name"]

                raw = await client.async_get_dairy(
                    student_id=student_id,
                    for_date=date.today(),
                )

                parsed = parse_dairy(
                    raw,
                    student=student_name,
                    date=today,
                )

                entry_data[DATA_PAYLOAD] = parsed
                async_dispatcher_send(self._hass, SIGNAL_DATA_UPDATED)

                _LOGGER.debug(
                    "ProfiMaktab: data updated for %s", student_name
                )

            except ProfiMaktabApiError as err:
                _LOGGER.error(
                    "ProfiMaktab: update failed for %s: %s",
                    student_name,
                    err,
                )
