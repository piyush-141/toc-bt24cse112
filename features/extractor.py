"""
Universal Case-Level Feature Extraction for Workflow Executions.

Transforms event-log sequences into structured numerical features for machine learning:
1. Total event count
2. Temporal features (total duration, mean, std, max, min inter-event time)
3. Event frequency features across all unique alphabet symbols in the domain
4. Transition bigram frequencies for sequential structure
5. Duplicate consecutive events / thrashing loops
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from workflow.specification import WorkflowEvent

# Canonical lists preserved for backwards compatibility with tests and older imports
CANONICAL_EVENTS = [e.value for e in WorkflowEvent]
KEY_TRANSITIONS = [
    ("SUBMIT_PAYMENT", "PAYMENT_SUCCESS"),
    ("SUBMIT_PAYMENT", "PAYMENT_FAIL"),
    ("PAYMENT_FAIL", "RETRY_PAYMENT"),
    ("RETRY_PAYMENT", "PAYMENT_FAIL"),
    ("RETRY_PAYMENT", "PAYMENT_SUCCESS"),
    ("PAYMENT_SUCCESS", "PACK_ORDER"),
    ("PACK_ORDER", "SHIP_ORDER"),
    ("SHIP_ORDER", "DELIVER_ORDER"),
    ("CANCEL_ORDER", "COMPLETE_REFUND"),
]


class FeatureExtractor:
    """
    Universal feature extractor for any workflow domain (E-Commerce, Healthcare, Education, Custom).
    Dynamically captures domain vocabulary while ensuring zero label leakage.
    """

    def __init__(self):
        self.feature_names_: List[str] = []
        self.known_alphabet_: List[str] = []
        self.known_bigrams_: List[Tuple[str, str]] = []

    def extract_features_df(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Extract case-level features from an event dataframe.

        Args:
            df: DataFrame containing at least ['case_id', 'timestamp', 'event_type'].

        Returns:
            Tuple of (features_df indexed by case_id, labels_series if ground_truth is present).
        """
        df_sorted = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_sorted["timestamp"]):
            try:
                df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"], format="ISO8601")
            except Exception:
                df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"], format="mixed")
        df_sorted = df_sorted.sort_values(by=["case_id", "timestamp"])

        # Dynamically discover alphabet and bigrams if not already fitted
        if not self.known_alphabet_:
            self.known_alphabet_ = sorted(list(df_sorted["event_type"].unique()))

        if not self.known_bigrams_:
            bigram_set: Set[Tuple[str, str]] = set()
            for _, group in df_sorted.groupby("case_id"):
                evs = group["event_type"].tolist()
                for i in range(len(evs) - 1):
                    bigram_set.add((evs[i], evs[i + 1]))
            self.known_bigrams_ = sorted(list(bigram_set))

        grouped = df_sorted.groupby("case_id")
        feature_rows: List[Dict[str, Any]] = []
        labels: Dict[str, str] = {}
        has_labels = "ground_truth_anomaly_type" in df_sorted.columns

        for case_id, group in grouped:
            events = group["event_type"].tolist()
            timestamps = group["timestamp"].tolist()

            feats = self._extract_case_vector(events, timestamps)
            feats["case_id"] = case_id
            feature_rows.append(feats)

            if has_labels:
                labels[case_id] = group["ground_truth_anomaly_type"].iloc[0]

        feat_df = pd.DataFrame(feature_rows).set_index("case_id")

        if not self.feature_names_:
            self.feature_names_ = list(feat_df.columns)
        else:
            feat_df = feat_df.reindex(columns=self.feature_names_, fill_value=0.0)

        labels_series = pd.Series(labels, name="ground_truth") if has_labels else None
        return feat_df, labels_series

    def _extract_case_vector(self, events: List[str], timestamps: List[pd.Timestamp]) -> Dict[str, float]:
        """Extract domain-agnostic numerical features for a single execution sequence."""
        n_events = len(events)
        features: Dict[str, float] = {}

        # 1. Total event count
        features["total_event_count"] = float(n_events)
        features["payment_attempt_count"] = float(events.count("SUBMIT_PAYMENT") + events.count("RETRY_PAYMENT"))

        # 2. Duplicate consecutive events (looping / retry indicator)
        dup_count = sum(1 for i in range(1, n_events) if events[i] == events[i - 1])
        features["duplicate_consecutive_events"] = float(dup_count)

        # 3. Temporal statistics
        if n_events >= 2 and len(timestamps) >= 2:
            time_diffs = [(timestamps[i] - timestamps[i - 1]).total_seconds() for i in range(1, n_events)]
            time_diffs = [max(0.0, td) for td in time_diffs]
            total_duration = (timestamps[-1] - timestamps[0]).total_seconds()

            features["total_duration_seconds"] = float(total_duration)
            features["total_duration_hours"] = float(total_duration / 3600.0)
            features["inter_event_time_mean"] = float(np.mean(time_diffs))
            features["inter_event_time_std"] = float(np.std(time_diffs)) if len(time_diffs) > 1 else 0.0
            features["inter_event_time_max"] = float(np.max(time_diffs))
            features["inter_event_time_min"] = float(np.min(time_diffs))
        else:
            features["total_duration_seconds"] = 0.0
            features["total_duration_hours"] = 0.0
            features["inter_event_time_mean"] = 0.0
            features["inter_event_time_std"] = 0.0
            features["inter_event_time_max"] = 0.0
            features["inter_event_time_min"] = 0.0

        # 4. Event Frequencies across domain alphabet
        for ev_name in self.known_alphabet_:
            cnt = events.count(ev_name)
            features[f"freq_{ev_name}"] = float(cnt / max(1, n_events))

        # 5. Transition Bigram Frequencies across domain transitions
        bigrams = list(zip(events[:-1], events[1:])) if n_events > 1 else []
        for (src, dst) in self.known_bigrams_:
            bg_name = f"trans_{src}_to_{dst}"
            features[bg_name] = float(bigrams.count((src, dst)))

        return features
