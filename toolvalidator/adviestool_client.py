from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(slots=True)
class AdviestoolResult:
    http_status: int | None
    response_json: dict[str, Any] | None
    error_message: str | None = None


@dataclass(slots=True)
class AdviestoolClient:
    base_url: str = "http://localhost:5000"
    timeout: float = 60.0

    def post_current(self, payload: dict[str, Any]) -> AdviestoolResult:
        url = f"{self.base_url.rstrip('/')}/current"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
                parsed = json.loads(response_body) if response_body else {}
                return AdviestoolResult(response.status, parsed)
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            try:
                parsed_error = json.loads(body_text) if body_text else None
            except json.JSONDecodeError:
                parsed_error = None
            if isinstance(parsed_error, dict):
                return AdviestoolResult(exc.code, parsed_error, body_text)
            return AdviestoolResult(exc.code, None, body_text or str(exc))
        except Exception as exc:
            return AdviestoolResult(None, None, str(exc))

