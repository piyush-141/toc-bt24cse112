"""Workflow specification and transition rules."""

from workflow.specification import (
    WorkflowState,
    WorkflowEvent,
    TRANSITIONS,
    TERMINAL_STATES,
    INITIAL_STATE,
    ALPHABET,
    ALL_STATES,
    get_permitted_events,
    is_terminal,
    get_rule_violation_description,
)

__all__ = [
    "WorkflowState",
    "WorkflowEvent",
    "TRANSITIONS",
    "TERMINAL_STATES",
    "INITIAL_STATE",
    "ALPHABET",
    "ALL_STATES",
    "get_permitted_events",
    "is_terminal",
    "get_rule_violation_description",
]
