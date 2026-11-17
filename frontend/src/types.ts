export interface DatasetMeta {
  name: string;
  domain?: string;
  workflow_id?: string;
  is_synthetic: boolean;
  case_count: number;
  event_count: number;
  generated_at: string;
}

export interface OverviewKPIs {
  total_executions: number;
  flagged_executions: number;
  flagged_percentage: number;
  rule_violations: number;
  ml_only_anomalies: number;
  normal_executions: number;
  incomplete_executions: number;
}

export interface ClassificationDistItem {
  classification: string;
  count: number;
}

export interface ScoreDistItem {
  range: string;
  count: number;
}

export interface OverviewData {
  dataset_meta: DatasetMeta;
  kpis: OverviewKPIs;
  classification_distribution: ClassificationDistItem[];
  score_distribution: ScoreDistItem[];
  calibrated_threshold: number;
  benchmark_summary: {
    test_cases: number;
    hybrid_f1: number;
    automata_f1: number;
    ml_f1: number;
  } | null;
}

export interface ExecutionRecord {
  case_id: string;
  automata_status: string;
  is_valid_automata: boolean;
  final_state: string;
  ml_anomaly_score: number;
  ml_threshold: number;
  ml_status: string;
  final_classification: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  violation_type: string | null;
  offending_event: string | null;
  offending_state: string | null;
  summary_explanation: string;
  automata_explanation: string;
  ml_explanation: string;
  actionable_next_step: string;
}

export interface ValidationStep {
  step_index: number;
  event: string;
  timestamp: string | null;
  state_before: string;
  state_after: string | null;
  is_valid: boolean;
  permitted_events: string[];
  error_message: string | null;
}

export interface ExecutionDetail {
  record: ExecutionRecord;
  events: Array<{
    timestamp: string;
    event_type: string;
    state_before?: string;
    state_after?: string;
  }>;
  validation_steps: ValidationStep[];
  offending_step_index: number | null;
}

export interface EvaluationCategoryStats {
  total_cases: number;
  flagged_cases: number;
  catch_rate: number;
}

export interface MetricBlock {
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
  false_positive_rate: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  confusion_matrix: {
    TN: number;
    FP: number;
    FN: number;
    TP: number;
  };
}

export interface EvaluationData {
  test_cases_count: number;
  calibrated_threshold: number;
  metrics: {
    automata_only: MetricBlock;
    ml_only: MetricBlock;
    clustering?: MetricBlock;
    sequence_model?: MetricBlock;
    hybrid: MetricBlock;
    supervised_rf: MetricBlock;
  };
  category_breakdown: {
    automata_only: Record<string, EvaluationCategoryStats>;
    ml_only: Record<string, EvaluationCategoryStats>;
    clustering?: Record<string, EvaluationCategoryStats>;
    sequence_model?: Record<string, EvaluationCategoryStats>;
    hybrid: Record<string, EvaluationCategoryStats>;
  };
  latencies: {
    feature_extraction_sec: number;
    training_sec: number;
    dfa_inference_sec: number;
    ml_inference_sec: number;
  };
}

export interface WorkflowSummary {
  id: string;
  name: string;
  domain: string;
  description: string;
  state_count: number;
  event_count: number;
  transition_count: number;
}

export interface WorkflowGraphData {
  id: string;
  name: string;
  domain: string;
  description: string;
  nodes: Array<{
    id: string;
    data: {
      label: string;
      isInitial: boolean;
      isTerminal: boolean;
      permittedEvents: string[];
    };
    position: { x: number; y: number };
    type: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
    animated?: boolean;
  }>;
  alphabet: string[];
  states?: string[];
  initialState: string;
  terminalStates: string[];
  reachability?: {
    all_states_count: number;
    reachable_states: string[];
    unreachable_states: string[];
    terminal_states: string[];
    all_terminals_reachable: boolean;
    is_valid_dfa: boolean;
    transition_count: number;
  };
}
