"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard, TrendingUp, DollarSign, Shield, AlertTriangle,
  BarChart3, RefreshCw, Users, MessageSquare, ThumbsUp, ThumbsDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useApp } from "@/contexts/AppContext";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CostBreakdown {
  date: string;
  total_cost: number;
  call_count: number;
  oss_calls: number;
  frontier_calls: number;
}

interface ModelUsage {
  model: string;
  call_count: number;
  total_cost: number;
}

interface GuardrailStats {
  total_checks: number;
  blocked_count: number;
  block_rate: number;
}

interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  details: any;
  ip_address: string | null;
  created_at: string;
}

interface DashboardData {
  daily_costs: CostBreakdown[];
  model_usage: ModelUsage[];
  guardrail_stats: GuardrailStats;
  total_conversations: number;
  total_messages: number;
  total_cost_all_time: number;
  recent_audit_logs: AuditLogEntry[];
  feedback_stats: {
    total: number;
    positive: number;
    negative: number;
    positive_rate: number;
  };
  daily_budget_limit: number;
  daily_spend: number;
  budget_warning: boolean;
}

const PIE_COLORS = ["#a3e635", "#fbbf24", "#60a5fa", "#f472b6", "#a78bfa", "#34d399"];

export default function AdminPage() {
  const { apiKey } = useApp();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/dashboard`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) {
        setData(await res.json());
      } else {
        setError(`HTTP ${res.status}`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiKey]);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  if (loading) {
    return (
      <main className="flex-1 flex items-center justify-center bg-zinc-950">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lime-500"></div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="flex-1 flex items-center justify-center bg-zinc-950">
        <div className="text-center space-y-3 text-zinc-500">
          <AlertTriangle className="h-10 w-10 mx-auto text-red-400" />
          <p className="text-sm">Failed to load dashboard: {error}</p>
          <Button onClick={fetchDashboard} variant="outline" size="sm" className="border-zinc-700 text-zinc-300">
            <RefreshCw className="h-3.5 w-3.5 mr-1" /> Retry
          </Button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col bg-zinc-950 overflow-hidden">
      <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-900/10 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-5 w-5 text-lime-500" />
          <span className="font-semibold text-sm">Admin Dashboard</span>
        </div>
        <div className="flex items-center gap-3">
          {data.budget_warning && (
            <div className="flex items-center gap-1.5 text-xs bg-red-950/30 border border-red-900/40 text-red-400 px-3 py-1.5 rounded-lg animate-pulse">
              <AlertTriangle className="h-3.5 w-3.5" />
              Budget exceeded: ${data.daily_spend.toFixed(4)} / ${data.daily_budget_limit.toFixed(2)}
            </div>
          )}
          <Button onClick={fetchDashboard} size="sm" variant="ghost" className="text-zinc-400 hover:text-zinc-200 text-xs gap-1.5">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="grid grid-cols-6 gap-4">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><MessageSquare className="h-3 w-3" /> Messages</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-zinc-100">{data.total_messages}</div></CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><Users className="h-3 w-3" /> Conversations</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-zinc-100">{data.total_conversations}</div></CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><DollarSign className="h-3 w-3" /> All-Time Cost</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-lime-400">${data.total_cost_all_time.toFixed(4)}</div></CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><TrendingUp className="h-3 w-3" /> Today Spend</CardTitle></CardHeader>
            <CardContent><div className={`text-2xl font-bold ${data.budget_warning ? "text-red-400" : "text-lime-400"}`}>${data.daily_spend.toFixed(4)}</div></CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><Shield className="h-3 w-3" /> Block Rate</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-amber-400">{data.guardrail_stats.block_rate}%</div></CardContent>
          </Card>
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader className="pb-2"><CardTitle className="text-xs text-zinc-400 font-mono flex items-center gap-1"><ThumbsUp className="h-3 w-3" /> Feedback</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-lime-400">{data.feedback_stats.positive_rate}%</div></CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader><CardTitle className="text-sm">Daily Cost (7 days)</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data.daily_costs}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" tick={{ fill: "#a1a1aa", fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                  <YAxis tick={{ fill: "#a1a1aa", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Line type="monotone" dataKey="total_cost" stroke="#a3e635" strokeWidth={2} dot={{ fill: "#a3e635" }} name="Cost ($)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader><CardTitle className="text-sm">Call Volume (7 days)</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.daily_costs}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="date" tick={{ fill: "#a1a1aa", fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                  <YAxis tick={{ fill: "#a1a1aa", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                  <Legend wrapperStyle={{ fontSize: "11px" }} />
                  <Bar dataKey="oss_calls" stackId="a" fill="#60a5fa" name="OSS" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="frontier_calls" stackId="a" fill="#a3e635" name="Frontier" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader><CardTitle className="text-sm">Model Usage Distribution</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={data.model_usage} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={3} dataKey="call_count" nameKey="model" label={({ model, call_count }: any) => `${model}: ${call_count}`}>
                    {data.model_usage.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", color: "#e4e4e7", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader><CardTitle className="text-sm">Guardrail & Feedback Summary</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Guardrail Checks</span>
                  <span className="text-zinc-200">{data.guardrail_stats.total_checks}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">Blocked</span>
                  <span className="text-red-400">{data.guardrail_stats.blocked_count}</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div className="bg-red-500 h-2 rounded-full" style={{ width: `${data.guardrail_stats.block_rate}%` }}></div>
                </div>
              </div>
              <div className="border-t border-zinc-800 pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400 flex items-center gap-1"><ThumbsUp className="h-3 w-3 text-lime-500" /> Positive</span>
                  <span className="text-lime-400">{data.feedback_stats.positive}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400 flex items-center gap-1"><ThumbsDown className="h-3 w-3 text-red-400" /> Negative</span>
                  <span className="text-red-400">{data.feedback_stats.negative}</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div className="bg-lime-500 h-2 rounded-full" style={{ width: `${data.feedback_stats.positive_rate}%` }}></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader><CardTitle className="text-sm">Recent Audit Logs</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="text-left py-2 px-2">Time</th>
                    <th className="text-left py-2 px-2">Action</th>
                    <th className="text-left py-2 px-2">User</th>
                    <th className="text-left py-2 px-2">IP</th>
                    <th className="text-left py-2 px-2">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_audit_logs.map((log) => (
                    <tr key={log.id} className="border-b border-zinc-800/50 text-zinc-300">
                      <td className="py-2 px-2 text-zinc-500">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="py-2 px-2">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                          log.action.includes("blocked") ? "bg-red-950/30 text-red-400" :
                          log.action.includes("guardrail") ? "bg-amber-950/30 text-amber-400" :
                          "bg-zinc-800 text-zinc-300"
                        }`}>{log.action}</span>
                      </td>
                      <td className="py-2 px-2 text-zinc-500">{log.user_id || "-"}</td>
                      <td className="py-2 px-2 text-zinc-500">{log.ip_address || "-"}</td>
                      <td className="py-2 px-2 text-zinc-500 max-w-[200px] truncate">
                        {log.details ? JSON.stringify(log.details).slice(0, 60) : "-"}
                      </td>
                    </tr>
                  ))}
                  {data.recent_audit_logs.length === 0 && (
                    <tr><td colSpan={5} className="py-4 text-center text-zinc-600">No audit logs yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
