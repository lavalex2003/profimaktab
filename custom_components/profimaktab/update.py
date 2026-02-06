from datetime import date
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, DATA_CLIENT, DATA_PAYLOAD, SIGNAL_DATA_UPDATED
from .parser import parse_dairy
from .api import ProfiMaktabApiError

_LOGGER = logging.getLogger(__name__)


async def async_update_entry(hass, entry):
    """Fetch and update data for a single ConfigEntry."""
    student_id = entry.data["student_id"]
    student_name = entry.data["student_name"]
    
    _LOGGER.info(
        "ProfiMaktab: fetching data for %s (ID: %s)",
        student_name,
        student_id,
    )
    
    try:
        entry_data = hass.data[DOMAIN][entry.entry_id]
        client = entry_data[DATA_CLIENT]

        raw = await client.async_get_dairy(
            student_id=student_id,
            for_date=date.today(),
        )

        parsed = parse_dairy(
            raw,
            student=student_name,
            date=date.today().isoformat(),
        )

        entry_data[DATA_PAYLOAD] = parsed

        # 🔔 Уведомляем все сенсоры
        async_dispatcher_send(hass, SIGNAL_DATA_UPDATED)

        _LOGGER.info(
            "ProfiMaktab: data updated for %s (lessons: %d, avg: %s)",
            student_name,
            parsed.get("lesson_count", 0),
            parsed.get("average", 0),
        )
    except ProfiMaktabApiError as err:
        _LOGGER.error(
            "ProfiMaktab: update failed for %s: %s",
            student_name,
            err,
        )
    except Exception as err:
        _LOGGER.exception(
            "ProfiMaktab: unexpected error for %s",
            student_name,
        )
