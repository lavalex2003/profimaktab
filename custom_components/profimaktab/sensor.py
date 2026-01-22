from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, DATA_PAYLOAD, SIGNAL_DATA_UPDATED


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            ProfiMaktabAverageMarkSensor(hass, entry),
            ProfiMaktabSchoolDaySensor(hass, entry),
        ]
    )


class _BaseProfiMaktabSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry

    @property
    def _payload(self):
        return self._hass.data[DOMAIN][self._entry.entry_id][DATA_PAYLOAD]

    async def async_added_to_hass(self) -> None:
        """Register dispatcher listener."""
        self.async_on_remove(
            async_dispatcher_connect(
                self._hass,
                SIGNAL_DATA_UPDATED,
                self._handle_data_update,
            )
        )

    def _handle_data_update(self) -> None:
        """Handle updated data safely from any thread."""
        self._hass.loop.call_soon_threadsafe(
            self.async_write_ha_state
        )

class ProfiMaktabAverageMarkSensor(_BaseProfiMaktabSensor):
    _attr_icon = "mdi:calculator-variant"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_average_mark"

    @property
    def name(self):
        return "Average Mark"

    @property
    def native_value(self):
        if not self._payload:
            return None
        return self._payload["average"]

    @property
    def extra_state_attributes(self):
        if not self._payload:
            return None
        return {
            "source": "profimaktab",
            "student": self._payload["student"],
            "marks": self._payload["marks"],
            "marks_count": self._payload["marks_count"],
            "date": self._payload["date"],
            "attribution": "Data provided by profiMaktab.uz",
        }


class ProfiMaktabSchoolDaySensor(_BaseProfiMaktabSensor):
    _attr_icon = "mdi:school"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_school_day"

    @property
    def name(self):
        return "School Day"

    @property
    def native_value(self):
        if not self._payload:
            return None
        return self._payload["date"]

    @property
    def extra_state_attributes(self):
        if not self._payload:
            return None
        return {
            "source": "profimaktab",
            "student": self._payload["student"],
            "lesson_count": self._payload["lesson_count"],
            "lessons": self._payload["lessons"],
            "attribution": "Data provided by profiMaktab.uz",
        }
