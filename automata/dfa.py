"""
Deterministic Finite Automaton (DFA) Execution Engine.

Implements M = (Q, Sigma, delta, q0, F) for validating event sequence strings w in Sigma*.
Provides chronological transition validation, reachability analysis, and formal
language verification for any workflow definition.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple, Any

from workflow.specification import (
    WorkflowDefinition,
    get_workflow_definition,
)


class AutomataStatus(str, Enum):
    """Validation outcome for an execution sequence."""
    VALID_COMPLETED = "VALID_COMPLETED"  # All transitions valid and reached terminal state
    VALID_INCOMPLETE = "VALID_INCOMPLETE"  # Valid prefix so far, but not yet terminal
    INVALID = "INVALID"  # Contains an illegal transition or unrecognized event


@dataclass
class ValidationStep:
    """Individual step validation in a workflow trace."""
    step_index: int
    event: str
    timestamp: Optional[str]
    state_before: str
    state_after: Optional[str]
    is_valid: bool
    permitted_events: List[str]
    error_message: Optional[str] = None


@dataclass
class ValidationResult:
    """Aggregated validation output for a workflow execution."""
    case_id: str
    is_valid: bool
    status: AutomataStatus
    final_state: str
    is_terminal: bool
    offending_step: Optional[ValidationStep] = None
    offending_event: Optional[str] = None
    offending_state: Optional[str] = None
    permitted_next: List[str] = field(default_factory=list)
    violation_rule: Optional[str] = None
    trace_length: int = 0
    steps: List[ValidationStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "is_valid": self.is_valid,
            "status": self.status.value,
            "final_state": self.final_state,
            "is_terminal": self.is_terminal,
            "offending_event": self.offending_event,
            "offending_state": self.offending_state,
            "permitted_next": self.permitted_next,
            "violation_rule": self.violation_rule,
            "trace_length": self.trace_length,
        }


def _to_str(s: Any) -> str:
    return s.value if hasattr(s, "value") else str(s)


class DFAEngine:
    """
    Deterministic Finite Automaton execution and validation engine.
    Supports any registered or dynamically created workflow definition.
    """

    def __init__(self, workflow_def: Optional[WorkflowDefinition] = None):
        self.workflow_def = workflow_def or get_workflow_definition("online_orders")
        self.initial_state = _to_str(self.workflow_def.initial_state)
        # Store transitions as string tuples
        self.transitions: Dict[Tuple[str, str], str] = {
            (_to_str(s), ev): _to_str(nxt)
            for (s, ev), nxt in self.workflow_def.transitions.items()
        }
        self.terminal_states: Set[str] = {_to_str(s) for s in self.workflow_def.terminal_states}
        self.alphabet: Set[str] = set(self.workflow_def.alphabet)
        self.all_states: Set[str] = {_to_str(s) for s in self.workflow_def.states}

    def delta(self, state: Any, event: str) -> Optional[str]:
        """Transition function delta: Q x Sigma -> Q (or None if undefined)."""
        s_val = _to_str(state)
        return self.transitions.get((s_val, event))

    def get_permitted_events(self, state: Any) -> List[str]:
        s_val = _to_str(state)
        return [ev for (s, ev) in self.transitions if s == s_val]

    def is_terminal(self, state: Any) -> bool:
        return _to_str(state) in self.terminal_states

    def get_rule_violation_description(self, current_state: Any, event: str) -> str:
        s_val = _to_str(current_state)
        return self.workflow_def.get_violation_description(s_val, event)

    def validate_trace(
        self,
        case_id: str,
        events: List[str],
        timestamps: Optional[List[str]] = None,
    ) -> ValidationResult:
        """
        Validate an execution sequence chronologically through the DFA.
        """
        current_state = self.initial_state
        steps: List[ValidationStep] = []
        is_sequence_valid = True
        offending_step = None
        offending_event = None
        offending_state = None
        violation_rule = None
        permitted_next: List[str] = []

        timestamps_list = timestamps or [None] * len(events)

        for idx, (event, ts) in enumerate(zip(events, timestamps_list)):
            state_before = current_state
            permitted = self.get_permitted_events(state_before)
            next_state = self.delta(state_before, event)

            if next_state is not None:
                step = ValidationStep(
                    step_index=idx + 1,
                    event=event,
                    timestamp=str(ts) if ts is not None else None,
                    state_before=state_before,
                    state_after=next_state,
                    is_valid=True,
                    permitted_events=permitted,
                    error_message=None,
                )
                steps.append(step)
                current_state = next_state
            else:
                is_sequence_valid = False
                error_msg = self.get_rule_violation_description(state_before, event)
                step = ValidationStep(
                    step_index=idx + 1,
                    event=event,
                    timestamp=str(ts) if ts is not None else None,
                    state_before=state_before,
                    state_after=None,
                    is_valid=False,
                    permitted_events=permitted,
                    error_message=error_msg,
                )
                steps.append(step)
                offending_step = step
                offending_event = event
                offending_state = state_before
                violation_rule = error_msg
                permitted_next = permitted
                break

        if not is_sequence_valid:
            status = AutomataStatus.INVALID
            reaches_terminal = False
        else:
            reaches_terminal = self.is_terminal(current_state)
            if reaches_terminal:
                status = AutomataStatus.VALID_COMPLETED
            else:
                status = AutomataStatus.VALID_INCOMPLETE
                permitted_next = self.get_permitted_events(current_state)

        return ValidationResult(
            case_id=case_id,
            is_valid=is_sequence_valid,
            status=status,
            final_state=current_state,
            is_terminal=reaches_terminal,
            offending_step=offending_step,
            offending_event=offending_event,
            offending_state=offending_state,
            permitted_next=permitted_next,
            violation_rule=violation_rule,
            trace_length=len(events),
            steps=steps,
        )

    def compute_reachability(self) -> Dict[str, Any]:
        """
        Perform BFS from initial state to determine reachability and paths.
        Validates that all designated terminal states are reachable from q0.
        """
        visited: Set[str] = {self.initial_state}
        queue: List[str] = [self.initial_state]

        while queue:
            curr = queue.pop(0)
            for (s, ev), nxt in self.transitions.items():
                if s == curr and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        unreachable = self.all_states - visited
        unreachable_terminals = self.terminal_states - visited

        return {
            "all_states_count": len(self.all_states),
            "reachable_states": sorted(list(visited)),
            "unreachable_states": sorted(list(unreachable)),
            "terminal_states": sorted(list(self.terminal_states)),
            "all_terminals_reachable": len(unreachable_terminals) == 0,
            "transition_count": len(self.transitions),
        }

    def get_graph_definition(self) -> Dict[str, Any]:
        """
        Return structured representation of states and directed edges for UI rendering.
        """
        return self.workflow_def.to_graph_data()
