"""
Unit tests for synthetic generator, loader, schema validation, and feature extraction.
"""

import unittest
import pandas as pd
from data.generator import SyntheticLogGenerator
from data.loader import load_event_log_csv, split_dataset_by_case
from data.schema import validate_event_log_schema
from features.extractor import FeatureExtractor


class TestDataAndFeatures(unittest.TestCase):
    def test_synthetic_generation_reproducibility(self):
        """Generator with the same seed must produce identical outputs."""
        gen1 = SyntheticLogGenerator(seed=123)
        df1 = gen1.generate_dataset(num_cases=50)

        gen2 = SyntheticLogGenerator(seed=123)
        df2 = gen2.generate_dataset(num_cases=50)

        pd.testing.assert_frame_equal(df1, df2)
        self.assertEqual(len(df1["case_id"].unique()), 50)
        self.assertIn("timestamp", df1.columns)
        self.assertIn("event_type", df1.columns)
        self.assertIn("ground_truth_anomaly_type", df1.columns)

    def test_schema_validation_success(self):
        """Valid dataframe should pass schema validation."""
        gen = SyntheticLogGenerator(seed=42)
        df = gen.generate_dataset(num_cases=20)
        is_valid, err, cleaned = validate_event_log_schema(df)
        self.assertTrue(is_valid)
        self.assertIsNone(err)
        self.assertEqual(len(cleaned), len(df))

    def test_schema_validation_missing_cols(self):
        """Missing mandatory column should fail validation with clear error message."""
        bad_df = pd.DataFrame({"case_id": ["C1"], "event_type": ["E1"]})
        is_valid, err, _ = validate_event_log_schema(bad_df)
        self.assertFalse(is_valid)
        self.assertIn("Missing mandatory schema columns", err)

    def test_case_split_no_leakage(self):
        """Split must partition by case_id with zero overlap between splits."""
        gen = SyntheticLogGenerator(seed=42)
        df = gen.generate_dataset(num_cases=100)

        train_df, val_df, test_df = split_dataset_by_case(df, 0.6, 0.2, 0.2, seed=42)

        train_cases = set(train_df["case_id"].unique())
        val_cases = set(val_df["case_id"].unique())
        test_cases = set(test_df["case_id"].unique())

        self.assertEqual(len(train_cases.intersection(val_cases)), 0)
        self.assertEqual(len(train_cases.intersection(test_cases)), 0)
        self.assertEqual(len(val_cases.intersection(test_cases)), 0)
        self.assertEqual(len(train_cases) + len(val_cases) + len(test_cases), 100)

    def test_feature_extractor_outputs(self):
        """Feature extractor should produce expected columns and no NaNs."""
        gen = SyntheticLogGenerator(seed=42)
        df = gen.generate_dataset(num_cases=30)

        extractor = FeatureExtractor()
        feat_df, labels = extractor.extract_features_df(df)

        self.assertEqual(len(feat_df), 30)
        self.assertFalse(feat_df.isna().any().any())
        self.assertIn("total_event_count", feat_df.columns)
        self.assertIn("payment_attempt_count", feat_df.columns)
        self.assertIn("total_duration_hours", feat_df.columns)
        self.assertIn("inter_event_time_mean", feat_df.columns)
        self.assertIsNotNone(labels)
        self.assertEqual(len(labels), 30)


if __name__ == "__main__":
    unittest.main()
