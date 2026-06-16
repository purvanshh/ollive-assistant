"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Plus, MessageSquare, Trash2, Settings, Sparkles,
  CheckCircle, ShieldAlert, BarChart3, Shield, LayoutDashboard
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useApp } from "@/contexts/AppContext";

const navItems = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/eval", label: "Evaluation", icon: BarChart3 },
  { href: "/admin", label: "Admin", icon: LayoutDashboard },
];

export function Sidebar() {
  const pathname = usePathname();
  const {
    apiKey, setApiKey, userId, setUserId,
    health, conversations, activeConvId, setActiveConvId,
    startNewChat, deleteConversation,
  } = useApp();

  const [showSettings, setShowSettings] = useState(false);

  return (
    <aside className="w-80 flex flex-col border-r border-zinc-800 bg-zinc-900/40 backdrop-blur-md">
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="bg-lime-500 text-black p-1.5 rounded-lg">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold tracking-tight text-md">Ollive AI Gateway</h1>
            <p className="text-[10px] text-zinc-500 font-mono">v1.0 · Local First</p>
          </div>
        </Link>
        <Button
          variant="ghost"
          size="icon"
          className="text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800"
          onClick={() => setShowSettings(!showSettings)}
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>

      {showSettings && (
        <div className="p-4 bg-zinc-800/80 border-b border-zinc-700 m-3 rounded-xl space-y-3">
          <h3 className="font-semibold text-xs text-zinc-400 tracking-wider uppercase">Connection Settings</h3>
          <div className="space-y-2">
            <div>
              <label className="text-[10px] text-zinc-400 font-mono">API Key</label>
              <Input
                value={apiKey}
                type="password"
                onChange={(e) => setApiKey(e.target.value)}
                className="bg-zinc-900 border-zinc-700 text-xs text-zinc-200"
              />
            </div>
            <div>
              <label className="text-[10px] text-zinc-400 font-mono">User ID</label>
              <Input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="bg-zinc-900 border-zinc-700 text-xs text-zinc-200"
              />
            </div>
            <Button
              size="sm"
              onClick={() => setShowSettings(false)}
              className="w-full bg-zinc-700 hover:bg-zinc-600 text-zinc-50 text-xs"
            >
              Save Configuration
            </Button>
          </div>
        </div>
      )}

      <nav className="px-3 py-2 border-b border-zinc-800">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-zinc-800 text-zinc-50"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0 opacity-70" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      {pathname === "/" && (
        <>
          <div className="p-3">
            <Button
              onClick={startNewChat}
              className="w-full bg-lime-500 hover:bg-lime-400 text-black font-semibold flex items-center gap-2 rounded-xl transition-all shadow-md shadow-lime-950/20"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </div>

          <ScrollArea className="flex-1 px-2 py-1">
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => setActiveConvId(conv.id)}
                  className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer text-sm font-medium transition-all ${
                    activeConvId === conv.id
                      ? "bg-zinc-800 text-zinc-50"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
                  }`}
                >
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <MessageSquare className="h-4 w-4 shrink-0 opacity-70" />
                    <span className="truncate">{conv.title || "Untitled Chat"}</span>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversation(conv.id);
                    }}
                    className="h-7 w-7 text-zinc-500 hover:text-red-400 hover:bg-zinc-700/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
              {conversations.length === 0 && (
                <div className="text-center py-8 text-zinc-500">
                  <p className="text-xs">No active chats. Start one above!</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </>
      )}

      <div className="p-3 border-t border-zinc-800 bg-zinc-950/20 text-xs flex items-center justify-between mt-auto">
        <span className="text-zinc-500">Service Status:</span>
        {health ? (
          <div className="flex items-center gap-1.5 text-lime-500">
            <CheckCircle className="h-3.5 w-3.5" />
            <span>{health.status.toUpperCase()}</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-amber-500">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>OFFLINE</span>
          </div>
        )}
      </div>
    </aside>
  );
}
