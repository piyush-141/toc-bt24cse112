"""
Synthetic Event Log Generator for Multi-Domain Process Workflows.

Generates reproducible, realistic workflow traces for:
1. Online Order & Payment Processing
2. Student Course Registration
3. Hospital Patient Appointment
4. Supply Chain B2B Order Management
5. Dynamically created Custom Workflows
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from workflow.specification import (
    WorkflowDefinition,
    get_workflow_definition,
    WorkflowState,
    WorkflowEvent,
    TRANSITIONS,
)


class SyntheticLogGenerator:
    """
    Generates synthetic workflow event logs with controlled ground-truth labels
    for any registered or custom workflow definition.
    """

    def __init__(self, seed: int = 42, workflow_def: Optional[WorkflowDefinition] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.workflow_def = workflow_def or get_workflow_definition("online_orders")

    def generate_dataset(
        self,
        num_cases: int = 1000,
        normal_ratio: float = 0.80,
        rule_anomaly_ratio: float = 0.10,
        behavioral_anomaly_ratio: float = 0.10,
        incomplete_ratio_in_normal: float = 0.05,
        start_date: datetime = datetime(2026, 1, 1, 8, 0, 0),
    ) -> pd.DataFrame:
        """
        Generate complete synthetic event log dataframe.
        """
        self.rng = random.Random(self.seed)

        num_rule = int(num_cases * rule_anomaly_ratio)
        num_behavioral = int(num_cases * behavioral_anomaly_ratio)
        num_normal = num_cases - num_rule - num_behavioral

        case_types: List[str] = (
            ["NORMAL"] * num_normal +
            ["RULE_ANOMALY"] * num_rule +
            ["BEHAVIORAL_ANOMALY"] * num_behavioral
        )
        self.rng.shuffle(case_types)

        all_events: List[Dict[str, Any]] = []
        current_base_time = start_date

        for idx, case_type in enumerate(case_types):
            case_id = f"CASE_{idx + 1:05d}"
            case_start = current_base_time + timedelta(
                minutes=self.rng.randint(0, 43200),
                seconds=self.rng.randint(0, 59)
            )

            if self.workflow_def.id == "online_orders":
                if case_type == "NORMAL":
                    is_incomplete = self.rng.random() < incomplete_ratio_in_normal
                    trace_events = self._generate_normal_trace(case_start, is_incomplete)
                    label = "INCOMPLETE" if is_incomplete else "NORMAL"
                elif case_type == "RULE_ANOMALY":
                    trace_events = self._generate_rule_anomaly_trace(case_start)
                    label = "RULE_ANOMALY"
                else:
                    trace_events = self._generate_behavioral_anomaly_trace(case_start)
                    label = "BEHAVIORAL_ANOMALY"
            else:
                # Generic graph walk simulation for other workflows
                is_incomplete = (case_type == "NORMAL") and (self.rng.random() < incomplete_ratio_in_normal)
                trace_events = self._generate_generic_trace(case_start, case_type, is_incomplete)
                label = "INCOMPLETE" if is_incomplete else case_type

            for ev in trace_events:
                ev["case_id"] = case_id
                ev["ground_truth_anomaly_type"] = label
                all_events.append(ev)

        df = pd.DataFrame(all_events)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")
        df = df.sort_values(by=["timestamp", "case_id"]).reset_index(drop=True)
        return df

    def _generate_generic_trace(
        self, start_time: datetime, case_type: str, is_incomplete: bool
    ) -> List[Dict[str, Any]]:
        """Walk the workflow definition state machine for any arbitrary workflow."""
        curr_time = start_time
        events: List[Dict[str, Any]] = []
        curr_state = self.workflow_def.initial_state

        max_steps = 15
        step_count = 0

        # Choose an early step to guarantee rule anomaly injection before termination
        rule_inject_step = self.rng.randint(1, 2) if case_type == "RULE_ANOMALY" else -1

        while step_count < max_steps:
            step_count += 1
            permitted = self.workflow_def.get_permitted_events(curr_state)
            if not permitted:
                break

            # If rule anomaly, guaranteed injection of illegal event
            if case_type == "RULE_ANOMALY" and step_count >= rule_inject_step:
                illegal_candidates = [e for e in self.workflow_def.alphabet if e not in permitted]
                ev = self.rng.choice(illegal_candidates) if illegal_candidates else "ILLEGAL_EXTERNAL_EVENT"
                events.append({
                    "timestamp": curr_time.isoformat(),
                    "event_type": ev,
                    "state_before": curr_state,
                    "state_after": "INVALID",
                })
                break

            chosen_ev = self.rng.choice(permitted)
            next_state = self.workflow_def.delta(curr_state, chosen_ev)

            # Advance time: if behavioral anomaly, guarantee extreme delay
            if case_type == "BEHAVIORAL_ANOMALY" and step_count == 2:
                curr_time += timedelta(days=self.rng.randint(15, 30))
            else:
                curr_time += timedelta(minutes=self.rng.randint(2, 60), seconds=self.rng.randint(0, 59))

            events.append({
                "timestamp": curr_time.isoformat(),
                "event_type": chosen_ev,
                "state_before": curr_state,
                "state_after": next_state,
            })
            curr_state = next_state

            if self.workflow_def.is_terminal(curr_state):
                break

        if is_incomplete and len(events) > 2:
            events = events[: len(events) - 1]

        return events

    def _generate_normal_trace(self, start_time: datetime, is_incomplete: bool) -> List[Dict[str, Any]]:
        """Generate normal order traces."""
        subtype = self.rng.choices(
            ["standard_delivery", "with_retries", "cancelled_before_payment", "cancelled_with_refund", "return_after_delivery"],
            weights=[0.65, 0.15, 0.08, 0.07, 0.05],
            k=1
        )[0]

        curr_time = start_time
        events: List[Dict[str, Any]] = []
        curr_state = "START"

        def add_event(ev: str):
            nonlocal curr_time, curr_state
            next_state = TRANSITIONS.get((curr_state, ev))
            events.append({
                "timestamp": curr_time.isoformat(),
                "event_type": ev,
                "state_before": curr_state,
                "state_after": next_state if next_state else "UNKNOWN",
            })
            if next_state:
                curr_state = next_state

        add_event("PLACE_ORDER")

        if subtype == "standard_delivery":
            curr_time += timedelta(minutes=self.rng.randint(2, 20))
            add_event("SUBMIT_PAYMENT")
            curr_time += timedelta(seconds=self.rng.randint(5, 60))
            add_event("PAYMENT_SUCCESS")
            curr_time += timedelta(minutes=self.rng.randint(30, 180))
            add_event("PACK_ORDER")
            curr_time += timedelta(hours=self.rng.randint(2, 24))
            add_event("SHIP_ORDER")
            curr_time += timedelta(hours=self.rng.randint(12, 72))
            add_event("DELIVER_ORDER")

        elif subtype == "with_retries":
            num_retries = self.rng.randint(1, 2)
            curr_time += timedelta(minutes=self.rng.randint(2, 15))
            add_event("SUBMIT_PAYMENT")
            for _ in range(num_retries):
                curr_time += timedelta(seconds=self.rng.randint(5, 45))
                add_event("PAYMENT_FAIL")
                curr_time += timedelta(minutes=self.rng.randint(1, 10))
                add_event("RETRY_PAYMENT")

            curr_time += timedelta(seconds=self.rng.randint(5, 45))
            add_event("PAYMENT_SUCCESS")
            curr_time += timedelta(minutes=self.rng.randint(30, 240))
            add_event("PACK_ORDER")
            curr_time += timedelta(hours=self.rng.randint(3, 24))
            add_event("SHIP_ORDER")
            curr_time += timedelta(hours=self.rng.randint(12, 72))
            add_event("DELIVER_ORDER")

        elif subtype == "cancelled_before_payment":
            if self.rng.random() < 0.5:
                curr_time += timedelta(minutes=self.rng.randint(5, 60))
                add_event("CANCEL_ORDER")
            else:
                curr_time += timedelta(minutes=self.rng.randint(2, 10))
                add_event("SUBMIT_PAYMENT")
                curr_time += timedelta(seconds=self.rng.randint(5, 30))
                add_event("PAYMENT_FAIL")
                curr_time += timedelta(minutes=self.rng.randint(2, 30))
                add_event("CANCEL_ORDER")

        elif subtype == "cancelled_with_refund":
            curr_time += timedelta(minutes=self.rng.randint(2, 15))
            add_event("SUBMIT_PAYMENT")
            curr_time += timedelta(seconds=self.rng.randint(5, 45))
            add_event("PAYMENT_SUCCESS")
            if self.rng.random() < 0.5:
                curr_time += timedelta(minutes=self.rng.randint(10, 60))
                add_event("CANCEL_ORDER")
            else:
                curr_time += timedelta(minutes=self.rng.randint(30, 120))
                add_event("PACK_ORDER")
                curr_time += timedelta(minutes=self.rng.randint(10, 60))
                add_event("CANCEL_ORDER")
            curr_time += timedelta(hours=self.rng.randint(1, 12))
            add_event("COMPLETE_REFUND")

        elif subtype == "return_after_delivery":
            curr_time += timedelta(minutes=self.rng.randint(2, 15))
            add_event("SUBMIT_PAYMENT")
            curr_time += timedelta(seconds=self.rng.randint(5, 45))
            add_event("PAYMENT_SUCCESS")
            curr_time += timedelta(minutes=self.rng.randint(30, 180))
            add_event("PACK_ORDER")
            curr_time += timedelta(hours=self.rng.randint(2, 24))
            add_event("SHIP_ORDER")
            curr_time += timedelta(hours=self.rng.randint(12, 72))
            add_event("DELIVER_ORDER")
            curr_time += timedelta(days=self.rng.randint(1, 5))
            add_event("REQUEST_REFUND")
            curr_time += timedelta(hours=self.rng.randint(6, 48))
            add_event("COMPLETE_REFUND")

        if is_incomplete and len(events) > 2:
            events = events[: self.rng.randint(2, len(events) - 1)]

        return events

    def _generate_rule_anomaly_trace(self, start_time: datetime) -> List[Dict[str, Any]]:
        """Traces violating DFA transitions."""
        anomaly_type = self.rng.choice([
            "ship_before_payment", "deliver_before_ship", "pack_without_payment",
            "refund_without_pending", "action_after_delivered", "skip_all_to_deliver"
        ])
        curr_time = start_time
        events: List[Dict[str, Any]] = []

        def add_ev(ev: str, s_before: str, s_after: str):
            nonlocal curr_time
            events.append({
                "timestamp": curr_time.isoformat(),
                "event_type": ev,
                "state_before": s_before,
                "state_after": s_after,
            })

        if anomaly_type == "ship_before_payment":
            add_ev("PLACE_ORDER", "START", "ORDER_PLACED")
            curr_time += timedelta(minutes=5)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            curr_time += timedelta(minutes=10)
            add_ev("SHIP_ORDER", "PAYMENT_PENDING", "INVALID")
        elif anomaly_type == "deliver_before_ship":
            add_ev("PLACE_ORDER", "START", "ORDER_PLACED")
            curr_time += timedelta(minutes=5)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            curr_time += timedelta(seconds=30)
            add_ev("PAYMENT_SUCCESS", "PAYMENT_PENDING", "PAYMENT_CONFIRMED")
            curr_time += timedelta(minutes=45)
            add_ev("PACK_ORDER", "PAYMENT_CONFIRMED", "ORDER_PACKED")
            curr_time += timedelta(hours=2)
            add_ev("DELIVER_ORDER", "ORDER_PACKED", "INVALID")
        elif anomaly_type == "pack_without_payment":
            add_ev("PLACE_ORDER", "START", "ORDER_PLACED")
            curr_time += timedelta(minutes=5)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            curr_time += timedelta(seconds=20)
            add_ev("PAYMENT_FAIL", "PAYMENT_PENDING", "PAYMENT_FAILED")
            curr_time += timedelta(minutes=10)
            add_ev("PACK_ORDER", "PAYMENT_FAILED", "INVALID")
        elif anomaly_type == "refund_without_pending":
            add_ev("PLACE_ORDER", "START", "ORDER_PLACED")
            curr_time += timedelta(minutes=10)
            add_ev("COMPLETE_REFUND", "ORDER_PLACED", "INVALID")
        else:
            add_ev("PLACE_ORDER", "START", "ORDER_PLACED")
            curr_time += timedelta(minutes=10)
            add_ev("DELIVER_ORDER", "ORDER_PLACED", "INVALID")

        return events

    def _generate_behavioral_anomaly_trace(self, start_time: datetime) -> List[Dict[str, Any]]:
        """Formally valid DFA transitions but extreme frequency or timing outliers."""
        pattern = self.rng.choice([
            "excessive_payment_retries", "massive_unusual_delay", "ultra_rapid_bot_execution"
        ])
        curr_time = start_time
        events: List[Dict[str, Any]] = []

        def add_ev(ev: str, s_before: str, s_after: str):
            nonlocal curr_time
            events.append({
                "timestamp": curr_time.isoformat(),
                "event_type": ev,
                "state_before": s_before,
                "state_after": s_after,
            })

        add_ev("PLACE_ORDER", "START", "ORDER_PLACED")

        if pattern == "excessive_payment_retries":
            retry_count = self.rng.randint(6, 11)
            curr_time += timedelta(minutes=2)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            for _ in range(retry_count):
                curr_time += timedelta(seconds=15)
                add_ev("PAYMENT_FAIL", "PAYMENT_PENDING", "PAYMENT_FAILED")
                curr_time += timedelta(seconds=30)
                add_ev("RETRY_PAYMENT", "PAYMENT_FAILED", "PAYMENT_PENDING")
            curr_time += timedelta(seconds=20)
            add_ev("PAYMENT_SUCCESS", "PAYMENT_PENDING", "PAYMENT_CONFIRMED")
            curr_time += timedelta(minutes=60)
            add_ev("PACK_ORDER", "PAYMENT_CONFIRMED", "ORDER_PACKED")
            curr_time += timedelta(hours=6)
            add_ev("SHIP_ORDER", "ORDER_PACKED", "ORDER_SHIPPED")
            curr_time += timedelta(hours=24)
            add_ev("DELIVER_ORDER", "ORDER_SHIPPED", "ORDER_DELIVERED")

        elif pattern == "massive_unusual_delay":
            curr_time += timedelta(days=5)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            curr_time += timedelta(minutes=30)
            add_ev("PAYMENT_SUCCESS", "PAYMENT_PENDING", "PAYMENT_CONFIRMED")
            curr_time += timedelta(days=22)  # 22 days delay!
            add_ev("PACK_ORDER", "PAYMENT_CONFIRMED", "ORDER_PACKED")
            curr_time += timedelta(days=6)
            add_ev("SHIP_ORDER", "ORDER_PACKED", "ORDER_SHIPPED")
            curr_time += timedelta(days=10)
            add_ev("DELIVER_ORDER", "ORDER_SHIPPED", "ORDER_DELIVERED")

        else:  # ultra_rapid_bot_execution
            curr_time += timedelta(milliseconds=200)
            add_ev("SUBMIT_PAYMENT", "ORDER_PLACED", "PAYMENT_PENDING")
            curr_time += timedelta(milliseconds=150)
            add_ev("PAYMENT_SUCCESS", "PAYMENT_PENDING", "PAYMENT_CONFIRMED")
            curr_time += timedelta(milliseconds=200)
            add_ev("PACK_ORDER", "PAYMENT_CONFIRMED", "ORDER_PACKED")
            curr_time += timedelta(milliseconds=300)
            add_ev("SHIP_ORDER", "ORDER_PACKED", "ORDER_SHIPPED")
            curr_time += timedelta(milliseconds=400)
            add_ev("DELIVER_ORDER", "ORDER_SHIPPED", "ORDER_DELIVERED")

        return events
