import type {
  Agent,
  AgentDetail,
  AgentCreateInput,
  AgentUpdateInput,
  AdminUser,
  AdminUserCreateInput,
  AdminUserUpdateInput,
  AuditLog,
  Conversation,
  ConversationAdmin,
  Message,
  Role,
  RoleCreateInput,
  RoleUpdateInput,
  Tool,
  ToolCreateInput,
  ToolUpdateInput,
  UserPublic
} from "@/lib/types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {})
    }
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function login(identifier: string, password: string) {
  return request<{ user: UserPublic }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password })
  });
}

export async function logout() {
  return request<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
}

export async function me() {
  return request<{ user: UserPublic }>("/api/auth/me");
}

export async function getAgents() {
  return request<Agent[]>("/api/agents");
}

export async function getConversations() {
  return request<Conversation[]>("/api/conversations");
}

export async function getConversationMessages(conversationId: number) {
  return request<Message[]>(`/api/conversations/${conversationId}/messages`);
}

export async function getAdminConversations() {
  return request<ConversationAdmin[]>("/api/admin/conversations");
}

export async function getAdminConversationMessages(conversationId: number) {
  return request<Message[]>(`/api/admin/conversations/${conversationId}/messages`);
}

export async function sendChat(agentId: number, message: string, conversationId?: number | null) {
  return request<{ conversation_id: number; assistant_message: string }>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ agent_id: agentId, message, conversation_id: conversationId ?? null })
  });
}

export async function getAdminUsers() {
  return request<AdminUser[]>("/api/admin/users");
}

export async function createAdminUser(payload: AdminUserCreateInput) {
  return request<AdminUser>("/api/admin/users", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminUser(userId: number, payload: AdminUserUpdateInput) {
  return request<AdminUser>(`/api/admin/users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteAdminUser(userId: number) {
  return request<{ ok: boolean }>(`/api/admin/users/${userId}`, { method: "DELETE" });
}

export async function getAdminRoles() {
  return request<Role[]>("/api/admin/roles");
}

export async function createAdminRole(payload: RoleCreateInput) {
  return request<Role>("/api/admin/roles", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminRole(roleId: number, payload: RoleUpdateInput) {
  return request<Role>(`/api/admin/roles/${roleId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteAdminRole(roleId: number) {
  return request<{ ok: boolean }>(`/api/admin/roles/${roleId}`, { method: "DELETE" });
}

export async function getAdminAgents() {
  return request<Agent[]>("/api/admin/agents");
}

export async function getAdminAgent(agentId: number) {
  return request<AgentDetail>(`/api/admin/agents/${agentId}`);
}

export async function createAdminAgent(payload: AgentCreateInput) {
  return request<Agent>("/api/admin/agents", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminAgent(agentId: number, payload: AgentUpdateInput) {
  return request<Agent>(`/api/admin/agents/${agentId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteAdminAgent(agentId: number) {
  return request<{ ok: boolean }>(`/api/admin/agents/${agentId}`, { method: "DELETE" });
}

export async function assignRoleToUser(userId: number, roleId: number) {
  return request<{ ok: boolean }>(`/api/admin/users/${userId}/roles/${roleId}`, { method: "POST" });
}

export async function unassignRoleFromUser(userId: number, roleId: number) {
  return request<{ ok: boolean }>(`/api/admin/users/${userId}/roles/${roleId}`, { method: "DELETE" });
}

export async function assignRoleToAgent(agentId: number, roleId: number) {
  return request<{ ok: boolean }>(`/api/admin/agents/${agentId}/roles/${roleId}`, { method: "POST" });
}

export async function unassignRoleFromAgent(agentId: number, roleId: number) {
  return request<{ ok: boolean }>(`/api/admin/agents/${agentId}/roles/${roleId}`, { method: "DELETE" });
}

export async function getAdminTools() {
  return request<Tool[]>("/api/admin/tools");
}

export async function createAdminTool(payload: ToolCreateInput) {
  return request<Tool>("/api/admin/tools", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAdminTool(toolId: number, payload: ToolUpdateInput) {
  return request<Tool>(`/api/admin/tools/${toolId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function deleteAdminTool(toolId: number) {
  return request<{ ok: boolean }>(`/api/admin/tools/${toolId}`, { method: "DELETE" });
}

export async function deleteAdminConversation(conversationId: number) {
  return request<{ ok: boolean }>(`/api/admin/conversations/${conversationId}`, { method: "DELETE" });
}

export async function updateAdminConversation(conversationId: number, archived: boolean) {
  return request<ConversationAdmin>(`/api/admin/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ archived })
  });
}

export async function assignToolToAgent(agentId: number, toolId: number, permissionLevel = "execute") {
  return request<{ ok: boolean }>(`/api/admin/agents/${agentId}/tools/${toolId}?permission_level=${encodeURIComponent(permissionLevel)}`, {
    method: "POST"
  });
}

export async function unassignToolFromAgent(agentId: number, toolId: number) {
  return request<{ ok: boolean }>(`/api/admin/agents/${agentId}/tools/${toolId}`, { method: "DELETE" });
}

export async function getAuditLogs() {
  return request<AuditLog[]>("/api/admin/audit");
}
