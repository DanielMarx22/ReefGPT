"use client";

import React from "react";
import { MessageSquare, X } from "lucide-react";
import { useChat } from "@/context/ChatContext";
import Chatbot from "@/components/Chatbot";
import { motion, AnimatePresence } from "framer-motion";

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

      {/* Drawer and Backdrop */}
      <AnimatePresence>
        {isChatOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsChatOpen(false)}
              className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              drag="x"
              dragDirectionLock
              dragConstraints={{ left: 0, right: 2000 }} // Drawer is physically free to move all the way right
              dragElastic={0} // No elasticity needed since it's within constraints
              onDragEnd={(e: any, info) => {
                // If Safari cancels the touch event mid-swipe, ignore it and let it snap back open
                if (e.type === 'touchcancel' || e.type === 'pointercancel') {
                  return;
                }

                // Require a deliberate swipe velocity (> 200) or distance (> 150px) to close
                const isSwipingRight = info.velocity.x > 200;
                const isSwipedFar = info.offset.x > 150;
                
                if (isSwipingRight || isSwipedFar) {
                  setIsChatOpen(false);
                }
              }}
              className="md:hidden fixed inset-y-0 right-0 w-[90vw] max-w-[400px] z-50 bg-slate-950/95 backdrop-blur-2xl border-l border-white/10 shadow-[-20px_0_50px_rgba(0,0,0,0.5)] flex flex-col"
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
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
