"""
Dynamic Evidence-Based Explanation Generator.

Generates precise, factual explanations for why a workflow execution was flagged:
- Exactly identifies the illegal transition, offending event, and required preconditions
- Contextualizes statistical ML anomalies with specific outlier features and thresholds
- Suggests permissible next steps where appropriate
"""

from typing import List, Dict, Any, Optional
import pandas as pd

from automata.dfa import ValidationResult, AutomataStatus


class AnomalyExplainer:
    """
    Generates dynamic, human-interpretable explanations from automata and ML diagnostics.
    """

    @staticmethod
    def generate_explanation(
        val_result: ValidationResult,
        ml_score: float,
        ml_threshold: float,
        is_ml_anomalous: bool,
        top_deviations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation components for an execution.

        Returns:
            Dict containing:
            - summary: One-sentence concise conclusion.
            - automata_reason: DFA validation explanation.
            - ml_reason: ML statistical outlier explanation.
            - actionable_next_step: Permitted alternative or remediation step.
        """
        is_rule_violated = not val_result.is_valid
        deviations = top_deviations or []

        # 1. Automata Explanation
        if is_rule_violated:
            state = val_result.offending_state or val_result.final_state
            ev = val_result.offending_event or "UNKNOWN_EVENT"
            permitted = val_result.permitted_next
            perm_str = ", ".join(f"'{p}'" for p in permitted) if permitted else "None (Terminal State)"
            automata_reason = (
                f"Rule violation at step {val_result.offending_step.step_index if val_result.offending_step else '?'}: "
                f"Event '{ev}' occurred while workflow was in state '{state}'. "
                f"{val_result.violation_rule}"
            )
            actionable_next_step = f"Permissible events from '{state}' were: [{perm_str}]."
        elif val_result.status == AutomataStatus.VALID_INCOMPLETE:
            permitted = val_result.permitted_next
            perm_str = ", ".join(f"'{p}'" for p in permitted) if permitted else "None"
            automata_reason = (
                f"Execution is in-progress (valid prefix): currently in state '{val_result.final_state}'. "
                f"No invalid transitions occurred so far."
            )
            actionable_next_step = f"Expected next events to advance workflow: [{perm_str}]."
        else:
            automata_reason = f"Automata validation passed: reached valid terminal state '{val_result.final_state}'."
            actionable_next_step = "Workflow finished normally. No further action needed."

        # 2. ML Statistical Explanation
        dev_summaries = []
        for d in deviations:
            feat = d["feature"]
            val = d["value"]
            med = d["median"]
            if "count" in feat or "attempts" in feat:
                dev_summaries.append(f"{feat}={int(val)} (median: {int(med)})")
            elif "duration" in feat or "hours" in feat:
                dev_summaries.append(f"{feat}={val:.1f}h (median: {med:.1f}h)")
            else:
                dev_summaries.append(f"{feat}={val:.2f} (median: {med:.2f})")

        dev_text = ", ".join(dev_summaries) if dev_summaries else "unusual combination of execution dynamics"

        if is_ml_anomalous:
            ml_reason = (
                f"ML model flagged statistical anomaly with score {ml_score:.3f} "
                f"(exceeding threshold {ml_threshold:.3f}). "
                f"Primary feature deviations: {dev_text}."
            )
        else:
            ml_reason = (
                f"ML behavioral profile is nominal with score {ml_score:.3f} "
                f"(below threshold {ml_threshold:.3f})."
            )

        # 3. Overall Summary
        if is_rule_violated and is_ml_anomalous:
            summary = (
                f"Invalid and Anomalous: Case violated workflow state rules at '{val_result.offending_event}' "
                f"and exhibited extreme statistical feature outliers (ML score: {ml_score:.3f})."
            )
        elif is_rule_violated:
            summary = (
                f"Invalid Transition: Offending event '{val_result.offending_event}' violated workflow rules "
                f"in state '{val_result.offending_state}'."
            )
        elif is_ml_anomalous:
            summary = (
                f"Suspicious Behavior: Followed formally valid state transitions, but flagged as a behavioral outlier "
                f"(ML score: {ml_score:.3f} > {ml_threshold:.3f}) due to {dev_text}."
            )
        elif val_result.status == AutomataStatus.VALID_INCOMPLETE:
            summary = f"Incomplete Execution: Follows valid workflow rules so far, awaiting terminal event in '{val_result.final_state}'."
        else:
            summary = "Normal Execution: Fully compliant with workflow rules and behavioral baselines."

        return {
            "summary": summary,
            "automata_reason": automata_reason,
            "ml_reason": ml_reason,
            "actionable_next_step": actionable_next_step,
        }

