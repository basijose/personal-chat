"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getAgents, getConversations, getConversationMessages, me } from "@/lib/api";
import type { Agent, Conversation, Message, UserPublic } from "@/lib/types";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const session = await me();
        setUser(session.user);
        const [agentList, conversationList] = await Promise.all([getAgents(), getConversations()]);
        setAgents(agentList);
        setConversations(conversationList);
        if (conversationList[0]) {
          setConversationId(conversationList[0].id);
          setMessages(await getConversationMessages(conversationList[0].id));
        }
      } catch (err) {
        router.push("/login");
        setError(err instanceof Error ? err.message : "No autenticado");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [router]);

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-ink-950 text-ink-100">
        <div className="text-sm uppercase tracking-[0.3em] text-accent-300">Cargando</div>
      </div>
    );
  }

  if (!user) {
    return <div className="min-h-screen bg-ink-950 text-white">{error ?? "Redirigiendo..."}</div>;
  }

  return (
    <AppShell
      user={user}
      initialAgents={agents}
      initialConversations={conversations}
      initialMessages={messages}
      initialConversationId={conversationId}
    />
  );
}
