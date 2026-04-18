"use client";

import { useState, useEffect, useMemo } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import Chatbot from "@/components/Chatbot";

export default function ReefOS() {
  // Chat State
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [devMode, setDevMode] = useState(true);
  const [sessionXrays, setSessionXrays] = useState<any[]>([]);

  // Data State
  const [logs, setLogs] = useState<any[]>([]);
  const [livestock, setLivestock] = useState("");
  const [saveStatus, setSaveStatus] = useState("");

  // New Parameter Form
  const [newParamName, setNewParamName] = useState("");
  const [newParamValue, setNewParamValue] = useState("");

  // Existing Parameter Form
  const [updateParamName, setUpdateParamName] = useState("");
  const [updateParamValue, setUpdateParamValue] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const logRes = await fetch(`http://127.0.0.1:8000/get-logs?t=${Date.now()}`);
      const logData = await logRes.json();
      if (logData.data) setLogs(logData.data);

      const chatRes = await fetch(`http://127.0.0.1:8000/get-chat-history?t=${Date.now()}`);
      const chatData = await chatRes.json();
      if (chatData.data) setMessages(chatData.data);

      const profRes = await fetch(`http://127.0.0.1:8000/get-profile?t=${Date.now()}`);
      const profData = await profRes.json();
      if (profData.livestock) setLivestock(profData.livestock);
    } catch (err) {
      console.error("Failed to fetch data", err);
    }
  };

  const saveProfile = async () => {
    setSaveStatus("Saving...");
    try {
      await fetch(`http://127.0.0.1:8000/update-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ livestock }),
      });
      setSaveStatus("Saved!");
      setTimeout(() => setSaveStatus(""), 2000);
    } catch (err) {
      setSaveStatus("Error saving");
    }
  };

  const submitLog = async (name: string, value: string, isNew: boolean) => {
    if (!name || !value) return;
    const val = parseFloat(value);
    if (isNaN(val)) {
      alert("Value must be a number");
      return;
    }

    try {
      await fetch(`http://127.0.0.1:8000/log-metric?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parameter: name.trim(), value: val }),
      });

      if (isNew) {
        setNewParamName("");
        setNewParamValue("");
      } else {
        setUpdateParamValue("");
      }
      fetchData();
    } catch (err) {
      alert("Failed to save log");
    }
  };

  const deleteLogs = async (paramName?: string) => {
    const msg = paramName ? `Delete all logs for ${paramName}?` : "Clear all parameter logs?";
    if (!confirm(msg)) return;

    const url = paramName
      ? `http://127.0.0.1:8000/delete-logs?parameter=${encodeURIComponent(paramName)}`
      : `http://127.0.0.1:8000/delete-logs`;

    await fetch(url, { method: "DELETE" });
    fetchData();
  };

  const deleteSingleLog = async (id: number) => {
    await fetch(`http://127.0.0.1:8000/delete-log/${id}`, { method: "DELETE" });
    fetchData();
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = input;

    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");

    try {
      const res = await fetch(`http://127.0.0.1:8000/chat?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      });
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
      if (data.debug_xray) setSessionXrays((prev) => [...prev, data.debug_xray]);
    } catch (err) { }
  };

  const latestMetrics = useMemo(() => {
    const grouped = logs.reduce((acc, log) => ({ ...acc, [log.parameter]: parseFloat(log.value) }), {});
    return Object.entries(grouped);
  }, [logs]);

  return (
    <div className="h-screen w-full bg-slate-950 text-slate-200 font-sans flex flex-col p-2">
      <div className="flex items-center justify-between mb-2 px-2">
        <h1 className="text-xl font-bold text-cyan-400 tracking-wider">ReefGPT<span className="text-slate-500 text-sm ml-2">Testing Rig</span></h1>
      </div>

      <Group orientation="horizontal" className="h-full rounded-xl overflow-hidden border border-white/10 shadow-2xl bg-black/40">

        {/* LEFT PANEL: Data Input */}
        <Panel defaultSize={40} minSize={20} className="p-6 overflow-y-auto flex flex-col gap-6 scrollbar-hide">

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center mb-3">
              <h2 className="text-lg font-bold text-cyan-400">Tank Profile</h2>
              <span className="text-xs text-green-400">{saveStatus}</span>
            </div>
            <textarea
              value={livestock}
              onChange={(e) => setLivestock(e.target.value)}
              className="w-full h-32 bg-black/50 border border-slate-700 rounded p-3 text-sm focus:border-cyan-500 outline-none resize-none mb-3 placeholder-slate-600"
              placeholder="e.g. Emperor Angelfish, Mixed SPS, Acans."
            />
            <button onClick={saveProfile} className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-2 rounded text-sm font-bold transition-colors">
              Save Profile
            </button>
          </div>

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
          <button
            onClick={() => setDevMode(!devMode)}
            className={`absolute top-3 right-3 z-50 text-xs px-2 py-1 rounded border transition-colors ${devMode ? "bg-cyan-500/20 border-cyan-500 text-cyan-300" : "bg-slate-800 border-slate-600 text-slate-400 hover:text-white"
              }`}
          >
            {devMode ? "X-Ray: ON" : "X-Ray: OFF"}
          </button>

          {devMode ? (
            <Group orientation="vertical">
              <Panel defaultSize={50} className="flex flex-col">
                <Chatbot messages={messages} input={input} setInput={setInput} sendMessage={sendMessage} />
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
                        <div className="text-slate-500 mb-2 border-b border-slate-800/50 pb-1 font-bold">
                          Turn {idx + 1}
                        </div>
                        <pre className="text-green-400 whitespace-pre-wrap">{JSON.stringify(xray, null, 2)}</pre>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 italic">Submit a prompt to begin logging reasoning...</p>
                )}
              </Panel>
            </Group>
          ) : (
            <Chatbot messages={messages} input={input} setInput={setInput} sendMessage={sendMessage} />
          )}
        </Panel>

      </Group>
    </div>
  );
}