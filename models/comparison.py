"""
Supervised Random Forest Benchmark Classifier (Comparison Model).
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class SupervisedBenchmarkModel:
    """
    Supervised Random Forest baseline for comparison against unsupervised Isolation Forest.
    Can also serve as the high-precision supervised backbone for the Hybrid Decision Engine.
    """

    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
        self.feature_names: List[str] = []
        self.feature_means: Dict[str, float] = {}
        self.feature_stds: Dict[str, float] = {}
        self.threshold: float = 0.50
        self.is_fitted = False

    def fit(self, X_train: pd.DataFrame, y_train_binary: pd.Series) -> "SupervisedBenchmarkModel":
        self.feature_names = list(X_train.columns)
        self.model.fit(X_train, y_train_binary)

        # Compute normal class statistics for feature explanation
        normal_mask = (y_train_binary == 0)
        X_normal = X_train[normal_mask] if normal_mask.sum() > 0 else X_train
        for col in self.feature_names:
            self.feature_means[col] = float(X_normal[col].mean())
            std_val = float(X_normal[col].std())
            self.feature_stds[col] = std_val if std_val > 1e-6 else 1.0

        self.is_fitted = True
        return self

    def predict(self, X_test: pd.DataFrame) -> np.ndarray:
        X_aligned = X_test.reindex(columns=self.feature_names, fill_value=0.0)
        return self.model.predict(X_aligned)

    def predict_proba(self, X_test: pd.DataFrame) -> np.ndarray:
        X_aligned = X_test.reindex(columns=self.feature_names, fill_value=0.0)
        return self.model.predict_proba(X_aligned)[:, 1]

    def predict_scores(self, X_test: pd.DataFrame) -> np.ndarray:
        """Alias for predict_proba to adhere to the ML model protocol."""
        return self.predict_proba(X_test)

    def explain_case(self, case_features: pd.Series, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Explain why a case was flagged by computing deviation from normal class,
        weighted by the Random Forest's feature importances.
        """
        if not self.is_fitted:
            return []

        deviations = []
        importances = self.model.feature_importances_

        for i, feat_name in enumerate(self.feature_names):
            val = float(case_features.get(feat_name, 0.0))
            mean_val = self.feature_means.get(feat_name, 0.0)
            std_val = self.feature_stds.get(feat_name, 1.0)
            z_score = abs(val - mean_val) / std_val
            imp = float(importances[i])

            weighted_impact = z_score * (1.0 + 5.0 * imp)

            deviations.append({
                "feature": feat_name,
                "value": val,
                "median": mean_val,
                "scale": std_val,
                "deviation_score": float(weighted_impact),
            })

        deviations.sort(key=lambda d: d["deviation_score"], reverse=True)
        return deviations[:top_k]
