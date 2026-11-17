"""
Unit and integration tests for ML model and hybrid detection engine.
"""

import unittest
import pandas as pd
from data.generator import SyntheticLogGenerator
from data.loader import split_dataset_by_case
from features.extractor import FeatureExtractor
from models.isolation_forest import WorkflowIsolationForest
from detection.engine import HybridDetectionEngine, FinalClassification


class TestModelsAndHybrid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = SyntheticLogGenerator(seed=42)
        df = gen.generate_dataset(num_cases=100, normal_ratio=0.8, rule_anomaly_ratio=0.1, behavioral_anomaly_ratio=0.1)
        train_df, val_df, test_df = split_dataset_by_case(df, 0.6, 0.2, 0.2, seed=42)

        extractor = FeatureExtractor()
        X_train, y_train = extractor.extract_features_df(train_df)
        X_val, y_val = extractor.extract_features_df(val_df)
        X_test, y_test = extractor.extract_features_df(test_df)

        y_val_bin = y_val.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)
        iso_forest = WorkflowIsolationForest(n_estimators=50, random_state=42)
        iso_forest.fit(X_train)
        iso_forest.tune_threshold_on_validation(X_val, y_val_bin)

        cls.full_df = df
        cls.test_df = test_df
        cls.iso_forest = iso_forest

    def test_isolation_forest_scoring(self):
        """Scores should be bounded between 0 and 1."""
        extractor = FeatureExtractor()
        X_test, _ = extractor.extract_features_df(self.test_df)

        scores = self.iso_forest.predict_scores(X_test)
        self.assertTrue((scores >= 0.0).all())
        self.assertTrue((scores <= 1.0).all())
        self.assertEqual(len(scores), len(X_test))

    def test_hybrid_engine_end_to_end(self):
        """Hybrid engine should produce valid detection records with classifications."""
        engine = HybridDetectionEngine(ml_model=self.iso_forest)
        records_df, val_results = engine.process_dataset(self.test_df)

        self.assertEqual(len(records_df), len(self.test_df["case_id"].unique()))
        self.assertIn("final_classification", records_df.columns)
        self.assertIn("summary_explanation", records_df.columns)
        self.assertIn("severity", records_df.columns)

        classifications = set(records_df["final_classification"].unique())
        self.assertIn("Normal", classifications)


if __name__ == "__main__":
    unittest.main()
