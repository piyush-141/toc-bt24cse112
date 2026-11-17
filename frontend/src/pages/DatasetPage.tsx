import React, { useState } from "react";
import {
  UploadCloud,
  RefreshCw,
  FileText,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { generateSyntheticDataset, uploadDatasetCsv } from "../api";
import { DatasetMeta } from "../types";

interface DatasetProps {
  meta: DatasetMeta | null;
  onDatasetUpdated: () => void;
}

export const DatasetPage: React.FC<DatasetProps> = ({ meta, onDatasetUpdated }) => {
  const [numCases, setNumCases] = useState<number>(1000);
  const [normalRatio, setNormalRatio] = useState<number>(0.80);
  const [ruleAnomalyRatio, setRuleAnomalyRatio] = useState<number>(0.10);
  const [behavioralRatio, setBehavioralRatio] = useState<number>(0.10);
  const [seed, setSeed] = useState<number>(42);

  const [generating, setGenerating] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setStatusMsg(null);
    try {
      const res = await generateSyntheticDataset({
        num_cases: numCases,
        normal_ratio: normalRatio,
        rule_anomaly_ratio: ruleAnomalyRatio,
        behavioral_anomaly_ratio: behavioralRatio,
        random_seed: seed,
      });
      setStatusMsg({
        type: "success",
        text: `Generated ${res.meta.case_count} cases and ${res.meta.event_count} events.`,
      });
      onDatasetUpdated();
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: err.response?.data?.detail || "Generation failed",
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setStatusMsg(null);
    try {
      const res = await uploadDatasetCsv(file);
      setStatusMsg({
        type: "success",
        text: `Loaded ${res.meta.case_count} cases from ${res.meta.name}.`,
      });
      onDatasetUpdated();
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: err.response?.data?.detail || "Upload failed",
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {statusMsg && (
        <div
          className={`p-3.5 rounded-2xl border text-xs font-mono flex items-center space-x-2 ${
            statusMsg.type === "success"
              ? "bg-emerald-50 border-emerald-100 text-emerald-800"
              : "bg-rose-50 border-rose-100 text-rose-800"
          }`}
        >
          {statusMsg.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Active Log Card */}
      {meta && (
        <div className="bg-white rounded-2xl p-5 border border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex items-center justify-between text-xs font-mono">
          <div>
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Active Dataset</span>
            <span className="text-sm font-bold text-slate-800">{meta.name}</span>
          </div>
          <div className="flex items-center space-x-4 text-slate-500">
            <span>{meta.case_count.toLocaleString()} cases</span>
            <span>{meta.event_count.toLocaleString()} events</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Synthetic Generator */}
        <div className="bg-white rounded-3xl p-6 border border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)]">
          <span className="text-sm font-bold text-slate-800 tracking-tight block mb-4">
            Synthetic Generator
          </span>

          <form onSubmit={handleGenerate} className="space-y-4 text-xs font-mono">
            <div>
              <label className="block text-slate-600 mb-1">Workflow Cases</label>
              <input
                type="number"
                min={50}
                max={10000}
                value={numCases}
                onChange={(e) => setNumCases(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-slate-400"
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-slate-600 mb-1">Normal</label>
                <input
                  type="number"
                  step={0.05}
                  value={normalRatio}
                  onChange={(e) => setNormalRatio(Number(e.target.value))}
                  className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900"
                />
              </div>
              <div>
                <label className="block text-slate-600 mb-1">DFA Violations</label>
                <input
                  type="number"
                  step={0.05}
                  value={ruleAnomalyRatio}
                  onChange={(e) => setRuleAnomalyRatio(Number(e.target.value))}
                  className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900"
                />
              </div>
              <div>
                <label className="block text-slate-600 mb-1">Behavioral</label>
                <input
                  type="number"
                  step={0.05}
                  value={behavioralRatio}
                  onChange={(e) => setBehavioralRatio(Number(e.target.value))}
                  className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-600 mb-1">Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900"
              />
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full mt-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white rounded-xl font-medium flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${generating ? "animate-spin" : ""}`} />
              <span>{generating ? "Generating..." : "Generate Dataset"}</span>
            </button>
          </form>
        </div>

        {/* CSV Upload */}
        <div className="bg-white rounded-3xl p-6 border border-slate-150 shadow-[0_4px_20px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div>
            <span className="text-sm font-bold text-slate-800 tracking-tight block mb-4">
              Upload CSV
            </span>

            <div className="border border-dashed border-slate-200 rounded-2xl p-8 text-center bg-slate-50/50">
              <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <div className="text-xs text-slate-600 mb-4 font-mono">
                Required columns: case_id, timestamp, event_type
              </div>
              <label className="cursor-pointer inline-flex items-center px-4 py-2 bg-white text-slate-700 rounded-xl text-xs font-mono font-medium border border-slate-200 shadow-xs hover:bg-slate-50 transition-colors">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
                <span>{uploading ? "Validating..." : "Choose File"}</span>
              </label>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 font-mono mt-4">
            Zero label leakage: features are extracted purely from timestamps and event sequences.
          </div>
        </div>
      </div>
    </div>
  );
};
