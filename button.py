from __future__ import annotations

import logging
from datetime import date

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import ProfiMaktabApiError
from .const import DOMAIN, DATA_CLIENT, DATA_PAYLOAD, SIGNAL_DATA_UPDATED
from .parser import parse_dairy

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the global update button ONCE."""
    _LOGGER.debug("ProfiMaktab button: async_setup_entry called for %s", entry.title)

    # Создаём кнопку ТОЛЬКО для первого entry
    # Используем тот же ключ, что и в __init__.py
    if hass.data[DOMAIN].get("button_created"):
        _LOGGER.debug("ProfiMaktab button: already created, skipping")
        return

    _LOGGER.info("ProfiMaktab button: creating global update button entity")
    async_add_entities([ProfiMaktabGlobalUpdateButton(hass)])
    _LOGGER.info("ProfiMaktab button: global update button entity created")


class ProfiMaktabGlobalUpdateButton(ButtonEntity):
    """Global button to update ProfiMaktab data for all students."""

    _attr_name = "Update ProfiMaktab Data"
    _attr_unique_id = "profimaktab_update_all"
    _attr_icon = "mdi:update"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def async_press(self) -> None:
        _LOGGER.info("ProfiMaktab button: global update button pressed")

        today = date.today().isoformat()
        updated_count = 0
        failed_count = 0

        for entry_id, entry_data in self._hass.data.get(DOMAIN, {}).items():
            # Пропускаем служебные ключи
            if entry_id == "button_created":
                continue

            # Проверяем, что это dict с данными entry
            if not isinstance(entry_data, dict):
                continue

            client = entry_data.get(DATA_CLIENT)
            if not client:
                _LOGGER.debug("ProfiMaktab button: no client for entry_id %s", entry_id)
                continue

            try:
                config_entry = self._hass.config_entries.async_get_entry(entry_id)
                if not config_entry:
                    _LOGGER.warning("ProfiMaktab button: config_entry not found for %s", entry_id)
                    continue

                student_id = config_entry.data["student_id"]
                student_name = config_entry.data["student_name"]

                _LOGGER.debug(
                    "ProfiMaktab button: updating data for %s (ID: %s)",
                    student_name,
                    student_id,
                )

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
                updated_count += 1

                _LOGGER.info(
                    "ProfiMaktab button: data updated for %s", student_name
                )

            except ProfiMaktabApiError as err:
                failed_count += 1
                _LOGGER.error(
                    "ProfiMaktab button: update failed for %s: %s",
                    student_name,
                    err,
                )
            except Exception as err:
                failed_count += 1
                _LOGGER.exception(
                    "ProfiMaktab button: unexpected error for %s: %s",
                    student_name,
                    err,
                )

        _LOGGER.info(
            "ProfiMaktab button: update complete (updated: %d, failed: %d)",
            updated_count,
            failed_count,
        )
