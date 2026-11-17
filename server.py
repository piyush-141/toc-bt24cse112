"""
FastAPI Server connecting Automata & ML Workflow Anomaly Detection Backend.
Supports multi-domain workflows and dynamic custom workflow creation.
"""

import os
import io
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np

from workflow.specification import (
    WorkflowDefinition,
    get_workflow_definition,
    list_available_workflows,
    register_custom_workflow,
    WORKFLOW_REGISTRY,
)
from automata.dfa import DFAEngine, AutomataStatus
from data.generator import SyntheticLogGenerator
from data.loader import load_event_log_csv, split_dataset_by_case
from features.extractor import FeatureExtractor
from models.isolation_forest import WorkflowIsolationForest
from detection.engine import HybridDetectionEngine
from evaluation.benchmark import EvaluationPipeline

app = FastAPI(
    title="Workflow Sentinel API",
    description="Automata and ML Hybrid Engine for Multi-Domain Process Workflows",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GlobalState:
    def __init__(self):
        self.active_workflow: WorkflowDefinition = get_workflow_definition("online_orders")
        self.dfa = DFAEngine(self.active_workflow)
        self.generator = SyntheticLogGenerator(seed=42, workflow_def=self.active_workflow)
        self.ml_model: Optional[WorkflowIsolationForest] = None
        self.current_events_df: Optional[pd.DataFrame] = None
        self.current_detections_df: Optional[pd.DataFrame] = None
        self.current_validation_results: Dict[str, Any] = {}
        self.benchmark_results: Optional[Dict[str, Any]] = None
        self.dataset_meta: Dict[str, Any] = {}

    def set_workflow(self, workflow_id: str, num_cases: int = 2000):
        """Switch active workflow and initialize training."""
        self.active_workflow = get_workflow_definition(workflow_id)
        self.dfa = DFAEngine(self.active_workflow)
        self.generator = SyntheticLogGenerator(seed=42, workflow_def=self.active_workflow)
        self.initialize_dataset(num_cases=num_cases)

    def initialize_dataset(self, num_cases: int = 2000):
        """Generate dataset and calibrate detectors."""
        csv_path = os.path.join("data", "sample_event_log.csv")
        if self.active_workflow.id == "online_orders" and os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")
                if len(df["case_id"].unique()) < num_cases:
                    df = self.generator.generate_dataset(num_cases=num_cases)
            except Exception:
                df = self.generator.generate_dataset(num_cases=num_cases)
        else:
            df = self.generator.generate_dataset(num_cases=num_cases)

        self.current_events_df = df
        train_df, val_df, test_df = split_dataset_by_case(df, 0.60, 0.20, 0.20, seed=42)

        pipeline = EvaluationPipeline(seed=42, dfa_engine=self.dfa)
        benchmark = pipeline.run_benchmark(train_df, val_df, test_df)
        self.ml_model = benchmark["trained_model"]
        self.benchmark_results = benchmark

        engine = HybridDetectionEngine(dfa_engine=self.dfa, ml_model=self.ml_model)
        records_df, val_results = engine.process_dataset(df)
        self.current_detections_df = records_df
        self.current_validation_results = val_results
        self.dataset_meta = {
            "name": f"{self.active_workflow.name}",
            "domain": self.active_workflow.domain,
            "workflow_id": self.active_workflow.id,
            "is_synthetic": True,
            "case_count": len(records_df),
            "event_count": len(df),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

state = GlobalState()


@app.on_event("startup")
def startup_event():
    # Large, varied dataset initialization on startup
    state.initialize_dataset(num_cases=2000)


@app.get("/api/workflows")
def get_workflows():
    """List all available workflows (presets and custom)."""
    return {
        "active_workflow_id": state.active_workflow.id,
        "workflows": list_available_workflows(),
    }


@app.post("/api/workflows/select/{workflow_id}")
def select_workflow(workflow_id: str):
    """Switch active workflow."""
    if workflow_id not in WORKFLOW_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    state.set_workflow(workflow_id, num_cases=2000)
    return {
        "status": "success",
        "active_workflow": state.active_workflow.to_graph_data(),
        "meta": state.dataset_meta,
    }


class CustomWorkflowRequest(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    initial_state: str
    states: List[str]
    alphabet: List[str]
    terminal_states: List[str]
    transitions: List[Dict[str, str]]  # [{"from": "A", "event": "E", "to": "B"}]


@app.post("/api/workflows/create")
def create_custom_workflow(req: CustomWorkflowRequest):
    """Create and activate a custom user-defined workflow."""
    w_def = register_custom_workflow(
        workflow_id=req.id,
        name=req.name,
        domain=req.domain,
        description=req.description,
        initial_state=req.initial_state,
        states=req.states,
        alphabet=req.alphabet,
        terminal_states=req.terminal_states,
        transitions_list=req.transitions,
    )
    state.set_workflow(w_def.id, num_cases=300)
    return {
        "status": "success",
        "active_workflow": state.active_workflow.to_graph_data(),
        "meta": state.dataset_meta,
    }


@app.get("/api/workflow/graph")
def get_workflow_graph():
    """Returns active workflow definition and graph in < 1ms."""
    return state.active_workflow.to_graph_data()


@app.get("/api/overview")
def get_overview_data():
    """Summary metrics and distributions for the overview page."""
    if state.current_detections_df is None:
        raise HTTPException(status_code=500, detail="Data not initialized")

    df = state.current_detections_df
    total = len(df)
    flagged = len(df[df["final_classification"].isin(["Suspicious", "Invalid", "Invalid + Anomalous"])])
    rule_viol = len(df[df["final_classification"].isin(["Invalid", "Invalid + Anomalous"])])
    ml_only = len(df[df["final_classification"] == "Suspicious"])
    normal_cnt = len(df[df["final_classification"] == "Normal"])
    incomplete_cnt = len(df[df["final_classification"] == "Incomplete"])

    classification_dist = (
        df["final_classification"].value_counts().reset_index().rename(columns={"index": "classification", "count": "count"}).to_dict(orient="records")
    )

    bins = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    hist_counts = pd.cut(df["ml_anomaly_score"], bins=bins).value_counts().sort_index().tolist()
    hist_data = [
        {"range": f"{bins[i]:.1f}-{bins[i+1]:.1f}", "count": int(c)}
        for i, c in enumerate(hist_counts)
    ]

    return {
        "dataset_meta": state.dataset_meta,
        "kpis": {
            "total_executions": total,
            "flagged_executions": flagged,
            "flagged_percentage": round((flagged / max(1, total)) * 100, 1),
            "rule_violations": rule_viol,
            "ml_only_anomalies": ml_only,
            "normal_executions": normal_cnt,
            "incomplete_executions": incomplete_cnt,
        },
        "classification_distribution": classification_dist,
        "score_distribution": hist_data,
        "calibrated_threshold": state.ml_model.threshold if state.ml_model else 0.50,
        "benchmark_summary": {
            "test_cases": state.benchmark_results["test_cases_count"] if state.benchmark_results else 0,
            "hybrid_f1": round(state.benchmark_results["metrics"]["hybrid"]["f1_score"], 3) if state.benchmark_results else 0,
            "automata_f1": round(state.benchmark_results["metrics"]["automata_only"]["f1_score"], 3) if state.benchmark_results else 0,
            "ml_f1": round(state.benchmark_results["metrics"]["ml_only"]["f1_score"], 3) if state.benchmark_results else 0,
        } if state.benchmark_results else None,
    }


def clean_nans(obj: Any) -> Any:
    """Recursively convert float NaN/inf values to None for clean JSON serialization."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nans(v) for v in obj]
    return obj


@app.get("/api/executions")
def get_executions(
    classification: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = 100,
    offset: int = 0,
):
    if state.current_detections_df is None:
        raise HTTPException(status_code=500, detail="No executions available")

    df = state.current_detections_df.copy()
    if classification and classification != "ALL":
        if classification.lower() == "invalid":
            df = df[df["final_classification"].isin(["Invalid", "Invalid + Anomalous"])]
        elif classification.lower() == "suspicious":
            df = df[df["final_classification"] == "Suspicious"]
        elif classification.lower() == "normal":
            df = df[df["final_classification"] == "Normal"]
        else:
            df = df[df["final_classification"] == classification]

    if severity and severity != "ALL":
        df = df[df["severity"] == severity]
    if search:
        s_upper = search.strip().upper()
        df = df[df["case_id"].str.upper().str.contains(s_upper)]

    total_filtered = len(df)
    page_items = clean_nans(df.iloc[offset : offset + limit].to_dict(orient="records"))

    return {
        "total": total_filtered,
        "limit": limit,
        "offset": offset,
        "items": page_items,
    }


@app.get("/api/executions/{case_id}")
def get_execution_detail(case_id: str):
    if state.current_detections_df is None or state.current_events_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")

    rec = state.current_detections_df[state.current_detections_df["case_id"] == case_id]
    if rec.empty:
        raise HTTPException(status_code=404, detail=f"Case ID '{case_id}' not found")

    rec_dict = clean_nans(rec.iloc[0].to_dict())
    val_res = state.current_validation_results.get(case_id)

    events_sub = state.current_events_df[state.current_events_df["case_id"] == case_id].sort_values("timestamp")
    events_list = clean_nans(events_sub.to_dict(orient="records"))

    steps_data = []
    if val_res:
        for s in val_res.steps:
            steps_data.append({
                "step_index": s.step_index,
                "event": s.event,
                "timestamp": s.timestamp,
                "state_before": s.state_before,
                "state_after": s.state_after,
                "is_valid": s.is_valid,
                "permitted_events": s.permitted_events,
                "error_message": s.error_message,
            })

    return {
        "record": rec_dict,
        "events": events_list,
        "validation_steps": steps_data,
        "offending_step_index": val_res.offending_step.step_index if (val_res and val_res.offending_step) else None,
    }


class GenerateDatasetRequest(BaseModel):
    num_cases: int = 500
    normal_ratio: float = 0.80
    rule_anomaly_ratio: float = 0.10
    behavioral_anomaly_ratio: float = 0.10
    random_seed: int = 42


@app.post("/api/dataset/generate")
def generate_dataset(req: GenerateDatasetRequest):
    state.generator = SyntheticLogGenerator(seed=req.random_seed, workflow_def=state.active_workflow)
    df = state.generator.generate_dataset(
        num_cases=req.num_cases,
        normal_ratio=req.normal_ratio,
        rule_anomaly_ratio=req.rule_anomaly_ratio,
        behavioral_anomaly_ratio=req.behavioral_anomaly_ratio,
    )
    state.current_events_df = df

    train_df, val_df, test_df = split_dataset_by_case(df, 0.60, 0.20, 0.20, seed=req.random_seed)
    pipeline = EvaluationPipeline(seed=req.random_seed, dfa_engine=state.dfa)
    benchmark = pipeline.run_benchmark(train_df, val_df, test_df)
    state.ml_model = benchmark["trained_model"]
    state.benchmark_results = benchmark

    engine = HybridDetectionEngine(dfa_engine=state.dfa, ml_model=state.ml_model)
    records_df, val_results = engine.process_dataset(df)
    state.current_detections_df = records_df
    state.current_validation_results = val_results
    state.dataset_meta = {
        "name": f"{state.active_workflow.name} ({req.num_cases} cases)",
        "domain": state.active_workflow.domain,
        "workflow_id": state.active_workflow.id,
        "is_synthetic": True,
        "case_count": len(records_df),
        "event_count": len(df),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return {"status": "success", "meta": state.dataset_meta}


@app.post("/api/dataset/upload")
async def upload_dataset_csv(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        csv_buffer = io.StringIO(contents.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file encoding: {str(e)}")

    is_valid, err, cleaned_df = load_event_log_csv(csv_buffer)
    if not is_valid or cleaned_df is None:
        raise HTTPException(status_code=400, detail=err or "Schema validation failed")

    state.current_events_df = cleaned_df
    train_df, val_df, test_df = split_dataset_by_case(cleaned_df, 0.60, 0.20, 0.20, seed=42)
    pipeline = EvaluationPipeline(seed=42, dfa_engine=state.dfa)
    benchmark = pipeline.run_benchmark(train_df, val_df, test_df)
    state.ml_model = benchmark["trained_model"]
    state.benchmark_results = benchmark

    engine = HybridDetectionEngine(dfa_engine=state.dfa, ml_model=state.ml_model)
    records_df, val_results = engine.process_dataset(cleaned_df)
    state.current_detections_df = records_df
    state.current_validation_results = val_results
    state.dataset_meta = {
        "name": file.filename or "Uploaded CSV",
        "domain": state.active_workflow.domain,
        "workflow_id": state.active_workflow.id,
        "is_synthetic": False,
        "case_count": len(records_df),
        "event_count": len(cleaned_df),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return {"status": "success", "meta": state.dataset_meta}


class RunCustomCaseRequest(BaseModel):
    case_id: Optional[str] = None
    events: List[str]
    time_delay_seconds: float = 60.0


@app.post("/api/executions/run-custom")
def run_custom_case(req: RunCustomCaseRequest):
    if not req.events:
        raise HTTPException(status_code=400, detail="Event sequence cannot be empty")

    case_id = req.case_id.strip() if req.case_id and req.case_id.strip() else f"CUSTOM_{int(time.time())}"
    
    # 1. Synthesize timestamps and event DataFrame
    base_time = pd.Timestamp.now()
    step_delay = max(0.1, float(req.time_delay_seconds))
    rows = []
    for i, ev in enumerate(req.events):
        rows.append({
            "case_id": case_id,
            "event_type": ev.strip(),
            "timestamp": base_time + pd.Timedelta(seconds=i * step_delay),
        })
    case_df = pd.DataFrame(rows)

    # 2. Run DFA & ML Hybrid Engine
    engine = HybridDetectionEngine(dfa_engine=state.dfa, ml_model=state.ml_model)
    rec_df, val_results = engine.process_dataset(case_df)

    if rec_df.empty:
        raise HTTPException(status_code=500, detail="Failed to process custom execution")

    rec_dict = clean_nans(rec_df.iloc[0].to_dict())
    val_res = val_results.get(case_id)

    # 3. Store into active state so it is visible in Executions list and inspectable
    if state.current_detections_df is not None:
        # Prepend to front of detections
        state.current_detections_df = pd.concat([rec_df, state.current_detections_df[state.current_detections_df["case_id"] != case_id]], ignore_index=True)
    else:
        state.current_detections_df = rec_df

    if state.current_events_df is not None:
        state.current_events_df = pd.concat([case_df, state.current_events_df[state.current_events_df["case_id"] != case_id]], ignore_index=True)
    else:
        state.current_events_df = case_df

    if val_res:
        state.current_validation_results[case_id] = val_res

    # 4. Construct step-by-step validation response
    steps_data = []
    if val_res:
        for s in val_res.steps:
            steps_data.append({
                "step_index": s.step_index,
                "event": s.event,
                "timestamp": s.timestamp,
                "state_before": s.state_before,
                "state_after": s.state_after,
                "is_valid": s.is_valid,
                "permitted_events": s.permitted_events,
                "error_message": s.error_message,
            })

    events_list = clean_nans(case_df.to_dict(orient="records"))

    return {
        "case_id": case_id,
        "record": rec_dict,
        "events": events_list,
        "validation_steps": steps_data,
        "offending_step_index": val_res.offending_step.step_index if (val_res and val_res.offending_step) else None,
    }


@app.get("/api/evaluation")
def get_evaluation():
    if state.benchmark_results is None:
        raise HTTPException(status_code=404, detail="Benchmark not yet executed")
    res = state.benchmark_results
    return {
        "test_cases_count": res["test_cases_count"],
        "calibrated_threshold": res["calibrated_threshold"],
        "metrics": res["metrics"],
        "category_breakdown": res["category_breakdown"],
        "latencies": res["latencies"],
    }


frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
