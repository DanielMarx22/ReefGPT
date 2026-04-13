import { Send } from "lucide-react";

export default function Chatbot({
  messages,
  input,
  setInput,
  sendMessage,
}: any) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-white/10 flex justify-between items-center backdrop-blur-md">
        <h2 className="text-lg font-bold text-cyan-400">ReefGPT</h2>
        <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Online
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m: any, i: number) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] p-3 text-sm leading-relaxed shadow-lg backdrop-blur-md ${m.role === "user" ? "bg-cyan-600/80 text-white rounded-2xl rounded-tr-sm" : "bg-white/10 border border-white/20 text-slate-100 rounded-2xl rounded-tl-sm"}`}
            >
              {m.content}
            </div>
          </div>
        ))}
      </div>
      <form
        onSubmit={sendMessage}
        className="p-3 border-t border-white/10 flex gap-2 backdrop-blur-md bg-black/30"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-black/50 border border-white/10 p-2.5 rounded-lg outline-none focus:border-cyan-500 text-sm"
          placeholder="Ask ReefGPT..."
        />
        <button
          type="submit"
          className="bg-cyan-600/80 text-white p-2.5 rounded-lg hover:bg-cyan-500 transition"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
