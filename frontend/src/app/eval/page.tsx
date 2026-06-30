"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart3, Play, RefreshCw, Download, Trophy, Target, Zap, Clock, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useApp } from "@/contexts/AppContext";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from "recharts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EvalRun {
  id: string;
  run_type: string;
  judge_model: string;
  passed: boolean;
  report_path: string | null;
  created_at: string;
}

interface DimScore {
  category: string;
  dimension: string;
  model_a_avg_score: number;
  model_b_avg_score: number;
  model_a_win_count: number;
  model_b_win_count: number;
  tie_count: number;
  prompt_count: number;
}

interface RunStats {
  run_id: string;
  run_type: string;
  judge_model: string;
  passed: boolean;
  created_at: string;
  total_prompts: number;
  model_a_name: string;
  model_b_name: string;
  model_a_wins: number;
  model_b_wins: number;
  ties: number;
  dimension_scores: DimScore[];
}

interface OverallStats {
  total_runs: number;
  completed_runs: number;
  active_models: string[];
  overall_model_a_win_rate: number;
  overall_model_b_win_rate: number;
  overall_tie_rate: number;
  recent_runs: EvalRun[];
}

const COLORS = ["#a3e635", "#fbbf24", "#6b7280", "#ef4444"];
const CHART_COLORS = { model_a: "#4ade80", model_b: "#60a5fa" };

export default function EvalPage() {
  const { apiKey } = useApp();
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runStats, setRunStats] = useState<RunStats | null>(null);
  const [overallStats, setOverallStats] = useState<OverallStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [runType, setRunType] = useState("smoke");
  const [judgeModel, setJudgeModel] = useState("gpt-4.1-mini");
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/runs?limit=20`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
        if (data.length > 0 && !selectedRunId) {
          setSelectedRunId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch runs", err);
    }
  }, [apiKey, selectedRunId]);

  const fetchRunStats = useCallback(async (runId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/runs/${runId}/stats`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) {
        setRunStats(await res.json());
      } else {
        setError("Failed to fetch run stats");
      }
    } catch (err) {
      setError("Network error fetching stats");
    } finally {
      setLoading(false);
    }
  }, [apiKey]);

  const fetchOverallStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/stats`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) setOverallStats(await res.json());
    } catch (err) {
      console.error("Failed to fetch overall stats", err);
    }
  }, [apiKey]);

  useEffect(() => { fetchRuns(); fetchOverallStats(); }, [fetchRuns, fetchOverallStats]);
  useEffect(() => {
    if (selectedRunId) fetchRunStats(selectedRunId);
  }, [selectedRunId, fetchRunStats]);

  const triggerEval = async () => {
    setTriggering(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/evaluations/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify({ run_type: runType, judge_model: judgeModel })
      });
      if (res.ok) {
        const data = await res.json();
        alert(data.message);
        setTimeout(() => { fetchRuns(); fetchOverallStats(); }, 3000);
      } else {
        const err = await res.json();
        alert(`Failed: ${err.detail}`);
      }
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  const winData = runStats ? [
    { name: runStats.model_a_name, value: runStats.model_a_wins, color: CHART_COLORS.model_a },
    { name: runStats.model_b_name, value: runStats.model_b_wins, color: CHART_COLORS.model_b },
    { name: "Tie", value: runStats.ties, color: COLORS[2] },
  ] : [];

  const barData = runStats?.dimension_scores?.map((d) => ({
    dimension: `${d.category}\n${d.dimension}`,
    [runStats.model_a_name || "Model A"]: d.model_a_avg_score,
    [runStats.model_b_name || "Model B"]: d.model_b_avg_score,
  })) || [];

  const radarData = runStats?.dimension_scores?.map((d) => ({
    dimension: d.dimension,
    A: d.model_a_avg_score,
    B: d.model_b_avg_score,
    fullMark: 5,
  })) || [];

  return (
    <main className="flex-1 flex flex-col bg-zinc-950 overflow-hidden">
      <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-900/10 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-5 w-5 text-lime-500" />
          <span className="font-semibold text-sm">Evaluation Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          <Select value={runType} onValueChange={(v) => v && setRunType(v)}>
            <SelectTrigger className="w-28 h-8 text-xs bg-zinc-900 border-zinc-700 text-zinc-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700 text-zinc-200">
              <SelectItem value="smoke">Smoke (2/prompt)</SelectItem>
              <SelectItem value="full">Full Suite</SelectItem>
            </SelectContent>
          </Select>
          <Select value={judgeModel} onValueChange={(v) => v && setJudgeModel(v)}>
            <SelectTrigger className="w-40 h-8 text-xs bg-zinc-900 border-zinc-700 text-zinc-200">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-700 text-zinc-200">
              <SelectItem value="gpt-4.1-mini">GPT-4.1 Mini</SelectItem>
              <SelectItem value="gpt-4.1">GPT-4.1</SelectItem>
            </SelectContent>
          </Select>
          <Button
            onClick={triggerEval}
            disabled={triggering}
            size="sm"
            className="bg-lime-500 hover:bg-lime-400 text-black text-xs gap-1.5"
          >
            <Play className="h-3.5 w-3.5" />
            {triggering ? "Running..." : "Run Eval"}
          </Button>
          {selectedRunId && (
            <Button
              onClick={() => {
                window.open(`${API_BASE_URL}/api/v1/evaluations/runs/${selectedRunId}/pdf?api_key=${apiKey}`, "_blank");
              }}
              size="sm"
              variant="outline"
              className="border-zinc-700 hover:bg-zinc-800 text-zinc-300 text-xs gap-1.5"
            >
              <Download className="h-3.5 w-3.5" />
              Download PDF
            </Button>
          )}
          <Button
            onClick={() => { fetchRuns(); fetchOverallStats(); if (selectedRunId) fetchRunStats(selectedRunId); }}
            size="sm" variant="ghost"
            className="text-zinc-400 hover:text-zinc-200 text-xs gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 border-r border-zinc-800 bg-zinc-900/20 flex flex-col shrink-0">
          <div className="p-3 border-b border-zinc-800">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Evaluation Runs</h3>
          </div>
          <ScrollArea className="flex-1">
            <div className="space-y-0.5 p-2">
              {runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition-all ${
                    selectedRunId === run.id
                      ? "bg-zinc-800 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${run.passed ? "bg-lime-500" : "bg-amber-500"}`}></span>
                    <span className="font-medium">{run.run_type.toUpperCase()}</span>
                  </div>
                  <div className="text-[10px] text-zinc-500 mt-0.5 truncate">
                    {new Date(run.created_at).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-zinc-600 truncate">{run.judge_model}</div>
                </button>
              ))}
              {runs.length === 0 && (
                <div className="text-center py-8 text-zinc-600 text-xs">
                  <AlertCircle className="h-6 w-6 mx-auto mb-2 opacity-30" />
                  No evaluation runs yet
                </div>
              )}
            </div>
          </ScrollArea>
          {overallStats && (
            <div className="p-3 border-t border-zinc-800 space-y-1.5">
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>Total Runs</span><span className="text-zinc-300">{overallStats.total_runs}</span>
              </div>
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>Completed</span><span className="text-lime-400">{overallStats.completed_runs}</span>
              </div>
            </div>
          )}
        </aside>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-950/20 border border-red-900/30 text-red-200 rounded-xl p-4 text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          {!selectedRunId && !loading && (
            <div className="h-full flex items-center justify-center text-zinc-600">
              <div className="text-center space-y-3">
                <BarChart3 className="h-12 w-12 mx-auto opacity-20" />
                <p className="text-sm">Select an evaluation run from the sidebar or trigger a new one</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lime-500"></div>
            </div>
          )}

          {runStats && !loading && (
            <>
              <div className="grid grid-cols-4 gap-4">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono">Total Prompts</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold text-zinc-100">{runStats.total_prompts}</div></CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><Trophy className="h-3 w-3 text-lime-500" /> {runStats.model_a_name} Wins</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold text-lime-400">{runStats.model_a_wins}</div></CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><Trophy className="h-3 w-3 text-blue-400" /> {runStats.model_b_name} Wins</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold text-blue-400">{runStats.model_b_wins}</div></CardContent>
                </Card>
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono">Ties</CardTitle></CardHeader>
                  <CardContent><div className="text-2xl font-bold text-zinc-400">{runStats.ties}</div></CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader><CardTitle className="text-sm">Per-Dimension Score Comparison</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={barData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                        <XAxis dataKey="dimension" tick={{ fill: "#a1a1aa", fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
                        <YAxis domain={[0, 5]} tick={{ fill: "#a1a1aa", fontSize: 10 }} />
                        <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                        <Legend wrapperStyle={{ fontSize: "11px", color: "#a1a1aa" }} />
                        <Bar dataKey={runStats.model_a_name || "Model A"} fill={CHART_COLORS.model_a} radius={[4, 4, 0, 0]} />
                        <Bar dataKey={runStats.model_b_name || "Model B"} fill={CHART_COLORS.model_b} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-900/50 border-zinc-800">
                  <CardHeader><CardTitle className="text-sm">Win Distribution</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie data={winData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                          {winData.map((entry, idx) => (
                            <Cell key={idx} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader><CardTitle className="text-sm">Radar Comparison</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={350}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#27272a" />
                      <PolarAngleAxis dataKey="dimension" tick={{ fill: "#a1a1aa", fontSize: 10 }} />
                      <PolarRadiusAxis domain={[0, 5]} tick={{ fill: "#a1a1aa", fontSize: 9 }} />
                      <Radar name={runStats.model_a_name || "Model A"} dataKey="A" stroke={CHART_COLORS.model_a} fill={CHART_COLORS.model_a} fillOpacity={0.2} />
                      <Radar name={runStats.model_b_name || "Model B"} dataKey="B" stroke={CHART_COLORS.model_b} fill={CHART_COLORS.model_b} fillOpacity={0.2} />
                      <Legend wrapperStyle={{ fontSize: "11px", color: "#a1a1aa" }} />
                      <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader><CardTitle className="text-sm flex items-center gap-2">
                  <Target className="h-4 w-4 text-lime-500" />
                  Detailed Dimension Scores
                </CardTitle></CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-zinc-800 text-zinc-400">
                          <th className="text-left py-2 px-2">Category</th>
                          <th className="text-left py-2 px-2">Dimension</th>
                          <th className="text-right py-2 px-2">{runStats.model_a_name} Score</th>
                          <th className="text-right py-2 px-2">{runStats.model_b_name} Score</th>
                          <th className="text-right py-2 px-2">Prompts</th>
                          <th className="text-right py-2 px-2">{runStats.model_a_name} Wins</th>
                          <th className="text-right py-2 px-2">{runStats.model_b_name} Wins</th>
                          <th className="text-right py-2 px-2">Ties</th>
                        </tr>
                      </thead>
                      <tbody>
                        {runStats.dimension_scores.map((ds, i) => (
                          <tr key={i} className="border-b border-zinc-800/50 text-zinc-300">
                            <td className="py-2 px-2 font-medium">{ds.category}</td>
                            <td className="py-2 px-2 text-zinc-400">{ds.dimension}</td>
                            <td className="py-2 px-2 text-right text-lime-400">{ds.model_a_avg_score}</td>
                            <td className="py-2 px-2 text-right text-blue-400">{ds.model_b_avg_score}</td>
                            <td className="py-2 px-2 text-right">{ds.prompt_count}</td>
                            <td className="py-2 px-2 text-right text-lime-400">{ds.model_a_win_count}</td>
                            <td className="py-2 px-2 text-right text-blue-400">{ds.model_b_win_count}</td>
                            <td className="py-2 px-2 text-right text-zinc-400">{ds.tie_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
