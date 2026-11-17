"""Automata package for workflow execution validation."""

from automata.dfa import (
    DFAEngine,
    ValidationResult,
    ValidationStep,
    AutomataStatus,
)

__all__ = [
    "DFAEngine",
    "ValidationResult",
    "ValidationStep",
    "AutomataStatus",
]
