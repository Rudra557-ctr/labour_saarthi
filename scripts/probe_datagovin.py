"""Extract machine-readable metadata from a data.gov.in resource page.

data.gov.in is a Nuxt SSR application: its resource pages embed a
`window.__NUXT__` payload that contains the resource's real metadata, including
`field_datafile_url` (a direct, keyless file path) and the API resource UUID.
Pulling that out is how we learn what a resource actually offers without an API
key, since the rendered HTML shows no download link and the catalogue cannot be
searched programmatically.

This is a PROBE: it reports what it finds and does not acquire anything.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

UA = {"User-Agent": "LMIS-SIH2026/0.1 (academic labour-market research prototype)"}
BASE = "https://www.data.gov.in/resource/"

FIELDS = (
    "field_data_licence",
    "field_granularity",
    "field_frequency",
    "field_file_format",
    "field_data_time_period_from",
    "field_data_time_period_to",
    "field_is_api_available",
    "field_data_publisher",
    "field_dc_ministry_department_name",
)


def nuxt_blob(html: str) -> str | None:
    m = re.search(r"window\.__NUXT__\s*=\s*(.*?)(?:;\s*)?</script>", html, re.S)
    if not m:
        return None
    return m.group(1).replace(r"/", "/").replace("\\u002F", "/")


def probe(slug: str, session: requests.Session) -> dict:
    url = BASE + slug
    out: dict[str, object] = {"slug": slug, "page_url": url}
    try:
        r = session.get(url, timeout=90)
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    out["http_status"] = r.status_code
    if r.status_code != 200:
        return out
    blob = nuxt_blob(r.text)
    if not blob:
        out["error"] = "no __NUXT__ payload"
        return out
    out["nuxt_chars"] = len(blob)

    datafiles = sorted(
        set(re.findall(r'["\'](https?://[^"\']*?/datafile/[^"\']+?)["\']', blob))
    )
    out["datafile_urls"] = [u[:400] for u in datafiles]
    out["api_resource_uuids"] = sorted(
        set(re.findall(r"api\.data\.gov\.in/resource/([0-9a-f\-]{20,})", blob))
    )
    # Any csv/xlsx filename mentioned, even if the full URL is not recoverable.
    out["file_names"] = sorted(
        set(re.findall(r"([A-Za-z0-9_\-\.]+\.(?:csv|xlsx|xls|json))", blob))
    )[:10]
    for f in FIELDS:
        m = re.search(re.escape(f) + r"\s*=\s*(\[[^\]]{0,300}\]|\{[^}]{0,300}\}|[^;,\n]{0,120})", blob)
        if m:
            out[f] = re.sub(r"\s+", " ", m.group(1))[:200]
    return out


def main() -> None:
    slugs = sys.argv[1:] or [
        "district-wise-total-msme-registered-enterprises-under-udyam-registration-till-last-date",
        "district-wise-enrolled-trained-assessed-certified-placed-under-pmkvy-21-april-2022",
        "state-wise-number-vacancies-mobilised-through-national-career-service-ncs-portal-15-11",
        "local-government-directory-lgd-states",
        "local-government-directory-lgd-sub-districts",
    ]
    s = requests.Session()
    s.headers.update(UA)
    results = [probe(slug, s) for slug in slugs]
    print(json.dumps(results, indent=2)[:12000])
    out = Path(__file__).resolve().parents[1] / "docs" / "datagovin_resource_probe.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
