import React, { useEffect, useState } from "react";
import { fetchEvaluation } from "../api";
import { EvaluationData, MetricBlock } from "../types";
import { Info, Sparkles } from "lucide-react";

export const EvaluationPage: React.FC = () => {
  const [data, setData] = useState<EvaluationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchEvaluation()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load evaluation", err);
        setLoading(false);
      });
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-80 text-xs text-slate-400 font-mono">
        <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const { metrics, category_breakdown, test_cases_count, calibrated_threshold } = data;

  const renderCard = (title: string, m?: MetricBlock, tag = "Detector", isHybrid = false) => {
    if (!m) return null;
    return (
      <div className={`bg-white rounded-3xl p-5 border ${isHybrid ? "border-slate-900 shadow-[0_4px_25px_rgba(0,0,0,0.06)]" : "border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)]"} flex flex-col justify-between`}>
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-800">{title}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
              isHybrid ? "bg-slate-900 text-white font-bold" : "bg-slate-100 text-slate-600"
            }`}>
              {tag}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-3 text-center">
            <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-mono">Precision</span>
              <span className="text-xs font-bold text-slate-800 font-mono">{(m.precision * 100).toFixed(1)}%</span>
            </div>
            <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-mono">Recall</span>
              <span className="text-xs font-bold text-slate-800 font-mono">{(m.recall * 100).toFixed(1)}%</span>
            </div>
            <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
              <span className="text-[10px] text-slate-400 block font-mono">F1-Score</span>
              <span className={`text-xs font-bold font-mono ${isHybrid ? "text-emerald-600 font-extrabold" : "text-slate-800"}`}>
                {m.f1_score.toFixed(3)}
              </span>
            </div>
          </div>

          {/* 2x2 Matrix */}
          <div className="grid grid-cols-2 gap-1 text-center text-xs font-mono bg-slate-50 p-2 rounded-2xl border border-slate-100">
            <div className="bg-white p-1.5 rounded-lg">
              <span className="text-slate-400 text-[9px] block">TN</span>
              <span className="font-bold text-slate-700 text-[11px]">{m.confusion_matrix.TN}</span>
            </div>
            <div className="bg-white p-1.5 rounded-lg">
              <span className="text-slate-400 text-[9px] block">FP</span>
              <span className="font-bold text-amber-600 text-[11px]">{m.confusion_matrix.FP}</span>
            </div>
            <div className="bg-white p-1.5 rounded-lg">
              <span className="text-slate-400 text-[9px] block">FN</span>
              <span className="font-bold text-rose-600 text-[11px]">{m.confusion_matrix.FN}</span>
            </div>
            <div className="bg-white p-1.5 rounded-lg">
              <span className="text-slate-400 text-[9px] block">TP</span>
              <span className="font-bold text-emerald-600 text-[11px]">{m.confusion_matrix.TP}</span>
            </div>
          </div>
        </div>

        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>False Positive Rate:</span>
          <span className="text-slate-700 font-semibold">{(m.false_positive_rate * 100).toFixed(1)}%</span>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Overview Grid with All Techniques Mentioned in Problem Statement */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {renderCard("Hybrid Decision Engine", metrics.hybrid, "Primary", true)}
        {renderCard("Deterministic Automaton (DFA)", metrics.automata_only, "Grammar Rules")}
        {renderCard("Isolation Forest", metrics.ml_only, "ML Statistical")}
        {renderCard("Process Clustering (K-Means)", metrics.clustering, "ML Clustering")}
        {renderCard("Markov Sequence Model", metrics.sequence_model, "ML Sequence NLL")}
        {renderCard("Supervised Random Forest", metrics.supervised_rf, "Supervised Baseline")}
      </div>

      {/* Precision Calibration & TOC Theory Insight */}
      <div className="bg-white rounded-3xl p-5 border border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex items-start space-x-4">
        <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 mt-0.5">
          <Info className="w-4 h-4" />
        </div>
        <div className="text-xs text-slate-600 space-y-2 flex-1">
          <div className="font-bold text-slate-800 text-xs">
            Dual-Engine Architecture: How DFA & ML Ensembles Collaborate
          </div>
          <p className="text-[11px] leading-relaxed text-slate-500">
            <strong>1. Deterministic Automaton (DFA) — Hard Rules:</strong> The DFA acts as a strict structural filter enforcing formal state transitions <code className="bg-slate-100 px-1 py-0.5 rounded font-mono">δ(state, event)</code>. It delivers guaranteed <strong>100% precision</strong> (zero false alarms) for grammatical violations like skipped steps or illegal out-of-turn actions, but cannot detect valid steps executed at abnormal speeds or excessive retries.
          </p>
          <p className="text-[11px] leading-relaxed text-slate-500">
            <strong>2. ML Ensembles (Isolation Forest, Markov NLL, K-Means) — Behavioral Context:</strong> When an event sequence is grammatically valid, the ML models inspect execution timings, duration percentiles, and transition likelihoods. They catch subtle, non-structural anomalies (e.g., bot bursts, prolonged bottlenecks, or infinite retry loops) that the DFA alone misses.
          </p>
          <p className="text-[11px] leading-relaxed text-slate-500">
            <strong>3. What if the DFA fails?</strong> Every trace is evaluated by <em>both</em> engines simultaneously. If the DFA rejects a step (<code className="bg-rose-50 text-rose-600 px-1 py-0.5 rounded font-mono">INVALID</code>), the ML models <em>still</em> analyze the trace. If ML also flags abnormal timing/frequencies, the system escalates it to <strong className="text-rose-600">CRITICAL: INVALID & ANOMALOUS</strong>; if ML finds standard metrics, it remains <strong className="text-amber-600">HIGH: INVALID</strong>. This provides immediate root-cause clarity between pure syntax mistakes and complex behavioral attacks.
          </p>
        </div>
      </div>

      {/* Category Breakdown Table */}
      <div className="bg-white rounded-3xl p-6 border border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-bold text-slate-800">Anomaly Category Recall</span>
          <span className="text-[11px] font-mono text-slate-400">{test_cases_count} test cases · Cutoff {calibrated_threshold.toFixed(2)}</span>
        </div>

        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-slate-100 text-slate-400 text-[10px] uppercase">
              <th className="py-2.5 px-3">Category</th>
              <th className="py-2.5 px-3">Cases</th>
              <th className="py-2.5 px-3">DFA</th>
              <th className="py-2.5 px-3">Isolation Forest</th>
              <th className="py-2.5 px-3">Clustering</th>
              <th className="py-2.5 px-3">Sequence</th>
              <th className="py-2.5 px-3 text-slate-900 font-bold">Hybrid</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {Object.keys(category_breakdown.hybrid).map((cat) => {
              const dfaStat = category_breakdown.automata_only[cat];
              const mlStat = category_breakdown.ml_only[cat];
              const clusterStat = category_breakdown.clustering?.[cat];
              const seqStat = category_breakdown.sequence_model?.[cat];
              const hybStat = category_breakdown.hybrid[cat];
              return (
                <tr key={cat} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-800">{cat}</td>
                  <td className="py-3 px-3 text-slate-400">{hybStat?.total_cases || 0}</td>
                  <td className="py-3 px-3">
                    <span className={dfaStat?.catch_rate === 1 ? "text-emerald-600 font-bold" : "text-slate-500"}>
                      {dfaStat ? `${(dfaStat.catch_rate * 100).toFixed(0)}%` : "—"}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={mlStat?.catch_rate > 0.8 ? "text-emerald-600 font-bold" : "text-amber-600"}>
                      {mlStat ? `${(mlStat.catch_rate * 100).toFixed(0)}%` : "—"}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-600">
                    {clusterStat ? `${(clusterStat.catch_rate * 100).toFixed(0)}%` : "—"}
                  </td>
                  <td className="py-3 px-3 text-slate-600">
                    {seqStat ? `${(seqStat.catch_rate * 100).toFixed(0)}%` : "—"}
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-emerald-600 font-bold">
                      {hybStat ? `${(hybStat.catch_rate * 100).toFixed(0)}%` : "—"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
