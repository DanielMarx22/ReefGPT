import { useEffect, useRef, useState } from "react";
import { Trash2 } from "lucide-react";

interface ChatbotProps {
  messages: { role: string; content: string | any }[];
  sendMessage: (message: string) => void;
  clearHistory?: () => void;
}

export default function Chatbot({ messages, sendMessage, clearHistory }: ChatbotProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 relative overflow-hidden">
      {/* Textured Background Pattern */}
      <div 
        className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2306b6d4' fill-opacity='0.15'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }}
      />
      
      {/* Ambient Glow */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-cyan-900/20 blur-[100px] rounded-full pointer-events-none z-0" />
      {clearHistory && messages.length > 0 && (
        <button 
          onClick={clearHistory}
          className="absolute top-2 left-4 z-10 bg-red-900/50 hover:bg-red-900/80 text-red-300 p-1.5 rounded text-xs flex items-center gap-1 transition-colors border border-red-800"
          title="Clear Chat History"
        >
          <Trash2 size={12} /> Clear History
        </button>
      )}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 pt-10">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-4 rounded-xl relative z-10 backdrop-blur-md shadow-lg transition-all ${msg.role === "user"
                ? "bg-cyan-950/40 border border-cyan-500/30 ml-auto max-w-[80%] shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                : "bg-slate-900/60 border border-white/10 mr-auto max-w-[90%]"
              }`}
          >
            <span className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2 block">
              {msg.role === "ai" ? "ReefGPT" : "You"}
            </span>
            <div className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
              {/* Fallback to prevent React crashes if a raw object slips through */}
              {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content, null, 2)}
            </div>
          </div>
        ))}
        {/* Invisible div acts as the scroll target */}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-white/10 bg-black/40 backdrop-blur-xl flex gap-2 relative z-10">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-black/50 border border-slate-700 rounded-lg p-3 text-sm focus:border-cyan-500 outline-none text-slate-200 placeholder-slate-500 transition-colors"
          placeholder="Ask ReefGPT..."
        />
        <button
          type="submit"
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
          disabled={!input.trim()}
        >
          Send
        </button>
      </form>
      <div className="bg-black/40 backdrop-blur-xl pb-2 px-4 text-center relative z-10">
        <span className="text-[10px] text-slate-500">ReefGPT can make mistakes. Please verify critical advice before acting. It does not control hardware.</span>
      </div>
    </div>
  );
}