"""
Hybrid Workflow Anomaly Detection Engine.

Integrates the Deterministic Finite Automaton (DFA) and Isolation Forest ML Model
using an explicit, interpretable decision policy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from automata.dfa import DFAEngine, ValidationResult, AutomataStatus
from features.extractor import FeatureExtractor
from models.isolation_forest import WorkflowIsolationForest
from detection.explainer import AnomalyExplainer


class FinalClassification(str, Enum):
    NORMAL = "Normal"
    SUSPICIOUS = "Suspicious"
    INVALID = "Invalid"
    INVALID_AND_ANOMALOUS = "Invalid + Anomalous"
    INCOMPLETE = "Incomplete"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DetectionRecord:
    case_id: str
    automata_status: str
    is_valid_automata: bool
    final_state: str
    ml_anomaly_score: float
    ml_threshold: float
    ml_status: str  # "Normal" or "Anomalous"
    final_classification: FinalClassification
    severity: AnomalySeverity
    violation_type: Optional[str]
    offending_event: Optional[str]
    offending_state: Optional[str]
    explanation: Dict[str, Any]
    feature_deviations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "automata_status": self.automata_status,
            "is_valid_automata": self.is_valid_automata,
            "final_state": self.final_state,
            "ml_anomaly_score": round(self.ml_anomaly_score, 4),
            "ml_threshold": round(self.ml_threshold, 4),
            "ml_status": self.ml_status,
            "final_classification": self.final_classification.value,
            "severity": self.severity.value,
            "violation_type": self.violation_type or "",
            "offending_event": self.offending_event or "",
            "offending_state": self.offending_state or "",
            "summary_explanation": self.explanation.get("summary", ""),
            "automata_explanation": self.explanation.get("automata_reason", ""),
            "ml_explanation": self.explanation.get("ml_reason", ""),
            "actionable_next_step": self.explanation.get("actionable_next_step", ""),
        }


class HybridDetectionEngine:
    """
    Coordinates DFA validation and ML scoring to generate explainable hybrid detections.
    """

    def __init__(self, dfa_engine: Optional[DFAEngine] = None, ml_model: Optional[WorkflowIsolationForest] = None):
        self.dfa = dfa_engine or DFAEngine()
        self.ml_model = ml_model
        self.feature_extractor = FeatureExtractor()

    def process_dataset(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, ValidationResult]]:
        """
        Run end-to-end hybrid detection on an entire event log dataframe.

        Returns:
            Tuple of:
            - records_df: pandas DataFrame with detection summary for each case_id.
            - validation_results: dict mapping case_id to step-by-step ValidationResult.
        """
        # Ensure proper sorting
        df_sorted = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_sorted["timestamp"]):
            try:
                df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"], format="ISO8601")
            except Exception:
                df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"], format="mixed")
        df_sorted = df_sorted.sort_values(by=["case_id", "timestamp"])

        # 1. Automata Validation for all cases
        validation_results: Dict[str, ValidationResult] = {}
        grouped = df_sorted.groupby("case_id")
        for case_id, grp in grouped:
            evs = grp["event_type"].tolist()
            tss = grp["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            res = self.dfa.validate_trace(case_id, evs, tss)
            validation_results[case_id] = res

        # 2. ML Feature Extraction
        features_df, _ = self.feature_extractor.extract_features_df(df_sorted)

        # 3. ML Scoring
        scores = {}
        threshold = 0.50
        if self.ml_model and self.ml_model.is_fitted:
            threshold = self.ml_model.threshold
            score_arr = self.ml_model.predict_scores(features_df)
            for cid, s in zip(features_df.index, score_arr):
                scores[cid] = float(s)
        else:
            # Fallback if model not yet fitted
            for cid in features_df.index:
                scores[cid] = 0.0

        # 4. Hybrid Decision Fusion & Explanation
        records: List[DetectionRecord] = []
        feats_dict = features_df.to_dict(orient="index") if self.ml_model and self.ml_model.is_fitted else {}
        for case_id in features_df.index:
            val_res = validation_results[case_id]
            ml_sc = scores.get(case_id, 0.0)
            is_ml_anom = ml_sc >= threshold

            # Top feature deviations (optimized: compute for flagged or requested cases)
            top_devs = []
            if self.ml_model and self.ml_model.is_fitted and (val_res.status == AutomataStatus.INVALID or is_ml_anom):
                top_devs = self.ml_model.explain_case(feats_dict.get(case_id, {}), top_k=3)

            # Continuous, graded anomaly score based on empirical deviation magnitude
            max_dev = max([float(d.get("deviation_score", 0.0)) for d in top_devs], default=0.0) if top_devs else 0.0

            # Decision Policy & Calibrated Anomaly Scores
            if val_res.status == AutomataStatus.INVALID:
                if is_ml_anom:
                    classification = FinalClassification.INVALID_AND_ANOMALOUS
                    severity = AnomalySeverity.CRITICAL
                    display_score = round(min(1.0, 0.93 + 0.07 * (1.0 - np.exp(-max_dev / 15.0))), 2)
                else:
                    classification = FinalClassification.INVALID
                    severity = AnomalySeverity.HIGH
                    display_score = 0.92
                violation_type = f"DFA Violation: {val_res.offending_event}"
            elif val_res.status == AutomataStatus.VALID_INCOMPLETE:
                classification = FinalClassification.INCOMPLETE
                severity = AnomalySeverity.LOW
                violation_type = None
                display_score = round(0.20 + 0.12 * (1.0 - np.exp(-max_dev / 10.0)), 2)
            else:  # VALID_COMPLETED
                if is_ml_anom:
                    classification = FinalClassification.SUSPICIOUS
                    severity = AnomalySeverity.MEDIUM
                    violation_type = "Behavioral Outlier"
                    # Graded continuous score reflecting statistical deviance severity across [0.58, 0.88]
                    # Asymptotically scales with deviation magnitude (delays, loops) without hitting a static 0.85 wall
                    display_score = round(0.58 + 0.30 * (1.0 - np.exp(-max(1.0, max_dev) / 22.0)), 2)
                else:
                    classification = FinalClassification.NORMAL
                    severity = AnomalySeverity.LOW
                    violation_type = None
                    display_score = round(0.02 + 0.12 * (1.0 - np.exp(-max_dev / 5.0)), 2)

            explanation = AnomalyExplainer.generate_explanation(
                val_result=val_res,
                ml_score=display_score,
                ml_threshold=threshold,
                is_ml_anomalous=is_ml_anom,
                top_deviations=top_devs,
            )

            rec = DetectionRecord(
                case_id=case_id,
                automata_status=val_res.status.value,
                is_valid_automata=val_res.is_valid,
                final_state=val_res.final_state,
                ml_anomaly_score=display_score,
                ml_threshold=threshold,
                ml_status="Anomalous" if is_ml_anom else "Normal",
                final_classification=classification,
                severity=severity,
                violation_type=violation_type,
                offending_event=val_res.offending_event,
                offending_state=val_res.offending_state,
                explanation=explanation,
                feature_deviations=top_devs,
            )
            records.append(rec)

        records_df = pd.DataFrame([r.to_dict() for r in records])
        return records_df, validation_results

