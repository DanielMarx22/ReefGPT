"use client";

import { useState, useEffect, useMemo } from "react";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import Chatbot from "@/components/Chatbot";
import ParameterGraph from "../components/Graphs";
import Dashboard from "../components/Dashboard";
import ActionPopup from "@/components/ActionPopup";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
);

export default function ReefOS() {
  // Chat State
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [devMode, setDevMode] = useState(true);
  const [sessionXrays, setSessionXrays] = useState<any[]>([]);
  const [xraysLoaded, setXraysLoaded] = useState(false);
  const [useV2, setUseV2] = useState(true);
  const [pendingActions, setPendingActions] = useState<any[]>([]);

  // Data State
  const [logs, setLogs] = useState<any[]>([]);

  // New Parameter Form
  const [newParamName, setNewParamName] = useState("");
  const [newParamValue, setNewParamValue] = useState("");

  // Existing Parameter Form
  const [updateParamName, setUpdateParamName] = useState("");
  const [updateParamValue, setUpdateParamValue] = useState("");
  const [prediction, setPrediction] = useState<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("reef_session_xrays");
      if (saved) {
        try {
          setSessionXrays(JSON.parse(saved));
        } catch (e) {}
      }
      setXraysLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (xraysLoaded && typeof window !== "undefined") {
      const last10 = sessionXrays.slice(-10);
      localStorage.setItem("reef_session_xrays", JSON.stringify(last10));
    }
  }, [sessionXrays, xraysLoaded]);

  useEffect(() => {
    // Initial load on mount
    fetchData();

    // Pro-Mode: Listen for database inserts
    const channel = supabase
      .channel('metrics-listener')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'metrics_log' },
        async (payload: any) => {  // <-- TYPE ADDED HERE
          console.log('New metric detected via Realtime!', payload);

          try {
            // 1. Instantly fetch the fresh ML status
            const predRes = await fetch(`http://localhost:8000/tank-status?t=${Date.now()}`);
            const predData = await predRes.json();
            if (predData.current_state) setPrediction(predData);

            // 2. Instantly fetch the updated logs
            const logRes = await fetch(`http://localhost:8000/get-logs?t=${Date.now()}`);
            const logData = await logRes.json();
            if (logData.data) setLogs(logData.data);
          } catch (err) {
            console.error("Failed to sync live data:", err);
          }
        }
      )
      .subscribe();

    // Cleanup listener on unmount
    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const fetchData = async () => {
    try {
      const logRes = await fetch(`http://localhost:8000/get-logs?t=${Date.now()}`);
      const logData = await logRes.json();
      if (logData.data) setLogs(logData.data);

      const chatRes = await fetch(`http://localhost:8000/get-chat-history?t=${Date.now()}`);
      const chatData = await chatRes.json();
      if (chatData.data) {
        setMessages(chatData.data);
        // Extract xrays from history
        const loadedXrays = chatData.data
          .filter((msg: any) => msg.role === 'ai' && msg.agent_reasoning)
          .map((msg: any) => msg.agent_reasoning);
        if (loadedXrays.length > 0) {
          setSessionXrays(loadedXrays.slice(-10));
        }
      }

      const predRes = await fetch(`http://localhost:8000/tank-status?t=${Date.now()}`);
      const predData = await predRes.json();
      if (predData.current_state) setPrediction(predData);
    } catch (err) {
      console.error("Failed to fetch data", err);
    }
  };

  const submitLog = async (name: string, value: string, isNew: boolean) => {
    if (!name || !value) return;
    const val = parseFloat(value);
    if (isNaN(val)) {
      alert("Value must be a number");
      return;
    }

    const paramName = name.trim();

    // OPTIMISTIC UI UPDATE: Instantly add to local state so the graph updates immediately
    const optimisticLog = {
      id: Date.now(), // Temporary ID until refresh
      parameter: paramName,
      value: val,
      timestamp: new Date().toISOString()
    };
    setLogs((prev) => [...prev, optimisticLog]);

    try {
      await fetch(`http://localhost:8000/log-metric?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parameter: paramName, value: val }),
      });

      if (isNew) {
        setNewParamName("");
        setNewParamValue("");
      } else {
        setUpdateParamValue("");
      }
      // Fetch fresh data from backend to ensure we have the real DB IDs and sync
      fetchData();
    } catch (err) {
      alert("Failed to save log");
      // Revert optimistic update if failed by fetching true state
      fetchData();
    }
  };

  const deleteLogs = async (paramName?: string) => {
    const msg = paramName ? `Delete all logs for ${paramName}?` : "Clear all parameter logs?";
    if (!confirm(msg)) return;

    const url = paramName
      ? `http://localhost:8000/delete-logs?parameter=${encodeURIComponent(paramName)}`
      : `http://localhost:8000/delete-logs`;

    await fetch(url, { method: "DELETE" });
    fetchData();
  };

  const deleteSingleLog = async (id: number) => {
    // Optimistically remove from UI
    setLogs((prev) => prev.filter(log => log.id !== id));
    await fetch(`http://localhost:8000/delete-log/${id}`, { method: "DELETE" });
    fetchData();
  };

  const sendMessage = async (userMessage: string) => {
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const endpoint = useV2 ? "chat-v2" : "chat";
      const res = await fetch(`http://localhost:8000/${endpoint}?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      });
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
      if (data.debug_xray) {
        setSessionXrays((prev) => {
          const updated = [...prev, data.debug_xray];
          return updated.slice(-10); // Keep only the last 10 in state
        });
      }
      if (data.proposed_actions && data.proposed_actions.length > 0) {
        const validActions = data.proposed_actions.filter((a: any) => {
          if (a.action === "add_inhabitant" && !a.species && !a.name) return false;
          return true;
        });
        if (validActions.length > 0) {
          setPendingActions(validActions);
        }
      }
    } catch (err) { }
  };

  const handleConfirmAction = async (actions: any[]) => {
    let successCount = 0;
    let failCount = 0;
    let errors: string[] = [];

    for (const action of actions) {
      try {
        if (action.action === "add_inhabitant") {
          const res = await fetch(`http://localhost:8000/add-inhabitant`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              category: action.category || "Other",
              species: action.species || "Unknown Species",
              name: action.name || action.species || "Unknown Item",
              count: action.count || 1,
              size: action.size || "",
              notes: action.notes || action.summary || "",
              care_info: action.care_info || "",
              image_url: "",
              date_added: action.date_added || new Date().toISOString()
            }),
          });
          if (res.ok) successCount++;
          else failCount++;
        } else if (action.action === "log_event") {
          const res = await fetch(`http://localhost:8000/log-event`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              summary: action.summary,
              event_type: "general"
            }),
          });
          if (res.ok) successCount++;
          else failCount++;
        } else if (action.action === "update_inhabitant" && action.id) {
          const res = await fetch(`http://localhost:8000/patch-inhabitant/${action.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(action),
          });
          const data = await res.json();
          if (res.ok && data.status !== "error") {
            successCount++;
          } else {
            failCount++;
            errors.push(data.message || "Unknown error");
          }
        } else if (action.action === "delete_inhabitant" && action.id) {
          const res = await fetch(`http://localhost:8000/delete-inhabitant/${action.id}`, {
            method: "DELETE"
          });
          const data = await res.json();
          if (res.ok && data.status !== "error") {
            successCount++;
          } else {
            failCount++;
            errors.push(data.message || "Unknown error");
          }
        }
      } catch (err: any) {
        console.error(err);
        failCount++;
        errors.push(err.message || "Network error");
      }
    }
    
    if (failCount === 0) {
      alert(`Success! Successfully executed ${successCount} action${successCount > 1 ? 's' : ''}.`);
    } else {
      alert(`Executed ${successCount} action(s). Failed ${failCount} action(s).\n\nErrors:\n${errors.join('\n')}`);
    }
    
    setPendingActions([]);
  };

  const handleDismissAction = () => {
    setPendingActions([]);
  };

  const latestMetrics = useMemo(() => {
    // Sort logs by time first so the grouped object always gets the absolute newest value
    const sorted = [...logs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    const grouped = sorted.reduce((acc, log) => ({ ...acc, [log.parameter]: parseFloat(log.value) }), {});
    return Object.entries(grouped);
  }, [logs]);

  return (
    <div className="h-full w-full flex flex-col p-2 relative">
      <ActionPopup 
        actions={pendingActions} 
        onConfirm={handleConfirmAction} 
        onDismiss={handleDismissAction} 
      />
      <Group orientation="horizontal" className="h-full rounded-xl overflow-hidden border border-white/10 shadow-2xl bg-black/40">

        {/* LEFT PANEL: Data Input */}
        <Panel defaultSize={40} minSize={20} className="p-6 overflow-y-auto flex flex-col gap-6 scrollbar-hide">

          {/* Tank Condition Alert 
             * ======================
             * Shows the current tank health status (STABLE/WARNING/CRITICAL)
             * Based on ML classification from /tank-status endpoint
             * 
             * Color coding:
             * - Green (state_id=0): STABLE - all parameters in optimal range
             * - Yellow (state_id=1): WARNING - parameters slightly off, may need attention
             * - Red (state_id=2): CRITICAL - immediate action required
             * 
             * Data source: /tank-status fetches latest readings from Supabase metrics_log
             * Updates every 5 seconds via polling in useEffect
             */}
          {prediction?.current_state && (
            <div className={`p-4 rounded-xl border backdrop-blur-md ${prediction.current_state.state_id === 0 ? "bg-green-900/20 border-green-500/30" :
              prediction.current_state.state_id === 1 ? "bg-yellow-900/20 border-yellow-500/30" :
                "bg-red-900/20 border-red-500/30"
              }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {prediction.current_state.state_id === 0 ? (
                    <ShieldCheck size={28} className="text-green-400" />
                  ) : (
                    <ShieldAlert size={28} className={prediction.current_state.state_id === 1 ? "text-yellow-400" : "text-red-400"} />
                  )}
                  <div>
                    <div className="text-xs text-slate-400 uppercase">Tank Condition</div>
                    <div className="text-xl font-bold text-white">
                      {prediction.current_state.state_id === 0 ? "STABLE" :
                        prediction.current_state.state_id === 1 ? "WARNING" : "CRITICAL"}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">ML Confidence</div>
                  <div className="text-lg font-bold text-white">
                    {Math.round((prediction.current_state.confidence || 0.8) * 100)}%
                  </div>
                </div>
              </div>
              {/* Display the actual parameter values and stability info */}
              {prediction.current_state.params && (
                <div className="mt-3 pt-3 border-t border-white/10">
                  <div className="grid grid-cols-4 gap-2 text-xs mb-2">
                    <div><span className="text-slate-400">pH:</span> <span className="text-white">{prediction.current_state.params.pH?.toFixed(1)}</span></div>
                    <div><span className="text-slate-400">Ca:</span> <span className="text-white">{prediction.current_state.params.Calcium?.toFixed(0)}</span></div>
                    <div><span className="text-slate-400">Mg:</span> <span className="text-white">{prediction.current_state.params.Magnesium?.toFixed(0)}</span></div>
                    <div><span className="text-slate-400">Alk:</span> <span className="text-white">{prediction.current_state.params.Alkalinity?.toFixed(1)}</span></div>
                  </div>
                  {/* Show stability info if available */}
                  {prediction.current_state.stability && (
                    <div className="text-xs text-slate-500">
                      {prediction.current_state.stability.days_analyzed > 0 && (
                        <span className="text-slate-400">({prediction.current_state.stability.days_analyzed} days)</span>
                      )}
                      pH ±{prediction.current_state.stability.ph_variance}, Alk ±{prediction.current_state.stability.alk_variance}
                      {prediction.current_state.stability.is_fluctuating && <span className="text-yellow-400 ml-1">(Fluctuating)</span>}
                      {prediction.current_state.stability.is_declining && <span className="text-red-400 ml-1">(Declining)</span>}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* New Parameter UI */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 className="text-lg font-bold text-cyan-400 mb-3">Log Parameters</h2>

            {/* Update Existing */}
            <div className="mb-4">
              <label className="text-xs text-slate-400 uppercase tracking-wider mb-1 block">Update Existing</label>
              <div className="flex gap-2">
                <select
                  value={updateParamName}
                  onChange={(e) => setUpdateParamName(e.target.value)}
                  className="flex-1 bg-black/50 border border-slate-700 rounded p-2 text-sm focus:border-cyan-500 outline-none"
                >
                  <option value="">Select Parameter</option>
                  {latestMetrics.map(([key]) => (
                    <option key={key} value={key}>{key.toUpperCase()}</option>
                  ))}
                </select>
                <input
                  type="number"
                  value={updateParamValue}
                  onChange={(e) => setUpdateParamValue(e.target.value)}
                  placeholder="Value"
                  className="w-24 bg-black/50 border border-slate-700 rounded p-2 text-sm focus:border-cyan-500 outline-none"
                />
                <button
                  onClick={() => submitLog(updateParamName, updateParamValue, false)}
                  className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm font-bold"
                >
                  Update
                </button>
              </div>
            </div>

            {/* Add New */}
            <div>
              <label className="text-xs text-slate-400 uppercase tracking-wider mb-1 block">Add Custom</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newParamName}
                  onChange={(e) => setNewParamName(e.target.value)}
                  placeholder="Name (e.g. Nitrate)"
                  className="flex-1 bg-black/50 border border-slate-700 rounded p-2 text-sm focus:border-cyan-500 outline-none"
                />
                <input
                  type="number"
                  value={newParamValue}
                  onChange={(e) => setNewParamValue(e.target.value)}
                  placeholder="Value"
                  className="w-24 bg-black/50 border border-slate-700 rounded p-2 text-sm focus:border-cyan-500 outline-none"
                />
                <button
                  onClick={() => submitLog(newParamName, newParamValue, true)}
                  className="bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded text-sm font-bold"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Current Known Values */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-bold text-cyan-400">Known Parameters</h2>
              <button onClick={() => deleteLogs()} className="text-xs text-red-400 hover:text-red-300">Clear All</button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {latestMetrics.length === 0 ? (
                <p className="text-xs text-slate-500 col-span-2">No data logged.</p>
              ) : (
                latestMetrics.map(([key, val]) => (
                  <div key={key} className="bg-black/50 border border-slate-800 p-3 rounded">
                    <div className="text-xs text-slate-400 uppercase tracking-wider">{key.toUpperCase()}</div>
                    <div className="text-lg font-bold">{val as number}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/*Graphs*/}
          <ParameterGraph logs={logs} />

          {/* Manage & Delete Logs */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 className="text-lg font-bold text-red-400 mb-4">Manage Logs</h2>

            {/* Delete Entire Category */}
            <div className="mb-5 pb-5 border-b border-slate-800">
              <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block">Delete Entire Parameter</label>
              <div className="flex gap-2">
                <select
                  id="deleteParamSelect"
                  className="flex-1 bg-black/50 border border-slate-700 rounded p-2 text-sm focus:border-red-500 outline-none"
                >
                  <option value="">Select Parameter...</option>
                  {latestMetrics.map(([key]) => (
                    <option key={key} value={key}>{key.toUpperCase()}</option>
                  ))}
                </select>
                <button
                  onClick={() => {
                    const sel = document.getElementById("deleteParamSelect") as HTMLSelectElement;
                    if (sel.value) {
                      deleteLogs(sel.value);
                      sel.value = "";
                    }
                  }}
                  className="bg-red-900/40 hover:bg-red-800 text-red-200 px-3 py-2 rounded text-sm font-bold transition-colors"
                >
                  Delete All
                </button>
              </div>
            </div>

            {/* Delete Individual Logs */}
            <div>
              <label className="text-xs text-slate-400 uppercase tracking-wider mb-2 block">Recent Entries</label>
              <div className="max-h-48 overflow-y-auto space-y-1 pr-1 scrollbar-hide">
                {[...logs].reverse().map(log => (
                  <div key={log.id} className="flex justify-between items-center bg-black/30 p-2 rounded border border-slate-800 hover:border-red-900/50 group transition-colors">
                    <span className="text-sm text-slate-300">
                      {log.parameter.toUpperCase()}: <b className="text-white ml-1">{log.value}</b>
                    </span>
                    <button
                      onClick={() => deleteSingleLog(log.id)}
                      className="text-xs text-red-400 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 bg-red-950/50 rounded hover:bg-red-900 hover:text-white"
                    >
                      Delete
                    </button>
                  </div>
                ))}
                {logs.length === 0 && <p className="text-xs text-slate-500">No logs found.</p>}
              </div>
            </div>
          </div>

        </Panel>

        <Separator className="w-2 bg-slate-950 flex items-center justify-center cursor-col-resize z-50 hover:bg-cyan-900/30 transition-colors">
          <div className="h-8 w-1 bg-slate-700 rounded-full" />
        </Separator>

        {/* RIGHT PANEL: Chat & X-Ray */}
        <Panel defaultSize={60} minSize={30} className="bg-black/20 border-l border-slate-800 flex flex-col relative">
          <div className="absolute top-3 right-3 z-50 flex gap-2">
            <button
              onClick={() => setUseV2(!useV2)}
              className={`text-xs px-3 py-1 rounded border transition-colors ${useV2 ? "bg-purple-500/20 border-purple-500 text-purple-300" : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"}`}
            >
              {useV2 ? "Engine: V2 (Agentic)" : "Engine: V1 (Standard)"}
            </button>
            <button
              onClick={() => setDevMode(!devMode)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${devMode ? "bg-cyan-500/20 border-cyan-500 text-cyan-300" : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"
                }`}
            >
              {devMode ? "X-Ray: ON" : "X-Ray: OFF"}
            </button>
          </div>

          {devMode ? (
            <Group orientation="vertical">
              <Panel defaultSize={50} className="flex flex-col">
                <Chatbot messages={messages} sendMessage={sendMessage} />
              </Panel>
              <Separator className="h-2 bg-slate-900 cursor-row-resize transition-colors hover:bg-cyan-900/30" />
              <Panel defaultSize={50} className="bg-slate-950 p-4 overflow-y-auto font-mono text-xs border-t border-slate-800 scrollbar-hide">
                <h3 className="text-cyan-400 font-bold mb-3 border-b border-cyan-900 pb-2 flex justify-between">
                  <span>🧠 Agent X-Ray (Session Log)</span>
                  <span className="text-slate-500">{sessionXrays.length} turns</span>
                </h3>

                {sessionXrays.length > 0 ? (
                  <div className="space-y-4 flex flex-col">
                    {sessionXrays.map((xray, idx) => (
                      <div key={idx} className="bg-black/50 p-3 rounded-lg border border-slate-800 shadow-inner">
                        <div className="flex justify-between items-center text-slate-500 mb-2 border-b border-slate-800/50 pb-1 font-bold">
                          <span>Turn {idx + 1}</span>
                          {xray.token_usage && (
                            <span className="text-purple-400/80 text-[10px]">
                              Total Tokens: {xray.token_usage.total_tokens || xray.token_usage.layer_1_tokens}
                              {xray.token_usage.total_saved && <span className="text-green-500 ml-2">(Saved ~{xray.token_usage.total_saved})</span>}
                            </span>
                          )}
                        </div>
                        {xray.orchestrator ? (
                          <div className="space-y-3 mt-2">
                            {/* Orchestrator Phase */}
                            <div className="border border-purple-900/50 rounded bg-purple-950/20 p-2">
                               <div className="text-purple-400 text-[10px] uppercase font-bold tracking-wider mb-1 flex justify-between">
                                  <span>Step 1: Orchestrator</span>
                                  <span className="text-slate-500">{xray.orchestrator.tokens} tkns</span>
                               </div>
                               <div className="text-slate-300 text-xs flex gap-2 items-center">
                                  <span className="text-slate-500">Decision:</span> 
                                  {xray.orchestrator.status === "SHORT_CIRCUIT" ? (
                                     <span className="text-red-400 font-bold bg-red-900/20 px-2 rounded">Short Circuit</span>
                                  ) : (
                                     <div className="flex gap-1 flex-wrap">
                                        {xray.orchestrator.decision?.map((d: string) => (
                                           <span key={d} className="bg-purple-900/40 text-purple-300 px-1.5 py-0.5 rounded text-[10px]">{d}</span>
                                        ))}
                                     </div>
                                  )}
                               </div>
                            </div>

                            {/* Subagents Phase */}
                            {xray.subagents && xray.subagents.length > 0 && (
                               <div className="border border-blue-900/50 rounded bg-blue-950/20 p-2 space-y-2">
                                  <div className="text-blue-400 text-[10px] uppercase font-bold tracking-wider mb-2">
                                     <span>Step 2: Subagents ({xray.subagents.length})</span>
                                  </div>
                                  {xray.subagents.map((sub: any, sIdx: number) => (
                                     <div key={sIdx} className="border-l-2 border-blue-700/50 pl-2">
                                        <div className="text-blue-300/80 text-[10px] font-bold flex justify-between">
                                           <span>{sub.node}</span>
                                           <span className="text-slate-500">{sub.tokens} tkns</span>
                                        </div>
                                        <div className="text-slate-300 text-xs mt-1">{sub.summary}</div>
                                     </div>
                                  ))}
                               </div>
                            )}

                            {/* Master Phase */}
                            {xray.master && (
                               <div className="border border-emerald-900/50 rounded bg-emerald-950/20 p-2">
                                  <div className="text-emerald-400 text-[10px] uppercase font-bold tracking-wider mb-1 flex justify-between">
                                     <span>Step 3: Master AI Synthesis</span>
                                     <span className="text-slate-500">{xray.master.tokens} tkns</span>
                                  </div>
                                  <div className="text-slate-500 text-[10px] mb-1">Internal Thoughts:</div>
                                  <div className="text-emerald-200/90 text-xs italic border-l-2 border-emerald-700/50 pl-2">
                                     {xray.master.internal_thoughts}
                                  </div>
                               </div>
                            )}
                          </div>
                        ) : xray.reasoning_steps ? (
                          <div className="space-y-2 mt-2">
                            {xray.reasoning_steps.map((step: any, sIdx: number) => (
                              <div key={sIdx} className="border-l-2 border-cyan-700/50 pl-3 py-1">
                                <div className="text-cyan-500/80 text-[10px] uppercase font-bold tracking-wider mb-1 flex justify-between">
                                  <span>{step.node}</span>
                                  <span className="text-slate-500">{step.tokens} tkns</span>
                                </div>
                                <div className="text-slate-300 text-xs">{step.summary}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <pre className="text-green-400 whitespace-pre-wrap text-[10px]">{JSON.stringify(xray, null, 2)}</pre>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">Submit a prompt to begin logging reasoning...</p>
                )}
              </Panel>
            </Group>
          ) : (
            <Chatbot messages={messages} sendMessage={sendMessage} />
          )}
        </Panel>

      </Group>
    </div>
  );
}