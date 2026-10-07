"""Publication layer: enforces the approved Step 7.1 contract.

Nothing here computes an analytical value. It reads what the warehouse already
holds, attaches the mandatory metadata envelope, and refuses to publish anything
the contract does not permit.
"""
from lmis.publish.contract import (
    ContractError,
    PublicationContract,
    build_envelopes,
    build_unavailability_register,
    load_contract,
    resolve_coverage,
)
from lmis.publish.terminology import (
    TerminologyViolation,
    lint_contract,
    lint_derivation_labels,
    lint_envelopes,
    lint_label_catalogue,
)

__all__ = [
    "ContractError",
    "PublicationContract",
    "TerminologyViolation",
    "build_envelopes",
    "build_unavailability_register",
    "lint_contract",
    "lint_derivation_labels",
    "lint_envelopes",
    "lint_label_catalogue",
    "load_contract",
    "resolve_coverage",
]
