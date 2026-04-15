"use client";
import { useState, useEffect, useMemo } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import Navbar from "@/components/Navbar";
import Dashboard from "@/components/Dashboard";
import Readings from "@/components/Readings";
import Chatbot from "@/components/Chatbot";

export default function ReefOS() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>(
    [],
  );
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<any[]>([]);
  const [newParam, setNewParam] = useState("");
  const [newValue, setNewValue] = useState("");
  const [activeTab, setActiveTab] = useState("Alkalinity");
  const [currentView, setCurrentView] = useState<"dashboard" | "charts">(
    "dashboard",
  );
  const [prediction, setPrediction] = useState<any>(null);
  const [dataSource, setDataSource] = useState("csv");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const logRes = await fetch(
        `http://127.0.0.1:8000/get-logs?t=${Date.now()}`,
      );
      const logData = await logRes.json();
      if (logData.data) setLogs(logData.data);

      const chatRes = await fetch(
        `http://127.0.0.1:8000/get-chat-history?t=${Date.now()}`,
      );
      const chatData = await chatRes.json();
      if (chatData.data) setMessages(chatData.data);

      // Fetch ML predictions based on dataSource
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

  const addManualLog = async () => {
    if (!newParam || !newValue) return;

    const val = parseFloat(newValue);
    if (isNaN(val)) {
      alert("Please enter a valid number.");
      return;
    }

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/log-metric?t=${Date.now()}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parameter: newParam.trim(), value: val }),
        },
      );

      const data = await res.json();

      // THIS WILL CATCH THE SILENT DATABASE ERROR
      if (data.status === "error") {
        alert("Database Error: " + data.message);
        return; // Stops here, prevents the text box from clearing
      }

      setNewValue("");
      setActiveTab(newParam.trim());
      fetchData();
    } catch (err) {
      alert("Network Error: Could not connect to the backend.");
    }
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
    } catch (err) {}
  };

  const uniqueParams = useMemo(
    () => {
      const validParams = ["Alkalinity", "Calcium", "Magnesium", "pH", "Temperature", "alk", "calcium", "magnesium", "ph", "temp"];
      const allParams = Array.from(new Set(logs.map((l) => l.parameter))).length > 0
        ? Array.from(new Set(logs.map((l) => l.parameter)))
        : ["Alkalinity"];
      // Filter and normalize to canonical names
      const normalized = allParams.map(p => {
        const lower = p?.toLowerCase();
        if (lower === "alk" || lower === "alkalinity") return "Alkalinity";
        if (lower === "ca" || lower === "calcium") return "Calcium";
        if (lower === "mg" || lower === "magnesium") return "Magnesium";
        if (lower === "ph") return "pH";
        if (lower === "temp" || lower === "temperature" || lower === "tds") return "Temperature";
        return null; // Filter out invalid params
      }).filter(Boolean);
      return normalized.length > 0 ? normalized : ["Alkalinity"];
    },
    [logs],
  );
  useEffect(() => {
    if (uniqueParams.length > 0 && !uniqueParams.includes(activeTab))
      setActiveTab(uniqueParams[0] as string);
  }, [uniqueParams, activeTab]);

  // Refetch predictions when data source changes
  useEffect(() => {
    const fetchPrediction = async () => {
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

  const handleDeleteLogs = async (param: string = null) => {
    try {
      const url = param 
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
            ) : (
              <Readings
                uniqueParams={uniqueParams}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                chartData={chartData}
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
