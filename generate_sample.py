"""
Generate baseline sample dataset and display reproducible evaluation results.
"""

from data.generator import SyntheticLogGenerator
from data.loader import split_dataset_by_case
from evaluation.benchmark import EvaluationPipeline
import os

os.makedirs("data", exist_ok=True)

print("Generating 1,000 cases synthetic event log...")
gen = SyntheticLogGenerator(seed=42)
df = gen.generate_dataset(num_cases=1000)
csv_path = os.path.join("data", "sample_event_log.csv")
df.to_csv(csv_path, index=False)
print(f"Saved sample dataset to {csv_path} ({len(df)} events)")

print("\nRunning benchmark on held-out test split...")
train_df, val_df, test_df = split_dataset_by_case(df, 0.6, 0.2, 0.2, seed=42)

pipeline = EvaluationPipeline(seed=42)
res = pipeline.run_benchmark(train_df, val_df, test_df)

print(f"Test cases count: {res['test_cases_count']}")
print(f"Calibrated ML threshold: {res['calibrated_threshold']:.3f}\n")

print(f"{'Detector':<26} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'FPR':<10}")
print("-" * 75)
for name, m in res['metrics'].items():
    print(f"{name:<26} | {m['precision']:<10.3f} | {m['recall']:<10.3f} | {m['f1_score']:<10.3f} | {m['false_positive_rate']:<10.3f}")

print("\nCategory Recall Breakdown:")
for cat, stats in res['category_breakdown']['hybrid'].items():
    dfa_cr = res['category_breakdown']['automata_only'].get(cat, {}).get('catch_rate', 0.0)
    ml_cr = res['category_breakdown']['ml_only'].get(cat, {}).get('catch_rate', 0.0)
    hyb_cr = stats.get('catch_rate', 0.0)
    print(f"  {cat:<22}: DFA={dfa_cr*100:5.1f}% | ML={ml_cr*100:5.1f}% | Hybrid={hyb_cr*100:5.1f}%")
