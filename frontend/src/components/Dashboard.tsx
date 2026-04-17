/**
 * Dashboard Component
 * ==============
 * Main control panel for ReefGPT frontend.
 * 
 * Functions:
 * - Log parameter readings manually
 * - Select data source (CSV/Supabase/Synthetic)
 * - View prediction state and 24-hour forecast
 * - Upload CSV or generate synthetic data
 * - Delete logs
 * 
 * Props:
 * - newParam, newValue: Current input values
 * - addManualLog: Function to log a reading
 * - latestMetrics: Current tank readings
 * - dataSource: Selected data source
 * - prediction: Current prediction state
 * - onUploadCSV, onGenerateSynthetic, onDeleteLogs: Action handlers
 */

import { Activity, Plus, TrendingUp, AlertTriangle, CheckCircle, Database, Cloud, FlaskConical, RefreshCw, Trash2 } from "lucide-react";

export default function Dashboard({
  newParam,
  setNewParam,
  newValue,
  setNewValue,
  addManualLog,
  latestMetrics,
  dataSource,
  setDataSource,
  prediction,
  onUploadCSV,
  onGenerateSynthetic,
  onDeleteLogs,
}: {
  newParam: any;
  setNewParam: any;
  newValue: any;
  setNewValue: any;
  addManualLog: any;
  latestMetrics: any;
  dataSource: any;
  setDataSource: any;
  prediction: any;
  onUploadCSV: any;
  onGenerateSynthetic: any;
  onDeleteLogs: any;
}) {
  const getTrendColor = (trend: string) => {
    if (trend === "stable") return "text-green-400";
    if (trend === "warning") return "text-yellow-400";
    return "text-red-400";
  };

  const getTrendIcon = (trend: string) => {
    if (trend === "stable") return <CheckCircle size={14} />;
    return <AlertTriangle size={14} />;
  };

  const sources = [
    { id: "csv", label: "CSV", icon: Database, desc: "Load file", hasAction: false },
    { id: "supabase", label: "Supabase", icon: Cloud, desc: "History", hasAction: false },
    { id: "synthetic", label: "Synthetic", icon: FlaskConical, desc: "Generate", hasAction: false },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Data Source Selector */}
      <div className="bg-black/40 p-3 rounded-xl border border-white/10 backdrop-blur-md">
        <div className="text-xs text-slate-400 mb-2">Data Source:</div>
        <div className="flex gap-2">
          {sources.map((src) => {
            const Icon = src.icon;
            return (
              <div key={src.id} className="flex flex-col gap-1">
                <button
                  onClick={() => setDataSource(src.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                    dataSource === src.id
                      ? "bg-cyan-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  <Icon size={14} />
                  {src.label}
                </button>
                {/* Switch to CSV */}
                {src.id === "csv" && dataSource === "csv" && (
                  <div className="text-xs text-slate-500 px-2">
                    Edit test_data.csv
                  </div>
                )}
                {/* Generate Synthetic */}
                {src.id === "synthetic" && dataSource === "synthetic" && (
                  <button
                    onClick={onGenerateSynthetic}
                    className="flex items-center justify-center gap-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs"
                  >
                    <RefreshCw size={12} />
                    Generate
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Delete Section */}
      <div className="bg-black/40 p-3 rounded-xl border border-white/10 backdrop-blur-md">
        <div className="text-xs text-slate-400 mb-2">Delete Logs:</div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (confirm("Delete ALL logs?")) onDeleteLogs();
            }}
            className="flex items-center gap-2 px-3 py-2 bg-red-900/50 hover:bg-red-800 text-red-400 rounded-lg text-sm transition"
          >
            <Trash2 size={14} /> All
          </button>
          {["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"].map((param) => (
            <button
              key={param}
              onClick={() => {
                if (confirm(`Delete all ${param} logs?`)) onDeleteLogs(param);
              }}
              className="px-3 py-2 bg-slate-800 hover:bg-red-900/50 text-slate-400 hover:text-red-400 rounded-lg text-sm transition"
            >
              {param}
            </button>
          ))}
        </div>
      </div>

      {/* ML Predictions Section */}
      {prediction && (
        <div className="bg-black/40 p-4 rounded-xl border border-white/10 backdrop-blur-md">
          <h3 className="font-bold mb-3 text-cyan-400 flex items-center gap-2">
            <TrendingUp size={18} /> 24-Hour Forecast
          </h3>
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(prediction.forecast_24h || {}).map(([param, data]: [string, any]) => (
              <div key={param} className="bg-slate-900/50 p-3 rounded-lg">
                <div className="text-xs text-slate-400 uppercase">{param}</div>
                <div className="text-lg font-bold text-white mt-1">{data.current}</div>
                <div className="text-xs text-slate-500">→ {data.predicted_24h}</div>
                <div className={`flex items-center gap-1 text-xs mt-2 ${getTrendColor(data.trend)}`}>
                  {getTrendIcon(data.trend)} {data.trend}
                </div>
              </div>
            ))}
          </div>
          {prediction.recommendations?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <div className="text-xs text-slate-400 mb-2">Recommendations:</div>
              <div className="flex flex-wrap gap-2">
                {prediction.recommendations.map((rec: string, i: number) => (
                  <span key={i} className="text-xs bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded">
                    {rec}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="bg-black/40 p-5 rounded-xl border border-white/10 backdrop-blur-md">
        <h3 className="font-bold mb-3 text-cyan-400 flex items-center gap-2">
          <Activity size={18} /> Quick Log
        </h3>
        <div className="flex gap-3">
          <select
            value={newParam}
            onChange={(e) => setNewParam(e.target.value)}
            className="bg-black/50 border border-white/10 p-2.5 rounded-lg w-1/3 outline-none focus:border-cyan-500 text-slate-300"
          >
            <option value="">Select Parameter</option>
            <option value="Alkalinity">Alkalinity</option>
            <option value="Calcium">Calcium</option>
            <option value="Magnesium">Magnesium</option>
            <option value="pH">pH</option>
            <option value="Temperature">Temperature</option>
          </select>
          <input
            type="number"
            step="0.01"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            placeholder="Value"
            className="bg-black/50 border border-white/10 p-2.5 rounded-lg w-32 outline-none focus:border-cyan-500"
          />
          <button
            onClick={addManualLog}
            disabled={!newParam}
            className={`bg-cyan-600/80 hover:bg-cyan-500 text-white font-semibold p-2.5 rounded-lg px-6 flex items-center gap-2 transition shadow-[0_0_15px_rgba(8,145,178,0.3)] ${!newParam ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Plus size={18} /> Save
          </button>
        </div>
        <div className="text-xs text-slate-500 mt-2">
          Valid parameters: Alkalinity, Calcium, Magnesium, pH, Temperature
        </div>
      </div>
      <h3 className="text-lg font-bold text-slate-300 pt-4">Latest Readings</h3>
      <div className="grid grid-cols-3 gap-4">
        {latestMetrics.length === 0 && (
          <p className="text-slate-500 col-span-3">No data logged yet.</p>
        )}
        {latestMetrics.map(([param, val]: any) => (
          <div
            key={param}
            className="bg-gradient-to-br from-slate-900 to-black p-6 rounded-xl border border-white/10 flex flex-col justify-center items-center shadow-lg"
          >
            <span className="text-slate-400 text-sm font-semibold uppercase tracking-wider">
              {param}
            </span>
            <span className="text-4xl font-black text-cyan-400 mt-2">
              {val}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
