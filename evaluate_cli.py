"""
CLI Evaluation and Verification Harness.
"""

import sys
from data.loader import load_event_log_csv, split_dataset_by_case
from evaluation.benchmark import EvaluationPipeline


def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample_event_log.csv"
    print(f"Loading event log from {csv_file}...")
    is_valid, err, df = load_event_log_csv(csv_file)
    if not is_valid:
        print(f"Error: {err}")
        sys.exit(1)

    print(f"Loaded {len(df)} events across {len(df['case_id'].unique())} cases.")
    train_df, val_df, test_df = split_dataset_by_case(df, 0.6, 0.2, 0.2, seed=42)

    pipeline = EvaluationPipeline(seed=42)
    res = pipeline.run_benchmark(train_df, val_df, test_df)

    print(f"\nEvaluated on {res['test_cases_count']} held-out test cases.")
    print(f"Optimal Threshold: {res['calibrated_threshold']:.3f}\n")
    print(f"{'Detector':<26} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'FPR':<10}")
    print("-" * 75)
    for name, m in res['metrics'].items():
        print(f"{name:<26} | {m['precision']:<10.3f} | {m['recall']:<10.3f} | {m['f1_score']:<10.3f} | {m['false_positive_rate']:<10.3f}")


if __name__ == "__main__":
    main()
