import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Readings({
  uniqueParams,
  activeTab,
  setActiveTab,
  chartData,
}: any) {
  return (
    <div className="h-full flex flex-col p-6">
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide border-b border-white/10">
        {uniqueParams.map((param: string) => (
          <button
            key={param}
            onClick={() => setActiveTab(param)}
            className={`px-4 py-2 text-sm font-semibold transition tracking-wide ${activeTab === param ? "text-cyan-400 border-b-2 border-cyan-400" : "text-slate-400 hover:text-slate-200"}`}
          >
            {param}
          </button>
        ))}
      </div>
      <div className="flex-1 w-full min-h-[300px]">
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
      </div>
    </div>
  );
}
