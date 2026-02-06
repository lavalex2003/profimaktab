from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any, Dict, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)


class ProfiMaktabApiError(Exception):
    """Base API error."""


class ProfiMaktabAuthError(ProfiMaktabApiError):
    """Authentication failed."""


class ProfiMaktabClient:
    """HTTP client for ProfiMaktab API."""

    BASE_URL = "https://api.profimaktab.uz/api"
    TOKEN_ENDPOINT = "/token/"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        *,
        request_timeout: int = 30,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

        self._access_token: Optional[str] = None
        self._auth_lock = asyncio.Lock()

    # ---------- Auth ----------

    async def async_login(self) -> None:
        """Authenticate and obtain access token."""
        url = f"{self.BASE_URL}{self.TOKEN_ENDPOINT}"
        payload = {
            "username": self._username,
            "password": self._password,
        }

        _LOGGER.debug("ProfiMaktab: logging in")

        async with self._session.post(
            url, json=payload, timeout=self._timeout
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error(
                    "ProfiMaktab: login failed (%s): %s", resp.status, text
                )
                raise ProfiMaktabAuthError("Login failed")

            data = await resp.json()

        access = data.get("access")
        if not access:
            _LOGGER.error("ProfiMaktab: access token missing in response")
            raise ProfiMaktabAuthError("Access token missing")

        self._access_token = access
        _LOGGER.debug("ProfiMaktab: login successful")

    async def async_ensure_authenticated(self) -> None:
        """
        Ensure we have a valid access token.
        Uses a lock to avoid concurrent re-logins.
        """
        if self._access_token:
            return

        async with self._auth_lock:
            # Double-check inside the lock
            if self._access_token:
                return
            await self.async_login()

    # ---------- Low-level request ----------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True,
    ) -> Any:
        await self.async_ensure_authenticated()

        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        async with self._session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json,
            timeout=self._timeout,
        ) as resp:
            if resp.status == 401 and retry_on_401:
                _LOGGER.debug("ProfiMaktab: 401 received, re-authenticating")
                # Token invalid/expired → relogin once
                self._access_token = None
                await self.async_login()
                return await self._request(
                    method,
                    path,
                    params=params,
                    json=json,
                    retry_on_401=False,
                )

            if resp.status >= 400:
                text = await resp.text()
                _LOGGER.error(
                    "ProfiMaktab: API error %s on %s: %s",
                    resp.status,
                    path,
                    text,
                )
                raise ProfiMaktabApiError(
                    f"API error {resp.status} on {path}"
                )

            return await resp.json()

    # ---------- High-level API ----------

    async def async_get_profile(self) -> Dict[str, Any]:
        """GET /profile/"""
        return await self._request("GET", "/profile/")

    async def async_get_student_contacts(self, contact_id: int) -> Dict[str, Any]:
        """GET /student_contacts/{contact_id}/"""
        return await self._request(
            "GET", f"/student_contacts/{contact_id}/"
        )

    async def async_get_student(self, student_id: int) -> Dict[str, Any]:
        """GET /student_students/{student_id}"""
        return await self._request(
            "GET", f"/student_students/{student_id}"
        )

    async def async_get_dairy(
        self,
        student_id: int,
        for_date: Optional[date] = None,
    ) -> Any:
        """GET /dairy/?for_date=YYYY-MM-DD&student={id}"""
        if for_date is None:
            for_date = date.today()

        params = {
            "for_date": for_date.isoformat(),
            "student": student_id,
        }

        return await self._request("GET", "/dairy/", params=params)
