/**
 * DataView Component
 * =================
 * Displays model readings and data by source.
 * 
 * Shows:
 * - Current data source and data points
 * - Latest readings from each source (synthetic/supabase/CSV)
 * - Model predictions
 */

import { Database, Cloud, FlaskConical, Clock, Activity, AlertTriangle, CheckCircle } from "lucide-react";

export default function DataView({
  logs,
  dataSource,
  setDataSource,
  prediction,
}: {
  logs: any[];
  dataSource: string;
  setDataSource: any;
  prediction: any;
}) {
  // Data sources
  const sources = [
    { id: "csv", label: "CSV", icon: Database, desc: "Uploaded CSV data" },
    { id: "supabase", label: "Supabase", icon: Cloud, desc: "Database historical data" },
    { id: "synthetic", label: "Synthetic", icon: FlaskConical, desc: "Generated test data" },
  ];
  
  // Get unique parameters from logs
  const paramSet = new Set(logs?.map((l: any) => l.parameter) || []);
  const uniqueParams = Array.from(paramSet);
  
  // Get latest values by parameter
  const latestByParam: Record<string, any> = {};
  if (logs && logs.length > 0) {
    // Group by parameter and get latest
    logs.forEach((log: any) => {
      if (!latestByParam[log.parameter] || 
          new Date(log.timestamp) > new Date(latestByParam[log.parameter].timestamp)) {
        latestByParam[log.parameter] = log;
      }
    });
  }
  
  return (
    <div className="h-full flex flex-col p-6 overflow-auto">
      {/* Data Source Selection */}
      <div className="mb-6">
        <h2 className="text-lg font-bold text-white mb-4">Data Source</h2>
        <div className="flex gap-2">
          {sources.map((source) => (
            <button
              key={source.id}
              onClick={() => setDataSource(source.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                dataSource === source.id 
                  ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/50" 
                  : "bg-white/5 text-slate-400 hover:bg-white/10 border border-white/10"
              }`}
            >
              <source.icon size={16} /> {source.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-500 mt-2">
          {sources.find(s => s.id === dataSource)?.desc}
        </p>
      </div>
      
      {/* Data Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Database size={14} /> Data Points
          </div>
          <div className="text-2xl font-bold text-white">{logs?.length || 0}</div>
        </div>
        
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Activity size={14} /> Parameters
          </div>
          <div className="text-2xl font-bold text-white">{uniqueParams.length}</div>
        </div>
        
        <div className="bg-white/5 rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
            <Clock size={14} /> Latest
          </div>
          <div className="text-2xl font-bold text-white">
            {logs?.length > 0 
              ? new Date(logs[logs.length - 1]?.timestamp || '').toLocaleDateString()
              : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* Current Tank State with Confidence Bars */}
      {prediction?.current_state && (
        <div className="mb-6">
          <h3 className="text-md font-semibold text-white mb-3">Tank State</h3>
          <div className={`flex items-center gap-3 p-4 rounded-lg border mb-3 ${
            prediction.current_state.state_id === 0 ? "bg-green-500/10 border-green-500/30" :
            prediction.current_state.state_id === 1 ? "bg-yellow-500/10 border-yellow-500/30" :
            "bg-red-500/10 border-red-500/30"
          }`}>
            {prediction.current_state.state_id === 0 ? (
              <CheckCircle className="text-green-400" size={24} />
            ) : (
              <AlertTriangle className={prediction.current_state.state_id === 1 ? "text-yellow-400" : "text-red-400"} size={24} />
            )}
            <div>
              <div className="font-bold text-white">{prediction.current_state.state_name}</div>
              <div className="text-xs text-slate-400">Confidence: {Math.round((prediction.current_state.confidence || 0.8) * 100)}%</div>
            </div>
          </div>
          
          {/* Confidence percentages for all states */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-green-400">Stable</span>
                <span className="text-sm font-bold text-white">
                  {Math.round((prediction.current_state.state_id === 0 ? (prediction.current_state.confidence || 0.8) : 0.3) * 100)}%
                </span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 rounded-full"
                  style={{ width: `${prediction.current_state.state_id === 0 ? (prediction.current_state.confidence || 0.8) * 100 : 30}%` }}
                />
              </div>
            </div>
            <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/20">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-yellow-400">Warning</span>
                <span className="text-sm font-bold text-white">
                  {Math.round((prediction.current_state.state_id === 1 ? (prediction.current_state.confidence || 0.8) : 0.4) * 100)}%
                </span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-yellow-500 rounded-full"
                  style={{ width: `${prediction.current_state.state_id === 1 ? (prediction.current_state.confidence || 0.8) * 100 : 40}%` }}
                />
              </div>
            </div>
            <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/20">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-red-400">Critical</span>
                <span className="text-sm font-bold text-white">
                  {Math.round((prediction.current_state.state_id === 2 ? (prediction.current_state.confidence || 0.8) : 0.2) * 100)}%
                </span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-500 rounded-full"
                  style={{ width: `${prediction.current_state.state_id === 2 ? (prediction.current_state.confidence || 0.8) * 100 : 20}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Latest Readings */}
      <div className="mb-6">
        <h3 className="text-md font-semibold text-white mb-3">Current Readings</h3>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(latestByParam).map(([param, data]: [string, any]) => (
            <div key={param} className="bg-white/5 rounded-lg p-3 border border-white/10">
              <div className="text-xs text-slate-500">{param}</div>
              <div className="text-lg font-bold text-white">{data.value}</div>
              <div className="text-xs text-slate-500">
                {new Date(data.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Model Info */}
      {prediction && (
        <div>
          <h3 className="text-md font-semibold text-white mb-3">Model Info</h3>
          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
            <div className="text-sm">
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Source:</span>
                <span className="text-white">{prediction.source}</span>
              </div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Data Points:</span>
                <span className="text-white">{prediction.data_points}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Version:</span>
                <span className="text-white">{prediction.model_version}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}