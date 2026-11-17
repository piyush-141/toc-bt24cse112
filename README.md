# Workflow Sentinel: Process Workflow Anomaly Detection Using Automata & Machine Learning

> **A dual-engine workflow monitoring and anomaly detection system implementing Deterministic Finite Automata (DFA) alongside unsupervised and supervised Machine Learning (Isolation Forest, Process Clustering, Markov Sequence Modeling, and Random Forest). Designed for compliance, process intelligence, and root-cause explanation across multi-domain business workflows.**

---

## 1. Executive Overview & Problem Statement Alignment

This platform directly solves **Problem 9: Anomaly Detection in Process Workflows Using Automata and ML**:

| Problem 9 Objective | Implementation in System |
|:---|:---|
| **Select a workflow and define states, events, transition rules** | Pre-built with the 4 problem-statement domains (**Online Payment Processing**, **Student Course Registration**, **Hospital Patient Appointments**, and **Supply Chain Order Management**), plus a visual **Custom Workflow Creator** to define any arbitrary process automaton. |
| **Generate or collect event logs containing normal and anomalous sequences** | Synthetic event log generator simulating valid process paths, timing delays, repetitive retry loops, invalid transitions, and skipped states, alongside CSV upload with schema validation. |
| **Build a finite-state model to identify invalid transitions** | Formal Deterministic Finite Automaton (DFA) engine $M = (Q, \Sigma, \delta, q_0, F)$ validating step-by-step transition legality, premature termination, and alphabet containment. |
| **Train ML models to detect statistical or sequential anomalies** | Implements and benchmarks all four required ML techniques: **Isolation Forest**, **Process Clustering (K-Means)**, **Markov Sequence Models (NLL)**, and **Supervised Random Forest**. |
| **Combine rule-based violations with ML anomaly scores** | Hybrid decision engine categorizing executions into **Normal**, **Suspicious** (statistical anomaly), **Invalid** (syntax violation), and **Invalid + Anomalous** (compound failure). |
| **Evaluate detection performance & explain each sequence** | Full benchmark suite computing Precision, Recall, F1, FPR, confusion matrices, category recall, and evidence-based diagnostic explanations for every execution. |
| **TOC Concepts** | State-transition systems, DFA formal 5-tuple, regular language acceptance $L(M)$, and BFS reachability analysis verifying reachable vs. dead states. |
| **Expected Outcome** | Minimal, light-mode canvas dashboard displaying execution paths, unusual transitions, reachability status, and anomaly scores with zero display delay. |

---

## 2. Theory of Computation (TOC) Formal Grounding

Every monitored workflow is represented as a formal Deterministic Finite Automaton (DFA):
$$M = (Q, \Sigma, \delta, q_0, F)$$

### Formal Components
1. **$Q$ (States)**: Finite set of distinct operational process states.
2. **$\Sigma$ (Alphabet)**: Finite alphabet of business event symbols.
3. **$\delta: Q \times \Sigma \to Q$ (Transition Function)**: Deterministic mapping defining valid state evolutions.
4. **$q_0 \in Q$ (Start State)**: Unique entry point for all process executions.
5. **$F \subseteq Q$ (Accepting States)**: Set of terminal states signifying complete fulfillment or authorized closure.

### Language Acceptance & Reachability
- **Regular Language Acceptance**:
  $$L(M) = \{w \in \Sigma^* \mid \delta^*(q_0, w) \in F\}$$
  A trace execution string $w = e_1 e_2 \dots e_n$ is accepted if every event is defined by $\delta$ and the process halts in an accepting state $q_n \in F$.
- **Breadth-First Search (BFS) Reachability**:
  The system computes the reachable set $R = \{q \in Q \mid \exists w \in \Sigma^*, \delta^*(q_0, w) = q\}$ to mathematically guarantee zero disconnected or unreachable states exist in the workflow graph.

---

## 3. Supported Multi-Domain Workflows

The application includes 4 pre-built domains and supports adding any custom automaton:

### 1. Online Payment & Order Processing (`online_orders`)
- **Domain**: E-Commerce & Retail
- **States (11)**: `START`, `ORDER_PLACED`, `PAYMENT_PENDING`, `PAYMENT_FAILED`, `PAYMENT_CONFIRMED`, `ORDER_PACKED`, `ORDER_SHIPPED`, `ORDER_DELIVERED`, `ORDER_CANCELLED`, `REFUND_PENDING`, `REFUND_COMPLETED`.
- **Key Anomaly Modes**: Premature shipping before payment, premature delivery before packing, unauthorized refund sequences, payment retry loops.

### 2. Student Course Registration (`student_registration`)
- **Domain**: Higher Education
- **States (9)**: `START`, `PORTAL_ACTIVE`, `COURSES_SELECTED`, `PREREQS_VERIFIED`, `ADVISOR_PENDING`, `PAYMENT_REQUIRED`, `ENROLLED_CONFIRMED`, `ON_WAITLIST`, `SESSION_ENDED`.
- **Key Anomaly Modes**: Bypassing prerequisite verification, enrolling without advisor clearance, skipping tuition payments.

### 3. Hospital Patient Appointment (`hospital_appointment`)
- **Domain**: Healthcare & Clinical Outpatient
- **States (9)**: `START`, `APPOINTMENT_REQUESTED`, `BOOKING_CONFIRMED`, `TRIAGE_WAITING`, `DOCTOR_EXAM_PENDING`, `EXAM_IN_PROGRESS`, `LAB_TESTING`, `PATIENT_DISCHARGED`, `VISIT_CANCELLED`.
- **Key Anomaly Modes**: Doctor examination without nurse triage, discharging before completing mandatory lab test orders.

### 4. Supply Chain B2B Order Management (`order_management`)
- **Domain**: Enterprise Logistics
- **States (9)**: `START`, `PO_RECEIVED`, `CREDIT_APPROVED`, `INVENTORY_RESERVED`, `IN_TRANSIT`, `DELIVERED_POD`, `DISPUTE_INVESTIGATION`, `ACCOUNT_SETTLED`, `ORDER_REJECTED`.
- **Key Anomaly Modes**: Dispatching goods before credit approval, closing purchase orders with unresolved open disputes.

### 5. Dynamic Custom Workflow Creator
- **Interactive UI Modal**: Allows defining any new process automaton on the fly by entering $Q, \Sigma, q_0, F$ and $\delta$ rules, or loading from pre-configured business templates (Expense Approval, Support Tickets, CI/CD Pipelines).
- **Smart DAG Layout**: Automatically arranges custom nodes in a clean topological grid.

---

## 4. Machine Learning Detectors & Benchmark

The system integrates four distinct ML approaches to detect subtle sequential and behavioral anomalies:

1. **Isolation Forest** (`models/isolation_forest.py`):
   - Unsupervised ensemble of isolation trees partitioning case-level frequency, inter-event timing, and transition count features.
   - Outputs normalized anomaly scores $s \in [0, 1]$. Cutoff threshold $\tau$ calibrated on validation split.
2. **Process Clustering (K-Means)** (`models/clustering.py`):
   - Clusters standard execution patterns in normalized feature space.
   - Calculates Euclidean distance to nearest cluster centroid as an outlier score.
3. **Markov Sequence Model** (`models/sequence_model.py`):
   - Models first-order transition probabilities $P(e_t \mid e_{t-1})$ with Laplace smoothing.
   - Computes normalized sequence Negative Log-Likelihood (NLL). Flags rare, improbable execution sequences.
4. **Supervised Random Forest Benchmark** (`models/comparison.py`):
   - Supervised classification model trained on labeled subsets to establish theoretical upper-bound performance.

---

## 5. How to Run the Project

You can run the project either as a **unified application** (single command) or by running the **Python backend server and React frontend separately**.

---

### Option A: Unified Single-Command Start (Recommended)
This runs the Python backend and serves the production-built React frontend together on port `8000`:

```bash
# 1. Install dependencies (first time only)
pip install -r requirements.txt

# 2. Start unified server
python start.py
```
Open **`http://localhost:8000`** in your browser.

---

### Option B: Running Backend Server & Frontend Separately (Development Mode)

If you are developing or want hot-reloading for the frontend, run the backend and frontend in two separate terminal windows:

#### Terminal 1 — Python Backend Server:
```bash
# Activate your python virtual environment (if using one)
# .venv\Scripts\activate   (Windows)
# source .venv/bin/activate (Linux/Mac)

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI server with live reload
uvicorn server:app --reload --port 8000
```
> The API will be available at **`http://localhost:8000`** (Swagger docs at `http://localhost:8000/docs`).

#### Terminal 2 — React Frontend (Vite):
```bash
# Navigate to the frontend directory
cd frontend

# Install frontend node modules (first time only)
npm install

# Start Vite dev server with Hot Module Replacement (HMR)
npm run dev
```
> The React dashboard will be running at **`http://localhost:5173`**.
> It automatically proxies all `/api/*` network requests to the Python backend running on port `8000`.

---

## 6. Development, Testing & Verification Guide

### Run Automated Unit Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```
*(Runs 16 unit and integration tests across DFA validation, dynamic feature extraction, ML models, and hybrid decision logic in < 1 second).*

### Rebuild Frontend Production Bundle
If you modify frontend code and want to serve it through `start.py` or FastAPI directly:
```bash
cd frontend
npm run build
```
This generates the optimized static files into `frontend/dist/`.

---

## 7. Decision Fusion Matrix & Anomaly Scoring

| DFA Syntax Status | ML Anomaly Score | Final Classification | Severity | Diagnostic Explanation |
|:---|:---:|:---|:---:|:---|
| `VALID_COMPLETED` | $0.02 - 0.15$ | **Normal** | `LOW` | Sequence strictly complies with DFA transition rules and typical durations. |
| `VALID_COMPLETED` | $0.60 - 0.85$ (graded) | **Suspicious** | `MEDIUM` | **Valid syntax, abnormal behavior**: Follows legal state transitions, but exhibits anomalous latency, looping, or retry thrashing. Score is graded based on deviation magnitude (never 1.00). |
| `INVALID` | $0.92 - 1.00$ | **Invalid** / **Invalid + Anomalous** | `HIGH` / `CRITICAL` | Predefined transition rule violated (e.g. state skipped or illegal event). Compound failure if combined with statistical outlier. |
| `VALID_INCOMPLETE`| $0.20 - 0.30$ | **Incomplete** | `LOW` | Valid prefix currently in-flight; has not yet reached terminal state. |
