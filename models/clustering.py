"""
Clustering-Based Anomaly Detector for Workflow Executions.

Implements KMeans process profiling:
- Groups normal executions into behavioral clusters (e.g., standard quick checkout, retry loops, cancellation flows).
- Computes Euclidean distance of each execution to its nearest cluster centroid.
- Flag cases exceeding the calibrated percentile threshold as cluster outliers.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler


class ClusteringAnomalyDetector:
    """
    K-Means Centroid-Distance Anomaly Detector.
    Identifies executions that do not conform to established normal process behavior clusters.
    """

    def __init__(self, n_clusters: int = 4, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = RobustScaler()
        self.kmeans: Optional[KMeans] = None
        self.threshold: float = 0.50
        self.min_normal_dist: float = 0.5
        self.max_normal_dist: float = 2.0
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, X_train: pd.DataFrame) -> "ClusteringAnomalyDetector":
        self.feature_names = list(X_train.columns)
        X_scaled = self.scaler.fit_transform(X_train)

        n_clusters = min(self.n_clusters, max(2, len(X_train) // 15))
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
        self.kmeans.fit(X_scaled)

        # Compute distances for normal training data to establish baseline
        distances = self._compute_min_distances(X_scaled)
        if len(distances) > 0:
            self.min_normal_dist = float(np.min(distances))
            self.max_normal_dist = float(np.max(distances))
        else:
            self.min_normal_dist = 0.5
            self.max_normal_dist = 2.5
        self.threshold = 0.50
        self.is_fitted = True
        return self

    def _compute_min_distances(self, X_scaled: np.ndarray) -> np.ndarray:
        """Compute Euclidean distance to the nearest cluster center."""
        centers = self.kmeans.cluster_centers_
        dists = np.linalg.norm(X_scaled[:, np.newaxis, :] - centers[np.newaxis, :, :], axis=2)
        return np.min(dists, axis=1)

    def predict_scores(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted or self.kmeans is None:
            raise RuntimeError("Detector must be fitted before predict_scores.")

        X_aligned = X.reindex(columns=self.feature_names, fill_value=0.0)
        X_scaled = self.scaler.transform(X_aligned)
        raw_distances = self._compute_min_distances(X_scaled)

        ceiling = self.max_normal_dist * 1.15 + 0.10
        scores = []
        for dist in raw_distances:
            if dist <= ceiling:
                span = max(1e-5, ceiling - self.min_normal_dist)
                norm = np.clip((dist - self.min_normal_dist) / span * 0.20, 0.0, 0.20)
            else:
                excess = dist - ceiling
                norm = 0.50 + 0.50 * np.clip(excess / max(1.0, ceiling), 0.0, 1.0)
            scores.append(float(norm))
        return np.array(scores)

    def predict(self, X: pd.DataFrame, threshold: Optional[float] = None) -> np.ndarray:
        th = threshold if threshold is not None else self.threshold
        scores = self.predict_scores(X)
        return (scores >= th).astype(int)
