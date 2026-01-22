from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ProfiMaktabClient, ProfiMaktabAuthError, ProfiMaktabApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ProfiMaktabConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ProfiMaktab."""

    VERSION = 1

    def __init__(self) -> None:
        self._client: ProfiMaktabClient | None = None
        self._children: Dict[int, Dict[str, Any]] = {}
        self._user_input: Dict[str, Any] = {}

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            self._client = ProfiMaktabClient(
                session=session,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )

            try:
                profile = await self._client.async_get_profile()
            except ProfiMaktabAuthError:
                errors["base"] = "invalid_auth"
            except ProfiMaktabApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"

            if not errors:
                additional = profile.get("additional_data") or {}
                contact_id = additional.get("contact_id")

                if not contact_id:
                    errors["base"] = "no_contact"
                else:
                    self._user_input = {
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        "contact_id": contact_id,
                    }
                    return await self.async_step_select_child()

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_select_child(self, user_input=None):
        errors = {}

        assert self._client is not None

        if not self._children:
            try:
                data = await self._client.async_get_student_contacts(
                    self._user_input["contact_id"]
                )
            except ProfiMaktabApiError:
                return self.async_abort(reason="cannot_connect")

            students = data.get("students", [])
            for student in students:
                sid = student["id"]
                user = student.get("user") or {}
                self._children[sid] = {
                    "student_id": sid,
                    "student_name": user.get("name", f"Student {sid}"),
                }

        if not self._children:
            return self.async_abort(reason="no_students")

        if user_input is not None:
            student_id = user_input["student_id"]

            # Проверка на дубликат
            for entry in self._async_current_entries():
                if entry.data.get("student_id") == student_id:
                    errors["base"] = "already_configured"
                    break

            if not errors:
                child = self._children[student_id]
                data = {
                    **self._user_input,
                    **child,
                }

                title = child["student_name"]
                return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Required("student_id"): vol.In(
                    {
                        sid: info["student_name"]
                        for sid, info in self._children.items()
                    }
                )
            }
        )

        return self.async_show_form(
            step_id="select_child",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ProfiMaktabOptionsFlow(config_entry)


class ProfiMaktabOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
