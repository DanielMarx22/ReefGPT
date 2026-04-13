import { LayoutDashboard, LineChart as ChartIcon } from "lucide-react";

export default function Navbar({ currentView, setCurrentView }: any) {
  return (
    <nav className="h-14 bg-black/60 border-b border-white/10 flex items-center px-6 gap-6 backdrop-blur-md shrink-0">
      <h1 className="text-xl font-black text-cyan-400 tracking-tight drop-shadow-md">
        REEF<span className="text-white">OS</span>
      </h1>
      <div className="flex gap-2">
        <button
          onClick={() => setCurrentView("dashboard")}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition ${currentView === "dashboard" ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/50" : "text-slate-400 hover:bg-white/5"}`}
        >
          <LayoutDashboard size={16} /> Dashboard
        </button>
        <button
          onClick={() => setCurrentView("charts")}
          className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition ${currentView === "charts" ? "bg-cyan-600/30 text-cyan-300 border border-cyan-500/50" : "text-slate-400 hover:bg-white/5"}`}
        >
          <ChartIcon size={16} /> Readings
        </button>
      </div>
    </nav>
  );
}
