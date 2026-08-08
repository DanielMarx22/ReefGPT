"use client";

import React from "react";
import { MessageSquare, X } from "lucide-react";
import { useChat } from "@/context/ChatContext";
import Chatbot from "@/components/Chatbot";

export default function GlobalChatDrawer() {
  const { isChatOpen, setIsChatOpen, messages, sendMessage, clearHistory } = useChat();

  return (
    <>
      {/* Floating Action Button (Mobile Only) */}
      <button
        onClick={() => setIsChatOpen(true)}
        className="md:hidden fixed bottom-6 right-6 z-40 bg-cyan-600 hover:bg-cyan-500 text-white p-4 rounded-full shadow-[0_0_20px_rgba(6,182,212,0.5)] transition-all"
        aria-label="Open Chat"
      >
        <MessageSquare size={24} />
      </button>

      {/* Full Screen Slide-out Drawer */}
      <div
        className={`md:hidden fixed inset-0 z-50 bg-slate-950 transition-transform duration-300 ease-in-out ${
          isChatOpen ? "translate-x-0" : "translate-x-full"
        } flex flex-col`}
      >
        <div className="h-16 border-b border-white/10 bg-black/40 flex items-center justify-between px-4 shrink-0">
          <h2 className="text-cyan-400 font-bold flex items-center gap-2">
            <MessageSquare size={20} /> ReefGPT
          </h2>
          <button
            onClick={() => setIsChatOpen(false)}
            className="text-slate-400 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors"
          >
            <X size={24} />
          </button>
        </div>
        <div className="flex-1 overflow-hidden relative">
          <Chatbot messages={messages} sendMessage={sendMessage} clearHistory={clearHistory} />
        </div>
      </div>
    </>
  );
}
