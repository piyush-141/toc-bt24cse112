import React, { useState, useEffect } from "react";
import { Header, NavTab } from "./components/Header";
import { Overview } from "./pages/Overview";
import { WorkflowExplorer } from "./pages/WorkflowExplorer";
import { Executions } from "./pages/Executions";
import { DatasetPage } from "./pages/DatasetPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { fetchOverview } from "./api";
import { OverviewData, ExecutionDetail } from "./types";

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>("workflow");
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [executionFilter, setExecutionFilter] = useState<string>("ALL");
  const [replayData, setReplayData] = useState<{ caseId: string; detail: ExecutionDetail } | null>(null);

  const loadOverview = () => {
    setLoading(true);
    fetchOverview()
      .then((data) => {
        setOverviewData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch overview", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const handleExploreExecutions = (filter = "ALL") => {
    setExecutionFilter(filter);
    setCurrentTab("executions");
  };

  const handleRunCase = (caseId: string, detail: ExecutionDetail) => {
    setReplayData({ caseId, detail });
    setCurrentTab("workflow");
  };

  return (
    <div className="min-h-screen bg-[#F1F4F9] text-slate-800 flex flex-col font-sans bg-canvas-dots">
      {/* Top Floating Header */}
      <Header
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        datasetName={overviewData?.dataset_meta?.name}
        isSynthetic={overviewData?.dataset_meta?.is_synthetic}
      />

      {/* Main Canvas Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-2 pb-10">
        {currentTab === "overview" && (
          <Overview
            data={overviewData}
            loading={loading}
            onExploreExecutions={handleExploreExecutions}
          />
        )}

        {currentTab === "workflow" && (
          <WorkflowExplorer
            replayData={replayData}
            onClearReplay={() => setReplayData(null)}
          />
        )}

        {currentTab === "executions" && (
          <Executions
            initialFilter={executionFilter}
            onRunCase={handleRunCase}
          />
        )}

        {currentTab === "dataset" && (
          <DatasetPage
            meta={overviewData?.dataset_meta || null}
            onDatasetUpdated={loadOverview}
          />
        )}

        {currentTab === "evaluation" && <EvaluationPage />}
      </main>
    </div>
  );
}

export default App;
