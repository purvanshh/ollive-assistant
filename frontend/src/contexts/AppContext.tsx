"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  model_used: string | null;
  tokens_used: number | null;
  cost_usd: number | null;
  routing_reason?: string | null;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  dependencies: {
    database: string;
    ollama: string;
    frontier: string;
  };
}

interface AppContextType {
  apiKey: string;
  setApiKey: (val: string) => void;
  userId: string;
  setUserId: (val: string) => void;
  modelOverride: string;
  setModelOverride: (val: string) => void;
  health: HealthStatus | null;
  conversations: Conversation[];
  activeConvId: string | null;
  setActiveConvId: (id: string | null) => void;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isLoadingMessages: boolean;
  fetchConversations: () => Promise<void>;
  fetchMessages: (convId: string) => Promise<void>;
  startNewChat: () => Promise<void>;
  deleteConversation: (convId: string) => Promise<void>;
}

const AppContext = createContext<AppContextType | null>(null);

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string>("test_api_key_12345");
  const [userId, setUserIdState] = useState<string>("default_user");
  const [modelOverride, setModelOverrideState] = useState<string>("auto");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);

  const setApiKey = useCallback((val: string) => {
    setApiKeyState(val);
    localStorage.setItem("ollive_api_key", val);
  }, []);

  const setUserId = useCallback((val: string) => {
    setUserIdState(val);
    localStorage.setItem("ollive_user_id", val);
  }, []);

  const setModelOverride = useCallback((val: string) => {
    setModelOverrideState(val);
    localStorage.setItem("ollive_model_override", val);
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedKey = localStorage.getItem("ollive_api_key");
      const savedUser = localStorage.getItem("ollive_user_id");
      const savedModel = localStorage.getItem("ollive_model_override");
      if (savedKey) setApiKeyState(savedKey);
      if (savedUser) setUserIdState(savedUser);
      if (savedModel) setModelOverrideState(savedModel);
    }
  }, []);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/health`)
      .then((res) => res.ok ? res.json() : null)
      .then((data) => setHealth(data || null))
      .catch(() => setHealth(null));
  }, []);

  const fetchConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations?user_id=${userId}&limit=50`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) setConversations(await res.json());
    } catch (err) {
      console.error("Failed to fetch conversations", err);
    }
  }, [userId, apiKey]);

  const fetchMessages = useCallback(async (convId: string) => {
    setIsLoadingMessages(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}/messages`, {
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) setMessages(await res.json());
    } catch (err) {
      console.error("Failed to fetch messages", err);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [apiKey]);

  const startNewChat = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify({ user_id: userId, title: "New Conversation" })
      });
      if (res.ok) {
        const data = await res.json();
        setConversations((prev) => [data, ...prev]);
        setActiveConvId(data.id);
      }
    } catch (err) {
      console.error("Failed to start new chat", err);
    }
  }, [userId, apiKey]);

  const deleteConversation = useCallback(async (convId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${convId}`, {
        method: "DELETE",
        headers: { "X-API-Key": apiKey }
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== convId));
        if (activeConvId === convId) setActiveConvId(null);
      }
    } catch (err) {
      console.error("Failed to delete conversation", err);
    }
  }, [apiKey, activeConvId]);

  useEffect(() => {
    if (userId && apiKey) fetchConversations();
  }, [userId, apiKey, fetchConversations]);

  useEffect(() => {
    if (activeConvId) fetchMessages(activeConvId);
    else setMessages([]);
  }, [activeConvId, fetchMessages]);

  return (
    <AppContext.Provider
      value={{
        apiKey,
        setApiKey,
        userId,
        setUserId,
        modelOverride,
        setModelOverride,
        health,
        conversations,
        activeConvId,
        setActiveConvId,
        messages,
        setMessages,
        isLoadingMessages,
        fetchConversations,
        fetchMessages,
        startNewChat,
        deleteConversation,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}
