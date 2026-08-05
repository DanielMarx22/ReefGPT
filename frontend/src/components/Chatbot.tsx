import { useEffect, useRef, useState } from "react";

interface ChatbotProps {
  messages: { role: string; content: string | any }[];
  sendMessage: (message: string) => void;
}

export default function Chatbot({ messages, sendMessage }: ChatbotProps) {
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
    <div className="flex flex-col h-full bg-black/40">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-4 rounded-xl ${msg.role === "user"
                ? "bg-cyan-900/30 border border-cyan-500/30 ml-auto max-w-[80%]"
                : "bg-slate-800/50 border border-slate-700 mr-auto max-w-[90%]"
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

      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800/50 bg-slate-900/50 flex gap-2">
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
      <div className="bg-slate-900/50 pb-2 px-4 text-center">
        <span className="text-[10px] text-slate-500">ReefGPT can make mistakes. Please verify critical advice before acting. It does not control hardware.</span>
      </div>
    </div>
  );
}