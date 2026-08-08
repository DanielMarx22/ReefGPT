"use client";

import React, { useState, useEffect } from "react";
import { MessageSquare, X } from "lucide-react";
import { useChat } from "@/context/ChatContext";
import Chatbot from "@/components/Chatbot";

export default function GlobalChatDrawer() {
  const { isChatOpen, setIsChatOpen, messages, sendMessage, clearHistory } = useChat();

  // Custom 1:1 Touch Tracking
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [dragX, setDragX] = useState(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (touchStart === null) return;
    const currentX = e.targetTouches[0].clientX;
    const deltaX = currentX - touchStart;

    // Only allow dragging to the right (positive delta)
    if (deltaX > 0) {
      setDragX(deltaX);
    }
  };

  useEffect(() => {
    if (!isChatOpen) {
      setDragX(0);
      setTouchStart(null);
    }
  }, [isChatOpen]);

  const handleTouchEnd = () => {
    // If they dragged more than 100px to the right, close it
    if (dragX > 100) {
      setIsChatOpen(false);
    } else {
      setDragX(0);
    }
    setTouchStart(null);
  };

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

      {/* Backdrop */}
      {isChatOpen && (
        <div
          onClick={() => setIsChatOpen(false)}
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300"
        />
      )}

      {/* Swipeable Slide-out Drawer */}
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={handleTouchEnd}
        style={{
          transform: `translateX(${isChatOpen ? dragX + "px" : "100%"})`,
          transitionProperty: "transform",
          transitionTimingFunction: "cubic-bezier(0.4, 0, 0.2, 1)",
          transitionDuration: dragX > 0 ? "0ms" : "300ms", // Instant track while dragging, smooth snap on release
        }}
        className="md:hidden fixed inset-y-0 right-0 w-[90vw] max-w-[400px] z-50 bg-slate-950/95 backdrop-blur-2xl border-l border-white/10 shadow-[-20px_0_50px_rgba(0,0,0,0.5)] flex flex-col touch-pan-y"
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
