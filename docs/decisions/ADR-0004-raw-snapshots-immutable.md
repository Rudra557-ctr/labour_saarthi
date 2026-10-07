# ADR-0004 — Raw snapshots are immutable and checksummed; manifests are version-controlled

- **Status:** Accepted
- **Date:** 2026-10-02
- **Step 0 reference:** layer L2, §14, finding F3

## Context

Verification showed that almost nothing we need has a working API: LGD needs a browser session, data.gov.in
needs a key, NCS and e-Shram are client-rendered, and LGD itself changes monthly. Sources are also unstable
— the NCO volume URLs reported by web search returned HTTP 404 and had to be rediscovered by scraping the
live landing page.

## Decision

- `data/raw/<SOURCE_ID>/<YYYY-MM-DD>/` holds original bytes, **never modified**. `acquire()` refuses to
  overwrite an existing file; changed upstream content lands in a new dated snapshot.
- Every snapshot carries `manifest.json` with sha256, size, HTTP status, licence, publisher and
  `verification_status`.
- Raw bytes are git-ignored; **manifests are committed** — they are the provenance record.
- `make verify` re-hashes every file against its manifest and exits non-zero on mismatch.
- `publication_vintage` stays `None` when the source does not state it. It is never defaulted to the
  download date.

## Consequences

- Results remain reproducible even if a source goes offline mid-competition — a real failure mode.
- Immutability is tested, not merely intended: tests assert that tampering and deletion are both detected.
