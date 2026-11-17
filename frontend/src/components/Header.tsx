import React from "react";
import {
  Activity,
  GitBranch,
  Layers,
  Database,
  BarChart2,
  Shield,
  Search,
} from "lucide-react";

export type NavTab = "overview" | "workflow" | "executions" | "dataset" | "evaluation";

interface HeaderProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  datasetName?: string;
  isSynthetic?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onSelectTab,
  datasetName,
  isSynthetic,
}) => {
  const tabs = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "workflow", label: "Workflow", icon: GitBranch },
    { id: "executions", label: "Executions", icon: Layers },
    { id: "dataset", label: "Dataset", icon: Database },
    { id: "evaluation", label: "Evaluation", icon: BarChart2 },
  ];

  return (
    <div className="flex items-center justify-between px-6 py-4 bg-transparent">
      {/* Brand Identity / Left Pill */}
      <div className="flex items-center space-x-3 bg-white px-3.5 py-2 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-slate-100">
        <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center text-white">
          <Shield className="w-3.5 h-3.5 fill-current" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-800 tracking-tight">Sentinel</span>
          <span className="text-[10px] font-mono font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
            {datasetName || "Online Orders"}
          </span>
        </div>
      </div>

      {/* Floating Center Capsule Navigation (As in reference image) */}
      <nav className="flex items-center space-x-1 bg-white/90 backdrop-blur-md px-2 py-1.5 rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.04)] border border-slate-100">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id as NavTab)}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? "bg-slate-900 text-white shadow-sm font-semibold"
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : "text-slate-400"}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Controls Pill */}
      <div className="flex items-center space-x-2 bg-white px-3 py-1.5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-slate-100 text-xs">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        <span className="text-slate-600 font-mono text-[11px] font-medium">Ready</span>
        {isSynthetic && (
          <span className="text-[10px] text-slate-400 font-mono">v1.0</span>
        )}
      </div>
    </div>
  );
};
