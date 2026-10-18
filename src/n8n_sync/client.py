"""Async public API v1 client. No private /rest endpoints are used."""

from typing import Any
from urllib.parse import quote

import httpx

from .errors import SyncError


class N8nClient:
    def __init__(
        self,
        url: str,
        api_key: str,
        timeout: float = 30,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        base = url.rstrip("/")
        if not base.endswith("/api/v1"):
            base += "/api/v1"
        self.http = httpx.AsyncClient(
            base_url=base + "/",
            headers={"X-N8N-API-KEY": api_key},
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.http.aclose()

    async def request(self, method: str, path: str, **kwargs) -> Any:
        try:
            response = await self.http.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            hint = {
                401: "check API key",
                403: "check API key permissions",
                404: "check instance URL and public API v1 availability",
                429: "rate limited; retry later",
            }.get(status, "check n8n server logs")
            raise SyncError(f"n8n {method} {path}: HTTP {status}; {hint}") from exc
        except httpx.RequestError as exc:
            raise SyncError(
                f"n8n request failed ({type(exc).__name__}); check connectivity"
            ) from exc
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise SyncError("n8n returned invalid JSON; check instance URL") from exc

    async def list_all(self, resource: str) -> list[dict]:
        result, seen = [], set()
        cursor = None
        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            page = await self.request("GET", resource, params=params)
            if (
                not isinstance(page, dict)
                or not isinstance(page.get("data"), list)
                or any(not isinstance(item, dict) for item in page["data"])
            ):
                raise SyncError(f"Unexpected n8n {resource} response")
            result.extend(page["data"])
            cursor = page.get("nextCursor")
            if not cursor:
                return result
            if not isinstance(cursor, str) or cursor in seen:
                raise SyncError("Invalid or repeated pagination cursor")
            seen.add(cursor)

    async def workflows(self) -> list[dict]:
        return await self.list_all("workflows")

    async def save(self, payload: dict, workflow_id: str | None = None) -> dict:
        path = (
            "workflows" if workflow_id is None else "workflows/" + quote(str(workflow_id), safe="")
        )
        result = await self.request("POST" if workflow_id is None else "PUT", path, json=payload)
        if not isinstance(result, dict) or not result.get("id"):
            raise SyncError("n8n save response is missing workflow ID")
        return result

    async def set_active(self, workflow_id: str, active: bool):
        action = "activate" if active else "deactivate"
        await self.request("POST", f"workflows/{quote(str(workflow_id), safe='')}/{action}")

    async def set_tags(self, workflow_id: str, tags: list[dict]):
        await self.request("PUT", f"workflows/{quote(str(workflow_id), safe='')}/tags", json=tags)
