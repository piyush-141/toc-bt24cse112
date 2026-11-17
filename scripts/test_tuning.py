import sys
sys.path.insert(0, ".")
from data.generator import SyntheticLogGenerator
from data.loader import split_dataset_by_case
from features.extractor import FeatureExtractor
from models.isolation_forest import WorkflowIsolationForest
from models.clustering import ClusteringAnomalyDetector
from models.sequence_model import MarkovSequenceModel
from evaluation.metrics import compute_metrics
import numpy as np

gen = SyntheticLogGenerator(seed=42)
df = gen.generate_dataset(num_cases=1000)
train_df, val_df, test_df = split_dataset_by_case(df, 0.60, 0.20, 0.20, seed=42)

fe = FeatureExtractor()
X_train, y_train_cat = fe.extract_features_df(train_df)
X_val, y_val_cat = fe.extract_features_df(val_df)
X_test, y_test_cat = fe.extract_features_df(test_df)

y_val_bin = y_val_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)
y_test_bin = y_test_cat.apply(lambda x: 1 if "ANOMALY" in str(x) else 0)

train_normal_idx = y_train_cat[y_train_cat == "NORMAL"].index
X_train_clean = X_train.loc[train_normal_idx]

# Test Isolation Forest
iso = WorkflowIsolationForest(n_estimators=150, contamination=0.05, random_state=42)
iso.fit(X_train_clean)
val_scores = iso.predict_scores(X_val)
test_scores = iso.predict_scores(X_test)

# Let's see what threshold on val gives highest precision while recall >= 0.50
best_t = 0.5
best_prec = 0
for t in np.linspace(0.5, 0.95, 46):
    preds = (val_scores >= t).astype(int)
    m = compute_metrics(y_val_bin, preds)
    if m["precision"] > best_prec and m["recall"] >= 0.30:
        best_prec = m["precision"]
        best_t = t

preds_test = (test_scores >= best_t).astype(int)
m_test = compute_metrics(y_test_bin, preds_test)
print(f"Calibrated IsoForest (val t={best_t:.2f}): Prec: {m_test['precision']*100:.1f}%, Rec: {m_test['recall']*100:.1f}%, FP: {m_test['false_positives']}, TP: {m_test['true_positives']}")

# Test Clustering
cluster = ClusteringAnomalyDetector(n_clusters=5, random_state=42)
cluster.fit(X_train_clean)
c_val = cluster.predict_scores(X_val)
c_test = cluster.predict_scores(X_test)

best_ct = 0.5
best_c_prec = 0
for t in np.linspace(0.5, 0.98, 49):
    preds = (c_val >= t).astype(int)
    m = compute_metrics(y_val_bin, preds)
    if m["precision"] > best_c_prec and m["recall"] >= 0.30:
        best_c_prec = m["precision"]
        best_ct = t

c_test_preds = (c_test >= best_ct).astype(int)
m_c_test = compute_metrics(y_test_bin, c_test_preds)
print(f"Calibrated Clustering (val t={best_ct:.2f}): Prec: {m_c_test['precision']*100:.1f}%, Rec: {m_c_test['recall']*100:.1f}%, FP: {m_c_test['false_positives']}, TP: {m_c_test['true_positives']}")

# Test Markov Sequence Model
train_traces = [grp["event_type"].tolist() for _, grp in train_df.groupby("case_id")]
val_traces = [grp["event_type"].tolist() for _, grp in val_df.groupby("case_id")]
test_traces = [grp["event_type"].tolist() for _, grp in test_df.groupby("case_id")]

seq = MarkovSequenceModel(smoothing=0.01)
seq.fit(train_traces)
s_val = seq.predict_scores(val_traces)
s_test = seq.predict_scores(test_traces)

best_st = 0.5
best_s_prec = 0
for t in np.linspace(0.3, 0.95, 66):
    preds = (s_val >= t).astype(int)
    m = compute_metrics(y_val_bin, preds)
    if m["precision"] > best_s_prec and m["recall"] >= 0.30:
        best_s_prec = m["precision"]
        best_st = t

s_test_preds = (s_test >= best_st).astype(int)
m_s_test = compute_metrics(y_test_bin, s_test_preds)
print(f"Calibrated Markov (val t={best_st:.2f}): Prec: {m_s_test['precision']*100:.1f}%, Rec: {m_s_test['recall']*100:.1f}%, FP: {m_s_test['false_positives']}, TP: {m_s_test['true_positives']}")
