"""
Sequence-Based Anomaly Detector using Bigram Transition Probabilities.

Models transition dynamics P(e_t | e_{t-1}) directly from event sequences:
- Learns stochastic transition matrix from observed normal executions with Laplace smoothing.
- Calculates the average Negative Log-Likelihood (NLL) for any sequence w in Sigma*.
- Identifies sequences with improbable or unnatural event ordering.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


class MarkovSequenceModel:
    """
    Bigram Markov sequence anomaly detector.
    Computes sequence anomaly scores based on statistical transition likelihood.
    """

    def __init__(self, smoothing: float = 0.01):
        self.smoothing = smoothing
        self.alphabet: List[str] = []
        self.transition_matrix: Dict[str, Dict[str, float]] = {}
        self.threshold: float = 0.50
        self.min_normal_nll: float = 0.5
        self.max_normal_nll: float = 1.5
        self.is_fitted: bool = False

    def fit(self, traces: List[List[str]]) -> "MarkovSequenceModel":
        """
        Learn transition probabilities from a collection of event lists.
        """
        all_events = set()
        for t in traces:
            all_events.update(t)
        self.alphabet = sorted(list(all_events))

        # Count bigram frequencies
        counts: Dict[str, Dict[str, float]] = {s: {d: 0.0 for d in self.alphabet} for s in self.alphabet}
        state_totals: Dict[str, float] = {s: 0.0 for s in self.alphabet}

        for t in traces:
            for i in range(len(t) - 1):
                s, d = t[i], t[i + 1]
                counts[s][d] += 1.0
                state_totals[s] += 1.0

        # Compute probabilities with Laplace smoothing
        V = max(1, len(self.alphabet))
        self.transition_matrix = {}
        for s in self.alphabet:
            self.transition_matrix[s] = {}
            total = state_totals[s] + self.smoothing * V
            for d in self.alphabet:
                prob = (counts[s][d] + self.smoothing) / total
                self.transition_matrix[s][d] = prob

        # Compute NLL bounds on training traces
        nlls = [self._score_single_trace(t) for t in traces if len(t) > 1]
        if nlls:
            self.min_normal_nll = float(np.min(nlls))
            self.max_normal_nll = float(np.max(nlls))
            self.threshold = 0.50
        else:
            self.min_normal_nll = 0.5
            self.max_normal_nll = 2.0
            self.threshold = 0.50

        self.is_fitted = True
        return self

    def _score_single_trace(self, trace: List[str]) -> float:
        """Calculate mean negative log-likelihood for a trace."""
        if len(trace) < 2:
            return 0.0

        nll_sum = 0.0
        count = 0
        for i in range(len(trace) - 1):
            s, d = trace[i], trace[i + 1]
            if s in self.transition_matrix and d in self.transition_matrix[s]:
                prob = self.transition_matrix[s][d]
            else:
                prob = self.smoothing / (1.0 + self.smoothing * max(1, len(self.alphabet)))
            nll_sum += -np.log(max(1e-10, prob))
            count += 1

        return nll_sum / max(1, count)

    def predict_scores(self, traces: List[List[str]]) -> np.ndarray:
        ceiling = self.max_normal_nll * 1.15 + 0.08
        scores = []
        for t in traces:
            raw_nll = self._score_single_trace(t)
            if raw_nll <= ceiling:
                span = max(1e-5, ceiling - self.min_normal_nll)
                norm = np.clip((raw_nll - self.min_normal_nll) / span * 0.20, 0.0, 0.20)
            else:
                excess = raw_nll - ceiling
                norm = 0.50 + 0.50 * np.clip(excess / max(1.0, ceiling), 0.0, 1.0)
            scores.append(float(norm))
        return np.array(scores)

    def predict(self, traces: List[List[str]], threshold: Optional[float] = None) -> np.ndarray:
        th = threshold if threshold is not None else self.threshold
        scores = self.predict_scores(traces)
        return (scores >= th).astype(int)
