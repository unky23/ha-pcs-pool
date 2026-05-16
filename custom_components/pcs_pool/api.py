from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import aiohttp

from .const import BASE_URL, CONTROLLERS_ENDPOINT, TOKEN_ENDPOINT


class PCSApiError(Exception):
    """Base PCS API error."""


class PCSAuthError(PCSApiError):
    """PCS authentication error."""


class PCSApiClient:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None

    async def async_login(self) -> None:
        url = urljoin(BASE_URL, TOKEN_ENDPOINT)

        async with self._session.post(
            url,
            data={
                "UserName": self._username,
                "Password": self._password,
                "grant_type": "password",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            text = await response.text()

            if response.status != 200:
                raise PCSAuthError(f"Login failed HTTP {response.status}: {text[:300]}")

            try:
                data = await response.json(content_type=None)
            except Exception as err:
                raise PCSAuthError(f"Login response is not JSON: {text[:300]}") from err

        token = data.get("access_token")
        if not token:
            raise PCSAuthError("No access_token in login response")

        self._access_token = token

    async def async_get_controllers(self) -> list[dict[str, Any]]:
        if not self._access_token:
            await self.async_login()

        data = await self._async_get_controllers_with_current_token()

        if data is None:
            await self.async_login()
            data = await self._async_get_controllers_with_current_token()

        if data is None:
            raise PCSAuthError("Unable to authorize PCS API request")

        if not isinstance(data, list):
            raise PCSApiError(f"Unexpected controllers response: {data!r}")

        return data

    async def _async_get_controllers_with_current_token(self) -> list[dict[str, Any]] | None:
        url = urljoin(BASE_URL, CONTROLLERS_ENDPOINT)

        async with self._session.get(
            url,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            text = await response.text()

            if response.status == 401:
                return None

            if response.status != 200:
                raise PCSApiError(f"Controllers request failed HTTP {response.status}: {text[:300]}")

            try:
                data = await response.json(content_type=None)
            except Exception as err:
                raise PCSApiError(f"Controllers response is not JSON: {text[:300]}") from err

        return data

    async def async_get_first_controller(self) -> dict[str, Any]:
        controllers = await self.async_get_controllers()

        if not controllers:
            raise PCSApiError("No controllers returned by PCS API")

        for controller in controllers:
            if controller.get("ka") is True:
                return controller

        return controllers[0]
