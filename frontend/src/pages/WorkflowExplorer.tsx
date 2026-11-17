import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  fetchWorkflowGraph,
  fetchWorkflows,
  selectWorkflow,
  createCustomWorkflow,
} from "../api";
import { WorkflowSummary, ExecutionDetail } from "../types";
import { CustomWorkflowNode } from "../components/CustomWorkflowNode";
import {
  ArrowRight,
  X,
  Plus,
  Check,
  ChevronDown,
  Sparkles,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  CheckCircle2,
  AlertOctagon,
} from "lucide-react";

// Pre-defined default nodes for instant 0ms initial render with clean minimal layout
const DEFAULT_INITIAL_NODES = [
  { id: "START", data: { label: "Start", isInitial: true, isTerminal: false, permittedEvents: ["PLACE_ORDER"] }, position: { x: 40, y: 200 }, type: "customWorkflowNode" },
  { id: "ORDER_PLACED", data: { label: "Order Placed", isInitial: false, isTerminal: false, permittedEvents: ["SUBMIT_PAYMENT", "CANCEL_ORDER"] }, position: { x: 220, y: 200 }, type: "customWorkflowNode" },
  { id: "PAYMENT_PENDING", data: { label: "Payment Pending", isInitial: false, isTerminal: false, permittedEvents: ["PAYMENT_SUCCESS", "PAYMENT_FAIL", "CANCEL_ORDER"] }, position: { x: 440, y: 200 }, type: "customWorkflowNode" },
  { id: "PAYMENT_FAILED", data: { label: "Payment Failed", isInitial: false, isTerminal: false, permittedEvents: ["RETRY_PAYMENT", "CANCEL_ORDER"] }, position: { x: 440, y: 340 }, type: "customWorkflowNode" },
  { id: "ORDER_CANCELLED", data: { label: "Order Cancelled", isInitial: false, isTerminal: true, permittedEvents: [] }, position: { x: 330, y: 60 }, type: "customWorkflowNode" },
  { id: "PAYMENT_CONFIRMED", data: { label: "Payment Confirmed", isInitial: false, isTerminal: false, permittedEvents: ["PACK_ORDER", "CANCEL_ORDER"] }, position: { x: 660, y: 200 }, type: "customWorkflowNode" },
  { id: "ORDER_PACKED", data: { label: "Order Packed", isInitial: false, isTerminal: false, permittedEvents: ["SHIP_ORDER", "CANCEL_ORDER"] }, position: { x: 860, y: 200 }, type: "customWorkflowNode" },
  { id: "REFUND_PENDING", data: { label: "Refund Pending", isInitial: false, isTerminal: false, permittedEvents: ["COMPLETE_REFUND"] }, position: { x: 760, y: 60 }, type: "customWorkflowNode" },
  { id: "REFUND_COMPLETED", data: { label: "Refund Completed", isInitial: false, isTerminal: true, permittedEvents: [] }, position: { x: 980, y: 60 }, type: "customWorkflowNode" },
  { id: "ORDER_SHIPPED", data: { label: "Order Shipped", isInitial: false, isTerminal: false, permittedEvents: ["DELIVER_ORDER"] }, position: { x: 1060, y: 200 }, type: "customWorkflowNode" },
  { id: "ORDER_DELIVERED", data: { label: "Order Delivered", isInitial: false, isTerminal: true, permittedEvents: ["REQUEST_REFUND"] }, position: { x: 1260, y: 200 }, type: "customWorkflowNode" },
];

const DEFAULT_INITIAL_EDGES = [
  { id: "e1", source: "START", target: "ORDER_PLACED", label: "PLACE_ORDER" },
  { id: "e2", source: "ORDER_PLACED", target: "PAYMENT_PENDING", label: "SUBMIT_PAYMENT" },
  { id: "e3", source: "ORDER_PLACED", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
  { id: "e4", source: "PAYMENT_PENDING", target: "PAYMENT_CONFIRMED", label: "PAYMENT_SUCCESS" },
  { id: "e5", source: "PAYMENT_PENDING", target: "PAYMENT_FAILED", label: "PAYMENT_FAIL" },
  { id: "e6", source: "PAYMENT_FAILED", target: "PAYMENT_PENDING", label: "RETRY_PAYMENT" },
  { id: "e7", source: "PAYMENT_PENDING", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
  { id: "e8", source: "PAYMENT_FAILED", target: "ORDER_CANCELLED", label: "CANCEL_ORDER" },
  { id: "e9", source: "PAYMENT_CONFIRMED", target: "ORDER_PACKED", label: "PACK_ORDER" },
  { id: "e10", source: "PAYMENT_CONFIRMED", target: "REFUND_PENDING", label: "CANCEL_ORDER" },
  { id: "e11", source: "ORDER_PACKED", target: "ORDER_SHIPPED", label: "SHIP_ORDER" },
  { id: "e12", source: "ORDER_PACKED", target: "REFUND_PENDING", label: "CANCEL_ORDER" },
  { id: "e13", source: "ORDER_SHIPPED", target: "ORDER_DELIVERED", label: "DELIVER_ORDER" },
  { id: "e14", source: "ORDER_DELIVERED", target: "REFUND_PENDING", label: "REQUEST_REFUND" },
  { id: "e15", source: "REFUND_PENDING", target: "REFUND_COMPLETED", label: "COMPLETE_REFUND" },
].map((e) => ({
  ...e,
  type: "smoothstep",
  markerEnd: { type: MarkerType.ArrowClosed, width: 10, height: 10, color: "#94A3B8" },
  style: { stroke: "#CBD5E1", strokeWidth: 1.5 },
  labelStyle: { fill: "#475569", fontFamily: "JetBrains Mono, monospace", fontSize: 8.5, fontWeight: 500 },
  labelBgStyle: { fill: "#FFFFFF", fillOpacity: 0.95, stroke: "#E2E8F0", strokeWidth: 1, rx: 5, ry: 5 },
}));

// Auto-fit viewport whenever workflow definition changes
function AutoFitter({ nodes }: { nodes: any[] }) {
  const { fitView } = useReactFlow();
  useEffect(() => {
    if (nodes && nodes.length > 0) {
      setTimeout(() => {
        fitView({ padding: 0.22, duration: 350 });
      }, 50);
    }
  }, [nodes, fitView]);
  return null;
}

// Camera controller that centers on active step during trace replay
function ReplayCameraController({ activeStep, nodes }: { activeStep: any; nodes: any[] }) {
  const { setCenter } = useReactFlow();

  useEffect(() => {
    if (!activeStep) return;
    const targetNodeId = (!activeStep.is_valid || !activeStep.state_after)
      ? activeStep.state_before
      : activeStep.state_after;

    const targetNode = nodes.find((n) => n.id === targetNodeId);
    if (targetNode && targetNode.position) {
      setCenter(targetNode.position.x + 75, targetNode.position.y + 20, { zoom: 1.05, duration: 350 });
    }
  }, [activeStep, nodes, setCenter]);

  return null;
}

export interface ReplayData {
  caseId: string;
  detail: ExecutionDetail;
}

export interface WorkflowExplorerProps {
  replayData?: ReplayData | null;
  onClearReplay?: () => void;
}

export const WorkflowExplorerContent: React.FC<WorkflowExplorerProps> = ({
  replayData,
  onClearReplay,
}) => {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string>("online_orders");
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [switching, setSwitching] = useState<boolean>(false);

  // Trace Replay states
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  // Form states for creating a new workflow
  const [newWfName, setNewWfName] = useState("");
  const [newWfDomain, setNewWfDomain] = useState("");
  const [newWfStates, setNewWfStates] = useState("START, SUBMITTED, REVIEW_PASSED, APPROVED, REJECTED");
  const [newWfEvents, setNewWfEvents] = useState("SUBMIT, PASS_REVIEW, APPROVE, REJECT");
  const [newWfInitial, setNewWfInitial] = useState("START");
  const [newWfTerminals, setNewWfTerminals] = useState("APPROVED, REJECTED");
  const [newWfTransitions, setNewWfTransitions] = useState(
    "START, SUBMIT, SUBMITTED\nSUBMITTED, PASS_REVIEW, REVIEW_PASSED\nREVIEW_PASSED, APPROVE, APPROVED\nSUBMITTED, REJECT, REJECTED"
  );

  const [nodes, setNodes, onNodesChange] = useNodesState<any>(DEFAULT_INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>(DEFAULT_INITIAL_EDGES);

  const nodeTypes = useMemo(() => ({ customWorkflowNode: CustomWorkflowNode }), []);

  const loadGraph = useCallback((wfId?: string) => {
    fetchWorkflowGraph()
      .then((data) => {
        if (data && data.nodes && data.nodes.length > 0) {
          const rfNodes = data.nodes.map((n) => ({
            id: n.id,
            type: "customWorkflowNode",
            position: n.position,
            data: n.data,
          }));

          const rfEdges = data.edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.label,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed, width: 10, height: 10, color: "#94A3B8" },
            style: { stroke: "#CBD5E1", strokeWidth: 1.5 },
            labelStyle: { fill: "#475569", fontFamily: "JetBrains Mono, monospace", fontSize: 8.5, fontWeight: 500 },
            labelBgStyle: { fill: "#FFFFFF", fillOpacity: 0.95, stroke: "#E2E8F0", strokeWidth: 1, rx: 5, ry: 5 },
          }));

          setNodes(rfNodes);
          setEdges(rfEdges);
          if (data.id) setActiveWorkflowId(data.id);
        }
      })
      .catch((err) => console.error("Error loading graph:", err));
  }, [setNodes, setEdges]);

  useEffect(() => {
    loadGraph();
    fetchWorkflows()
      .then((res) => {
        setWorkflows(res.workflows);
        setActiveWorkflowId(res.active_workflow_id);
      })
      .catch((err) => console.error("Error loading workflows:", err));
  }, [loadGraph]);

  // Handle Trace Replay initialization
  useEffect(() => {
    if (replayData) {
      setCurrentStepIndex(0);
      setIsPlaying(true);
      setSelectedNode(null);
    }
  }, [replayData?.caseId]);

  const validationSteps = useMemo(() => {
    if (!replayData?.detail?.validation_steps) return [];
    return replayData.detail.validation_steps;
  }, [replayData]);

  // Auto-play stepper interval
  useEffect(() => {
    if (!replayData || !isPlaying || validationSteps.length === 0) return;

    const intervalMs = Math.round(1400 / playbackSpeed);
    const timer = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < validationSteps.length - 1) {
          return prev + 1;
        } else {
          setIsPlaying(false);
          return prev;
        }
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [replayData, isPlaying, playbackSpeed, validationSteps.length]);

  const activeStep = validationSteps[currentStepIndex];

  // Dynamic Nodes with replay highlight states
  const displayNodes = useMemo(() => {
    if (!replayData || !activeStep) return nodes;

    return nodes.map((node) => {
      const isTarget = activeStep.state_after ? node.id === activeStep.state_after : false;
      const isSource = node.id === activeStep.state_before;
      const isViolationNode = !activeStep.is_valid && (node.id === activeStep.state_before || (activeStep.state_after && node.id === activeStep.state_after));

      if (isViolationNode) {
        return {
          ...node,
          data: {
            ...node.data,
            isActive: true,
            isViolating: true,
            isSource: false,
            stepBadge: `Violation`,
          },
        };
      }

      if (isTarget) {
        return {
          ...node,
          data: {
            ...node.data,
            isActive: true,
            isViolating: false,
            isSource: false,
            stepBadge: `Step ${currentStepIndex + 1}`,
          },
        };
      }

      if (isSource) {
        return {
          ...node,
          data: {
            ...node.data,
            isActive: false,
            isViolating: false,
            isSource: true,
          },
        };
      }

      return {
        ...node,
        data: {
          ...node.data,
          isActive: false,
          isViolating: false,
          isSource: false,
          stepBadge: undefined,
        },
      };
    });
  }, [nodes, replayData, activeStep, currentStepIndex]);

  // Dynamic Edges with active replay animation
  const displayEdges = useMemo(() => {
    if (!replayData || !activeStep) return edges;

    return edges.map((edge) => {
      const isCurrentTransition =
        edge.source === activeStep.state_before &&
        (edge.target === activeStep.state_after || edge.label === activeStep.event);

      const isPriorTransition = validationSteps.slice(0, currentStepIndex).some(
        (st) => st.state_before === edge.source && st.state_after === edge.target
      );

      if (isCurrentTransition) {
        const color = activeStep.is_valid ? "#2563EB" : "#E11D48";
        return {
          ...edge,
          animated: true,
          style: { stroke: color, strokeWidth: 2.5 },
          markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color },
          labelStyle: { fill: color, fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700 },
          labelBgStyle: { fill: "#FFFFFF", fillOpacity: 0.98, stroke: color, strokeWidth: 1.5, rx: 5, ry: 5 },
        };
      }

      if (isPriorTransition) {
        return {
          ...edge,
          animated: false,
          style: { stroke: "#64748B", strokeWidth: 1.8 },
          markerEnd: { type: MarkerType.ArrowClosed, width: 10, height: 10, color: "#64748B" },
          labelStyle: { fill: "#475569", fontFamily: "JetBrains Mono, monospace", fontSize: 8.5, fontWeight: 500 },
        };
      }

      return {
        ...edge,
        animated: false,
        style: { stroke: "#E2E8F0", strokeWidth: 1.5, opacity: 0.35 },
        markerEnd: { type: MarkerType.ArrowClosed, width: 8, height: 8, color: "#CBD5E1" },
      };
    });
  }, [edges, replayData, activeStep, currentStepIndex, validationSteps]);

  const handleSelectWorkflow = async (wfId: string) => {
    setDropdownOpen(false);
    if (wfId === activeWorkflowId) return;
    setSwitching(true);
    try {
      await selectWorkflow(wfId);
      setActiveWorkflowId(wfId);
      loadGraph(wfId);
    } catch (err) {
      console.error("Failed to select workflow:", err);
    } finally {
      setSwitching(false);
    }
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWfName) return;

    const id = "custom_" + newWfName.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    const states = newWfStates.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
    const alphabet = newWfEvents.split(",").map((e) => e.trim().toUpperCase()).filter(Boolean);
    const terminals = newWfTerminals.split(",").map((t) => t.trim().toUpperCase()).filter(Boolean);

    const transitionsList: Array<{ from: string; event: string; to: string }> = [];
    newWfTransitions.split("\n").forEach((line) => {
      const parts = line.split(",").map((p) => p.trim());
      if (parts.length === 3) {
        transitionsList.push({ from: parts[0].toUpperCase(), event: parts[1].toUpperCase(), to: parts[2].toUpperCase() });
      }
    });

    setSwitching(true);
    try {
      await createCustomWorkflow({
        id,
        name: newWfName,
        domain: newWfDomain || "Custom Domain",
        description: `Custom defined workflow with ${states.length} states and ${transitionsList.length} transitions.`,
        initial_state: newWfInitial.trim().toUpperCase(),
        states,
        alphabet,
        terminal_states: terminals,
        transitions: transitionsList,
      });

      setShowCreateModal(false);
      setActiveWorkflowId(id);
      loadGraph(id);
      const res = await fetchWorkflows();
      setWorkflows(res.workflows);
    } catch (err) {
      console.error("Failed to create workflow:", err);
    } finally {
      setSwitching(false);
    }
  };

  const activeWorkflow = workflows.find((w) => w.id === activeWorkflowId) || {
    name: "Online Payment & Orders",
    domain: "E-Commerce",
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Normal":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "Invalid":
      case "Invalid + Anomalous":
        return "bg-rose-50 text-rose-700 border-rose-200";
      case "Suspicious":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="relative bg-white rounded-3xl border border-slate-100 shadow-[0_4px_25px_rgba(0,0,0,0.03)] h-[740px] overflow-hidden">
      {/* Top Floating Control Bar: Workflow Switcher, Create Button, Legend */}
      <div className="absolute top-4 left-6 right-6 z-10 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-2.5 pointer-events-auto">
          {/* Workflow Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center space-x-2 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl border border-slate-200/90 shadow-xs hover:border-slate-300 transition-all text-xs cursor-pointer group"
            >
              <div className="w-2 h-2 rounded-full bg-blue-600" />
              <div className="text-left font-mono">
                <span className="font-bold text-slate-800">{activeWorkflow.name}</span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 transition-transform" />
            </button>

            {dropdownOpen && (
              <div className="absolute top-12 left-0 w-72 bg-white rounded-2xl border border-slate-150 shadow-[0_12px_32px_rgba(0,0,0,0.09)] p-2 z-50 text-xs animate-in fade-in duration-150">
                <div className="px-3 py-1.5 text-[10px] uppercase font-mono font-bold text-slate-400 tracking-wider">
                  Select Workflow Domain
                </div>
                <div className="space-y-1 mt-1 max-h-56 overflow-y-auto">
                  {workflows.map((wf) => (
                    <button
                      key={wf.id}
                      onClick={() => handleSelectWorkflow(wf.id)}
                      className={`w-full text-left px-3 py-2 rounded-xl flex items-center justify-between transition-colors ${
                        wf.id === activeWorkflowId
                          ? "bg-slate-900 text-white font-semibold"
                          : "hover:bg-slate-50 text-slate-700"
                      }`}
                    >
                      <div>
                        <div className="font-medium">{wf.name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{wf.domain}</div>
                      </div>
                      {wf.id === activeWorkflowId && <Check className="w-3.5 h-3.5 text-white" />}
                    </button>
                  ))}
                </div>

                <div className="pt-2 mt-2 border-t border-slate-100">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      setShowCreateModal(true);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-blue-600 font-semibold hover:bg-blue-50/80 transition-colors flex items-center space-x-2"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create Custom Workflow</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Prominent Direct "+ Create Workflow" Button */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-2 rounded-2xl shadow-xs transition-all text-xs font-semibold cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-blue-400" />
            <span>+ Create Workflow</span>
          </button>
        </div>

        {/* Right Toolbar: Mini Legend */}
        {!replayData && (
          <div className="flex items-center space-x-2 pointer-events-auto">
            <div className="flex items-center space-x-2 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl border border-slate-200/90 shadow-xs text-[11px] font-mono">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                <span className="text-slate-600 font-medium">Initial (q₀)</span>
              </span>
              <span className="text-slate-300">·</span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-slate-600 font-medium">Accepting (F)</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Switcher Overlay Indicator */}
      {switching && (
        <div className="absolute inset-0 bg-white/60 backdrop-blur-xs z-30 flex items-center justify-center text-xs font-mono text-slate-600 space-x-2">
          <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
          <span>Switching workflow automaton...</span>
        </div>
      )}

      {/* ReactFlow Canvas */}
      <ReactFlow
        nodes={displayNodes}
        edges={displayEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => setSelectedNode(node)}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.22 }}
        attributionPosition="bottom-left"
      >
        {!replayData && <AutoFitter nodes={nodes} />}
        {replayData && <ReplayCameraController activeStep={activeStep} nodes={displayNodes} />}
        <Background color="#CBD5E1" gap={22} size={1} />
        <Controls className="!bg-white !border-slate-150 !rounded-xl shadow-xs !fill-slate-600" />
        <MiniMap
          nodeColor={(node: any) => {
            if (node.data?.isViolating) return "#E11D48";
            if (node.data?.isActive) return "#2563EB";
            if (node.data?.isInitial) return "#3B82F6";
            if (node.data?.isTerminal) return "#10B981";
            return "#E2E8F0";
          }}
          className="!bg-white !border-slate-150 !rounded-xl shadow-xs"
        />
      </ReactFlow>

      {/* MINIMAL, UNCLUTTERED TRACE RUNNER & STEP DIAGNOSIS CARD */}
      {replayData && activeStep && (
        <div className="absolute top-4 right-6 z-20 w-80 bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 shadow-[0_8px_30px_rgba(0,0,0,0.08)] p-3.5 text-xs animate-in fade-in duration-150 space-y-2.5">
          {/* Header row: Case ID, Status Badge, Close */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="font-mono font-bold text-slate-800 text-xs">
                {replayData.caseId}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border font-semibold ${getStatusColor(replayData.detail.record.final_classification)}`}>
                {replayData.detail.record.final_classification}
              </span>
            </div>
            <button
              onClick={onClearReplay}
              className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              title="Close replay"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Clean Transition Path: State Before -> Event -> State After */}
          <div className="px-2.5 py-1.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between font-mono text-[11px]">
            <span className="font-semibold text-slate-700 truncate max-w-[85px]" title={activeStep.state_before}>
              {activeStep.state_before}
            </span>
            <div className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-blue-50 border border-blue-100 text-blue-700 text-[10px] font-bold">
              <span className="truncate max-w-[95px]">{activeStep.event}</span>
              <ArrowRight className="w-2.5 h-2.5 text-blue-500 shrink-0" />
            </div>
            <span
              className={`font-semibold truncate max-w-[85px] ${activeStep.state_after ? "text-slate-700" : "text-rose-600"}`}
              title={activeStep.state_after || "REJECT"}
            >
              {activeStep.state_after || "REJECT"}
            </span>
          </div>

              {/* Verdict: Clear, step-by-step reasoning */}
              <div>
                {activeStep.is_valid ? (
                  <div className="flex items-start space-x-1.5 text-emerald-800 bg-emerald-50/70 border border-emerald-100/80 rounded-xl p-2 text-[11px] leading-snug">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-600" />
                    <div>
                      <span className="font-semibold block text-[11px]">Valid Step Execution</span>
                      <span className="text-[10.5px] text-emerald-700/90 font-sans block">
                        Transitioned from <strong>{activeStep.state_before}</strong> to <strong>{activeStep.state_after}</strong> successfully.
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start space-x-1.5 text-rose-800 bg-rose-50/80 border border-rose-200/80 rounded-xl p-2 text-[11px] leading-snug">
                    <AlertOctagon className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-600" />
                    <div>
                      <span className="font-bold block text-[11px] text-rose-900">Grammar Rule Violation</span>
                      <span className="text-[10.5px] text-rose-700 font-sans block">
                        Symbol <code className="font-mono bg-rose-100 px-1 py-0.5 rounded text-rose-900">{activeStep.event}</code> cannot be executed from state <strong>{activeStep.state_before}</strong>.
                      </span>
                      {activeStep.permitted_events && activeStep.permitted_events.length > 0 && (
                        <span className="text-[10px] text-rose-600 font-mono block mt-1">
                          Permitted here: {activeStep.permitted_events.join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

          {/* Integrated Play, Pause & Stepper Controls */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setCurrentStepIndex((p) => Math.max(0, p - 1))}
                disabled={currentStepIndex === 0}
                className="p-1.5 text-slate-500 hover:text-slate-800 disabled:opacity-30 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                title="Previous step"
              >
                <SkipBack className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg shadow-xs flex items-center space-x-1 text-[11px] font-mono cursor-pointer transition-all"
                title={isPlaying ? "Pause trace animation" : "Play trace animation"}
              >
                {isPlaying ? <Pause className="w-3 h-3 fill-white" /> : <Play className="w-3 h-3 fill-white" />}
                <span>{isPlaying ? "Pause" : "Play"}</span>
              </button>
              <button
                onClick={() => setCurrentStepIndex((p) => Math.min(validationSteps.length - 1, p + 1))}
                disabled={currentStepIndex === validationSteps.length - 1}
                className="p-1.5 text-slate-500 hover:text-slate-800 disabled:opacity-30 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                title="Next step"
              >
                <SkipForward className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Step Counter & Speed */}
            <div className="flex items-center space-x-2">
              <span className="text-[10.5px] font-mono text-slate-500">
                Step {currentStepIndex + 1}/{validationSteps.length}
              </span>
              <button
                onClick={() => setPlaybackSpeed((s) => (s === 1 ? 2 : s === 2 ? 0.5 : 1))}
                className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold cursor-pointer"
                title="Animation speed"
              >
                {playbackSpeed}x
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating State Inspector Popup (Non-Replay Mode) */}
      {!replayData && selectedNode && (
        <div className="absolute top-4 right-6 z-20 w-72 bg-white rounded-2xl border border-slate-150 shadow-[0_8px_30px_rgba(0,0,0,0.08)] p-3.5 text-xs animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
            <div>
              <span className="text-[9.5px] uppercase font-mono text-slate-400 tracking-wider">State Details</span>
              <div className="text-xs font-bold text-slate-800 mt-0.5">{selectedNode.id}</div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="w-5 h-5 rounded-md bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
            >
              <X className="w-3 h-3" />
            </button>
          </div>

          <div className="mt-2.5">
            <span className="text-[10px] font-semibold text-slate-500 uppercase font-mono block mb-1.5">Permitted Transitions</span>
            {selectedNode.data.permittedEvents?.length > 0 ? (
              <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                {selectedNode.data.permittedEvents.map((ev: string) => (
                  <div
                    key={ev}
                    className="flex items-center space-x-1.5 bg-slate-50 border border-slate-100 px-2 py-1 rounded-md text-slate-700 font-mono text-[10.5px]"
                  >
                    <ArrowRight className="w-2.5 h-2.5 text-blue-500 shrink-0" />
                    <span>{ev}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-slate-400 italic font-mono text-[10.5px] p-2 bg-slate-50 rounded-lg">
                Terminal state. Sequence halts here.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Floating Action Button (Bottom Right) to Create Automaton (Non-Replay Mode) */}
      {!replayData && (
        <button
          onClick={() => setShowCreateModal(true)}
          className="absolute bottom-6 right-6 z-20 w-11 h-11 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl shadow-lg flex items-center justify-center cursor-pointer transition-all hover:scale-105 active:scale-95 group"
          title="Create New Workflow Automaton"
        >
          <Plus className="w-4 h-4 text-blue-400 group-hover:rotate-90 transition-transform" />
        </button>
      )}

      {/* Create Custom Workflow Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl border border-slate-150 shadow-[0_20px_50px_rgba(0,0,0,0.15)] max-w-lg w-full p-6 text-xs text-slate-700">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <div className="w-7 h-7 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  Σ
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Define Workflow Automaton</h3>
                  <p className="text-[11px] text-slate-400">Specify states, alphabet symbols, and transition rules</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="w-7 h-7 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateWorkflow} className="mt-4 space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Workflow Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Student Registration"
                    value={newWfName}
                    onChange={(e) => setNewWfName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-sans"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Domain
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Education / Healthcare"
                    value={newWfDomain}
                    onChange={(e) => setNewWfDomain(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-sans"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                  States Q (comma-separated)
                </label>
                <input
                  type="text"
                  required
                  value={newWfStates}
                  onChange={(e) => setNewWfStates(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                  Alphabet Σ (Events)
                </label>
                <input
                  type="text"
                  required
                  value={newWfEvents}
                  onChange={(e) => setNewWfEvents(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Initial State q₀
                  </label>
                  <input
                    type="text"
                    required
                    value={newWfInitial}
                    onChange={(e) => setNewWfInitial(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                    Accepting / Terminal States F
                  </label>
                  <input
                    type="text"
                    required
                    value={newWfTerminals}
                    onChange={(e) => setNewWfTerminals(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 font-bold mb-1">
                  Transition Function δ: From, Event, To (One per line)
                </label>
                <textarea
                  rows={4}
                  required
                  value={newWfTransitions}
                  onChange={(e) => setNewWfTransitions(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500 font-mono text-[11px] leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium cursor-pointer shadow-xs flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  <span>Create & Activate Automaton</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export const WorkflowExplorer: React.FC<WorkflowExplorerProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowExplorerContent {...props} />
    </ReactFlowProvider>
  );
};
