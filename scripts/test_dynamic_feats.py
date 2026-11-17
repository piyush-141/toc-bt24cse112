import sys
sys.path.insert(0, ".")
from workflow.specification import get_workflow_definition
from automata.dfa import DFAEngine
from data.generator import SyntheticLogGenerator
from data.loader import split_dataset_by_case
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load Hospital Appointment
wf = get_workflow_definition("hospital_appointment")
dfa = DFAEngine(wf)
gen = SyntheticLogGenerator(seed=42, workflow_def=wf)
df = gen.generate_dataset(num_cases=400)
train_df, val_df, test_df = split_dataset_by_case(df, 0.60, 0.20, 0.20, seed=42)

# Dynamic Feature Extractor
def extract_dynamic_features(dataset_df, train_alphabet=None, train_bigrams=None):
    if train_alphabet is None:
        train_alphabet = sorted(list(dataset_df["event_type"].unique()))
    
    # Collect all bigrams
    if train_bigrams is None:
        bg_set = set()
        for _, grp in dataset_df.groupby("case_id"):
            evs = grp["event_type"].tolist()
            for i in range(len(evs) - 1):
                bg_set.add((evs[i], evs[i+1]))
        train_bigrams = sorted(list(bg_set))

    rows = []
    labels = {}
    for case_id, grp in dataset_df.groupby("case_id"):
        grp = grp.sort_values("timestamp")
        evs = grp["event_type"].tolist()
        tss = pd.to_datetime(grp["timestamp"]).tolist()
        n = len(evs)
        f = {}
        f["total_events"] = n
        
        # Temporal
        if n > 1:
            diffs = [(tss[i] - tss[i-1]).total_seconds() for i in range(1, n)]
            total_sec = (tss[-1] - tss[0]).total_seconds()
            f["total_duration_sec"] = total_sec
            f["inter_event_mean"] = float(np.mean(diffs))
            f["inter_event_std"] = float(np.std(diffs)) if len(diffs) > 1 else 0.0
            f["inter_event_max"] = float(np.max(diffs))
            f["inter_event_min"] = float(np.min(diffs))
        else:
            f["total_duration_sec"] = 0.0
            f["inter_event_mean"] = 0.0
            f["inter_event_std"] = 0.0
            f["inter_event_max"] = 0.0
            f["inter_event_min"] = 0.0
            
        # Frequency of all alphabet symbols
        for ev in train_alphabet:
            f[f"freq_{ev}"] = evs.count(ev) / max(1, n)
            
        # Bigrams
        bgs = list(zip(evs[:-1], evs[1:])) if n > 1 else []
        for (s, d) in train_bigrams:
            f[f"bg_{s}_{d}"] = bgs.count((s, d))
            
        f["case_id"] = case_id
        rows.append(f)
        if "ground_truth_anomaly_type" in grp.columns:
            labels[case_id] = grp["ground_truth_anomaly_type"].iloc[0]

    feat_df = pd.DataFrame(rows).set_index("case_id")
    label_ser = pd.Series(labels) if labels else None
    return feat_df, label_ser, train_alphabet, train_bigrams

X_train, y_train_cat, alph, bgs = extract_dynamic_features(train_df)
X_val, y_val_cat, _, _ = extract_dynamic_features(val_df, alph, bgs)
X_test, y_test_cat, _, _ = extract_dynamic_features(test_df, alph, bgs)

y_train_bin = y_train_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)
y_test_bin = y_test_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train_bin)
rf_preds = rf.predict(X_test)

from evaluation.metrics import compute_metrics
m = compute_metrics(y_test_bin, rf_preds)
print("DYNAMIC RF ON HOSPITAL APPOINTMENT:")
print(f"Precision: {m['precision']*100:.1f}% | Recall: {m['recall']*100:.1f}% | FP: {m['false_positives']} | TP: {m['true_positives']}")

