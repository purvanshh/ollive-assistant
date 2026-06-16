"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Send, Sparkles, Database, ShieldAlert, CheckCircle, HelpCircle, User, Zap, Paperclip, FileText, X,
  ThumbsUp, ThumbsDown
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useApp } from "@/contexts/AppContext";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChatPage() {
  const {
    apiKey, userId, modelOverride, setModelOverride,
    health, conversations, activeConvId, setActiveConvId,
    messages, setMessages, fetchMessages, fetchConversations, startNewChat,
  } = useApp();

  const [input, setInput] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [streamText, setStreamText] = useState<string>("");
  const [streamModel, setStreamModel] = useState<string>("");
  const [streamRoutingReason, setStreamRoutingReason] = useState<string>("");
  const [streamCost, setStreamCost] = useState<number>(0.0);
  const [streamStatus, setStreamStatus] = useState<string>("");
  const [streamToolQuery, setStreamToolQuery] = useState<string>("");
  const [attachedFile, setAttachedFile] = useState<{ name: string; content: string } | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamText]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      alert("File size exceeds the 10MB limit.");
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/files/upload`, {
        method: "POST",
        headers: { "X-API-Key": apiKey },
        body: formData
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setAttachedFile({ name: data.filename, content: data.parsed_content });
    } catch (err: any) {
      alert(`Failed to parse file: ${err.message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const estimateCost = (text: string) => {
    if (!text.trim()) return null;
    const isFrontier = modelOverride === "frontier" || (
      modelOverride === "auto" && (() => {
        const lower = text.toLowerCase();
        const codingKeywords = ["python", "javascript", "typescript", "c++", "rust", "java", "html", "css", "function", "class", "write code", "implement", "coding", "program", "regex", "debugging", "debug", "compile", "script", "algorithm", "database query", "sql"];
        const mathComplexKeywords = ["solve", "equation", "formula", "calculus", "algebra", "integral", "derivative", "theorem", "matrix", "geometry", "proof", "trigonometry"];
        const reasoningKeywords = ["explain step-by-step", "explain step by step", "why does", "analyze", "compare and contrast", "logical", "critical thinking", "implications", "pros and cons", "evaluate", "detailed breakdown", "summarize the argument"];
        const multimodalKeywords = ["image", "photo", "picture", "screenshot", "diagram", "pdf", "csv"];
        return codingKeywords.some(kw => lower.includes(kw)) || mathComplexKeywords.some(kw => lower.includes(kw)) || reasoningKeywords.some(kw => lower.includes(kw)) || multimodalKeywords.some(kw => lower.includes(kw));
      })()
    );
    if (isFrontier) {
      const inputTokens = Math.max(1, Math.ceil(text.length / 4));
      return { cost: (inputTokens * 5.0) / 1_000_000, model: "Frontier (GPT-4)" };
    }
    return null;
  };

  const submitFeedback = async (messageId: string, rating: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify({ message_id: messageId, rating })
      });
    } catch (err) {
      console.error("Failed to submit feedback", err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    let currentConvId = activeConvId;
    if (!currentConvId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
          body: JSON.stringify({ user_id: userId, title: "New Conversation" })
        });
        if (res.ok) {
          const data = await res.json();
          currentConvId = data.id;
          setActiveConvId(data.id);
          fetchConversations();
        } else {
          alert("Failed to initialize conversation session.");
          return;
        }
      } catch (err) {
        console.error("Failed to auto-create conversation", err);
        return;
      }
    }

    const userPrompt = input;
    setInput("");
    setIsGenerating(true);
    setStreamText("");
    setStreamModel("");
    setStreamRoutingReason("");
    setStreamCost(0.0);
    setStreamStatus("");
    setStreamToolQuery("");

    const fileContentToSend = attachedFile ? attachedFile.content : null;
    const fileNameToSend = attachedFile ? attachedFile.name : null;
    setAttachedFile(null);

    const tempUserMsg = {
      id: `temp-u-${Date.now()}`,
      conversation_id: currentConvId!,
      role: "user" as const,
      content: fileNameToSend ? `[Attached File: ${fileNameToSend}]\n\n${userPrompt}` : userPrompt,
      model_used: null,
      tokens_used: null,
      cost_usd: null,
      created_at: new Date().toISOString()
    };
    setMessages((prev: any) => [...prev, tempUserMsg]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
        body: JSON.stringify({
          conversation_id: currentConvId,
          prompt: userPrompt,
          model_override: modelOverride,
          file_content: fileContentToSend
        })
      });

      if (!response.ok) throw new Error(`Server returned HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("ReadableStream not supported.");

      let accumulatedContent = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          if (trimmed.startsWith("data: ")) {
            const dataStr = trimmed.slice(6).trim();
            if (dataStr === "[DONE]") break;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.status === "searching") {
                setStreamStatus("searching");
                setStreamToolQuery(parsed.query || "");
              } else if (parsed.status === "running_code") {
                setStreamStatus("running_code");
                setStreamToolQuery(parsed.code || "");
              } else {
                if (parsed.status === "completed_search" || parsed.status === "completed_code") {
                  setStreamStatus("");
                }
                const content = parsed.choices?.[0]?.delta?.content || "";
                if (parsed.model) setStreamModel(parsed.model);
                if (parsed.routing_reason) setStreamRoutingReason(parsed.routing_reason);
                if (parsed.cost !== undefined) setStreamCost(parsed.cost);
                accumulatedContent += content;
                setStreamText(accumulatedContent);
              }
            } catch (err) {
              console.error("Failed to parse chunk JSON:", err);
            }
          }
        }
      }

      await fetchMessages(currentConvId!);
      await fetchConversations();

    } catch (err: any) {
      const tempErrorMsg = {
        id: `temp-err-${Date.now()}`,
        conversation_id: currentConvId!,
        role: "assistant" as const,
        content: `Error generating response: ${err?.message || err}`,
        model_used: "error",
        tokens_used: 0,
        cost_usd: 0.0,
        created_at: new Date().toISOString()
      };
      setMessages((prev: any) => [...prev, tempErrorMsg]);
    } finally {
      setIsGenerating(false);
      setStreamText("");
    }
  };

  return (
    <main className="flex-1 flex flex-col bg-zinc-950">
      <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-900/10 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-sm">
            {activeConvId
              ? conversations.find(c => c.id === activeConvId)?.title || "Chat"
              : "New Conversation"}
          </span>
          {health && (
            <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 font-mono">
              <span>· DB: {health.dependencies.database}</span>
              <span>· Local: {health.dependencies.ollama}</span>
              <span>· Frontier: {health.dependencies.frontier}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-zinc-400 bg-zinc-900 p-1.5 rounded-xl border border-zinc-800">
            <Zap className="h-3.5 w-3.5 text-lime-500" />
            <Select value={modelOverride} onValueChange={(val) => setModelOverride(val || "auto")}>
              <SelectTrigger className="border-0 bg-transparent h-5 text-xs text-zinc-200 focus:ring-0 p-0 font-medium">
                <SelectValue placeholder="Model Preference" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800 text-zinc-200">
                <SelectItem value="auto">Auto (Router)</SelectItem>
                <SelectItem value="oss">Force OSS</SelectItem>
                <SelectItem value="frontier">Force Frontier</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg: any) => (
          <div key={msg.id}
            className={`flex items-start gap-3.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div className={`p-2 rounded-xl shrink-0 ${
              msg.role === "user"
                ? "bg-zinc-800 text-zinc-100"
                : msg.model_used === "blocked"
                  ? "bg-red-950/40 text-red-500 border border-red-900/50"
                  : "bg-lime-950/20 text-lime-400 border border-lime-900/30"
            }`}>
              {msg.role === "user" ? <User className="h-4 w-4" /> : <Database className="h-4 w-4" />}
            </div>
            <div className="space-y-1.5 max-w-[75%]">
              <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-zinc-900 text-zinc-100 rounded-tr-none border border-zinc-800/80 shadow-md shadow-black/10"
                  : msg.model_used === "blocked"
                    ? "bg-red-950/20 text-red-200 border border-red-900/30 rounded-tl-none"
                    : "bg-zinc-900/50 text-zinc-200 border border-zinc-850 rounded-tl-none shadow-md shadow-black/5"
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.role === "assistant" && (
                <div className="flex flex-wrap items-center gap-2 text-[10px] text-zinc-500 font-mono px-1">
                  <span className="bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800 text-zinc-300">
                    {msg.model_used || "Local OSS"}
                  </span>
                  <span className="bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800 flex items-center gap-1 text-zinc-300">
                    {msg.cost_usd && msg.cost_usd > 0 ? `$${msg.cost_usd.toFixed(6)}` : "Free (local)"}
                  </span>
                  {msg.tokens_used ? <span className="bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">{msg.tokens_used} tkn</span> : null}
                  {msg.routing_reason && (
                    <span className="bg-lime-500/10 text-lime-400 px-1.5 py-0.5 rounded border border-lime-500/20">
                      Reason: {msg.routing_reason}
                    </span>
                  )}
                  {msg.id && !msg.id.startsWith("temp-") && (
                    <div className="flex items-center gap-0.5 ml-1">
                      <button
                        onClick={() => submitFeedback(msg.id, 1)}
                        className="p-0.5 rounded hover:bg-lime-500/20 text-zinc-500 hover:text-lime-400 transition-colors"
                        title="Helpful"
                      >
                        <ThumbsUp className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => submitFeedback(msg.id, -1)}
                        className="p-0.5 rounded hover:bg-red-500/20 text-zinc-500 hover:text-red-400 transition-colors"
                        title="Not helpful"
                      >
                        <ThumbsDown className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isGenerating && (streamText || streamStatus === "searching" || streamStatus === "running_code") && (
          <div className="flex items-start gap-3.5 flex-row animate-fade-in">
            <div className="p-2 rounded-xl shrink-0 bg-lime-950/20 text-lime-400 border border-lime-900/30">
              <Database className="h-4 w-4" />
            </div>
            <div className="space-y-1.5 max-w-[75%]">
              {streamStatus === "searching" && (
                <div className="p-4 rounded-2xl text-sm bg-zinc-900/50 text-zinc-400 border border-zinc-850 rounded-tl-none flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-lime-500"></div>
                  <span>Searching web for &quot;{streamToolQuery}&quot;...</span>
                </div>
              )}
              {streamStatus === "running_code" && (
                <div className="p-4 rounded-2xl text-sm bg-zinc-900/50 text-zinc-400 border border-zinc-850 rounded-tl-none flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-500"></div>
                  <span>Executing python code...</span>
                </div>
              )}
              {streamText && (
                <div className="p-4 rounded-2xl text-sm bg-zinc-900/50 text-zinc-200 border border-zinc-850 rounded-tl-none">
                  <p className="whitespace-pre-wrap">{streamText}</p>
                </div>
              )}
              <div className="flex flex-wrap items-center gap-2 text-[10px] text-zinc-500 font-mono px-1">
                <span className="animate-pulse bg-lime-500/10 text-lime-400 px-1.5 py-0.5 rounded border border-lime-900/40">
                  {streamStatus === "searching" || streamStatus === "running_code" ? "thinking..." : "streaming..."}
                </span>
                {streamModel && (
                  <span className="bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800 text-zinc-300">{streamModel}</span>
                )}
                {streamModel && (
                  <span className="bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800 text-zinc-300">
                    {streamCost > 0 ? `$${streamCost.toFixed(6)}` : "Free (local)"}
                  </span>
                )}
                {streamRoutingReason && (
                  <span className="bg-lime-500/10 text-lime-400 px-1.5 py-0.5 rounded border border-lime-500/20 animate-fade-in">
                    Reason: {streamRoutingReason}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {messages.length === 0 && !isGenerating && (
          <div className="h-full flex flex-col items-center justify-center py-24 text-zinc-600 text-center max-w-md mx-auto space-y-4">
            <div className="p-4 bg-zinc-900 rounded-3xl border border-zinc-800 shadow-xl">
              <Sparkles className="h-12 w-12 text-lime-500 mx-auto" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-zinc-300">Welcome to Ollive AI Gateway</h3>
              <p className="text-xs text-zinc-500">
                Ask a question. Simple questions will route locally, while complex reasoning queries route to frontier APIs. Local Llama Guard 3 stands watch on all chats.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full pt-4">
              <button
                onClick={() => setInput("What is 2 + 2?")}
                className="p-2.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-400 hover:text-zinc-200 rounded-xl text-left text-xs border border-zinc-800/80 transition-all"
              >
                <span className="font-semibold block text-zinc-300">Simple Math</span>
                &quot;What is 2 + 2?&quot;
              </button>
              <button
                onClick={() => setInput("Write a Python function to compute the first 10 Fibonacci numbers")}
                className="p-2.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-400 hover:text-zinc-200 rounded-xl text-left text-xs border border-zinc-800/80 transition-all"
              >
                <span className="font-semibold block text-zinc-300">Code Generation</span>
                &quot;Write a Fibonacci func...&quot;
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="p-6 border-t border-zinc-800 bg-zinc-900/10 backdrop-blur-md">
        <div className="flex flex-col gap-2 mb-3">
          {isUploading && (
            <div className="flex items-center gap-2 text-[11px] font-mono text-zinc-400 bg-zinc-900 px-3 py-2 rounded-xl animate-pulse border border-zinc-800">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-zinc-400"></div>
              <span>Uploading and parsing file...</span>
            </div>
          )}
          {attachedFile && (
            <div className="flex items-center justify-between text-[11px] font-mono bg-lime-500/10 border border-lime-500/25 text-lime-400 px-3 py-2 rounded-xl animate-fade-in shadow-inner">
              <div className="flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 text-lime-400" />
                <span>Attached: <strong>{attachedFile.name}</strong> (~{Math.round(attachedFile.content.length / 1024)} KB)</span>
              </div>
              <button type="button" onClick={() => setAttachedFile(null)} className="text-lime-500 hover:text-red-400 transition-colors">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
          {(() => {
            const promptText = attachedFile ? attachedFile.content + "\n" + input : input;
            const estimation = estimateCost(promptText);
            if (estimation) {
              return (
                <div className="flex items-center gap-2 text-[11px] font-mono bg-lime-500/10 border border-lime-500/25 text-lime-400 px-3 py-2 rounded-xl animate-fade-in shadow-inner">
                  <Sparkles className="h-3.5 w-3.5 animate-pulse text-lime-400" />
                  <span>
                    Detected complex query. Routing to <strong>{estimation.model}</strong>. Est. Input Cost: <strong>${estimation.cost.toFixed(6)}</strong>
                  </span>
                </div>
              );
            }
            return null;
          })()}
        </div>
        <form onSubmit={handleSendMessage} className="relative flex items-center">
          <input
            type="file" ref={fileInputRef} onChange={handleFileUpload}
            accept=".pdf,.csv,.txt" className="hidden"
          />
          <Button
            type="button" variant="ghost" size="icon"
            disabled={isGenerating || isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="absolute left-2 top-2 h-9 w-9 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-xl flex items-center justify-center transition-all"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isGenerating ? "Streaming response..." : "Type your message here..."}
            disabled={isGenerating}
            className="w-full bg-zinc-900 border-zinc-800 rounded-2xl py-6 pr-14 pl-12 text-sm focus-visible:ring-lime-500 text-zinc-100 placeholder-zinc-500 shadow-inner"
          />
          <Button
            type="submit" size="icon"
            disabled={isGenerating || !input.trim()}
            className="absolute right-2 top-2 bg-lime-500 hover:bg-lime-400 text-black rounded-xl h-9 w-9 flex items-center justify-center transition-all shadow-md shadow-lime-950/20"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
        <div className="mt-2 text-center">
          <span className="text-[10px] text-zinc-600 font-mono">
            Layered local security actively checks all prompts. Model cost and metrics are recorded in real-time.
          </span>
        </div>
      </div>
    </main>
  );
}
