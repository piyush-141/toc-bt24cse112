import React from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { OverviewData } from "../types";

interface OverviewProps {
  data: OverviewData | null;
  loading: boolean;
  onExploreExecutions: (filter?: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({
  data,
  loading,
  onExploreExecutions,
}) => {
  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-80 text-slate-400 font-mono text-xs">
        <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const { kpis, classification_distribution, score_distribution, calibrated_threshold, benchmark_summary } = data;

  const getBarColor = (name: string) => {
    switch (name) {
      case "Normal":
        return "#10B981";
      case "Suspicious":
        return "#F59E0B";
      case "Invalid":
        return "#EF4444";
      case "Invalid + Anomalous":
        return "#991B1B";
      default:
        return "#64748B";
    }
  };

  return (
    <div className="space-y-6">
      {/* 4 Clean Minimal Metric Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
            Analyzed
          </span>
          <div className="text-2xl font-bold text-slate-800 font-mono mt-2">
            {kpis.total_executions.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">100% trace coverage</span>
        </div>

        {/* Flagged */}
        <div
          onClick={() => onExploreExecutions("ALL")}
          className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all cursor-pointer flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
              Anomalies
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-800 transition-colors" />
          </div>
          <div className="text-2xl font-bold text-amber-500 font-mono mt-2">
            {kpis.flagged_executions.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">{kpis.flagged_percentage}% detection rate</span>
        </div>

        {/* Rule Violations */}
        <div
          onClick={() => onExploreExecutions("Invalid")}
          className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all cursor-pointer flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
              DFA Violations
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-800 transition-colors" />
          </div>
          <div className="text-2xl font-bold text-rose-500 font-mono mt-2">
            {kpis.rule_violations.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Grammar violations</span>
        </div>

        {/* Behavioral */}
        <div
          onClick={() => onExploreExecutions("Suspicious")}
          className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all cursor-pointer flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
              Behavioral Outliers
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-800 transition-colors" />
          </div>
          <div className="text-2xl font-bold text-amber-600 font-mono mt-2">
            {kpis.ml_only_anomalies.toLocaleString()}
          </div>
          <span className="text-[11px] text-slate-400 mt-1">Isolation Forest flags</span>
        </div>
      </div>

      {/* 2 Core Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Classification Breakdown */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-800 tracking-tight">Decisions</span>
            <span className="text-[10px] font-mono text-slate-400">Deterministic + ML</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={classification_distribution} margin={{ top: 10, right: 10, left: -25, bottom: 10 }}>
                <XAxis dataKey="classification" stroke="#CBD5E1" fontSize={10} tick={{ fill: "#64748B" }} />
                <YAxis stroke="#CBD5E1" fontSize={10} tick={{ fill: "#64748B" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderRadius: "12px",
                    border: "1px solid #E2E8F0",
                    fontSize: "11px",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {classification_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.classification)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Score Distribution */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-800 tracking-tight">ML Anomaly Score Distribution</span>
            <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
              Cutoff ≥ {calibrated_threshold.toFixed(2)}
            </span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={score_distribution} margin={{ top: 10, right: 10, left: -25, bottom: 10 }}>
                <XAxis dataKey="range" stroke="#CBD5E1" fontSize={10} tick={{ fill: "#64748B" }} />
                <YAxis stroke="#CBD5E1" fontSize={10} tick={{ fill: "#64748B" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderRadius: "12px",
                    border: "1px solid #E2E8F0",
                    fontSize: "11px",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
                  }}
                />
                <Bar dataKey="count" fill="#3B82F6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Held-out Test Benchmark Capsule */}
      {benchmark_summary && (
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex items-center justify-between">
          <div className="flex items-center space-x-3 text-xs">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="font-semibold text-slate-800">Test Set F1-Scores:</span>
            <span className="text-slate-500 font-mono">
              Hybrid <strong className="text-emerald-600">{benchmark_summary.hybrid_f1}</strong> · DFA{" "}
              {benchmark_summary.automata_f1} · ML {benchmark_summary.ml_f1}
            </span>
          </div>
          <button
            onClick={() => onExploreExecutions("ALL")}
            className="text-xs font-semibold text-slate-800 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-100 transition-colors"
          >
            View Executions →
          </button>
        </div>
      )}
    </div>
  );
};
