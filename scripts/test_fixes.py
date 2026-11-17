import sys
sys.path.insert(0, ".")
from workflow.specification import get_workflow_definition
from automata.dfa import DFAEngine
from evaluation.metrics import compute_metrics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

wf = get_workflow_definition("hospital_appointment")

def fixed_generate_generic_trace(workflow_def, rng, start_time, case_type, is_incomplete):
    curr_time = start_time
    events = []
    curr_state = workflow_def.initial_state
    step_count = 0
    max_steps = 15

    # Always inject rule anomaly on step 1 or 2
    rule_inject_step = rng.randint(1, 2) if case_type == "RULE_ANOMALY" else -1

    while step_count < max_steps:
        step_count += 1
        permitted = workflow_def.get_permitted_events(curr_state)
        if not permitted:
            break

        if case_type == "RULE_ANOMALY" and step_count >= rule_inject_step:
            illegal_candidates = [e for e in workflow_def.alphabet if e not in permitted]
            ev = rng.choice(illegal_candidates) if illegal_candidates else "ILLEGAL_EXTERNAL_EVENT"
            events.append({
                "timestamp": curr_time.isoformat(),
                "event_type": ev,
                "state_before": curr_state,
                "state_after": "INVALID",
            })
            break

        chosen_ev = rng.choice(permitted)
        next_state = workflow_def.delta(curr_state, chosen_ev)

        # Behavioral timing anomaly
        if case_type == "BEHAVIORAL_ANOMALY" and step_count == 2:
            curr_time += timedelta(days=rng.randint(15, 30))
        else:
            curr_time += timedelta(minutes=rng.randint(2, 60), seconds=rng.randint(0, 59))

        events.append({
            "timestamp": curr_time.isoformat(),
            "event_type": chosen_ev,
            "state_before": curr_state,
            "state_after": next_state,
        })
        curr_state = next_state

        if workflow_def.is_terminal(curr_state):
            break

    if is_incomplete and len(events) > 2:
        events = events[:-1]

    return events

# Test trace generation
rng = random.Random(42)
all_evs = []
for idx in range(400):
    cid = f"CASE_{idx+1:05d}"
    ctype = "NORMAL" if idx < 320 else ("RULE_ANOMALY" if idx < 360 else "BEHAVIORAL_ANOMALY")
    st = datetime(2026, 1, 1, 8, 0) + timedelta(minutes=rng.randint(0, 40000))
    evs = fixed_generate_generic_trace(wf, rng, st, ctype, False)
    for e in evs:
        e["case_id"] = cid
        e["ground_truth_anomaly_type"] = ctype
        all_evs.append(e)

df = pd.DataFrame(all_evs)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Test new Markov Model logic
class FixedMarkovModel:
    def __init__(self, smoothing=0.01):
        self.smoothing = smoothing
        self.transition_matrix = {}
        self.max_norm_nll = 1.5
        self.min_norm_nll = 0.5
        self.alphabet = []

    def fit(self, traces):
        all_events = set()
        for t in traces:
            all_events.update(t)
        self.alphabet = sorted(list(all_events))
        counts = {s: {d: 0.0 for d in self.alphabet} for s in self.alphabet}
        state_totals = {s: 0.0 for s in self.alphabet}
        for t in traces:
            for i in range(len(t) - 1):
                s, d = t[i], t[i + 1]
                counts[s][d] += 1.0
                state_totals[s] += 1.0
        V = len(self.alphabet)
        for s in self.alphabet:
            self.transition_matrix[s] = {}
            total = state_totals[s] + self.smoothing * V
            for d in self.alphabet:
                self.transition_matrix[s][d] = (counts[s][d] + self.smoothing) / total

        nlls = [self._score(t) for t in traces if len(t) > 1]
        self.min_norm_nll = float(np.percentile(nlls, 2.0))
        self.max_norm_nll = float(np.percentile(nlls, 98.0))
        return self

    def _score(self, trace):
        if len(trace) < 2:
            return 0.0
        nll_sum = 0.0
        for i in range(len(trace) - 1):
            s, d = trace[i], trace[i + 1]
            prob = self.transition_matrix.get(s, {}).get(d, 1e-4)
            nll_sum += -np.log(max(1e-10, prob))
        return nll_sum / max(1, len(trace) - 1)

    def predict_scores(self, traces):
        scores = []
        for t in traces:
            raw = self._score(t)
            if raw <= self.max_norm_nll:
                # Normal range maps to 0.0 - 0.20
                span = max(1e-5, self.max_norm_nll - self.min_norm_nll)
                sc = np.clip((raw - self.min_norm_nll) / span * 0.20, 0.0, 0.20)
            else:
                # Anomalous range maps to 0.50 - 1.00
                excess = raw - self.max_norm_nll
                sc = 0.50 + 0.50 * np.clip(excess / max(1.0, self.max_norm_nll), 0.0, 1.0)
            scores.append(float(sc))
        return np.array(scores)

from data.loader import split_dataset_by_case
train_df, val_df, test_df = split_dataset_by_case(df, 0.60, 0.20, 0.20, seed=42)

train_traces = [grp["event_type"].tolist() for _, grp in train_df.groupby("case_id")]
test_traces = [grp["event_type"].tolist() for _, grp in test_df.groupby("case_id")]
y_test_bin = test_df.groupby("case_id")["ground_truth_anomaly_type"].first().apply(lambda x: 1 if "ANOMALY" in str(x) else 0)

mkv = FixedMarkovModel(smoothing=0.01)
mkv.fit(train_traces)
scs = mkv.predict_scores(test_traces)
preds = (scs >= 0.50).astype(int)

m = compute_metrics(y_test_bin, preds)
print("FIXED MARKOV MODEL METRICS:")
print(f"Precision: {m['precision']*100:.1f}% | Recall: {m['recall']*100:.1f}% | FP: {m['false_positives']} | TP: {m['true_positives']} | FPR: {m['false_positive_rate']*100:.1f}%")
