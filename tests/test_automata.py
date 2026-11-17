"""
Unit and integration tests for the workflow DFA engine (unittest compatible).
"""

import unittest
from workflow.specification import (
    WorkflowState,
    WorkflowEvent,
    INITIAL_STATE,
    TERMINAL_STATES,
)
from automata.dfa import DFAEngine, AutomataStatus


class TestAutomata(unittest.TestCase):
    def setUp(self):
        self.dfa = DFAEngine()

    def test_standard_happy_path(self):
        """Standard order completion should be accepted and reach terminal state."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.PACK_ORDER.value,
            WorkflowEvent.SHIP_ORDER.value,
            WorkflowEvent.DELIVER_ORDER.value,
        ]
        res = self.dfa.validate_trace("CASE_HAPPY_1", events)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.VALID_COMPLETED)
        self.assertEqual(res.final_state, WorkflowState.ORDER_DELIVERED.value)
        self.assertTrue(res.is_terminal)
        self.assertIsNone(res.offending_step)

    def test_payment_retry_and_success(self):
        """Payment retries within allowed state loops should be valid."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_FAIL.value,
            WorkflowEvent.RETRY_PAYMENT.value,
            WorkflowEvent.PAYMENT_FAIL.value,
            WorkflowEvent.RETRY_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.PACK_ORDER.value,
            WorkflowEvent.SHIP_ORDER.value,
            WorkflowEvent.DELIVER_ORDER.value,
        ]
        res = self.dfa.validate_trace("CASE_RETRY_1", events)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.VALID_COMPLETED)
        self.assertEqual(res.final_state, WorkflowState.ORDER_DELIVERED.value)

    def test_cancellation_and_refund_path(self):
        """Cancellation after payment should transition through REFUND_PENDING to REFUND_COMPLETED."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.CANCEL_ORDER.value,
            WorkflowEvent.COMPLETE_REFUND.value,
        ]
        res = self.dfa.validate_trace("CASE_REFUND_1", events)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.VALID_COMPLETED)
        self.assertEqual(res.final_state, WorkflowState.REFUND_COMPLETED.value)

    def test_invalid_premature_shipping(self):
        """Shipping before payment confirmation and packing must be flagged as INVALID."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.SHIP_ORDER.value,
        ]
        res = self.dfa.validate_trace("CASE_PREMATURE_SHIP", events)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.INVALID)
        self.assertEqual(res.offending_event, WorkflowEvent.SHIP_ORDER.value)
        self.assertEqual(res.offending_state, WorkflowState.PAYMENT_PENDING.value)
        self.assertIn("Premature shipping violation", res.violation_rule)

    def test_invalid_delivery_before_dispatch(self):
        """Delivery directly from packing without shipping must be rejected."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.PACK_ORDER.value,
            WorkflowEvent.DELIVER_ORDER.value,
        ]
        res = self.dfa.validate_trace("CASE_OUT_OF_ORDER_DELIVER", events)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.INVALID)
        self.assertEqual(res.offending_event, WorkflowEvent.DELIVER_ORDER.value)
        self.assertEqual(res.offending_state, WorkflowState.ORDER_PACKED.value)

    def test_unknown_event(self):
        """Events outside the alphabet Sigma must be rejected."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            "UNREGISTERED_HACK_EVENT",
        ]
        res = self.dfa.validate_trace("CASE_UNKNOWN_EV", events)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.INVALID)
        self.assertEqual(res.offending_event, "UNREGISTERED_HACK_EVENT")
        self.assertIn("not in the recognized workflow alphabet", res.violation_rule)

    def test_incomplete_execution(self):
        """Traces stopped mid-flow with valid transitions should be INCOMPLETE, not INVALID."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.PACK_ORDER.value,
        ]
        res = self.dfa.validate_trace("CASE_INCOMPLETE_1", events)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.VALID_INCOMPLETE)
        self.assertEqual(res.final_state, WorkflowState.ORDER_PACKED.value)
        self.assertFalse(res.is_terminal)
        self.assertIn(WorkflowEvent.SHIP_ORDER.value, res.permitted_next)

    def test_actions_after_terminal_state(self):
        """No events allowed after reaching an accepting terminal state."""
        events = [
            WorkflowEvent.PLACE_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
            WorkflowEvent.PAYMENT_SUCCESS.value,
            WorkflowEvent.PACK_ORDER.value,
            WorkflowEvent.SHIP_ORDER.value,
            WorkflowEvent.DELIVER_ORDER.value,
            WorkflowEvent.SUBMIT_PAYMENT.value,
        ]
        res = self.dfa.validate_trace("CASE_AFTER_TERMINAL", events)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, AutomataStatus.INVALID)
        self.assertEqual(res.offending_state, WorkflowState.ORDER_DELIVERED.value)
        self.assertIn("Terminal state violation", res.violation_rule)

    def test_reachability(self):
        """All terminal states must be reachable from q0."""
        reach = self.dfa.compute_reachability()
        self.assertTrue(reach["all_terminals_reachable"])
        self.assertEqual(len(reach["unreachable_states"]), 0)


if __name__ == "__main__":
    unittest.main()
