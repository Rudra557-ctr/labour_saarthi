import pytest
import yaml

from lmis.common.registry import (
    RegistryError,
    VALID_ROLES,
    VALID_STATUS,
    get_source,
    load_registry,
)


def test_registry_loads_and_validates():
    reg = load_registry()
    assert len(reg) >= 12
    for sid, src in reg.items():
        assert src["source_id"] == sid
        assert src["role"] in VALID_ROLES
        assert src["verification_status"] in VALID_STATUS


def test_licence_gate_rejects_unregistered_source():
    """Acquisition must be impossible for a source that is not registered."""
    with pytest.raises(RegistryError):
        get_source("SOME_SOURCE_WE_NEVER_REGISTERED")


def test_every_source_declares_what_it_actually_publishes():
    """geo_level_available and occ_coding_scheme must be stated, and 'unknown'
    is an allowed honest answer. They must never be silently absent."""
    for sid, src in load_registry().items():
        assert src["geo_level_available"], sid
        assert src["occ_coding_scheme"], sid


def test_sources_yaml_is_valid_yaml():
    from lmis.common.paths import SOURCES_YAML

    doc = yaml.safe_load(SOURCES_YAML.read_text())
    assert doc["schema_version"] == 1
