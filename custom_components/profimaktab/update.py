from datetime import date
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, DATA_CLIENT, DATA_PAYLOAD, SIGNAL_DATA_UPDATED
from .parser import parse_dairy

_LOGGER = logging.getLogger(__name__)


async def async_update_entry(hass, entry):
    """Fetch and update data for a single ConfigEntry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    client = entry_data[DATA_CLIENT]

    student_id = entry.data["student_id"]
    student_name = entry.data["student_name"]

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

    _LOGGER.debug(
        "ProfiMaktab: initial data loaded for %s", student_name
    )
