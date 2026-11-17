"""
Multi-Domain Workflow Specification Registry for Automata & Process Mining.

Supports standard enterprise domain workflows:
1. Online Order & Payment Processing
2. Student Course Registration Workflow
3. Hospital Patient Appointment & Clinical Workflow
4. Supply Chain B2B Order Management Workflow
5. User-Created Custom Workflows
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, Tuple, List, Optional, Any


@dataclass
class WorkflowDefinition:
    """Formal representation of a business process automaton."""
    id: str
    name: str
    domain: str
    description: str
    initial_state: str
    states: List[str]
    alphabet: List[str]
    terminal_states: List[str]
    transitions: Dict[Tuple[str, str], str]  # (state, event) -> next_state
    layout: Dict[str, Dict[str, int]] = field(default_factory=dict)
    rule_descriptions: Dict[str, str] = field(default_factory=dict)

    def get_permitted_events(self, state: str) -> List[str]:
        return [ev for (s, ev) in self.transitions if s == state]

    def is_terminal(self, state: str) -> bool:
        return state in self.terminal_states

    def delta(self, state: str, event: str) -> Optional[str]:
        return self.transitions.get((state, event))

    def get_violation_description(self, current_state: str, event: str) -> str:
        permitted = self.get_permitted_events(current_state)
        perm_str = ", ".join(f"'{p}'" for p in permitted) if permitted else "None (Terminal State)"

        if current_state in self.terminal_states:
            return (
                f"Terminal state violation: Process reached terminal state '{current_state}'. "
                f"No subsequent events permitted, but received '{event}'."
            )
        if event not in self.alphabet:
            return (
                f"Alphabet violation: Event '{event}' is not in the recognized workflow alphabet Sigma. "
                f"Expected one of [{perm_str}]."
            )
        rule_key = f"{current_state}::{event}"
        if rule_key in self.rule_descriptions:
            return self.rule_descriptions[rule_key]

        return (
            f"Invalid transition: Event '{event}' is illegal from state '{current_state}'. "
            f"Permitted next events: [{perm_str}]."
        )

    def to_graph_data(self) -> Dict[str, Any]:
        """Convert to React Flow compatible nodes and edges."""
        nodes = []
        for s in self.states:
            pos = self.layout.get(s, {"x": 200, "y": 200})
            nodes.append({
                "id": s,
                "data": {
                    "label": s.replace("_", " ").title(),
                    "isInitial": s == self.initial_state,
                    "isTerminal": s in self.terminal_states,
                    "permittedEvents": self.get_permitted_events(s),
                },
                "position": pos,
                "type": "customWorkflowNode",
            })

        edges = []
        for idx, ((src, ev), dst) in enumerate(self.transitions.items()):
            edges.append({
                "id": f"e_{idx}_{src}_{dst}",
                "source": src,
                "target": dst,
                "label": ev,
            })

        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "initialState": self.initial_state,
            "terminalStates": self.terminal_states,
            "alphabet": sorted(list(self.alphabet)),
            "nodes": nodes,
            "edges": edges,
        }


# ==========================================================
# 1. ONLINE ORDER & PAYMENT PROCESSING (DEFAULT)
# ==========================================================
ONLINE_ORDERS_TRANSITIONS: Dict[Tuple[str, str], str] = {
    ("START", "PLACE_ORDER"): "ORDER_PLACED",
    ("ORDER_PLACED", "SUBMIT_PAYMENT"): "PAYMENT_PENDING",
    ("ORDER_PLACED", "CANCEL_ORDER"): "ORDER_CANCELLED",
    ("PAYMENT_PENDING", "PAYMENT_SUCCESS"): "PAYMENT_CONFIRMED",
    ("PAYMENT_PENDING", "PAYMENT_FAIL"): "PAYMENT_FAILED",
    ("PAYMENT_PENDING", "CANCEL_ORDER"): "ORDER_CANCELLED",
    ("PAYMENT_FAILED", "RETRY_PAYMENT"): "PAYMENT_PENDING",
    ("PAYMENT_FAILED", "CANCEL_ORDER"): "ORDER_CANCELLED",
    ("PAYMENT_CONFIRMED", "PACK_ORDER"): "ORDER_PACKED",
    ("PAYMENT_CONFIRMED", "CANCEL_ORDER"): "REFUND_PENDING",
    ("ORDER_PACKED", "SHIP_ORDER"): "ORDER_SHIPPED",
    ("ORDER_PACKED", "CANCEL_ORDER"): "REFUND_PENDING",
    ("ORDER_SHIPPED", "DELIVER_ORDER"): "ORDER_DELIVERED",
    ("ORDER_DELIVERED", "REQUEST_REFUND"): "REFUND_PENDING",
    ("REFUND_PENDING", "COMPLETE_REFUND"): "REFUND_COMPLETED",
}

ONLINE_ORDERS_LAYOUT = {
    "START": {"x": 40, "y": 200},
    "ORDER_PLACED": {"x": 220, "y": 200},
    "PAYMENT_PENDING": {"x": 440, "y": 200},
    "PAYMENT_FAILED": {"x": 440, "y": 340},
    "ORDER_CANCELLED": {"x": 330, "y": 60},
    "PAYMENT_CONFIRMED": {"x": 660, "y": 200},
    "ORDER_PACKED": {"x": 860, "y": 200},
    "REFUND_PENDING": {"x": 760, "y": 60},
    "REFUND_COMPLETED": {"x": 980, "y": 60},
    "ORDER_SHIPPED": {"x": 1060, "y": 200},
    "ORDER_DELIVERED": {"x": 1260, "y": 200},
}

ONLINE_ORDERS_RULE_DESCRIPTIONS = {
    "PAYMENT_PENDING::SHIP_ORDER": "Premature shipping violation: Order cannot be shipped before payment is confirmed and goods are packed.",
    "PAYMENT_PENDING::DELIVER_ORDER": "Premature delivery violation: Order cannot be delivered before payment, packing, and shipping.",
    "ORDER_PACKED::DELIVER_ORDER": "Premature delivery violation: Order cannot be delivered before dispatching via shipment.",
    "ORDER_PLACED::PACK_ORDER": "Premature packing violation: Order cannot be packed before payment is submitted and confirmed.",
    "ORDER_PLACED::SHIP_ORDER": "Premature shipping violation: Order cannot be shipped before payment is processed.",
    "START::SUBMIT_PAYMENT": "Sequence skipped initiation: Payment cannot be submitted before order placement.",
}

ONLINE_ORDERS_DEF = WorkflowDefinition(
    id="online_orders",
    name="Online Payment & Order Processing",
    domain="E-Commerce",
    description="Customer ordering lifecycle from placement, payment verification, fulfillment, delivery, and refunds.",
    initial_state="START",
    states=[
        "START", "ORDER_PLACED", "PAYMENT_PENDING", "PAYMENT_FAILED", "PAYMENT_CONFIRMED",
        "ORDER_PACKED", "ORDER_SHIPPED", "ORDER_DELIVERED", "ORDER_CANCELLED",
        "REFUND_PENDING", "REFUND_COMPLETED"
    ],
    alphabet=[
        "PLACE_ORDER", "SUBMIT_PAYMENT", "PAYMENT_SUCCESS", "PAYMENT_FAIL", "RETRY_PAYMENT",
        "CANCEL_ORDER", "PACK_ORDER", "SHIP_ORDER", "DELIVER_ORDER", "REQUEST_REFUND", "COMPLETE_REFUND"
    ],
    terminal_states=["ORDER_DELIVERED", "ORDER_CANCELLED", "REFUND_COMPLETED"],
    transitions=ONLINE_ORDERS_TRANSITIONS,
    layout=ONLINE_ORDERS_LAYOUT,
    rule_descriptions=ONLINE_ORDERS_RULE_DESCRIPTIONS,
)


# ==========================================================
# 2. STUDENT COURSE REGISTRATION WORKFLOW
# ==========================================================
STUDENT_REG_TRANSITIONS: Dict[Tuple[str, str], str] = {
    ("START", "STUDENT_LOGIN"): "PORTAL_ACTIVE",
    ("PORTAL_ACTIVE", "SELECT_COURSES"): "COURSES_SELECTED",
    ("PORTAL_ACTIVE", "LOGOUT"): "SESSION_ENDED",
    ("COURSES_SELECTED", "CHECK_PREREQUISITES"): "PREREQS_VERIFIED",
    ("COURSES_SELECTED", "DROP_SELECTION"): "PORTAL_ACTIVE",
    ("PREREQS_VERIFIED", "REQUEST_ADVISOR_APPROVAL"): "ADVISOR_PENDING",
    ("PREREQS_VERIFIED", "JOIN_WAITLIST"): "ON_WAITLIST",
    ("ADVISOR_PENDING", "APPROVE_SCHEDULE"): "PAYMENT_REQUIRED",
    ("ADVISOR_PENDING", "REJECT_SCHEDULE"): "COURSES_SELECTED",
    ("PAYMENT_REQUIRED", "PAY_TUITION"): "ENROLLED_CONFIRMED",
    ("PAYMENT_REQUIRED", "FINANCIAL_AID_HOLD"): "PORTAL_ACTIVE",
}

STUDENT_REG_LAYOUT = {
    "START": {"x": 40, "y": 200},
    "PORTAL_ACTIVE": {"x": 220, "y": 200},
    "SESSION_ENDED": {"x": 330, "y": 60},
    "COURSES_SELECTED": {"x": 440, "y": 200},
    "PREREQS_VERIFIED": {"x": 660, "y": 200},
    "ON_WAITLIST": {"x": 660, "y": 340},
    "ADVISOR_PENDING": {"x": 860, "y": 200},
    "PAYMENT_REQUIRED": {"x": 1060, "y": 200},
    "ENROLLED_CONFIRMED": {"x": 1260, "y": 200},
}

STUDENT_REG_DEF = WorkflowDefinition(
    id="student_registration",
    name="Student Course Registration",
    domain="Higher Education",
    description="University course enrollment workflow validating prerequisites, advisor clearance, and tuition payment.",
    initial_state="START",
    states=[
        "START", "PORTAL_ACTIVE", "COURSES_SELECTED", "PREREQS_VERIFIED",
        "ADVISOR_PENDING", "PAYMENT_REQUIRED", "ENROLLED_CONFIRMED",
        "ON_WAITLIST", "SESSION_ENDED"
    ],
    alphabet=[
        "STUDENT_LOGIN", "SELECT_COURSES", "CHECK_PREREQUISITES", "DROP_SELECTION",
        "REQUEST_ADVISOR_APPROVAL", "APPROVE_SCHEDULE", "REJECT_SCHEDULE",
        "PAY_TUITION", "JOIN_WAITLIST", "FINANCIAL_AID_HOLD", "LOGOUT"
    ],
    terminal_states=["ENROLLED_CONFIRMED", "ON_WAITLIST", "SESSION_ENDED"],
    transitions=STUDENT_REG_TRANSITIONS,
    layout=STUDENT_REG_LAYOUT,
)


# ==========================================================
# 3. HOSPITAL PATIENT APPOINTMENT & CLINICAL WORKFLOW
# ==========================================================
HOSPITAL_TRANSITIONS: Dict[Tuple[str, str], str] = {
    ("START", "BOOK_APPOINTMENT"): "APPOINTMENT_REQUESTED",
    ("APPOINTMENT_REQUESTED", "CONFIRM_SLOT"): "BOOKING_CONFIRMED",
    ("APPOINTMENT_REQUESTED", "CANCEL_APPT"): "VISIT_CANCELLED",
    ("BOOKING_CONFIRMED", "PATIENT_CHECKIN"): "TRIAGE_WAITING",
    ("BOOKING_CONFIRMED", "CANCEL_APPT"): "VISIT_CANCELLED",
    ("TRIAGE_WAITING", "RECORD_VITALS"): "DOCTOR_EXAM_PENDING",
    ("DOCTOR_EXAM_PENDING", "PERFORM_EXAM"): "EXAM_IN_PROGRESS",
    ("EXAM_IN_PROGRESS", "ORDER_LAB_TESTS"): "LAB_TESTING",
    ("LAB_TESTING", "SUBMIT_RESULTS"): "EXAM_IN_PROGRESS",
    ("EXAM_IN_PROGRESS", "PRESCRIBE_DISCHARGE"): "PATIENT_DISCHARGED",
}

HOSPITAL_LAYOUT = {
    "START": {"x": 40, "y": 200},
    "APPOINTMENT_REQUESTED": {"x": 220, "y": 200},
    "VISIT_CANCELLED": {"x": 330, "y": 60},
    "BOOKING_CONFIRMED": {"x": 440, "y": 200},
    "TRIAGE_WAITING": {"x": 660, "y": 200},
    "DOCTOR_EXAM_PENDING": {"x": 860, "y": 200},
    "EXAM_IN_PROGRESS": {"x": 1060, "y": 200},
    "LAB_TESTING": {"x": 1060, "y": 340},
    "PATIENT_DISCHARGED": {"x": 1260, "y": 200},
}

HOSPITAL_DEF = WorkflowDefinition(
    id="hospital_appointment",
    name="Hospital Patient Appointment",
    domain="Healthcare & Clinics",
    description="Clinical outpatient journey from booking, check-in, nurse triage, physician exam, and discharge.",
    initial_state="START",
    states=[
        "START", "APPOINTMENT_REQUESTED", "BOOKING_CONFIRMED", "TRIAGE_WAITING",
        "DOCTOR_EXAM_PENDING", "EXAM_IN_PROGRESS", "LAB_TESTING",
        "PATIENT_DISCHARGED", "VISIT_CANCELLED"
    ],
    alphabet=[
        "BOOK_APPOINTMENT", "CONFIRM_SLOT", "CANCEL_APPT", "PATIENT_CHECKIN",
        "RECORD_VITALS", "PERFORM_EXAM", "ORDER_LAB_TESTS", "SUBMIT_RESULTS",
        "PRESCRIBE_DISCHARGE"
    ],
    terminal_states=["PATIENT_DISCHARGED", "VISIT_CANCELLED"],
    transitions=HOSPITAL_TRANSITIONS,
    layout=HOSPITAL_LAYOUT,
)


# ==========================================================
# 4. SUPPLY CHAIN B2B ORDER MANAGEMENT
# ==========================================================
SUPPLY_CHAIN_TRANSITIONS: Dict[Tuple[str, str], str] = {
    ("START", "SUBMIT_PO"): "PO_RECEIVED",
    ("PO_RECEIVED", "CREDIT_CHECK_PASS"): "CREDIT_APPROVED",
    ("PO_RECEIVED", "CREDIT_CHECK_FAIL"): "ORDER_REJECTED",
    ("CREDIT_APPROVED", "ALLOCATE_INVENTORY"): "INVENTORY_RESERVED",
    ("INVENTORY_RESERVED", "DISPATCH_GOODS"): "IN_TRANSIT",
    ("IN_TRANSIT", "CONFIRM_DELIVERY_POD"): "DELIVERED_POD",
    ("DELIVERED_POD", "RAISE_DISPUTE"): "DISPUTE_INVESTIGATION",
    ("DELIVERED_POD", "CLOSE_PO"): "ACCOUNT_SETTLED",
    ("DISPUTE_INVESTIGATION", "SETTLE_CLAIM"): "ACCOUNT_SETTLED",
}

SUPPLY_CHAIN_LAYOUT = {
    "START": {"x": 40, "y": 200},
    "PO_RECEIVED": {"x": 220, "y": 200},
    "ORDER_REJECTED": {"x": 330, "y": 60},
    "CREDIT_APPROVED": {"x": 440, "y": 200},
    "INVENTORY_RESERVED": {"x": 660, "y": 200},
    "IN_TRANSIT": {"x": 860, "y": 200},
    "DELIVERED_POD": {"x": 1060, "y": 200},
    "DISPUTE_INVESTIGATION": {"x": 1060, "y": 340},
    "ACCOUNT_SETTLED": {"x": 1260, "y": 200},
}

SUPPLY_CHAIN_DEF = WorkflowDefinition(
    id="order_management",
    name="Supply Chain B2B Order Management",
    domain="Logistics & Enterprise",
    description="Enterprise purchase order lifecycle with credit checks, inventory reservation, freight dispatch, and proof of delivery.",
    initial_state="START",
    states=[
        "START", "PO_RECEIVED", "CREDIT_APPROVED", "INVENTORY_RESERVED",
        "IN_TRANSIT", "DELIVERED_POD", "DISPUTE_INVESTIGATION", "ACCOUNT_SETTLED", "ORDER_REJECTED"
    ],
    alphabet=[
        "SUBMIT_PO", "CREDIT_CHECK_PASS", "CREDIT_CHECK_FAIL", "ALLOCATE_INVENTORY",
        "DISPATCH_GOODS", "CONFIRM_DELIVERY_POD", "RAISE_DISPUTE", "SETTLE_CLAIM", "CLOSE_PO"
    ],
    terminal_states=["ACCOUNT_SETTLED", "ORDER_REJECTED"],
    transitions=SUPPLY_CHAIN_TRANSITIONS,
    layout=SUPPLY_CHAIN_LAYOUT,
)


# ==========================================================
# GLOBAL REGISTRY & FACTORY
# ==========================================================
WORKFLOW_REGISTRY: Dict[str, WorkflowDefinition] = {
    "online_orders": ONLINE_ORDERS_DEF,
    "student_registration": STUDENT_REG_DEF,
    "hospital_appointment": HOSPITAL_DEF,
    "order_management": SUPPLY_CHAIN_DEF,
}


def get_workflow_definition(workflow_id: str = "online_orders") -> WorkflowDefinition:
    """Retrieve workflow by ID, defaulting to online_orders."""
    return WORKFLOW_REGISTRY.get(workflow_id, ONLINE_ORDERS_DEF)


def register_custom_workflow(
    workflow_id: str,
    name: str,
    domain: str,
    description: str,
    initial_state: str,
    states: List[str],
    alphabet: List[str],
    terminal_states: List[str],
    transitions_list: List[Dict[str, str]],
) -> WorkflowDefinition:
    """
    Dynamically register a new custom workflow.
    transitions_list: [{'from': 'A', 'event': 'E', 'to': 'B'}]
    """
    transitions_dict = {}
    for item in transitions_list:
        transitions_dict[(item["from"], item["event"])] = item["to"]

    # Calculate automatic grid layout
    layout = {}
    x_step = 220
    for idx, s in enumerate(states):
        col = idx % 5
        row = idx // 5
        layout[s] = {"x": 40 + col * x_step, "y": 60 + row * 160}

    w_def = WorkflowDefinition(
        id=workflow_id,
        name=name,
        domain=domain,
        description=description,
        initial_state=initial_state,
        states=states,
        alphabet=alphabet,
        terminal_states=terminal_states,
        transitions=transitions_dict,
        layout=layout,
    )
    WORKFLOW_REGISTRY[workflow_id] = w_def
    return w_def


def list_available_workflows() -> List[Dict[str, Any]]:
    """List all registered workflows with summary metadata."""
    return [
        {
            "id": w.id,
            "name": w.name,
            "domain": w.domain,
            "description": w.description,
            "state_count": len(w.states),
            "event_count": len(w.alphabet),
            "transition_count": len(w.transitions),
        }
        for w in WORKFLOW_REGISTRY.values()
    ]


# Backward compatibility aliases for existing modules
WorkflowState = Enum("WorkflowState", {s: s for s in ONLINE_ORDERS_DEF.states})
WorkflowEvent = Enum("WorkflowEvent", {e: e for e in ONLINE_ORDERS_DEF.alphabet})
TRANSITIONS = ONLINE_ORDERS_DEF.transitions
INITIAL_STATE = ONLINE_ORDERS_DEF.initial_state
TERMINAL_STATES = set(ONLINE_ORDERS_DEF.terminal_states)
ALPHABET = set(ONLINE_ORDERS_DEF.alphabet)
ALL_STATES = set(ONLINE_ORDERS_DEF.states)


def get_permitted_events(state: Any) -> List[str]:
    s_val = state.value if hasattr(state, "value") else str(state)
    return ONLINE_ORDERS_DEF.get_permitted_events(s_val)


def is_terminal(state: Any) -> bool:
    s_val = state.value if hasattr(state, "value") else str(state)
    return ONLINE_ORDERS_DEF.is_terminal(s_val)


def get_rule_violation_description(current_state: Any, event: str) -> str:
    s_val = current_state.value if hasattr(current_state, "value") else str(current_state)
    return ONLINE_ORDERS_DEF.get_violation_description(s_val, event)
