import React, { useState, useEffect } from "react";
import {
  Search,
  ArrowRight,
  AlertOctagon,
  Clock,
  Shield,
  X,
  Play,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import { fetchExecutions, fetchExecutionDetail, runCustomCase, fetchWorkflowGraph } from "../api";
import { ExecutionRecord, ExecutionDetail } from "../types";

interface ExecutionsProps {
  initialFilter?: string;
  onRunCase?: (caseId: string, detail: ExecutionDetail) => void;
}

export const Executions: React.FC<ExecutionsProps> = ({ initialFilter = "ALL", onRunCase }) => {
  const [items, setItems] = useState<ExecutionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExecutionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Filters
  const [classificationFilter, setClassificationFilter] = useState<string>(initialFilter);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Custom Case Builder Modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [customCaseId, setCustomCaseId] = useState<string>("");
  const [customSteps, setCustomSteps] = useState<string[]>([]);
  const [customDelaySecs, setCustomDelaySecs] = useState<number>(60);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflowGraph().then((data) => {
      if (data && data.alphabet) {
        setAvailableEvents(data.alphabet);
      }
    }).catch(console.error);
  }, []);

  useEffect(() => {
    loadList();
  }, [classificationFilter, searchQuery]);

  const loadList = () => {
    setLoading(true);
    fetchExecutions({
      classification: classificationFilter,
      search: searchQuery,
      limit: 100,
      offset: 0,
    })
      .then((data) => {
        const newItems = data.items || [];
        setItems(newItems);
        setLoading(false);
        if (newItems.length > 0) {
          const stillSelected = newItems.some((it) => it.case_id === selectedCaseId);
          if (!stillSelected) {
            handleSelectCase(newItems[0].case_id);
          }
        } else {
          setSelectedCaseId(null);
          setDetail(null);
        }
      })
      .catch((err) => {
        console.error("Failed to load executions", err);
        setItems([]);
        setSelectedCaseId(null);
        setDetail(null);
        setLoading(false);
      });
  };

  const handleSelectCase = (caseId: string) => {
    setSelectedCaseId(caseId);
    setDetailLoading(true);
    fetchExecutionDetail(caseId)
      .then((data) => {
        setDetail(data);
        setDetailLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load execution detail", err);
        setDetailLoading(false);
      });
  };

  const getStatusColor = (cls: string) => {
    switch (cls) {
      case "Normal":
        return "text-emerald-600 bg-emerald-50 border-emerald-100";
      case "Suspicious":
        return "text-amber-600 bg-amber-50 border-amber-100";
      case "Invalid":
        return "text-rose-600 bg-rose-50 border-rose-100";
      case "Invalid + Anomalous":
        return "text-red-700 bg-red-50 border-red-200 font-bold";
      default:
        return "text-slate-600 bg-slate-50 border-slate-100";
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-100 shadow-[0_4px_25px_rgba(0,0,0,0.03)] h-[720px] overflow-hidden flex">
      {/* Left List Pane (Outliner style like reference image) */}
      <div className="w-80 border-r border-slate-100 flex flex-col h-full bg-slate-50/40">
        {/* Search & Filter Bar */}
        <div className="p-4 border-b border-slate-100 space-y-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search Case ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-400 font-mono"
              />
            </div>
            <button
              onClick={() => {
                setCustomCaseId(`CASE_CUSTOM_${Math.floor(100 + Math.random() * 900)}`);
                setCustomSteps([]);
                setCreateError(null);
                setShowCreateModal(true);
              }}
              className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center space-x-1 shrink-0 cursor-pointer shadow-xs transition-all"
              title="Create your own custom case"
            >
              <Plus className="w-3.5 h-3.5 text-blue-400" />
              <span>New Case</span>
            </button>
          </div>

          <div className="flex gap-1 overflow-x-auto pb-1 text-[11px] font-medium text-slate-500">
            {["ALL", "Invalid", "Suspicious", "Normal"].map((f) => (
              <button
                key={f}
                onClick={() => setClassificationFilter(f)}
                className={`px-2.5 py-1 rounded-lg transition-colors shrink-0 cursor-pointer ${
                  classificationFilter === f
                    ? "bg-slate-900 text-white font-semibold"
                    : "bg-white border border-slate-200 hover:bg-slate-100"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable Trace Items */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400 font-mono">Loading cases...</div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 font-mono">No cases found</div>
          ) : (
            items.map((item) => {
              const isSelected = item.case_id === selectedCaseId;
              return (
                <div
                  key={item.case_id}
                  onClick={() => handleSelectCase(item.case_id)}
                  className={`p-3.5 cursor-pointer transition-all group relative ${
                    isSelected ? "bg-white shadow-xs font-semibold" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-800 tracking-tight">
                      {item.case_id}
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <span className={`text-[10px] px-2 py-0.5 rounded-md border font-mono ${getStatusColor(item.final_classification)}`}>
                        {item.final_classification}
                      </span>
                      {onRunCase && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            fetchExecutionDetail(item.case_id).then((d) => onRunCase(item.case_id, d));
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded-md bg-slate-900 text-white hover:bg-blue-600 transition-all cursor-pointer shadow-xs"
                          title={`Run ${item.case_id} on workflow automaton`}
                        >
                          <Play className="w-2.5 h-2.5 fill-white" />
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono mt-1">
                    <span>{item.automata_status}</span>
                    <span>Score {item.ml_anomaly_score.toFixed(2)}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Canvas / Detail Pane */}
      <div className="flex-1 p-6 overflow-y-auto bg-white flex flex-col justify-between">
        {detailLoading ? (
          <div className="flex items-center justify-center h-full text-xs text-slate-400 font-mono">
            Loading trace telemetry...
          </div>
        ) : !detail ? (
          <div className="flex items-center justify-center h-full text-xs text-slate-400 font-mono">
            Select a case to inspect its transitions and anomaly explanation.
          </div>
        ) : (
          <div className="space-y-6">
            {/* Top Case Header Capsule */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <span className="text-lg font-bold font-mono text-slate-800">
                  {detail.record.case_id}
                </span>
                <span className={`text-xs px-2.5 py-1 rounded-lg border font-mono ${getStatusColor(detail.record.final_classification)}`}>
                  {detail.record.final_classification}
                </span>
                <span className="text-xs font-mono text-slate-500">
                  ML Score: <strong className="text-slate-800">{detail.record.ml_anomaly_score.toFixed(3)}</strong>
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => onRunCase && detail && onRunCase(detail.record.case_id, detail)}
                  className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-2 rounded-xl text-xs font-mono font-medium shadow-xs hover:shadow-md transition-all cursor-pointer group"
                  title="Run step-by-step trace animation on the workflow automaton"
                >
                  <Play className="w-3.5 h-3.5 text-blue-400 fill-blue-400 group-hover:scale-110 transition-transform" />
                  <span>Run Trace on Workflow</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>
            </div>

            {/* Explanation Note (Styled cleanly like Note in reference image) */}
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100 text-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Anomaly Diagnosis
              </span>
              <p className="text-slate-800 leading-relaxed font-medium">
                {detail.record.summary_explanation}
              </p>
              {detail.record.automata_explanation && (
                <div className="mt-2 text-[11px] text-slate-600 font-mono pt-2 border-t border-slate-200/60">
                  {detail.record.automata_explanation}
                </div>
              )}
            </div>

            {/* Chronological Sequence */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono block mb-3">
                Chronological Events ({detail.validation_steps.length})
              </span>

              <div className="space-y-2">
                {detail.validation_steps.map((step) => {
                  const isViolating = !step.is_valid;
                  return (
                    <div
                      key={step.step_index}
                      className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between transition-all ${
                        isViolating
                          ? "bg-rose-50 border-rose-200 text-rose-900"
                          : "bg-white border-slate-150 text-slate-800 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className={`w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                          isViolating ? "bg-rose-200 text-rose-800" : "bg-slate-100 text-slate-600"
                        }`}>
                          {step.step_index}
                        </span>
                        <span className="font-semibold">{step.event}</span>
                      </div>

                      <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                        <span>{step.state_before}</span>
                        <ArrowRight className="w-3 h-3 text-slate-400" />
                        <span className={isViolating ? "font-bold text-rose-600" : "font-medium text-slate-800"}>
                          {step.state_after || "INVALID"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Custom Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </span>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Create Custom Execution Case</h3>
                  <p className="text-[11px] text-slate-400">Design an event sequence to test against the DFA & ML engines</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {createError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-mono">
                {createError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                  Case Identifier
                </label>
                <input
                  type="text"
                  value={customCaseId}
                  onChange={(e) => setCustomCaseId(e.target.value)}
                  placeholder="e.g. CASE_MY_TEST"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                  Step Delay Between Events (Seconds)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="0.1"
                    step="1"
                    value={customDelaySecs}
                    onChange={(e) => setCustomDelaySecs(parseFloat(e.target.value) || 60)}
                    className="w-32 px-3 py-1.5 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs"
                  />
                  <span className="text-[11px] text-slate-400">
                    {customDelaySecs <= 1 ? "⚡ High velocity / bot traffic" : customDelaySecs >= 3600 ? "🐢 Long delay / stalling" : "Normal human timing"}
                  </span>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold">
                    Event Sequence ({customSteps.length} steps)
                  </label>
                  {customSteps.length > 0 && (
                    <button
                      onClick={() => setCustomSteps([])}
                      className="text-[10px] text-rose-600 hover:underline font-mono cursor-pointer"
                    >
                      Clear All
                    </button>
                  )}
                </div>

                {/* Steps List */}
                <div className="min-h-24 max-h-40 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                  {customSteps.length === 0 ? (
                    <div className="h-20 flex items-center justify-center text-slate-400 text-xs font-mono">
                      Click events below to append steps
                    </div>
                  ) : (
                    customSteps.map((ev, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono shadow-2xs"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="w-4 h-4 rounded-md bg-slate-100 text-slate-500 flex items-center justify-center text-[10px]">
                            {idx + 1}
                          </span>
                          <span className="font-semibold text-slate-800">{ev}</span>
                        </div>
                        <button
                          onClick={() => setCustomSteps(customSteps.filter((_, i) => i !== idx))}
                          className="text-slate-400 hover:text-rose-600 p-0.5 rounded cursor-pointer"
                          title="Remove step"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Quick Append Event Buttons */}
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1.5">
                  Available Alphabet Σ (Click to Add)
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                  {availableEvents.map((ev) => (
                    <button
                      key={ev}
                      onClick={() => setCustomSteps([...customSteps, ev])}
                      className="px-2.5 py-1 bg-white border border-slate-200 hover:border-slate-400 hover:bg-slate-100 rounded-lg text-[11px] font-mono text-slate-700 transition-colors cursor-pointer flex items-center space-x-1"
                    >
                      <Plus className="w-2.5 h-2.5 text-slate-400" />
                      <span>{ev}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmitting || customSteps.length === 0}
                onClick={() => {
                  if (customSteps.length === 0) {
                    setCreateError("Please select at least one event step.");
                    return;
                  }
                  setIsSubmitting(true);
                  setCreateError(null);
                  runCustomCase({
                    case_id: customCaseId,
                    events: customSteps,
                    time_delay_seconds: customDelaySecs,
                  })
                    .then((detailRes) => {
                      setIsSubmitting(false);
                      setShowCreateModal(false);
                      loadList();
                      const cid = detailRes.record?.case_id || customCaseId;
                      handleSelectCase(cid);
                      if (onRunCase) {
                        onRunCase(cid, detailRes);
                      }
                    })
                    .catch((err) => {
                      setIsSubmitting(false);
                      setCreateError(err?.response?.data?.detail || "Failed to execute custom case");
                    });
                }}
                className={`px-4 py-2 rounded-xl text-white text-xs font-semibold flex items-center space-x-1.5 shadow-xs transition-all ${
                  isSubmitting || customSteps.length === 0
                    ? "bg-slate-300 cursor-not-allowed"
                    : "bg-slate-900 hover:bg-slate-800 cursor-pointer"
                }`}
              >
                <Play className="w-3 h-3 fill-white" />
                <span>{isSubmitting ? "Running..." : "Evaluate & Run Case"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
