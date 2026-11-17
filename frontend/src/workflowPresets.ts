import { WorkflowGraphData } from "./types";

export const PRESET_WORKFLOWS: Record<string, WorkflowGraphData> = {
  online_orders: {
    id: "online_orders",
    name: "Online Payment & Order Processing",
    domain: "E-Commerce",
    description: "Customer ordering lifecycle from placement, payment verification, fulfillment, delivery, and refunds.",
    initialState: "START",
    terminalStates: ["ORDER_DELIVERED", "ORDER_CANCELLED", "REFUND_COMPLETED"],
    states: [
      "START", "ORDER_PLACED", "PAYMENT_PENDING", "PAYMENT_FAILED", "PAYMENT_CONFIRMED",
      "ORDER_PACKED", "ORDER_SHIPPED", "ORDER_DELIVERED", "ORDER_CANCELLED",
      "REFUND_PENDING", "REFUND_COMPLETED"
    ],
    alphabet: [
      "PLACE_ORDER", "SUBMIT_PAYMENT", "PAYMENT_SUCCESS", "PAYMENT_FAIL", "RETRY_PAYMENT",
      "CANCEL_ORDER", "PACK_ORDER", "SHIP_ORDER", "DELIVER_ORDER", "REQUEST_REFUND", "COMPLETE_REFUND"
    ],
    reachability: {
      all_states_count: 11,
      reachable_states: [
        "START", "ORDER_PLACED", "PAYMENT_PENDING", "PAYMENT_FAILED", "PAYMENT_CONFIRMED",
        "ORDER_PACKED", "ORDER_SHIPPED", "ORDER_DELIVERED", "ORDER_CANCELLED",
        "REFUND_PENDING", "REFUND_COMPLETED"
      ],
      unreachable_states: [],
      terminal_states: ["ORDER_DELIVERED", "ORDER_CANCELLED", "REFUND_COMPLETED"],
      all_terminals_reachable: true,
      is_valid_dfa: true,
      transition_count: 15,
    },
    nodes: [
      { id: "START", type: "customWorkflowNode", position: { x: 30, y: 180 }, data: { label: "Start", isInitial: true, isTerminal: false, permittedEvents: ["PLACE_ORDER"] } },
      { id: "ORDER_PLACED", type: "customWorkflowNode", position: { x: 230, y: 180 }, data: { label: "Order Placed", isInitial: false, isTerminal: false, permittedEvents: ["SUBMIT_PAYMENT", "CANCEL_ORDER"] } },
      { id: "PAYMENT_PENDING", type: "customWorkflowNode", position: { x: 440, y: 180 }, data: { label: "Payment Pending", isInitial: false, isTerminal: false, permittedEvents: ["PAYMENT_SUCCESS", "PAYMENT_FAIL", "CANCEL_ORDER"] } },
      { id: "PAYMENT_FAILED", type: "customWorkflowNode", position: { x: 440, y: 340 }, data: { label: "Payment Failed", isInitial: false, isTerminal: false, permittedEvents: ["RETRY_PAYMENT", "CANCEL_ORDER"] } },
      { id: "ORDER_CANCELLED", type: "customWorkflowNode", position: { x: 340, y: 30 }, data: { label: "Order Cancelled", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "PAYMENT_CONFIRMED", type: "customWorkflowNode", position: { x: 660, y: 180 }, data: { label: "Payment Confirmed", isInitial: false, isTerminal: false, permittedEvents: ["PACK_ORDER", "CANCEL_ORDER"] } },
      { id: "ORDER_PACKED", type: "customWorkflowNode", position: { x: 880, y: 180 }, data: { label: "Order Packed", isInitial: false, isTerminal: false, permittedEvents: ["SHIP_ORDER", "CANCEL_ORDER"] } },
      { id: "REFUND_PENDING", type: "customWorkflowNode", position: { x: 770, y: 30 }, data: { label: "Refund Pending", isInitial: false, isTerminal: false, permittedEvents: ["COMPLETE_REFUND"] } },
      { id: "REFUND_COMPLETED", type: "customWorkflowNode", position: { x: 990, y: 30 }, data: { label: "Refund Completed", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "ORDER_SHIPPED", type: "customWorkflowNode", position: { x: 1100, y: 180 }, data: { label: "Order Shipped", isInitial: false, isTerminal: false, permittedEvents: ["DELIVER_ORDER"] } },
      { id: "ORDER_DELIVERED", type: "customWorkflowNode", position: { x: 1320, y: 180 }, data: { label: "Order Delivered", isInitial: false, isTerminal: true, permittedEvents: ["REQUEST_REFUND"] } },
    ],
    edges: [
      { id: "e1", source: "START", target: "ORDER_PLACED", label: "PLACE_ORDER" },
      { id: "e2", source: "ORDER_PLACED", target: "PAYMENT_PENDING", label: "SUBMIT_PAYMENT" },
      { id: "e3", source: "ORDER_PLACED", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
      { id: "e4", source: "PAYMENT_PENDING", target: "PAYMENT_CONFIRMED", label: "PAYMENT_SUCCESS" },
      { id: "e5", source: "PAYMENT_PENDING", target: "PAYMENT_FAILED", label: "PAYMENT_FAIL" },
      { id: "e6", source: "PAYMENT_PENDING", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
      { id: "e7", source: "PAYMENT_FAILED", target: "PAYMENT_PENDING", label: "RETRY_PAYMENT" },
      { id: "e8", source: "PAYMENT_FAILED", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
      { id: "e9", source: "PAYMENT_CONFIRMED", target: "ORDER_PACKED", label: "PACK_ORDER" },
      { id: "e10", source: "PAYMENT_CONFIRMED", target: "REFUND_PENDING", label: "CANCEL_ORDER" },
      { id: "e11", source: "ORDER_PACKED", target: "ORDER_SHIPPED", label: "SHIP_ORDER" },
      { id: "e12", source: "ORDER_PACKED", target: "REFUND_PENDING", label: "CANCEL_ORDER" },
      { id: "e13", source: "ORDER_SHIPPED", target: "ORDER_DELIVERED", label: "DELIVER_ORDER" },
      { id: "e14", source: "ORDER_DELIVERED", target: "REFUND_PENDING", label: "REQUEST_REFUND" },
      { id: "e15", source: "REFUND_PENDING", target: "REFUND_COMPLETED", label: "COMPLETE_REFUND" },
    ],
  },

  student_registration: {
    id: "student_registration",
    name: "Student Course Registration",
    domain: "Higher Education",
    description: "University course enrollment workflow validating prerequisites, advisor clearance, and tuition payment.",
    initialState: "START",
    terminalStates: ["ENROLLED_CONFIRMED", "ON_WAITLIST", "SESSION_ENDED"],
    states: [
      "START", "PORTAL_ACTIVE", "COURSES_SELECTED", "PREREQS_VERIFIED",
      "ADVISOR_PENDING", "PAYMENT_REQUIRED", "ENROLLED_CONFIRMED",
      "ON_WAITLIST", "SESSION_ENDED"
    ],
    alphabet: [
      "STUDENT_LOGIN", "SELECT_COURSES", "CHECK_PREREQUISITES", "DROP_SELECTION",
      "REQUEST_ADVISOR_APPROVAL", "APPROVE_SCHEDULE", "REJECT_SCHEDULE",
      "PAY_TUITION", "JOIN_WAITLIST", "FINANCIAL_AID_HOLD", "LOGOUT"
    ],
    reachability: {
      all_states_count: 9,
      reachable_states: [
        "START", "PORTAL_ACTIVE", "COURSES_SELECTED", "PREREQS_VERIFIED",
        "ADVISOR_PENDING", "PAYMENT_REQUIRED", "ENROLLED_CONFIRMED",
        "ON_WAITLIST", "SESSION_ENDED"
      ],
      unreachable_states: [],
      terminal_states: ["ENROLLED_CONFIRMED", "ON_WAITLIST", "SESSION_ENDED"],
      all_terminals_reachable: true,
      is_valid_dfa: true,
      transition_count: 11,
    },
    nodes: [
      { id: "START", type: "customWorkflowNode", position: { x: 30, y: 160 }, data: { label: "Start", isInitial: true, isTerminal: false, permittedEvents: ["STUDENT_LOGIN"] } },
      { id: "PORTAL_ACTIVE", type: "customWorkflowNode", position: { x: 230, y: 160 }, data: { label: "Portal Active", isInitial: false, isTerminal: false, permittedEvents: ["SELECT_COURSES", "LOGOUT"] } },
      { id: "SESSION_ENDED", type: "customWorkflowNode", position: { x: 230, y: 30 }, data: { label: "Session Ended", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "COURSES_SELECTED", type: "customWorkflowNode", position: { x: 440, y: 160 }, data: { label: "Courses Selected", isInitial: false, isTerminal: false, permittedEvents: ["CHECK_PREREQUISITES", "DROP_SELECTION"] } },
      { id: "PREREQS_VERIFIED", type: "customWorkflowNode", position: { x: 650, y: 160 }, data: { label: "Prereqs Verified", isInitial: false, isTerminal: false, permittedEvents: ["REQUEST_ADVISOR_APPROVAL", "JOIN_WAITLIST"] } },
      { id: "ON_WAITLIST", type: "customWorkflowNode", position: { x: 650, y: 310 }, data: { label: "On Waitlist", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "ADVISOR_PENDING", type: "customWorkflowNode", position: { x: 860, y: 160 }, data: { label: "Advisor Pending", isInitial: false, isTerminal: false, permittedEvents: ["APPROVE_SCHEDULE", "REJECT_SCHEDULE"] } },
      { id: "PAYMENT_REQUIRED", type: "customWorkflowNode", position: { x: 1070, y: 160 }, data: { label: "Payment Required", isInitial: false, isTerminal: false, permittedEvents: ["PAY_TUITION", "FINANCIAL_AID_HOLD"] } },
      { id: "ENROLLED_CONFIRMED", type: "customWorkflowNode", position: { x: 1280, y: 160 }, data: { label: "Enrolled Confirmed", isInitial: false, isTerminal: true, permittedEvents: [] } },
    ],
    edges: [
      { id: "sr1", source: "START", target: "PORTAL_ACTIVE", label: "STUDENT_LOGIN" },
      { id: "sr2", source: "PORTAL_ACTIVE", target: "COURSES_SELECTED", label: "SELECT_COURSES" },
      { id: "sr3", source: "PORTAL_ACTIVE", target: "SESSION_ENDED", label: "LOGOUT" },
      { id: "sr4", source: "COURSES_SELECTED", target: "PREREQS_VERIFIED", label: "CHECK_PREREQUISITES" },
      { id: "sr5", source: "COURSES_SELECTED", target: "PORTAL_ACTIVE", label: "DROP_SELECTION" },
      { id: "sr6", source: "PREREQS_VERIFIED", target: "ADVISOR_PENDING", label: "REQUEST_ADVISOR_APPROVAL" },
      { id: "sr7", source: "PREREQS_VERIFIED", target: "ON_WAITLIST", label: "JOIN_WAITLIST" },
      { id: "sr8", source: "ADVISOR_PENDING", target: "PAYMENT_REQUIRED", label: "APPROVE_SCHEDULE" },
      { id: "sr9", source: "ADVISOR_PENDING", target: "COURSES_SELECTED", label: "REJECT_SCHEDULE" },
      { id: "sr10", source: "PAYMENT_REQUIRED", target: "ENROLLED_CONFIRMED", label: "PAY_TUITION" },
      { id: "sr11", source: "PAYMENT_REQUIRED", target: "PORTAL_ACTIVE", label: "FINANCIAL_AID_HOLD" },
    ],
  },

  hospital_appointment: {
    id: "hospital_appointment",
    name: "Hospital Patient Appointment",
    domain: "Healthcare & Clinics",
    description: "Clinical outpatient journey from booking, check-in, nurse triage, physician exam, and discharge.",
    initialState: "START",
    terminalStates: ["PATIENT_DISCHARGED", "VISIT_CANCELLED"],
    states: [
      "START", "APPOINTMENT_REQUESTED", "BOOKING_CONFIRMED", "TRIAGE_WAITING",
      "DOCTOR_EXAM_PENDING", "EXAM_IN_PROGRESS", "LAB_TESTING",
      "PATIENT_DISCHARGED", "VISIT_CANCELLED"
    ],
    alphabet: [
      "BOOK_APPOINTMENT", "CONFIRM_SLOT", "CANCEL_APPT", "PATIENT_CHECKIN",
      "RECORD_VITALS", "PERFORM_EXAM", "ORDER_LAB_TESTS", "SUBMIT_RESULTS",
      "PRESCRIBE_DISCHARGE"
    ],
    reachability: {
      all_states_count: 9,
      reachable_states: [
        "START", "APPOINTMENT_REQUESTED", "BOOKING_CONFIRMED", "TRIAGE_WAITING",
        "DOCTOR_EXAM_PENDING", "EXAM_IN_PROGRESS", "LAB_TESTING",
        "PATIENT_DISCHARGED", "VISIT_CANCELLED"
      ],
      unreachable_states: [],
      terminal_states: ["PATIENT_DISCHARGED", "VISIT_CANCELLED"],
      all_terminals_reachable: true,
      is_valid_dfa: true,
      transition_count: 10,
    },
    nodes: [
      { id: "START", type: "customWorkflowNode", position: { x: 30, y: 160 }, data: { label: "Start", isInitial: true, isTerminal: false, permittedEvents: ["BOOK_APPOINTMENT"] } },
      { id: "APPOINTMENT_REQUESTED", type: "customWorkflowNode", position: { x: 230, y: 160 }, data: { label: "Appointment Requested", isInitial: false, isTerminal: false, permittedEvents: ["CONFIRM_SLOT", "CANCEL_APPT"] } },
      { id: "VISIT_CANCELLED", type: "customWorkflowNode", position: { x: 330, y: 30 }, data: { label: "Visit Cancelled", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "BOOKING_CONFIRMED", type: "customWorkflowNode", position: { x: 440, y: 160 }, data: { label: "Booking Confirmed", isInitial: false, isTerminal: false, permittedEvents: ["PATIENT_CHECKIN", "CANCEL_APPT"] } },
      { id: "TRIAGE_WAITING", type: "customWorkflowNode", position: { x: 650, y: 160 }, data: { label: "Triage Waiting", isInitial: false, isTerminal: false, permittedEvents: ["RECORD_VITALS"] } },
      { id: "DOCTOR_EXAM_PENDING", type: "customWorkflowNode", position: { x: 860, y: 160 }, data: { label: "Doctor Exam Pending", isInitial: false, isTerminal: false, permittedEvents: ["PERFORM_EXAM"] } },
      { id: "EXAM_IN_PROGRESS", type: "customWorkflowNode", position: { x: 1070, y: 160 }, data: { label: "Exam In Progress", isInitial: false, isTerminal: false, permittedEvents: ["ORDER_LAB_TESTS", "PRESCRIBE_DISCHARGE"] } },
      { id: "LAB_TESTING", type: "customWorkflowNode", position: { x: 1070, y: 310 }, data: { label: "Lab Testing", isInitial: false, isTerminal: false, permittedEvents: ["SUBMIT_RESULTS"] } },
      { id: "PATIENT_DISCHARGED", type: "customWorkflowNode", position: { x: 1290, y: 160 }, data: { label: "Patient Discharged", isInitial: false, isTerminal: true, permittedEvents: [] } },
    ],
    edges: [
      { id: "h1", source: "START", target: "APPOINTMENT_REQUESTED", label: "BOOK_APPOINTMENT" },
      { id: "h2", source: "APPOINTMENT_REQUESTED", target: "BOOKING_CONFIRMED", label: "CONFIRM_SLOT" },
      { id: "h3", source: "APPOINTMENT_REQUESTED", target: "VISIT_CANCELLED", label: "CANCEL_APPT" },
      { id: "h4", source: "BOOKING_CONFIRMED", target: "TRIAGE_WAITING", label: "PATIENT_CHECKIN" },
      { id: "h5", source: "BOOKING_CONFIRMED", target: "VISIT_CANCELLED", label: "CANCEL_APPT" },
      { id: "h6", source: "TRIAGE_WAITING", target: "DOCTOR_EXAM_PENDING", label: "RECORD_VITALS" },
      { id: "h7", source: "DOCTOR_EXAM_PENDING", target: "EXAM_IN_PROGRESS", label: "PERFORM_EXAM" },
      { id: "h8", source: "EXAM_IN_PROGRESS", target: "LAB_TESTING", label: "ORDER_LAB_TESTS" },
      { id: "h9", source: "LAB_TESTING", target: "EXAM_IN_PROGRESS", label: "SUBMIT_RESULTS" },
      { id: "h10", source: "EXAM_IN_PROGRESS", target: "PATIENT_DISCHARGED", label: "PRESCRIBE_DISCHARGE" },
    ],
  },

  order_management: {
    id: "order_management",
    name: "Supply Chain B2B Order Management",
    domain: "Logistics & Enterprise",
    description: "Enterprise purchase order lifecycle with credit checks, inventory reservation, freight dispatch, and proof of delivery.",
    initialState: "START",
    terminalStates: ["ACCOUNT_SETTLED", "ORDER_REJECTED"],
    states: [
      "START", "PO_RECEIVED", "CREDIT_APPROVED", "INVENTORY_RESERVED",
      "IN_TRANSIT", "DELIVERED_POD", "DISPUTE_INVESTIGATION", "ACCOUNT_SETTLED", "ORDER_REJECTED"
    ],
    alphabet: [
      "SUBMIT_PO", "CREDIT_CHECK_PASS", "CREDIT_CHECK_FAIL", "ALLOCATE_INVENTORY",
      "DISPATCH_GOODS", "CONFIRM_DELIVERY_POD", "RAISE_DISPUTE", "SETTLE_CLAIM", "CLOSE_PO"
    ],
    reachability: {
      all_states_count: 9,
      reachable_states: [
        "START", "PO_RECEIVED", "CREDIT_APPROVED", "INVENTORY_RESERVED",
        "IN_TRANSIT", "DELIVERED_POD", "DISPUTE_INVESTIGATION", "ACCOUNT_SETTLED", "ORDER_REJECTED"
      ],
      unreachable_states: [],
      terminal_states: ["ACCOUNT_SETTLED", "ORDER_REJECTED"],
      all_terminals_reachable: true,
      is_valid_dfa: true,
      transition_count: 9,
    },
    nodes: [
      { id: "START", type: "customWorkflowNode", position: { x: 30, y: 160 }, data: { label: "Start", isInitial: true, isTerminal: false, permittedEvents: ["SUBMIT_PO"] } },
      { id: "PO_RECEIVED", type: "customWorkflowNode", position: { x: 230, y: 160 }, data: { label: "PO Received", isInitial: false, isTerminal: false, permittedEvents: ["CREDIT_CHECK_PASS", "CREDIT_CHECK_FAIL"] } },
      { id: "ORDER_REJECTED", type: "customWorkflowNode", position: { x: 230, y: 30 }, data: { label: "Order Rejected", isInitial: false, isTerminal: true, permittedEvents: [] } },
      { id: "CREDIT_APPROVED", type: "customWorkflowNode", position: { x: 440, y: 160 }, data: { label: "Credit Approved", isInitial: false, isTerminal: false, permittedEvents: ["ALLOCATE_INVENTORY"] } },
      { id: "INVENTORY_RESERVED", type: "customWorkflowNode", position: { x: 650, y: 160 }, data: { label: "Inventory Reserved", isInitial: false, isTerminal: false, permittedEvents: ["DISPATCH_GOODS"] } },
      { id: "IN_TRANSIT", type: "customWorkflowNode", position: { x: 860, y: 160 }, data: { label: "In Transit", isInitial: false, isTerminal: false, permittedEvents: ["CONFIRM_DELIVERY_POD"] } },
      { id: "DELIVERED_POD", type: "customWorkflowNode", position: { x: 1070, y: 160 }, data: { label: "Delivered POD", isInitial: false, isTerminal: false, permittedEvents: ["RAISE_DISPUTE", "CLOSE_PO"] } },
      { id: "DISPUTE_INVESTIGATION", type: "customWorkflowNode", position: { x: 1070, y: 310 }, data: { label: "Dispute Investigation", isInitial: false, isTerminal: false, permittedEvents: ["SETTLE_CLAIM"] } },
      { id: "ACCOUNT_SETTLED", type: "customWorkflowNode", position: { x: 1290, y: 160 }, data: { label: "Account Settled", isInitial: false, isTerminal: true, permittedEvents: [] } },
    ],
    edges: [
      { id: "om1", source: "START", target: "PO_RECEIVED", label: "SUBMIT_PO" },
      { id: "om2", source: "PO_RECEIVED", target: "CREDIT_APPROVED", label: "CREDIT_CHECK_PASS" },
      { id: "om3", source: "PO_RECEIVED", target: "ORDER_REJECTED", label: "CREDIT_CHECK_FAIL" },
      { id: "om4", source: "CREDIT_APPROVED", target: "INVENTORY_RESERVED", label: "ALLOCATE_INVENTORY" },
      { id: "om5", source: "INVENTORY_RESERVED", target: "IN_TRANSIT", label: "DISPATCH_GOODS" },
      { id: "om6", source: "IN_TRANSIT", target: "DELIVERED_POD", label: "CONFIRM_DELIVERY_POD" },
      { id: "om7", source: "DELIVERED_POD", target: "DISPUTE_INVESTIGATION", label: "RAISE_DISPUTE" },
      { id: "om8", source: "DELIVERED_POD", target: "ACCOUNT_SETTLED", label: "CLOSE_PO" },
      { id: "om9", source: "DISPUTE_INVESTIGATION", target: "ACCOUNT_SETTLED", label: "SETTLE_CLAIM" },
    ],
  },
};

export const TEMPLATE_EXAMPLES = [
  {
    name: "Customer Support Ticket",
    domain: "IT Services",
    states: "START, OPEN, IN_TRIAGE, ESCALATED, RESOLVED, CLOSED",
    events: "CREATE_TICKET, ASSIGN_AGENT, ESCALATE, PROVIDE_FIX, CONFIRM_RESOLUTION",
    initial: "START",
    terminals: "CLOSED",
    transitions:
      "START, CREATE_TICKET, OPEN\nOPEN, ASSIGN_AGENT, IN_TRIAGE\nIN_TRIAGE, ESCALATE, ESCALATED\nIN_TRIAGE, PROVIDE_FIX, RESOLVED\nESCALATED, PROVIDE_FIX, RESOLVED\nRESOLVED, CONFIRM_RESOLUTION, CLOSED",
  },
  {
    name: "Expense Report Approval",
    domain: "Corporate Finance",
    states: "START, DRAFT, SUBMITTED, MANAGER_APPROVED, AUDIT_FLAGGED, REIMBURSED, REJECTED",
    events: "CREATE_EXPENSE, SUBMIT_REPORT, APPROVE_MANAGER, FLAG_AUDIT, REIMBURSE, REJECT",
    initial: "START",
    terminals: "REIMBURSED, REJECTED",
    transitions:
      "START, CREATE_EXPENSE, DRAFT\nDRAFT, SUBMIT_REPORT, SUBMITTED\nSUBMITTED, APPROVE_MANAGER, MANAGER_APPROVED\nSUBMITTED, REJECT, REJECTED\nMANAGER_APPROVED, FLAG_AUDIT, AUDIT_FLAGGED\nMANAGER_APPROVED, REIMBURSE, REIMBURSED\nAUDIT_FLAGGED, REIMBURSE, REIMBURSED\nAUDIT_FLAGGED, REJECT, REJECTED",
  },
  {
    name: "Code Review & CI/CD Pipeline",
    domain: "Software Engineering",
    states: "START, PR_OPENED, TESTS_PASSED, REVIEW_APPROVED, MERGED, BUILD_FAILED",
    events: "OPEN_PR, RUN_TESTS, FAIL_TESTS, APPROVE_PR, MERGE_CODE",
    initial: "START",
    terminals: "MERGED, BUILD_FAILED",
    transitions:
      "START, OPEN_PR, PR_OPENED\nPR_OPENED, RUN_TESTS, TESTS_PASSED\nPR_OPENED, FAIL_TESTS, BUILD_FAILED\nTESTS_PASSED, APPROVE_PR, REVIEW_APPROVED\nREVIEW_APPROVED, MERGE_CODE, MERGED",
  },
];

