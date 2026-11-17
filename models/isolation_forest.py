"""
Isolation Forest Machine Learning Anomaly Detector.

Implements:
- Training Isolation Forest on workflow execution feature vectors.
- Validation-set threshold selection (maximizing F1 or target sensitivity).
- Normalized anomaly scoring [0, 1] where higher values denote greater anomaly severity.
- Feature importance / attribution estimation for explainability.
- Model serialization and deserialization.
"""

import os
import pickle
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


class WorkflowIsolationForest:
    """
    Isolation Forest detector with normalized anomaly scoring and threshold calibration.
    """

    def __init__(
        self,
        n_estimators: int = 150,
        max_samples: str = "auto",
        contamination: float = 0.10,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.random_state = random_state

        self.model: Optional[IsolationForest] = None
        self.scaler: RobustScaler = RobustScaler()
        self.threshold: float = 0.50  # calibrated on validation set
        self.min_normal_raw: float = -0.1
        self.max_normal_raw: float = 0.3
        self.min_score: float = -0.5
        self.max_score: float = 0.5
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, X_train: pd.DataFrame) -> "WorkflowIsolationForest":
        """
        Fit Isolation Forest and robust scaler on training feature dataframe.
        """
        self.feature_names = list(X_train.columns)
        X_scaled = self.scaler.fit_transform(X_train)

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)

        # Baseline raw scores for normal training data
        raw_scores = self.model.decision_function(X_scaled)
        if len(raw_scores) > 0:
            self.min_normal_raw = float(np.percentile(raw_scores, 2.0))
            self.max_normal_raw = float(np.percentile(raw_scores, 98.0))
        else:
            self.min_normal_raw = 0.0
            self.max_normal_raw = 0.2
        if self.max_normal_raw <= self.min_normal_raw:
            self.max_normal_raw = self.min_normal_raw + 0.1

        self.min_score = self.min_normal_raw
        self.max_score = self.max_normal_raw
        self.threshold = 0.50
        self.is_fitted = True
        return self

    def tune_threshold_on_validation(
        self,
        X_val: pd.DataFrame,
        y_val_binary: pd.Series,
    ) -> float:
        """
        Calibrate anomaly score threshold on a held-out validation set to optimize F0.5 score.

        Args:
            X_val: Validation feature vectors.
            y_val_binary: Binary ground truth (1 for anomalous, 0 for normal).

        Returns:
            Optimal threshold in range [0, 1].
        """
        scores = self.predict_scores(X_val)
        y_true = np.array(y_val_binary)

        best_threshold = 0.40
        best_objective = -1.0

        thresholds = np.linspace(0.25, 0.80, 56)
        for t in thresholds:
            y_pred = (scores >= t).astype(int)
            tp = np.sum((y_true == 1) & (y_pred == 1))
            fp = np.sum((y_true == 0) & (y_pred == 1))
            fn = np.sum((y_true == 1) & (y_pred == 0))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            # F0.5 score: weights precision 2x higher than recall to penalize false positives
            f05 = (1.25 * precision * recall / (0.25 * precision + recall)) if (0.25 * precision + recall) > 0 else 0.0

            if f05 > best_objective:
                best_objective = f05
                best_threshold = float(t)

        self.threshold = best_threshold
        return best_threshold

    def predict_scores(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute normalized anomaly scores in [0, 1], where 1 = highly anomalous.
        Uses standard logistic inversion centered around the decision boundary (raw=0).
        Higher score = more anomalous.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("WorkflowIsolationForest must be fitted before predict_scores.")

        # Reindex to ensure feature alignment
        X_aligned = X.reindex(columns=self.feature_names, fill_value=0.0)
        X_scaled = self.scaler.transform(X_aligned)
        raw_scores = self.model.decision_function(X_scaled)

        # Continuous logistic transformation centered at decision boundary
        # raw > 0 (inliers) map to < 0.50; raw < 0 (outliers) map to > 0.50
        scores = 1.0 / (1.0 + np.exp(12.0 * raw_scores))
        return np.clip(scores, 0.0, 1.0)

    def predict(self, X: pd.DataFrame, threshold: Optional[float] = None) -> np.ndarray:
        """
        Predict binary anomalies: 1 = anomalous, 0 = normal.
        """
        th = threshold if threshold is not None else self.threshold
        scores = self.predict_scores(X)
        return (scores >= th).astype(int)

    def explain_case(self, case_features: pd.Series, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Determine the top unusual feature deviations for a single execution.
        Computes z-score distance relative to the scaler's center and scale.
        """
        deviations = []
        for i, feat_name in enumerate(self.feature_names):
            val = float(case_features.get(feat_name, 0.0))
            center = float(self.scaler.center_[i])
            scale = float(self.scaler.scale_[i]) if self.scaler.scale_[i] > 0 else 1.0
            z_score = abs(val - center) / scale

            deviations.append({
                "feature": feat_name,
                "value": val,
                "median": center,
                "scale": scale,
                "deviation_score": float(z_score),
            })

        # Sort descending by deviation
        deviations.sort(key=lambda d: d["deviation_score"], reverse=True)
        return deviations[:top_k]

    def save(self, filepath: str) -> None:
        """Serialize model to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str) -> "WorkflowIsolationForest":
        """Deserialize model from file."""
        with open(filepath, "rb") as f:
            return pickle.load(f)

