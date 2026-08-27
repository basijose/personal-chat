"use client";

import { logout } from "@/lib/api";
import type { Agent, Conversation, Message, UserPublic } from "@/lib/types";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type Props = {
  user: UserPublic;
  initialAgents: Agent[];
  initialConversations: Conversation[];
  initialMessages: Message[];
  initialConversationId: number | null;
};

export function AppShell({ user, initialAgents, initialConversations, initialMessages, initialConversationId }: Props) {
  const router = useRouter();
  const [agents, setAgents] = useState(initialAgents);
  const [conversations, setConversations] = useState(initialConversations);
  const [messages, setMessages] = useState(initialMessages);
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(initialAgents[0]?.id ?? null);
  const [conversationId, setConversationId] = useState<number | null>(initialConversationId);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeAgent = useMemo(() => agents.find((agent) => agent.id === selectedAgentId) ?? null, [agents, selectedAgentId]);

  async function refreshConversations() {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/conversations`, {
      credentials: "include"
    });
    if (response.ok) {
      setConversations(await response.json());
    }
  }

  async function startNewConversation() {
    if (!selectedAgentId) return;
    setConversationId(null);
    setMessages([]);
    setError(null);
  }

  async function loadConversation(targetId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/conversations/${targetId}/messages`, {
        credentials: "include"
      });
      if (!response.ok) throw new Error("No se pudo cargar la conversación");
      setConversationId(targetId);
      setMessages(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage() {
    if (!draft.trim() || !selectedAgentId) return;
    const content = draft.trim();
    setDraft("");
    setError(null);
    setMessages((current) => [...current, { id: Date.now(), conversation_id: conversationId ?? 0, role: "user", content, metadata: {} }]);
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: selectedAgentId, message: content, conversation_id: conversationId })
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "No se pudo enviar el mensaje");
      }
      const data = (await response.json()) as { conversation_id: number; assistant_message: string };
      setConversationId(data.conversation_id);
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, conversation_id: data.conversation_id, role: "assistant", content: data.assistant_message, metadata: {} }
      ]);
      await refreshConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  async function doLogout() {
    await logout().catch(() => undefined);
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(24,165,110,0.16),_transparent_30%),linear-gradient(180deg,_#07111f_0%,_#0d1726_100%)] text-ink-100">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 lg:grid-cols-[320px_1fr]">
        <aside className="border-b border-white/10 bg-ink-950/70 p-5 backdrop-blur lg:border-r lg:border-b-0">
          <div className="mb-6">
            <div className="text-xs uppercase tracking-[0.35em] text-accent-300">Personal Chat</div>
            <h1 className="mt-2 text-2xl font-semibold">Asistente inteligente corporativo</h1>
            <p className="mt-2 text-sm text-ink-200">Sesión: {user.username}</p>
          </div>
          <button onClick={() => void startNewConversation()} className="mb-4 w-full rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-accent-600">
            Nueva conversación
          </button>
          <div className="mb-6">
            <label className="mb-2 block text-xs uppercase tracking-[0.2em] text-ink-200">Agente activo</label>
            <select
              value={selectedAgentId ?? ""}
              onChange={(event) => setSelectedAgentId(Number(event.target.value))}
              className="w-full rounded-xl border border-white/10 bg-ink-900 px-3 py-3 text-sm text-white outline-none"
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs text-ink-200">{activeAgent?.description ?? "Sin agente seleccionado"}</p>
          </div>
          <div className="mb-6">
            <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-200">Conversaciones recientes</div>
            <div className="space-y-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => void loadConversation(conversation.id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left text-sm transition ${
                    conversationId === conversation.id ? "border-accent-400 bg-accent-500/15 text-white" : "border-white/10 bg-ink-900/60 text-ink-100 hover:bg-ink-800"
                  }`}
                >
                  <div className="font-medium">{conversation.title}</div>
                  <div className="mt-1 text-xs text-ink-200">#{conversation.id}</div>
                </button>
              ))}
            </div>
          </div>
          <div className="mb-6">
            <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-200">Agentes disponibles</div>
            <div className="space-y-2">
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => setSelectedAgentId(agent.id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left text-sm transition ${
                    selectedAgentId === agent.id ? "border-accent-400 bg-accent-500/15 text-white" : "border-white/10 bg-ink-900/60 text-ink-100 hover:bg-ink-800"
                  }`}
                >
                  <div className="font-medium">{agent.name}</div>
                  <div className="mt-1 text-xs text-ink-200">{agent.slug}</div>
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-3">
            {user.is_superadmin ? (
              <button onClick={() => router.push("/admin")} className="flex-1 rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800">
                Administración
              </button>
            ) : null}
            <button onClick={() => void doLogout()} className="rounded-xl border border-white/10 px-4 py-3 text-sm font-semibold text-ink-100 hover:bg-white/5">
              Logout
            </button>
          </div>
        </aside>
        <main className="flex min-h-screen flex-col p-4 lg:p-8">
          <div className="mb-4 rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-accent-300">Chat</div>
                <h2 className="mt-2 text-3xl font-semibold">{activeAgent?.name ?? "Seleccioná un agente"}</h2>
                <p className="mt-2 max-w-3xl text-sm text-ink-200">{activeAgent?.description ?? "Los permisos se validan en backend antes de cada tool."}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-ink-900/70 px-4 py-3 text-sm text-ink-100">
                <div className="text-xs uppercase tracking-[0.2em] text-ink-200">Proveedor</div>
                <div className="mt-1">{activeAgent?.provider ?? "-"}</div>
              </div>
            </div>
          </div>
          <div className="flex-1 rounded-3xl border border-white/10 bg-ink-950/50 shadow-panel backdrop-blur">
            <div className="flex h-full flex-col">
              <div className="flex-1 space-y-4 overflow-y-auto p-5">
                {messages.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-8 text-sm text-ink-200">
                    Iniciá una conversación. El backend decidirá si el agente y las herramientas están permitidos.
                  </div>
                ) : null}
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`max-w-3xl rounded-2xl px-4 py-3 text-sm leading-6 ${
                      message.role === "user" ? "ml-auto bg-accent-500 text-white" : "border border-white/10 bg-ink-900 text-ink-100"
                    }`}
                  >
                    <div className="mb-2 text-[11px] uppercase tracking-[0.25em] opacity-70">{message.role}</div>
                    <div>{message.content}</div>
                  </div>
                ))}
              </div>
              <div className="border-t border-white/10 p-4">
                {error ? <div className="mb-3 rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}
                <div className="flex flex-col gap-3 md:flex-row">
                  <textarea
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    placeholder="Escribí un mensaje..."
                    rows={3}
                    className="min-h-[84px] flex-1 rounded-2xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none placeholder:text-ink-600"
                  />
                  <button
                    disabled={loading || !selectedAgentId}
                    onClick={() => void sendMessage()}
                    className="rounded-2xl bg-accent-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-600 disabled:cursor-not-allowed disabled:opacity-60 md:w-36"
                  >
                    {loading ? "Enviando..." : "Enviar"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
