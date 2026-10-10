"""HHMS WHO ICD-11 lookup service."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from app.config.settings import get_settings
from app.schemas.icd11 import ICD11SearchResult
from app.core.exceptions import ConfigurationException, ExternalServiceException


class ICD11Service:
    """On-demand WHO ICD-11 search with a short-lived token cache."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at = 0.0

    async def search(self, query: str, limit: int = 10) -> list[ICD11SearchResult]:
        query = query.strip()
        if not query:
            return []

        settings = get_settings()
        if not settings.WHO_ICD11_CLIENT_ID or not settings.WHO_ICD11_CLIENT_SECRET:
            raise ConfigurationException("WHO ICD-11 API credentials are not configured.")

        token = await self._get_token(settings)
        url = (
            f"{settings.WHO_ICD11_API_BASE_URL.rstrip('/')}/icd/release/11/"
            f"{quote(settings.WHO_ICD11_RELEASE, safe='')}/mms/search?"
            f"{urlencode({'q': query})}"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Accept-Language": "en",
            "API-Version": "v2",
        }

        payload = await asyncio.to_thread(self._request_json, "GET", url, headers, None)
        return self._parse_results(payload, settings.WHO_ICD11_RELEASE, limit)

    async def _get_token(self, settings: object) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at:
            return self._token

        credentials = (
            f"{settings.WHO_ICD11_CLIENT_ID}:{settings.WHO_ICD11_CLIENT_SECRET}"
        ).encode()
        basic = base64.b64encode(credentials).decode()
        body = urlencode({"grant_type": "client_credentials", "scope": "icdapi_access"}).encode()
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        payload = await asyncio.to_thread(
            self._request_json,
            "POST",
            settings.WHO_ICD11_TOKEN_URL,
            headers,
            body,
        )
        token = payload.get("access_token")
        if not token:
            raise ExternalServiceException("WHO ICD-11 authentication returned no access token.")

        self._token = str(token)
        expires_in = int(payload.get("expires_in", 3600))
        self._token_expires_at = now + max(expires_in - 60, 60)
        return self._token

    @staticmethod
    def _request_json(
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
    ) -> dict:
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise ExternalServiceException("WHO ICD-11 service request failed.") from exc

    @staticmethod
    def _parse_results(
        payload: dict,
        release: str,
        limit: int,
    ) -> list[ICD11SearchResult]:
        rows = payload.get("destinationEntities") or payload.get("entities") or []
        results: list[ICD11SearchResult] = []
        for row in rows[:limit]:
            title = row.get("title") or row.get("label") or ""
            if isinstance(title, dict):
                title = title.get("@value", "")
            code = row.get("theCode") or row.get("code")
            uri = row.get("id") or row.get("@id")
            if title:
                results.append(
                    ICD11SearchResult(
                        code=str(code) if code else None,
                        title=str(title),
                        uri=str(uri) if uri else None,
                        release=release,
                    )
                )
        return results


icd11_service = ICD11Service()

__all__ = ["ICD11SearchResult", "ICD11Service", "icd11_service"]
