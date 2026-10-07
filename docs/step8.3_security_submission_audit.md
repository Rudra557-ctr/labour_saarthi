# Step 8.3 — Security / Submission Audit

Date: 2026-10-06 · **Result: PASS** · No secret value is reproduced in this document.

**Scope:** 203 text files across the repository, excluding `.venv/`, `__pycache__/`, `.git/`,
`data/raw/` and binary assets.

---

## Findings

| Category | Result |
|---|---|
AWS access keys | **PASS** — no match |
Private key blocks (RSA / EC / OpenSSH / PGP) | **PASS** — no match |
API key / access token / client secret assignments | **PASS** — no match |
Password assignments | **PASS** — no match |
Bearer tokens in headers | **PASS** — no match |
Slack / GitHub tokens | **PASS** — no match |
JWTs | **PASS** — no match |
Connection strings with embedded credentials | **PASS** — no match |
`.env` / dotenv files | **PASS** — none present (not even `.env.example`) |
Hard-coded absolute local paths in shipped code | **PASS** — no `/Users/…` in `src/`, `api/`, `config/`, `pyproject.toml` or `Makefile` |
Private / internal URLs in shipped code or config | **PASS** — none |

**No issue found. Nothing was modified.**

---

## Why this repository is low-risk by construction

- **No credential is required to run it.** The warehouse is a local DuckDB file; the API is read-only and
  unauthenticated; the dashboard is static. There is no login, no session, no token.
- **The one credential the project *would* need is deliberately absent.** The data.gov.in PMKVY district
  resource requires a registered API key the project does not hold — recorded as `ACCESS_PENDING` in
  `supply_evidence_matrix` rather than worked around.
- **Paths resolve relatively.** `src/lmis/common/paths.py` derives everything from the module location, so
  no machine-specific path is baked in.
- **The warehouse connection is opened read-only**, so no route can write.

---

## Submission-time items — **MANUAL CHECK**

These are not defects; they are actions required before the repository is published.

| # | Item | Status | Action |
|---|---|---|---|
1 | **No `.git` directory exists** | **MANUAL** | The repository has never been committed, so nothing can have been committed accidentally — a clean starting position. Initialise, verify `.gitignore`, and review `git status` **before** the first commit. |
2 | `.gitignore` present | PASS | Confirm it excludes `.venv/`, `data/raw/`, `data/staging/`, `data/standardized/`, `db/*.duckdb`, `__pycache__/`. **Check `git status` after `git add -A` and before committing.** |
3 | Raw data under `data/raw/` | **MANUAL** | 35 files, 50.5 MB of official PDFs and downloads. They carry no secrets, but check each source's licence before republishing. `config/sources.yaml` records the licence for all 26. |
4 | `db/lmis.duckdb` | **MANUAL** | ~Contains only derived official data. Decide whether to ship it (fast demo start) or require `make reproduce` (clean repo). If shipped, it must be reproducible from the raw snapshots — it is. |
5 | Presenter machine | **MANUAL** | Confirm no personal credentials, browser sessions or unrelated tabs are visible when screen-sharing. |

---

## What was **not** done

- **No file was modified.** The brief permits automatic removal only where an existing repository process
  supports it safely; none was needed.
- **No penetration test.** This is a lightweight secrets and hygiene audit, as scoped.
- **No dependency vulnerability scan.** Out of scope, and no scanner is available in this environment.

---

## Prior security work (Step 7.5, for reference)

A hostile-input review of the running application found and fixed **one reflected XSS** in the dashboard,
where `esc()` escaped `& < > "` but not the single quote and an inline handler interpolated a URL-hash
argument. It was closed in three layers — validate the route argument, escape the delimiter, remove the
interpolation — with a static test asserting that no inline handler interpolates anything but a
compile-time constant.

Also verified then and still true: no CORS exposure, no debug flag, parameterised SQL only, no stack traces
across 12 hostile inputs, path traversal refused, warehouse read-only.

---

**Overall: PASS.** Five manual items remain, all of them ordinary pre-publication hygiene rather than
findings.
