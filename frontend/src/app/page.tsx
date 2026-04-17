/**
 * ReefOS Main Page
 * =============
 * Main application page for the ReefGPT reef aquarium management system.
 * 
 * This is the main entry point that composes all components:
 * - Navbar: Navigation header
 * - Dashboard: Parameter logging, data source selection, predictions
 * - Readings: Charts showing parameter trends
 * - Chatbot: AI chat interface
 * 
 * Data Flow:
 * 1. Fetches logs from Supabase on load
 * 2. Fetches ML predictions from backend API
 * 3. Displays real-time tank state and forecasts
 * 
 * API Endpoints Used:
 * - GET /get-logs: Fetch parameter logs
 * - GET /get-chat-history: Fetch chat history  
 * - GET /predict/full-analysis: Get ML predictions
 * - POST /log-metric: Log a parameter reading
 * - POST /chat: Chat with ReefGPT
 */

"use client";

import { useState, useEffect, useMemo } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import Navbar from "@/components/Navbar";
import Dashboard from "@/components/Dashboard";
import Readings from "@/components/Readings";
import DataView from "@/components/DataView";
import Chatbot from "@/components/Chatbot";

export default function ReefOS() {
  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================
  
  // Chat messages (user/AI conversation)
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  
  // Chat input text
  const [input, setInput] = useState("");
  
  // Parameter logs from Supabase
  const [logs, setLogs] = useState<any[]>([]);
  
  // New parameter input (for logging)
  const [newParam, setNewParam] = useState("");
  const [newValue, setNewValue] = useState("");
  
  // Active parameter tab in charts
  const [activeTab, setActiveTab] = useState<string>("Alkalinity");
  
  // Current view (dashboard, charts, or data)
  const [currentView, setCurrentView] = useState<"dashboard" | "charts" | "data">("dashboard");
  
  // ML prediction results
  const [prediction, setPrediction] = useState<any>(null);
  
  // Data source selection (csv/supabase/synthetic)
  const [dataSource, setDataSource] = useState("csv");
  
  useEffect(() => {
    fetchData();
  }, []);

  /**
   * Fetch data from the ReefGPT API.
   * 
   * Gets:
   * - Parameter logs from Supabase
   * - Chat history for conversation context
   * - ML predictions based on current dataSource
   * - Model assessment results
   */
  const fetchData = async () => {
    try {
      // Fetch data based on selected source
      let dataRecords: any[] = [];
      
      if (dataSource === "synthetic") {
        // Fetch generated synthetic data
        const synthRes = await fetch(
          `http://127.0.0.1:8000/data/synthetic?t=${Date.now()}`,
        );
        const synthData = await synthRes.json();
        if (synthData.data) dataRecords = synthData.data;
      } else if (dataSource === "csv") {
        // Fetch from CSV file
        const csvRes = await fetch(
          `http://127.0.0.1:8000/data/csv?t=${Date.now()}`,
        );
        const csvData = await csvRes.json();
        if (csvData.data) dataRecords = csvData.data;
      } else {
        // Default: fetch from Supabase
        const logRes = await fetch(
          `http://127.0.0.1:8000/get-logs?t=${Date.now()}`,
        );
        const logData = await logRes.json();
        if (logData.data) dataRecords = logData.data;
      }
      
      setLogs(dataRecords);

      // Fetch chat history
      const chatRes = await fetch(
        `http://127.0.0.1:8000/get-chat-history?t=${Date.now()}`,
      );
      const chatData = await chatRes.json();
      if (chatData.data) setMessages(chatData.data);

      // Fetch ML predictions based on selected data source
      try {
        const predRes = await fetch(
          `http://127.0.0.1:8000/predict/full-analysis?source=${dataSource}`,
        );
        const predData = await predRes.json();
        setPrediction(predData);
      } catch (err) {
        console.log("Prediction not available");
      }
    } catch (err) {}
  };

  /**
   * Log a parameter reading to the database.
   * 
   * Sends to POST /log-metric endpoint which:
   * 1. Validates parameter name (normalizes aliases)
   * 2. Validates against physical limits (pH 0-14, etc.)
   * 3. Saves to Supabase metrics_log table
   * 
   * Shows error if:
   * - Parameter unknown
   * - Value out of physical limits
   * - Database connection failed
   */
  const addManualLog = async () => {
    if (!newParam || !newValue) return;

    // Parse the value as a number
    const val = parseFloat(newValue);
    if (isNaN(val)) {
      alert("Please enter a valid number.");
      return;
    }

    try {
      // Send to backend API
      const res = await fetch(
        `http://127.0.0.1:8000/log-metric?t=${Date.now()}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parameter: newParam.trim(), value: val }),
        },
      );

      const data = await res.json();

      // Handle validation errors (physical limits, unknown parameter)
      if (data.status === "error") {
        alert(data.message);
        return;
      }

      // Clear input and refresh data
      setNewValue("");
      setActiveTab(newParam.trim());
      fetchData();
    } catch (err) {
      alert("Network Error: Could not connect to the backend.");
    }
  };

  /**
   * Send a chat message to ReefGPT.
   * 
   * Sends to POST /chat endpoint which:
   * 1. Gets tank data from Supabase
   * 2. Searches vector DB for relevant context (RAG)
   * 3. Injects context into LLM prompt (Llama 3.1)
   * 4. Returns AI response
   * 
   * The RAG system uses the user's question to search
   * 1377 knowledge vectors for relevant reef information.
   */
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMessage = input;
    
    // Optimistically add user message to UI
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    
    try {
      // Send to ReefGPT chat API
      const res = await fetch(`http://127.0.0.1:8000/chat?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      });
      const data = await res.json();
      
      // Add AI response to chat
      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
    } catch (err) {}
  };

  const VALID_PARAMS = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature"] as const;
  type ValidParam = typeof VALID_PARAMS[number];

  const uniqueParams = useMemo((): string[] => {
      const allParams = Array.from(new Set(logs.map((l) => l.parameter))).length > 0
        ? Array.from(new Set(logs.map((l) => l.parameter)))
        : ["Alkalinity"];
      const normalized: string[] = [];
      for (const p of allParams) {
        const lower = p?.toLowerCase();
        if (lower === "alk" || lower === "alkalinity") normalized.push("Alkalinity");
        else if (lower === "ca" || lower === "calcium") normalized.push("Calcium");
        else if (lower === "mg" || lower === "magnesium") normalized.push("Magnesium");
        else if (lower === "ph") normalized.push("pH");
        else if (lower === "temp" || lower === "temperature" || lower === "tds") normalized.push("Temperature");
      }
      return normalized.length > 0 ? normalized : ["Alkalinity"];
    },
    [logs],
  );
  useEffect(() => {
    if (uniqueParams.length > 0 && !uniqueParams.includes(activeTab))
      setActiveTab(uniqueParams[0] as string);
  }, [uniqueParams, activeTab]);

  // Refetch data and predictions when data source changes
  useEffect(() => {
    const fetchPrediction = async () => {
      // Fetch data based on selected source
      let dataRecords: any[] = [];
      
      if (dataSource === "synthetic") {
        const synthRes = await fetch(
          `http://127.0.0.1:8000/data/synthetic?t=${Date.now()}`,
        );
        const synthData = await synthRes.json();
        if (synthData.data) dataRecords = synthData.data;
      } else if (dataSource === "csv") {
        const csvRes = await fetch(
          `http://127.0.0.1:8000/data/csv?t=${Date.now()}`,
        );
        const csvData = await csvRes.json();
        if (csvData.data) dataRecords = csvData.data;
      } else {
        const logRes = await fetch(
          `http://127.0.0.1:8000/get-logs?t=${Date.now()}`,
        );
        const logData = await logRes.json();
        if (logData.data) dataRecords = logData.data;
      }
      
      setLogs(dataRecords);
      
      // Fetch predictions
      try {
        const predRes = await fetch(
          `http://127.0.0.1:8000/predict/full-analysis?source=${dataSource}`,
        );
        const predData = await predRes.json();
        setPrediction(predData);
      } catch (err) {
        console.log("Prediction not available");
      }
    };
    fetchPrediction();
  }, [dataSource]);

  // Handlers for CSV upload and synthetic generation
  const handleUploadCSV = async (formData: FormData) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/predict/upload-csv", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.status === "success") {
        // Refetch with CSV source
        const predRes = await fetch(
          `http://127.0.0.1:8000/predict/full-analysis?source=csv`,
        );
        setPrediction(await predRes.json());
      }
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  const handleGenerateSynthetic = async () => {
    try {
      await fetch("http://127.0.0.1:8000/predict/generate-synthetic", {
        method: "POST",
      });
      const predRes = await fetch(
        `http://127.0.0.1:8000/predict/full-analysis?source=synthetic`,
      );
      setPrediction(await predRes.json());
    } catch (err) {
      console.error("Generate failed", err);
    }
  };

  const handleDeleteLogs = async (param?: string) => {
    try {
      const url = param !== undefined
        ? `http://127.0.0.1:8000/delete-logs?parameter=${encodeURIComponent(param)}`
        : "http://127.0.0.1:8000/delete-logs";
      const res = await fetch(url, { method: "DELETE" });
      const data = await res.json();
      if (data.status === "success") {
        alert(`Deleted ${data.deleted} log(s)`);
        fetchData();
      }
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  const chartData = useMemo(
    () =>
      logs
        .filter((l) => l.parameter === activeTab)
        .map((l) => ({
          date: new Date(l.timestamp).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
          }),
          value: parseFloat(l.value),
        })),
    [logs, activeTab],
  );
  const latestMetrics = useMemo(
    () =>
      Object.entries(
        logs.reduce(
          (acc, log) => ({ ...acc, [log.parameter]: parseFloat(log.value) }),
          {},
        ),
      ).slice(0, 6),
    [logs],
  );

  return (
    <div className="h-screen w-full bg-slate-950 text-slate-200 font-sans flex flex-col overflow-hidden">
      <Navbar currentView={currentView} setCurrentView={setCurrentView} />

      <div
        className="flex-1 p-2 overflow-hidden"
        style={{
          background:
            "radial-gradient(circle at 50% 0%, #0f172a 0%, #020617 100%)",
        }}
      >
        {/* autoSaveId remembers your dragged panel widths */}
        <Group
          orientation="horizontal"
          className="h-full rounded-xl overflow-hidden border border-white/10 shadow-2xl bg-black/40 backdrop-blur-xl"
        >
          <Panel defaultSize={60} minSize={20}>
            {currentView === "dashboard" ? (
              <Dashboard
                newParam={newParam}
                setNewParam={setNewParam}
                newValue={newValue}
                setNewValue={setNewValue}
                addManualLog={addManualLog}
                latestMetrics={latestMetrics}
                dataSource={dataSource}
                setDataSource={setDataSource}
                prediction={prediction}
                onUploadCSV={handleUploadCSV}
                onGenerateSynthetic={handleGenerateSynthetic}
                onDeleteLogs={handleDeleteLogs}
              />
            ) : currentView === "charts" ? (
              <Readings
                uniqueParams={uniqueParams}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                dataSource={dataSource}
                setDataSource={setDataSource}
                logs={logs}
              />
            ) : (
              <DataView
                logs={logs}
                dataSource={dataSource}
                setDataSource={setDataSource}
                prediction={prediction}
              />
            )}
          </Panel>

          {/* Thicker drag handle (w-4) with clear hover indicator */}
          <Separator className="w-4 bg-white/5 hover:bg-cyan-500/50 transition-colors flex items-center justify-center cursor-col-resize z-50 group">
            <div className="h-12 w-1.5 bg-white/30 group-hover:bg-white rounded-full transition-colors" />
          </Separator>

          {/* Removed maxSize constraint so you can expand it freely */}
          <Panel
            defaultSize={40}
            minSize={20}
            className="bg-black/20 border-l border-white/10 flex flex-col"
          >
            <Chatbot
              messages={messages}
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
            />
          </Panel>
        </Group>
      </div>
    </div>
  );
}
