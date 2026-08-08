"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { fetchWithAuth } from "@/lib/api";

interface ChatContextType {
  messages: any[];
  sendMessage: (userMessage: string) => Promise<void>;
  clearHistory: () => Promise<void>;
  devMode: boolean;
  setDevMode: (val: boolean) => void;
  useV2: boolean;
  setUseV2: (val: boolean) => void;
  sessionXrays: any[];
  setSessionXrays: React.Dispatch<React.SetStateAction<any[]>>;
  pendingActions: any[];
  setPendingActions: React.Dispatch<React.SetStateAction<any[]>>;
  isChatOpen: boolean;
  setIsChatOpen: (val: boolean) => void;
  fetchChatHistory: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [devMode, setDevMode] = useState(false);
  const [sessionXrays, setSessionXrays] = useState<any[]>([]);
  const [xraysLoaded, setXraysLoaded] = useState(false);
  const [useV2, setUseV2] = useState(true);
  const [pendingActions, setPendingActions] = useState<any[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false); // Mobile Drawer State

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedXrays = localStorage.getItem("reef_session_xrays");
      if (savedXrays) {
        try {
          setSessionXrays(JSON.parse(savedXrays));
        } catch (e) {}
      }
      setXraysLoaded(true);
      fetchChatHistory();
    }
  }, []);

  useEffect(() => {
    if (xraysLoaded && typeof window !== "undefined") {
      const last10 = sessionXrays.slice(-10);
      localStorage.setItem("reef_session_xrays", JSON.stringify(last10));
    }
  }, [sessionXrays, xraysLoaded]);

  const fetchChatHistory = async () => {
    try {
      const chatRes = await fetchWithAuth(`/get-chat-history?t=${Date.now()}`);
      const chatData = await chatRes.json();
      if (chatData.data) {
        setMessages(chatData.data);
        const loadedXrays = chatData.data
          .filter((msg: any) => msg.role === 'ai' && msg.agent_reasoning)
          .map((msg: any) => msg.agent_reasoning);
        if (loadedXrays.length > 0) {
          setSessionXrays(loadedXrays.slice(-10));
        }
      }
    } catch (err) {
      console.error("Failed to fetch chat history", err);
    }
  };

  const sendMessage = async (userMessage: string) => {
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const endpoint = useV2 ? "chat-v2" : "chat";
      const res = await fetchWithAuth(`/${endpoint}?t=${Date.now()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage }),
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const data = await res.json();

      setMessages((prev) => [...prev, { role: "ai", content: data.reply }]);
      if (data.debug_xray) {
        setSessionXrays((prev) => {
          const updated = [...prev, data.debug_xray];
          return updated.slice(-10);
        });
      }
      if (data.proposed_actions && data.proposed_actions.length > 0) {
        const validActions = data.proposed_actions.filter((a: any) => {
          if (a.action === "add_inhabitant" && !a.species && !a.name) return false;
          return true;
        });
        if (validActions.length > 0) {
          setPendingActions(validActions);
        }
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [...prev, { role: "ai", content: `System Error: Failed to reach the AI server (${err.message || "Unknown Network Error"}). Please check the backend logs.` }]);
    }
  };

  const clearHistory = async () => {
    if (!confirm("Are you sure you want to clear the chat history for this tank?")) return;
    try {
      await fetchWithAuth(`/chat-history`, { method: "DELETE" });
      setMessages([]);
      setSessionXrays([]);
      localStorage.removeItem("reef_session_xrays");
    } catch (err) {
      console.error("Failed to clear chat history", err);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        sendMessage,
        clearHistory,
        devMode,
        setDevMode,
        useV2,
        setUseV2,
        sessionXrays,
        setSessionXrays,
        pendingActions,
        setPendingActions,
        isChatOpen,
        setIsChatOpen,
        fetchChatHistory
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
