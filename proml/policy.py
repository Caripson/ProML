"""Policy evaluation helpers for ProML."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .parser import PolicyBlock


@dataclass
class PolicyWarning:
    message: str


class PolicyViolation(RuntimeError):
    """Raised when a policy check fails."""


class PolicyEvaluator:
    """Evaluates local policy rules before returning a model output."""

    def __init__(self, block: PolicyBlock | None) -> None:
        self.block = block

    def validate(self) -> List[PolicyWarning]:
        warnings: List[PolicyWarning] = []
        if self.block is None:
            return warnings
        local = self.block.local or {}
        safety_checks = local.get("safety_checks", [])
        if isinstance(safety_checks, list):
            for index, check in enumerate(safety_checks):
                if not isinstance(check, dict):
                    warnings.append(PolicyWarning(f"Safety check #{index + 1} is not a mapping."))
                    continue
                if "ensure" not in check:
                    warnings.append(PolicyWarning(f"Safety check #{index + 1} is missing an 'ensure' key."))
        return warnings

    def enforce(self, output_payload: Dict[str, Any]) -> None:
        """Placeholder enforcement hook. Future work will integrate real validators."""
        # Currently this is a stub; concrete policy types should be enforced here.
        return None
