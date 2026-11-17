# Machine Learning & Automata Theory in Workflow Sentinel

This document provides a comprehensive explanation of every detector card shown on the Evaluation dashboard, what each model does, what features/signals are extracted, their operational significance, why certain precision values are $100\%$, and whether only the Hybrid engine matters.

---

## 1. Quick Summary of the 6 Evaluator Cards

| Detector Card | Category / Type | Core Metric in Screenshot | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **Deterministic Automaton (DFA)** | Theory of Computation (Grammar / Rule-Based) | Precision: $100.0\%$, Recall: $48.0\%$, F1: $0.649$ | Enforces formal structural rules (syntax, transition validity, valid start & terminal states). Zero false positives on grammar violations. |
| **Isolation Forest** | ML Statistical (Unsupervised Tree Ensemble) | Precision: $33.3\%$, Recall: $1.3\%$, F1: $0.026$ | Detects numeric outliers (extreme event counts, timing delays, duration anomalies) via random recursive partitioning. |
| **Process Clustering (K-Means)** | ML Clustering (Unsupervised Geometric Distance) | Precision: $100.0\%$, Recall: $52.0\%$, F1: $0.684$ | Groups normal workflows into standard operational profiles; flags traces far from cluster centroids. |
| **Markov Sequence Model** | ML Sequence Probability (Stochastic Transition NLL) | Precision: $100.0\%$, Recall: $17.3\%$, F1: $0.295$ | Learns probability of transition pairs $P(e_t \mid e_{t-1})$; flags rare or unusual order of events using Negative Log-Likelihood (NLL). |
| **Supervised Random Forest** | Supervised ML (Ensemble Decision Trees) | Precision: $100.0\%$, Recall: $100.0\%$, F1: $1.000$ | Learns directly from ground-truth labels as an upper-bound benchmark for classification power. |
| **Hybrid Decision Engine** | Dual-Engine Synthesis (DFA + Ensemble ML) | Precision: $100.0\%$, Recall: $100.0\%$, F1: $1.000$ | **Primary operational engine**. Combines mathematical DFA guarantees with ML anomaly thresholds to capture all structural and behavioral anomalies. |

---

## 2. In-Depth Explanation of Each Component

### A. Deterministic Finite Automaton (DFA)
* **What it is**: A formal mathematical state machine $M = (Q, \Sigma, \delta, q_0, F)$ based on Theory of Computation (TOC).
* **What it uses from the data**:
  * Event labels in sequential order: $w = (e_1, e_2, \dots, e_n)$.
  * State transition mappings $\delta(q, e)$.
  * Start state $q_0$ and accepting states $F$.
* **How it detects anomalies**:
  * If a sequence contains an undefined step (e.g., shipping an order before payment is confirmed), $\delta(q, e)$ is undefined. The automaton immediately rejects the sequence.
  * If the execution halts before reaching an accepting state $q \in F$, it flags an incomplete/premature termination.
* **Its Significance & Limitations**:
  * **Significance**: Mathematically unshakeable. If a rule says *"Never discharge a patient without triage"*, a DFA catches it with 100% certainty and zero false alarms.
  * **Limitation**: Completely blind to *timing*, *duration*, or *abnormal retry frequencies* that still follow the legal syntax (e.g., 50 failed payment retries is grammatically valid in a loop, but statistically fraudulent). That is why Recall is only $48.0\%$ (it catches structural violations, but misses statistical/behavioral ones).

---

### B. Isolation Forest
* **What it is**: An unsupervised ensemble algorithm that builds random decision trees (iTrees) to isolate anomalies.
* **What it uses from the data**:
  * Vectorized numeric case features: trace duration, inter-event time deltas, total event count, event frequency histograms.
* **How it detects anomalies**:
  * Anomalies are few and different, meaning they get isolated near the root of the tree with fewer splits (short path length).
  * Points with short average path lengths receive a high anomaly score.
* **Its Significance & Limitations**:
  * **Significance**: Excellent for finding pure extreme outliers (e.g., a process that took 10 hours instead of 5 minutes, or had 200 events instead of 5).
  * **Why its numbers are lower here (F1: $0.026$)**: In synthetic or structured workflow logs, anomalies often consist of a single swapped event or subtle order violation rather than extreme numeric duration spikes. Without massive timing variances, Isolation Forest only isolates the most extreme case (catching 1 TP with 2 FP).

---

### C. Process Clustering (K-Means)
* **What it is**: An unsupervised geometric algorithm that partitions workflows into $k$ clusters of typical operational behavior.
* **What it uses from the data**:
  * Normalized feature vectors representing event presence, relative frequency, and process flow patterns.
* **How it detects anomalies**:
  * Computes the distance from each workflow's feature vector to the nearest cluster centroid $\mu_k$.
  * Workflows whose distance exceeds a distance percentile threshold are flagged as anomalous.
* **Its Significance**:
  * Discovers natural behavioral archetypes (e.g., "fast-track checkout", "standard checkout with coupon", "disputed return"). Traces that do not fit standard operational paths get flagged.
  * Yields $52.0\%$ Recall and $0\%$ False Positive Rate because irregular event combinations project far outside normal cluster boundaries.

---

### D. Markov Sequence Model (NLL)
* **What it is**: A stochastic statistical model that calculates the probability of transitioning from event $A$ to event $B$:
  $$P(e_t \mid e_{t-1}) = \frac{\text{Count}(e_{t-1} \to e_t) + \alpha}{\text{Count}(e_{t-1}) + \alpha \cdot |\Sigma|}$$
  *(using Laplace smoothing $\alpha$)*.
* **What it uses from the data**:
  * Sequential transition bigrams $(e_{t-1}, e_t)$.
* **How it detects anomalies**:
  * For any execution trace, it sums the Negative Log-Likelihood (NLL) across all steps:
    $$\text{NLL}(w) = -\frac{1}{n} \sum_{t=1}^n \log P(e_t \mid e_{t-1})$$
  * Common paths have high probability (low NLL). Sequences containing rare or unseen transitions accumulate high NLL scores and exceed the threshold.
* **Its Significance**:
  * Bridges grammar and statistics. Unlike the strict binary DFA, the Markov model gives a continuous likelihood score.
  * Catches rare sequences that are technically possible but statistically abnormal in real-world traffic.

---

### E. Supervised Random Forest
* **What it is**: A supervised ensemble of decision trees trained with ground-truth labeled historical logs (`is_anomaly = 0 or 1`).
* **What it uses from the data**:
  * All tabular sequence features, transition bigrams, time metrics, and event frequencies alongside the supervised labels.
* **How it detects anomalies**:
  * Learns non-linear decision boundaries splitting features to separate normal from anomalous classes.
* **Its Significance & Purpose**:
  * Acts as a **Theoretical Ceiling / Benchmark**.
  * Shows how well an ML model could perform if you had abundant labeled historical anomalies.
  * **Real-world caveat**: In production, new anomalies are zero-day (unlabeled), so unsupervised models and DFAs are essential when true labels do not exist beforehand.

---

### F. Hybrid Decision Engine (The Primary Engine)
* **What it is**: A dual-engine synthesis system combining formal automata theory (DFA) with multi-model ML scoring.
* **How it works & What happens if DFA fails**:
  * **Parallel Evaluation**: Every trace is evaluated by **both** the DFA and the ML models concurrently. The ML models are **never skipped**, even if the DFA rejects the trace.
  * **If DFA Fails (`AutomataStatus.INVALID`)**:
    * If ML also detects anomalies (severe delay, flood, or rare transition likelihood), the execution is classified as:
      $$\mathbf{CRITICAL:}\ \text{INVALID \& ANOMALOUS}\quad (\text{Score } \approx 0.95 - 1.00)$$
    * If ML finds standard durations and regular event counts, it is classified as:
      $$\mathbf{HIGH:}\ \text{INVALID (Pure Structural Rule Violation)}\quad (\text{Score } = 0.92)$$
    * **Why this matters**: Operators immediately know whether someone made an innocent out-of-order process error or if an adversarial attack was combined with a bot flood.
  * **If DFA Passes (`AutomataStatus.VALID_COMPLETED`)**:
    * The trace is syntactically sound. The engine now inspects the ML anomaly score.
    * If ML triggers ($\ge \text{threshold}$), it is classified as:
      $$\mathbf{MEDIUM:}\ \text{SUSPICIOUS (Behavioral Outlier)}\quad (\text{Score } \in [0.58, 0.88])$$
    * If ML is also clean, it is classified as:
      $$\mathbf{LOW:}\ \text{NORMAL}\quad (\text{Score } \le 0.15)$$
  * **If DFA Halts Prematurely (`AutomataStatus.VALID_INCOMPLETE`)**:
    * It is classified as:
      $$\mathbf{LOW:}\ \text{INCOMPLETE}\quad (\text{Score } \approx 0.20 - 0.32)$$

---

## 2.1 Complete Execution Flowchart: What Happens When a Trace Arrives?

```
                          ┌─────────────────────────────┐
                          │    Incoming Workflow Trace  │
                          │   (Event sequence + Timestamps)│
                          └──────────────┬──────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
                    ▼                                         ▼
         ┌───────────────────────┐               ┌────────────────────────┐
         │      DFA Engine       │               │      ML Ensembles      │
         │  (Grammar Validation) │               │   (Feature Extraction) │
         └──────────┬────────────┘               └───────────┬────────────┘
                    │                                        │
           Does sequence follow                    Extract timing, duration,
           valid transitions δ?                     frequencies & bigrams
                    │                                        │
          ┌─────────┴─────────┐                              ▼
          │                   │                 Compute Ensembles Score:
      [ PASSED ]          [ FAILED ]             Isolation Forest + Markov
          │                   │                              │
          │                   │                              ▼
          │                   │                    Is Score >= Threshold?
          │                   │                              │
          │                   ├───────────────────────┬──────┴──────┐
          │                   │                       │             │
          │                   ▼                       ▼             ▼
          │            ML ALSO FLAGS            ML IS CLEAN   (ML Decision)
          │                   │                       │
          │                   ▼                       ▼
          │            ┌─────────────┐         ┌─────────────┐
          │            │  CRITICAL   │         │    HIGH     │
          │            │  INVALID &  │         │   INVALID   │
          │            │  ANOMALOUS  │         │ (Rule Only) │
          │            │ (Score ~1.0)│         │ (Score 0.92)│
          │            └─────────────┘         └─────────────┘
          │
          └───────────────────────────┐
                                      ▼
                               Is ML Anomalous?
                                ├── YES ──> [ SUSPICIOUS (Score 0.58 - 0.88) ]
                                └── NO  ──> [ NORMAL (Score 0.02 - 0.14) ]
```

---

## 3. Why Are Several Precisions $100.0\%$? Is It Fake?

### No, it is not fake. Here is the mathematical reason:

Recall the definition of **Precision**:
$$\text{Precision} = \frac{\text{True Positives (TP)}}{\text{True Positives (TP)} + \text{False Positives (FP)}}$$

* Look at the confusion matrices in your screenshot:
  * **DFA**: $\text{TP} = 36, \mathbf{FP = 0}$. $\implies \frac{36}{36 + 0} = 100.0\%$
  * **Process Clustering**: $\text{TP} = 39, \mathbf{FP = 0}$. $\implies \frac{39}{39 + 0} = 100.0\%$
  * **Markov Sequence Model**: $\text{TP} = 13, \mathbf{FP = 0}$. $\implies \frac{13}{13 + 0} = 100.0\%$
* **Why is FP zero?**
  1. **Strict Determinism**: A DFA only fires when a transition violates defined business rules. A completely normal transaction will **never** trigger an undefined DFA transition. Hence, $\text{FP} = 0$.
  2. **Conservative Calibrated Thresholds**: For the unsupervised models (Clustering and Markov), the anomaly thresholds are calibrated on known clean baseline behavior. The threshold is set high enough so that no normal trace is accidentally flagged.
  3. **The Trade-Off is Low Recall, NOT Fake Precision**:
     * Notice the DFA missed 39 anomalies ($\text{FN} = 39$, Recall is only $48\%$).
     * The Markov model missed 62 anomalies ($\text{FN} = 62$, Recall is only $17.3\%$).
     * If this were "fake" or overfitted to look perfect, the Recall would also be $100\%$. The models are being very conservative: **when they raise an alarm, they are 100% certain, but they miss other anomaly types.**

---

## 4. Is ONLY the Hybrid Model Important?

### Short Answer:
**In production output, the Hybrid Engine is the most effective detector, but the individual models are critical for explanation, defense-in-depth, and operational diagnostics.**

### Long Answer: Why the individual models are necessary:

1. **Root-Cause Explainability (The "Why")**:
   * If a system simply says *"Anomaly detected (Score: 0.98)"*, operators cannot act quickly.
   * Because we keep the individual models active, the Hybrid Engine can provide exact diagnostics:
     * *DFA alerted?* $\to$ *"Compliance violation: Step 'ORDER_SHIPPED' occurred before 'PAYMENT_CONFIRMED'."*
     * *Markov alerted?* $\to$ *"Statistical anomaly: Sequence of actions is historically unprecedented."*
     * *Isolation Forest alerted?* $\to$ *"Performance anomaly: Execution latency exceeded $3.5\sigma$."*
2. **Complementary Coverage**:
   * A DFA alone has only $48\%$ recall. It misses fraud rings that execute valid sequences at inhuman speeds.
   * Pure ML alone suffers from false alarms or poor explainability.
3. **Upper-Bound Validation (Random Forest)**:
   * Having the Supervised Random Forest benchmark proves that the feature extraction pipeline captures enough signal to achieve near-optimal separation.
4. **Defense in Depth**:
   * If a business process updates without the DFA schema being updated immediately, the unsupervised models (Clustering, Markov) continue catching anomalies independently.

---

## 5. Summary Mental Model

```
             ┌────────────────────────────────────────────────────────┐
             │                     INCOMING TRACE                     │
             └───────────────────────────┬────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
               [ STRUCTURAL CHECK ]             [ STATISTICAL CHECK ]
                       DFA                      Markov, K-Means, iForest
                         │                               │
        Catches: Invalid transitions,           Catches: Delays, loops,
        skipped steps, illegal states.          unusual frequencies.
        (Precision: 100%, Recall: 48%)          (Precision: High, Variable Recall)
                         │                               │
                         └───────────────┬───────────────┘
                                         ▼
                         ┌───────────────────────────────┐
                         │     HYBRID DECISION ENGINE    │
                         │   Combines both for 100% F1   │
                         │  Provides exact root cause    │
                         └───────────────────────────────┘
```

