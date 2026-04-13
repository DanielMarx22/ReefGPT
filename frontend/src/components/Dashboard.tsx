import { Activity, Plus } from "lucide-react";

export default function Dashboard({
  newParam,
  setNewParam,
  newValue,
  setNewValue,
  addManualLog,
  latestMetrics,
}: any) {
  return (
    <div className="space-y-6 p-6">
      <div className="bg-black/40 p-5 rounded-xl border border-white/10 backdrop-blur-md">
        <h3 className="font-bold mb-3 text-cyan-400 flex items-center gap-2">
          <Activity size={18} /> Quick Log
        </h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={newParam}
            onChange={(e) => setNewParam(e.target.value)}
            placeholder="e.g., Iodine"
            className="bg-black/50 border border-white/10 p-2.5 rounded-lg w-1/3 outline-none focus:border-cyan-500"
          />
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
            className="bg-cyan-600/80 hover:bg-cyan-500 text-white font-semibold p-2.5 rounded-lg px-6 flex items-center gap-2 transition shadow-[0_0_15px_rgba(8,145,178,0.3)]"
          >
            <Plus size={18} /> Save
          </button>
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
