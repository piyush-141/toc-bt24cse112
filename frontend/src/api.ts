import axios from "axios";
import {
  OverviewData,
  ExecutionRecord,
  ExecutionDetail,
  EvaluationData,
  WorkflowGraphData,
  DatasetMeta,
  WorkflowSummary,
} from "./types";

const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const fetchWorkflows = async (): Promise<{
  active_workflow_id: string;
  workflows: WorkflowSummary[];
}> => {
  const res = await api.get("/workflows");
  return res.data;
};

export const selectWorkflow = async (
  workflowId: string
): Promise<{ status: string; active_workflow: WorkflowGraphData; meta: DatasetMeta }> => {
  const res = await api.post(`/workflows/select/${workflowId}`);
  return res.data;
};

export const createCustomWorkflow = async (data: {
  id: string;
  name: string;
  domain: string;
  description: string;
  initial_state: string;
  states: string[];
  alphabet: string[];
  terminal_states: string[];
  transitions: Array<{ from: string; event: string; to: string }>;
}): Promise<{ status: string; active_workflow: WorkflowGraphData; meta: DatasetMeta }> => {
  const res = await api.post("/workflows/create", data);
  return res.data;
};

export const fetchOverview = async (): Promise<OverviewData> => {
  const res = await api.get<OverviewData>("/overview");
  return res.data;
};

export const fetchWorkflowGraph = async (): Promise<WorkflowGraphData> => {
  const res = await api.get<WorkflowGraphData>("/workflow/graph");
  return res.data;
};

export const fetchExecutions = async (params: {
  classification?: string;
  severity?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; limit: number; offset: number; items: ExecutionRecord[] }> => {
  const res = await api.get("/executions", { params });
  return res.data;
};

export const fetchExecutionDetail = async (caseId: string): Promise<ExecutionDetail> => {
  const res = await api.get<ExecutionDetail>(`/executions/${caseId}`);
  return res.data;
};

export const fetchEvaluation = async (): Promise<EvaluationData> => {
  const res = await api.get<EvaluationData>("/evaluation");
  return res.data;
};

export const generateSyntheticDataset = async (params: {
  num_cases: number;
  normal_ratio: number;
  rule_anomaly_ratio: number;
  behavioral_anomaly_ratio: number;
  random_seed: number;
}): Promise<{ status: string; meta: DatasetMeta }> => {
  const res = await api.post("/dataset/generate", params);
  return res.data;
};

export const uploadDatasetCsv = async (file: File): Promise<{ status: string; meta: DatasetMeta }> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/dataset/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const runCustomCase = async (params: {
  case_id?: string;
  events: string[];
  time_delay_seconds?: number;
}): Promise<ExecutionDetail> => {
  const res = await api.post<ExecutionDetail>("/executions/run-custom", params);
  return res.data;
};
