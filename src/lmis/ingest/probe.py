"""Access probes for sources whose availability is still unverified.

A probe answers exactly one question: "can this be acquired programmatically,
and at what granularity?" It records the honest answer, including BLOCKED and
UNKNOWN. A probe never guesses a URL pattern into existence and never reports
success it did not observe.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

import requests

UA = {"User-Agent": "LMIS-SIH2026/0.1 (academic labour-market research prototype)"}
Verdict = Literal["ACCESSIBLE", "BLOCKED_JS", "BLOCKED_AUTH", "NOT_FOUND", "ERROR", "PARTIAL"]


@dataclass
class ProbeResult:
    probe_id: str
    question: str
    url: str
    http_status: int | None
    verdict: Verdict
    evidence: str
    implication: str

    def as_dict(self) -> dict:
        return asdict(self)


def _get(url: str, timeout: int = 60) -> tuple[int | None, str, str]:
    try:
        r = requests.get(url, timeout=timeout, headers=UA, allow_redirects=True)
    except Exception as exc:
        return None, "", f"{type(exc).__name__}: {exc}"
    return r.status_code, r.text if "text" in r.headers.get("content-type", "") else "", ""


def looks_like_js_app(html: str) -> bool:
    """A server-rendered report page has tables; an SPA shell has scripts and no
    data rows. Used to distinguish 'no data' from 'data is client-rendered'."""
    if not html:
        return False
    has_rows = len(re.findall(r"<tr", html, re.I)) > 3
    has_app_root = bool(re.search(r'id="(root|app)"|__NEXT_DATA__|ng-app|dwr/', html, re.I))
    heavy_script = html.lower().count("<script") > 10
    return (not has_rows) and (has_app_root or heavy_script)
