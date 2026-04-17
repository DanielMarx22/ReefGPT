/**
 * Readings Chart Component
 * =================
 * Displays parameter readings as interactive line charts,
 * separated by data source (CSV, Supabase, Synthetic).
 */

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Database, Cloud, FlaskConical } from "lucide-react";

export default function Readings({
  uniqueParams,
  activeTab,
  setActiveTab,
  dataSource,
  setDataSource,
  logs,
}: {
  uniqueParams: string[];
  activeTab: string;
  setActiveTab: any;
  dataSource: string;
  setDataSource: any;
  logs: any[];
}) {
  // Data sources
  const sources = [
    { id: "csv", label: "CSV", icon: Database },
    { id: "supabase", label: "Supabase", icon: Cloud },
    { id: "synthetic", label: "Synthetic", icon: FlaskConical },
  ];
  
  // Get unique parameters
  const paramSet = new Set(logs?.map((l: any) => l.parameter) || []);
  const params = Array.from(paramSet);
  
  // Get chart data for current parameter and source
  const getChartData = () => {
    if (!logs || logs.length === 0) return [];
    
    const filtered = logs.filter((l: any) => {
      if (l.parameter !== activeTab) return false;
      // Filter by source if the data has a source field
      if (l.source && l.source !== dataSource) return false;
      // For Supabase logs (no source field), show when dataSource is "supabase"
      if (!l.source && dataSource !== "supabase") return false;
      return true;
    });
    return filtered
      .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map((l: any) => ({
        date: new Date(l.timestamp).toLocaleDateString(),
        value: l.value,
        source: l.source || "supabase",
      }));
  };
  
  const chartData = getChartData();
  
  return (
    <div className="h-full flex flex-col p-6">
      {/* Data Source Tabs */}
      <div className="flex gap-2 mb-4 border-b border-white/10 pb-2">
        {sources.map((source) => (
          <button
            key={source.id}
            onClick={() => setDataSource(source.id)}
            className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium transition rounded-lg ${
              dataSource === source.id
                ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/50"
                : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
            }`}
          >
            <source.icon size={14} /> {source.label}
          </button>
        ))}
      </div>
      
      {/* Parameter Tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide border-b border-white/10">
        {params.map((param: string) => (
          <button
            key={param}
            onClick={() => setActiveTab(param)}
            className={`px-4 py-2 text-sm font-semibold transition tracking-wide ${
              activeTab === param
                ? "text-cyan-400 border-b-2 border-cyan-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {param}
          </button>
        ))}
      </div>
      
      {/* Chart */}
      <div className="flex-1 w-full min-h-[300px]">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#ffffff1a"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                stroke="#94a3b8"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#94a3b8"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                domain={["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(0,0,0,0.8)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "8px",
                }}
                itemStyle={{ color: "#22d3ee", fontWeight: "bold" }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#22d3ee"
                strokeWidth={3}
                dot={{ r: 4, fill: "#000", stroke: "#22d3ee", strokeWidth: 2 }}
                activeDot={{ r: 6, fill: "#22d3ee", stroke: "#fff" }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500">
            No data available for {activeTab} in {dataSource} source
          </div>
        )}
      </div>
      
      {/* Stats */}
      <div className="flex gap-4 mt-4 pt-4 border-t border-white/10">
        <div className="text-xs text-slate-500">
          <span className="font-medium text-slate-400">{sources.find(s => s.id === dataSource)?.label}</span> source
        </div>
        <div className="text-xs text-slate-500">
          <span className="font-medium text-slate-400">{chartData.length}</span> data points
        </div>
        {chartData.length > 0 && (
          <div className="text-xs text-slate-500">
            Range: <span className="font-medium text-slate-400">
              {Math.min(...chartData.map((d: any) => d.value)).toFixed(1)} - {Math.max(...chartData.map((d: any) => d.value)).toFixed(1)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}