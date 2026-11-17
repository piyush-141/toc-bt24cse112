"""
Repeatable Benchmark Pipeline for Automata, ML, and Hybrid Detection.

Evaluates and compares:
1. Automata-Only Detection (DFA regular language grammar)
2. Isolation Forest (statistical outlier detector)
3. Process Clustering (K-Means distance to centroid)
4. Sequence Model (Markov transition likelihood)
5. Hybrid Detection Engine (Grammar + ML Decision Fusion)
6. Supervised Benchmark (Random Forest)
"""

import time
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np

from automata.dfa import DFAEngine, AutomataStatus
from features.extractor import FeatureExtractor
from models.isolation_forest import WorkflowIsolationForest
from models.comparison import SupervisedBenchmarkModel
from models.clustering import ClusteringAnomalyDetector
from models.sequence_model import MarkovSequenceModel
from evaluation.metrics import compute_metrics, compute_category_breakdown


class EvaluationPipeline:
    """
    Standardized, reproducible evaluation harness executed on held-out test sets.
    """

    def __init__(self, seed: int = 42, dfa_engine: DFAEngine = None):
        self.seed = seed
        self.dfa = dfa_engine or DFAEngine()
        self.feature_extractor = FeatureExtractor()

    def run_benchmark(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Run the complete evaluation suite on train, val, test splits.
        """
        # 1. Feature Extraction
        t0 = time.time()
        X_train, y_train_cat = self.feature_extractor.extract_features_df(train_df)
        X_val, y_val_cat = self.feature_extractor.extract_features_df(val_df)
        X_test, y_test_cat = self.feature_extractor.extract_features_df(test_df)
        feature_latency = time.time() - t0

        # Extract event sequences for sequence modeling
        train_traces = [grp["event_type"].tolist() for _, grp in train_df.groupby("case_id")]
        train_normal_idx_set = set(y_train_cat[y_train_cat == "NORMAL"].index)
        train_normal_traces = [grp["event_type"].tolist() for cid, grp in train_df.groupby("case_id") if cid in train_normal_idx_set]
        val_traces = [grp["event_type"].tolist() for _, grp in val_df.groupby("case_id")]
        test_traces = [grp["event_type"].tolist() for _, grp in test_df.groupby("case_id")]

        # Create binary ground truth: 1 for any anomaly, 0 for normal/incomplete
        y_val_bin = y_val_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)
        y_test_bin = y_test_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)

        # 2. Train Isolation Forest and tune threshold on validation set (precision-weighted F0.5)
        t0 = time.time()
        train_normal_idx = y_train_cat[y_train_cat == "NORMAL"].index
        X_train_clean = X_train.loc[train_normal_idx] if len(train_normal_idx) > 50 else X_train

        iso_forest = WorkflowIsolationForest(n_estimators=100, random_state=self.seed)
        iso_forest.fit(X_train_clean)
        best_threshold = iso_forest.tune_threshold_on_validation(X_val, y_val_bin)
        train_latency = time.time() - t0

        # 3. Train Clustering Anomaly Detector (K-Means) with threshold calibration
        clustering_model = ClusteringAnomalyDetector(n_clusters=4, random_state=self.seed)
        clustering_model.fit(X_train_clean)
        c_val_scores = clustering_model.predict_scores(X_val)

        best_c_th = 0.50
        best_c_score = -1.0
        for t in np.linspace(0.40, 0.98, 59):
            preds_v = (c_val_scores >= t).astype(int)
            tp = np.sum((y_val_bin == 1) & (preds_v == 1))
            fp = np.sum((y_val_bin == 0) & (preds_v == 1))
            fn = np.sum((y_val_bin == 1) & (preds_v == 0))
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f05 = (1.25 * prec * rec) / (0.25 * prec + rec) if (0.25 * prec + rec) > 0 else 0.0
            if f05 > best_c_score and rec >= 0.35:
                best_c_score = f05
                best_c_th = float(t)

        cluster_scores = clustering_model.predict_scores(X_test)
        cluster_preds = (cluster_scores >= best_c_th).astype(int)

        # 4. Train Markov Sequence Anomaly Detector with threshold calibration
        seq_model = MarkovSequenceModel(smoothing=0.01)
        seq_model.fit(train_normal_traces if len(train_normal_traces) > 20 else train_traces)
        s_val_scores = seq_model.predict_scores(val_traces)

        best_s_th = 0.50
        best_s_score = -1.0
        for t in np.linspace(0.30, 0.95, 66):
            preds_v = (s_val_scores >= t).astype(int)
            tp = np.sum((y_val_bin == 1) & (preds_v == 1))
            fp = np.sum((y_val_bin == 0) & (preds_v == 1))
            fn = np.sum((y_val_bin == 1) & (preds_v == 0))
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f05 = (1.25 * prec * rec) / (0.25 * prec + rec) if (0.25 * prec + rec) > 0 else 0.0
            if f05 > best_s_score and rec >= 0.30:
                best_s_score = f05
                best_s_th = float(t)

        seq_scores = seq_model.predict_scores(test_traces)
        seq_preds = (seq_scores >= best_s_th).astype(int)

        # 5. Supervised Comparison Model (Random Forest)
        y_train_bin = y_train_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)
        supervised_rf = SupervisedBenchmarkModel(n_estimators=100, random_state=self.seed)
        supervised_rf.fit(X_train, y_train_bin)
        rf_preds = supervised_rf.predict(X_test)

        # 6. Automata-Only Evaluation on Test Set
        t0 = time.time()
        dfa_preds = []
        test_grouped = test_df.groupby("case_id")
        for case_id in X_test.index:
            grp = test_grouped.get_group(case_id)
            evs = grp["event_type"].tolist()
            val_res = self.dfa.validate_trace(case_id, evs)
            dfa_preds.append(1 if val_res.status == AutomataStatus.INVALID else 0)
        dfa_latency = time.time() - t0
        dfa_preds = np.array(dfa_preds)

        # 7. Isolation Forest Predictions on Test Set
        t0 = time.time()
        ml_scores = iso_forest.predict_scores(X_test)
        ml_preds = (ml_scores >= best_threshold).astype(int)
        ml_latency = time.time() - t0

        # 8. Hybrid Evaluation on Test Set
        # Architecture: Formal Deterministic Automaton (DFA) + Supervised / High-Precision ML
        # A sequence is flagged if Automata reports INVALID (grammar violation) OR
        # ML model detects behavioral anomaly (temporal delay, retry loop, thrashing).
        hybrid_preds = ((dfa_preds == 1) | (rf_preds == 1)).astype(int)

        # 9. Compute Metrics across all 6 techniques
        dfa_metrics = compute_metrics(y_test_bin, dfa_preds)
        ml_metrics = compute_metrics(y_test_bin, ml_preds)
        clustering_metrics = compute_metrics(y_test_bin, cluster_preds)
        seq_metrics = compute_metrics(y_test_bin, seq_preds)
        hybrid_metrics = compute_metrics(y_test_bin, hybrid_preds)
        rf_metrics = compute_metrics(y_test_bin, rf_preds)

        # Category breakdowns
        dfa_breakdown = compute_category_breakdown(y_test_cat, dfa_preds)
        ml_breakdown = compute_category_breakdown(y_test_cat, ml_preds)
        clustering_breakdown = compute_category_breakdown(y_test_cat, cluster_preds)
        seq_breakdown = compute_category_breakdown(y_test_cat, seq_preds)
        hybrid_breakdown = compute_category_breakdown(y_test_cat, hybrid_preds)

        return {
            "test_cases_count": len(X_test),
            "calibrated_threshold": best_threshold,
            "metrics": {
                "automata_only": dfa_metrics,
                "ml_only": ml_metrics,
                "clustering": clustering_metrics,
                "sequence_model": seq_metrics,
                "hybrid": hybrid_metrics,
                "supervised_rf": rf_metrics,
            },
            "category_breakdown": {
                "automata_only": dfa_breakdown,
                "ml_only": ml_breakdown,
                "clustering": clustering_breakdown,
                "sequence_model": seq_breakdown,
                "hybrid": hybrid_breakdown,
            },
            "latencies": {
                "feature_extraction_sec": feature_latency,
                "training_sec": train_latency,
                "dfa_inference_sec": dfa_latency,
                "ml_inference_sec": ml_latency,
            },
            "trained_model": supervised_rf,
            "iso_forest_model": iso_forest,
        }
