from __future__ import annotations

import json
import urllib.error
import urllib.request


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str, token: str, user_agent: str = "EZS-Orchestrator/2"):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.user_agent = user_agent

    def request(self, method: str, path: str, payload: dict | None = None, timeout: float = 10.0):
        body = None
        headers = {
            "Accept": "application/json",
            "X-EZScore-Analysis-Token": self.token,
            "User-Agent": self.user_agent,
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                if int(response.status) == 204 or not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ApiError(f"HTTP {exc.code} {path}: {detail[:500]}") from exc
        except Exception as exc:
            raise ApiError(f"{path}: {exc}") from exc

    def get(self, path: str, timeout: float = 10.0):
        return self.request("GET", path, None, timeout)

    def post(self, path: str, payload: dict | None = None, timeout: float = 10.0):
        return self.request("POST", path, payload or {}, timeout)
