from pathlib import Path

from lmis.ingest.manifest import (
    FileRecord,
    Manifest,
    sha256_file,
    utc_now_iso,
    verify_snapshot,
)


def _snapshot(tmp_path: Path, content: bytes = b"hello lmis") -> Path:
    f = tmp_path / "a.txt"
    f.write_bytes(content)
    man = Manifest(
        source_id="TEST",
        retrieved_at=utc_now_iso(),
        files=[
            FileRecord(
                name="a.txt", url="https://example.invalid/a", sha256=sha256_file(f),
                size_bytes=f.stat().st_size,
            )
        ],
    )
    man.write(tmp_path)
    return tmp_path


def test_verify_snapshot_passes_for_intact_snapshot(tmp_path):
    assert verify_snapshot(_snapshot(tmp_path)) == []


def test_verify_snapshot_detects_modified_bytes(tmp_path):
    """Immutability is only meaningful if tampering is detectable."""
    snap = _snapshot(tmp_path)
    (snap / "a.txt").write_bytes(b"tampered")
    problems = verify_snapshot(snap)
    assert len(problems) == 1 and "sha256 mismatch" in problems[0][1]


def test_verify_snapshot_detects_missing_file(tmp_path):
    snap = _snapshot(tmp_path)
    (snap / "a.txt").unlink()
    assert verify_snapshot(snap) == [("a.txt", "missing")]


def test_publication_vintage_is_not_invented(tmp_path):
    """A vintage the source does not state must stay None, not be set to the
    download date."""
    rec = FileRecord(name="x", url=None, sha256="0" * 64, size_bytes=1)
    assert rec.publication_vintage is None
