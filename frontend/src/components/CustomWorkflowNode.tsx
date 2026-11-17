import React from "react";
import { Handle, Position } from "@xyflow/react";

export const CustomWorkflowNode = ({ data }: any) => {
  const { label, isInitial, isTerminal, isActive, isViolating, isSource, stepBadge } = data;

  const getBorderAndBg = () => {
    if (isViolating) {
      return "border-rose-500 bg-rose-50/90 ring-2 ring-rose-500/20 shadow-[0_0_18px_rgba(244,63,94,0.3)] animate-pulse";
    }
    if (isActive) {
      return "border-blue-600 bg-blue-50/80 ring-2 ring-blue-500/20 shadow-[0_0_18px_rgba(37,99,235,0.25)] scale-[1.02]";
    }
    if (isSource) {
      return "border-slate-400 bg-slate-50/90 shadow-xs";
    }
    return "border-slate-200/90 bg-white hover:border-slate-300 shadow-xs hover:shadow-sm";
  };

  return (
    <div
      className={`relative rounded-xl px-3 py-2 min-w-[125px] max-w-[155px] border transition-all text-left flex items-center justify-between gap-2 select-none ${getBorderAndBg()}`}
    >
      {/* Floating step badge in trace replay mode */}
      {stepBadge && (
        <div
          className={`absolute -top-2.5 left-2 px-1.5 py-0.2 rounded-full text-[8.5px] font-mono font-bold shadow-xs tracking-tight ${
            isViolating ? "bg-rose-600 text-white" : "bg-blue-600 text-white"
          }`}
        >
          {stepBadge}
        </div>
      )}

      {/* Target Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-1.5 !h-1.5 !bg-slate-400 !border !border-white !-left-1"
      />
      <Handle
        type="target"
        id="top"
        position={Position.Top}
        className="!w-1.5 !h-1.5 !bg-slate-400 !border !border-white !-top-1"
      />

      {/* State label & minimal dot */}
      <div className="flex items-center space-x-2 min-w-0 flex-1">
        <span
          className={`w-2 h-2 rounded-full shrink-0 ${
            isViolating
              ? "bg-rose-500 ring-2 ring-rose-200"
              : isActive
              ? "bg-blue-600 ring-2 ring-blue-200"
              : isInitial
              ? "bg-blue-500 ring-2 ring-blue-100"
              : isTerminal
              ? "bg-emerald-500 ring-2 ring-emerald-100"
              : "bg-slate-300"
          }`}
        />
        <span className="text-[11.5px] font-semibold text-slate-800 tracking-tight leading-tight truncate">
          {label}
        </span>
      </div>

      {/* Formal Automata Marker */}
      {isInitial && (
        <span className="text-[9px] font-mono font-bold text-blue-600 bg-blue-50 px-1 py-0.2 rounded shrink-0">
          q₀
        </span>
      )}
      {isTerminal && (
        <span className="text-[9px] font-mono font-bold text-emerald-600 bg-emerald-50 px-1 py-0.2 rounded shrink-0">
          F
        </span>
      )}

      {/* Source Handles */}
      <Handle
        type="source"
        id="bottom"
        position={Position.Bottom}
        className="!w-1.5 !h-1.5 !bg-slate-400 !border !border-white !-bottom-1"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-1.5 !h-1.5 !bg-slate-400 !border !border-white !-right-1"
      />
    </div>
  );
};
