/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import {
  assignRoleToAgent,
  assignRoleToUser,
  assignToolToAgent,
  createAdminAgent,
  createAdminRole,
  createAdminTool,
  createAdminUser,
  deleteAdminConversation,
  deleteAdminAgent,
  deleteAdminRole,
  deleteAdminTool,
  deleteAdminUser,
  getAdminAgent,
  getAdminConversationMessages,
  getAdminConversations,
  getAdminAgents,
  getAdminRoles,
  getAdminTools,
  getAdminUsers,
  getAuditLogs,
  unassignRoleFromAgent,
  unassignRoleFromUser,
  unassignToolFromAgent,
  updateAdminConversation,
  updateAdminAgent,
  updateAdminRole,
  updateAdminTool,
  updateAdminUser
} from "@/lib/api";
import type { Agent, AgentDetail, AdminUser, AuditLog, ConversationAdmin, Message, Role, Tool } from "@/lib/types";
import { useEffect, useState, type ReactNode } from "react";

type Props = {
  userName: string;
};

type TabKey = "overview" | "users" | "roles" | "agents" | "tools" | "conversations" | "audit";
type NoticeKind = "success" | "error" | "info";

type Notice = {
  kind: NoticeKind;
  text: string;
};

type UserFormState = {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  active: boolean;
  is_superadmin: boolean;
  roleIds: number[];
};

type RoleFormState = {
  name: string;
  description: string;
};

type AgentFormState = {
  name: string;
  slug: string;
  description: string;
  system_prompt: string;
  provider: string;
  model: string;
  temperature: string;
  active: boolean;
};

type ToolFormState = {
  name: string;
  slug: string;
  description: string;
  tool_type: string;
  configuration: string;
  active: boolean;
};

const emptyUserForm = (): UserFormState => ({
  username: "",
  email: "",
  password: "Demo1234!",
  first_name: "",
  last_name: "",
  active: true,
  is_superadmin: false,
  roleIds: []
});

const emptyRoleForm = (): RoleFormState => ({
  name: "",
  description: ""
});

const emptyAgentForm = (): AgentFormState => ({
  name: "",
  slug: "",
  description: "",
  system_prompt: "",
  provider: "mock",
  model: "mock",
  temperature: "0.2",
  active: true
});

const emptyToolForm = (): ToolFormState => ({
  name: "",
  slug: "",
  description: "",
  tool_type: "mock",
  configuration: "{}",
  active: true
});

export function AdminPanel({ userName }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [conversations, setConversations] = useState<ConversationAdmin[]>([]);
  const [conversationMessages, setConversationMessages] = useState<Message[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationAdmin | null>(null);
  const [audit, setAudit] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editingRoleId, setEditingRoleId] = useState<number | null>(null);
  const [editingAgentId, setEditingAgentId] = useState<number | null>(null);
  const [editingToolId, setEditingToolId] = useState<number | null>(null);
  const [selectedAgentDetail, setSelectedAgentDetail] = useState<AgentDetail | null>(null);

  const [userForm, setUserForm] = useState<UserFormState>(emptyUserForm);
  const [roleForm, setRoleForm] = useState<RoleFormState>(emptyRoleForm);
  const [agentForm, setAgentForm] = useState<AgentFormState>(emptyAgentForm);
  const [toolForm, setToolForm] = useState<ToolFormState>(emptyToolForm);

  const [agentRoleTarget, setAgentRoleTarget] = useState<string>("");
  const [agentRoleValue, setAgentRoleValue] = useState<string>("");
  const [assignmentAgentId, setAssignmentAgentId] = useState<string>("");
  const [assignmentToolId, setAssignmentToolId] = useState<string>("");
  const [assignmentPermission, setAssignmentPermission] = useState("execute");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [conversationUserFilter, setConversationUserFilter] = useState("");
  const [conversationAgentFilter, setConversationAgentFilter] = useState("");
  const [conversationArchivedFilter, setConversationArchivedFilter] = useState<"all" | "active" | "archived">("all");
  const [conversationDateFrom, setConversationDateFrom] = useState("");
  const [conversationDateTo, setConversationDateTo] = useState("");

  async function loadAll() {
    const [u, r, a, t, c, l] = await Promise.all([
      getAdminUsers(),
      getAdminRoles(),
      getAdminAgents(),
      getAdminTools(),
      getAdminConversations(),
      getAuditLogs()
    ]);
    setUsers(u);
    setRoles(r);
    setAgents(a);
    setTools(t);
    setConversations(c);
    setAudit(l);
  }

  useEffect(() => {
    void loadAll()
      .then(() => setLoading(false))
      .catch((error) => {
        setLoading(false);
        setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudieron cargar los datos" });
      });
  }, []);

  useEffect(() => {
    if (!editingUserId && roles.length && userForm.roleIds.length === 0) {
      setUserForm((current) => ({ ...current, roleIds: [roles[0].id] }));
    }
  }, [editingUserId, roles, userForm.roleIds.length]);

  useEffect(() => {
    if (!assignmentAgentId && agents.length) {
      setAssignmentAgentId(String(agents[0].id));
    }
  }, [agents, assignmentAgentId]);

  useEffect(() => {
    if (!assignmentToolId && tools.length) {
      setAssignmentToolId(String(tools[0].id));
    }
  }, [assignmentToolId, tools]);

  useEffect(() => {
    if (!agentRoleTarget && agents.length) {
      setAgentRoleTarget(String(agents[0].id));
    }
  }, [agentRoleTarget, agents]);

  useEffect(() => {
    if (!agentRoleValue && roles.length) {
      setAgentRoleValue(String(roles[0].id));
    }
  }, [agentRoleValue, roles]);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const matchesQuery = (value: string) => !normalizedQuery || value.toLowerCase().includes(normalizedQuery);
  const matchesStatus = (active: boolean) => statusFilter === "all" || (statusFilter === "active" && active) || (statusFilter === "inactive" && !active);

  const filteredUsers = users.filter((item) => {
    const searchable = [item.username, item.email, item.first_name, item.last_name, item.roles.join(" ")].join(" ");
    return matchesQuery(searchable) && matchesStatus(item.active);
  });
  const filteredRoles = roles.filter((item) => matchesQuery([item.name, item.description].join(" ")));
  const filteredAgents = agents.filter((item) => {
    const searchable = [item.name, item.slug, item.description, item.provider, item.model, item.roles?.join(" ") ?? ""].join(" ");
    return matchesQuery(searchable) && matchesStatus(item.active);
  });
  const filteredTools = tools.filter((item) => {
    const searchable = [item.name, item.slug, item.description, item.tool_type].join(" ");
    return matchesQuery(searchable) && matchesStatus(item.active);
  });
  const filteredConversations = conversations.filter((item) => {
    const searchable = [item.title, item.user_username, item.agent_name, String(item.message_count)].join(" ");
    const archiveMatches =
      conversationArchivedFilter === "all" ||
      (conversationArchivedFilter === "archived" && item.archived) ||
      (conversationArchivedFilter === "active" && !item.archived);
    const userMatches = !conversationUserFilter || item.user_username.toLowerCase().includes(conversationUserFilter.trim().toLowerCase());
    const agentMatches = !conversationAgentFilter || item.agent_name.toLowerCase().includes(conversationAgentFilter.trim().toLowerCase());
    const createdAt = item.created_at ? new Date(item.created_at) : null;
    const fromMatches = !conversationDateFrom || (createdAt ? createdAt >= new Date(`${conversationDateFrom}T00:00:00`) : false);
    const toMatches = !conversationDateTo || (createdAt ? createdAt <= new Date(`${conversationDateTo}T23:59:59.999`) : false);
    return matchesQuery(searchable) && archiveMatches && userMatches && agentMatches && fromMatches && toMatches;
  });
  const filteredAudit = audit.filter((item) => {
    const searchable = [item.action, item.status, item.request_summary, item.result_summary, String(item.user_id ?? ""), String(item.agent_id ?? ""), String(item.tool_id ?? "")].join(" ");
    return matchesQuery(searchable);
  });

  async function refreshWithNotice(message: string) {
    setNotice({ kind: "success", text: message });
    await loadAll();
  }

  async function loadSelectedAgentDetail(agentId: number) {
    const detail = await getAdminAgent(agentId);
    setSelectedAgentDetail(detail);
    return detail;
  }

  async function loadSelectedConversationMessages(conversationId: number) {
    const messages = await getAdminConversationMessages(conversationId);
    setConversationMessages(messages);
    return messages;
  }

  async function selectConversation(item: ConversationAdmin) {
    setSelectedConversation(item);
    await loadSelectedConversationMessages(item.id);
    setActiveTab("conversations");
  }

  function beginEditUser(item: AdminUser) {
    setEditingUserId(item.id);
    setActiveTab("users");
    setUserForm({
      username: item.username,
      email: item.email,
      password: "Demo1234!",
      first_name: item.first_name,
      last_name: item.last_name,
      active: item.active,
      is_superadmin: item.is_superadmin,
      roleIds: roles.filter((role) => item.roles.includes(role.name)).map((role) => role.id)
    });
  }

  function beginEditRole(item: Role) {
    setEditingRoleId(item.id);
    setActiveTab("roles");
    setRoleForm({ name: item.name, description: item.description });
  }

  async function beginEditAgent(item: Agent) {
    setEditingAgentId(item.id);
    setActiveTab("agents");
    try {
      const detail = await loadSelectedAgentDetail(item.id);
      setAgentForm({
        name: detail.name,
        slug: detail.slug,
        description: detail.description,
        system_prompt: detail.system_prompt,
        provider: detail.provider,
        model: detail.model,
        temperature: String(detail.temperature),
        active: detail.active
      });
    } catch {
      setSelectedAgentDetail(null);
      setAgentForm({
        name: item.name,
        slug: item.slug,
        description: item.description,
        system_prompt: "",
        provider: item.provider,
        model: item.model,
        temperature: String(item.temperature),
        active: item.active
      });
    }
  }

  function beginEditTool(item: Tool) {
    setEditingToolId(item.id);
    setActiveTab("tools");
    setToolForm({
      name: item.name,
      slug: item.slug,
      description: item.description,
      tool_type: item.tool_type,
      configuration: JSON.stringify(item.configuration ?? {}, null, 2),
      active: item.active
    });
  }

  async function saveUser() {
    setSaving(true);
    setNotice(null);
    try {
      if (editingUserId) {
        await updateAdminUser(editingUserId, {
          first_name: userForm.first_name,
          last_name: userForm.last_name,
          active: userForm.active,
          is_superadmin: userForm.is_superadmin,
          role_ids: userForm.roleIds
        });
        setNotice({ kind: "success", text: "Usuario actualizado" });
      } else {
        await createAdminUser({
          username: userForm.username,
          email: userForm.email,
          password: userForm.password,
          first_name: userForm.first_name,
          last_name: userForm.last_name,
          active: userForm.active,
          is_superadmin: userForm.is_superadmin,
          role_ids: userForm.roleIds
        });
        setNotice({ kind: "success", text: "Usuario creado" });
      }
      setEditingUserId(null);
      setUserForm(emptyUserForm());
      await loadAll();
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo guardar el usuario" });
    } finally {
      setSaving(false);
    }
  }

  async function saveRole() {
    setSaving(true);
    setNotice(null);
    try {
      if (editingRoleId) {
        await updateAdminRole(editingRoleId, roleForm);
        setNotice({ kind: "success", text: "Rol actualizado" });
      } else {
        await createAdminRole(roleForm);
        setNotice({ kind: "success", text: "Rol creado" });
      }
      setEditingRoleId(null);
      setRoleForm(emptyRoleForm());
      await loadAll();
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo guardar el rol" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteRole(item: Role) {
    if (!window.confirm(`Borrar rol ${item.name}?`)) {
      return;
    }
    setSaving(true);
    try {
      await deleteAdminRole(item.id);
      if (editingRoleId === item.id) {
        resetRoleForm();
      }
      await refreshWithNotice("Rol eliminado");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo eliminar el rol" });
    } finally {
      setSaving(false);
    }
  }

  async function saveAgent() {
    setSaving(true);
    setNotice(null);
    try {
      const payload = {
        name: agentForm.name,
        slug: agentForm.slug,
        description: agentForm.description,
        system_prompt: agentForm.system_prompt,
        provider: agentForm.provider,
        model: agentForm.model,
        temperature: Number(agentForm.temperature),
        active: agentForm.active
      };
      if (editingAgentId) {
        await updateAdminAgent(editingAgentId, payload);
        setNotice({ kind: "success", text: "Agente actualizado" });
      } else {
        await createAdminAgent(payload);
        setNotice({ kind: "success", text: "Agente creado" });
      }
      setEditingAgentId(null);
      setAgentForm(emptyAgentForm());
      await loadAll();
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo guardar el agente" });
    } finally {
      setSaving(false);
    }
  }

  async function saveTool() {
    setSaving(true);
    setNotice(null);
    try {
      const parsedConfiguration = toolForm.configuration.trim() ? JSON.parse(toolForm.configuration) : {};
      const payload = {
        name: toolForm.name,
        slug: toolForm.slug,
        description: toolForm.description,
        tool_type: toolForm.tool_type,
        configuration: parsedConfiguration as Record<string, unknown>,
        active: toolForm.active
      };
      if (editingToolId) {
        await updateAdminTool(editingToolId, payload);
        setNotice({ kind: "success", text: "Herramienta actualizada" });
      } else {
        await createAdminTool(payload);
        setNotice({ kind: "success", text: "Herramienta creada" });
      }
      setEditingToolId(null);
      setToolForm(emptyToolForm());
      await loadAll();
    } catch (error) {
      setNotice({
        kind: "error",
        text: error instanceof SyntaxError ? "La configuración JSON no es válida" : error instanceof Error ? error.message : "No se pudo guardar la herramienta"
      });
    } finally {
      setSaving(false);
    }
  }

  async function toggleUserActive(item: AdminUser) {
    setSaving(true);
    try {
      await updateAdminUser(item.id, { active: !item.active });
      await refreshWithNotice(`Usuario ${item.active ? "desactivado" : "activado"}`);
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo actualizar el usuario" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteUser(item: AdminUser) {
    if (!window.confirm(`Borrar usuario ${item.username}?`)) {
      return;
    }
    setSaving(true);
    try {
      await deleteAdminUser(item.id);
      if (editingUserId === item.id) {
        resetUserForm();
      }
      await refreshWithNotice("Usuario eliminado");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo eliminar el usuario" });
    } finally {
      setSaving(false);
    }
  }

  async function toggleAgentActive(item: Agent) {
    setSaving(true);
    try {
      await updateAdminAgent(item.id, { active: !item.active });
      await refreshWithNotice(`Agente ${item.active ? "desactivado" : "activado"}`);
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo actualizar el agente" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteAgent(item: Agent) {
    if (!window.confirm(`Borrar agente ${item.name}?`)) {
      return;
    }
    setSaving(true);
    try {
      await deleteAdminAgent(item.id);
      if (editingAgentId === item.id) {
        resetAgentForm();
      }
      await refreshWithNotice("Agente eliminado");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo eliminar el agente" });
    } finally {
      setSaving(false);
    }
  }

  async function toggleToolActive(item: Tool) {
    setSaving(true);
    try {
      await updateAdminTool(item.id, { active: !item.active });
      await refreshWithNotice(`Herramienta ${item.active ? "desactivada" : "activada"}`);
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo actualizar la herramienta" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteTool(item: Tool) {
    if (!window.confirm(`Borrar herramienta ${item.name}?`)) {
      return;
    }
    setSaving(true);
    try {
      await deleteAdminTool(item.id);
      if (editingToolId === item.id) {
        resetToolForm();
      }
      await refreshWithNotice("Herramienta eliminada");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo eliminar la herramienta" });
    } finally {
      setSaving(false);
    }
  }

  async function deleteConversation(item: ConversationAdmin) {
    if (!window.confirm(`Borrar conversación "${item.title}"?`)) {
      return;
    }
    setSaving(true);
    try {
      await deleteAdminConversation(item.id);
      if (selectedConversation?.id === item.id) {
        setSelectedConversation(null);
        setConversationMessages([]);
      }
      await refreshWithNotice("Conversación eliminada");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo eliminar la conversación" });
    } finally {
      setSaving(false);
    }
  }

  async function toggleConversationArchived(item: ConversationAdmin) {
    setSaving(true);
    try {
      await updateAdminConversation(item.id, !item.archived);
      if (selectedConversation?.id === item.id) {
        setSelectedConversation({ ...item, archived: !item.archived });
      }
      await refreshWithNotice(`Conversación ${item.archived ? "restaurada" : "archivada"}`);
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo actualizar la conversación" });
    } finally {
      setSaving(false);
    }
  }

  function exportJson(filename: string, data: unknown) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  async function exportConversation(item: ConversationAdmin) {
    const messages = item.id === selectedConversation?.id ? conversationMessages : await getAdminConversationMessages(item.id);
    exportJson(`conversation-${item.id}.json`, {
      conversation: item,
      messages
    });
  }

  function exportFilteredConversations() {
    exportJson("conversations-filtered.json", {
      filters: {
        query: searchQuery,
        user: conversationUserFilter,
        agent: conversationAgentFilter,
        archived: conversationArchivedFilter,
        date_from: conversationDateFrom,
        date_to: conversationDateTo
      },
      conversations: filteredConversations
    });
  }

  async function doAssignUserRole() {
    if (!editingUserId || userForm.roleIds.length === 0) {
      return;
    }
    setSaving(true);
    try {
      for (const roleId of userForm.roleIds) {
        await assignRoleToUser(editingUserId, roleId);
      }
      await refreshWithNotice("Roles asignados al usuario");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudieron asignar los roles" });
    } finally {
      setSaving(false);
    }
  }

  async function doAssignAgentRole() {
    if (!agentRoleTarget || !agentRoleValue) {
      return;
    }
    setSaving(true);
    try {
      await assignRoleToAgent(Number(agentRoleTarget), Number(agentRoleValue));
      if (editingAgentId) {
        await loadSelectedAgentDetail(editingAgentId);
      }
      await refreshWithNotice("Rol asignado al agente");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo asignar el rol al agente" });
    } finally {
      setSaving(false);
    }
  }

  async function doAssignToolToAgent() {
    if (!assignmentAgentId || !assignmentToolId) {
      return;
    }
    setSaving(true);
    try {
      await assignToolToAgent(Number(assignmentAgentId), Number(assignmentToolId), assignmentPermission);
      if (editingAgentId) {
        await loadSelectedAgentDetail(editingAgentId);
      }
      await refreshWithNotice("Herramienta asignada al agente");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo asignar la herramienta" });
    } finally {
      setSaving(false);
    }
  }

  async function removeRoleFromSelectedAgent(roleId: number) {
    if (!editingAgentId) {
      return;
    }
    setSaving(true);
    try {
      await unassignRoleFromAgent(editingAgentId, roleId);
      await loadSelectedAgentDetail(editingAgentId);
      await refreshWithNotice("Rol quitado del agente");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo quitar el rol" });
    } finally {
      setSaving(false);
    }
  }

  async function removeToolFromSelectedAgent(toolId: number) {
    if (!editingAgentId) {
      return;
    }
    setSaving(true);
    try {
      await unassignToolFromAgent(editingAgentId, toolId);
      await loadSelectedAgentDetail(editingAgentId);
      await refreshWithNotice("Herramienta quitada del agente");
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "No se pudo quitar la herramienta" });
    } finally {
      setSaving(false);
    }
  }

  function resetUserForm() {
    setEditingUserId(null);
    setUserForm(emptyUserForm());
  }

  function resetRoleForm() {
    setEditingRoleId(null);
    setRoleForm(emptyRoleForm());
  }

  function resetAgentForm() {
    setEditingAgentId(null);
    setAgentForm(emptyAgentForm());
    setSelectedAgentDetail(null);
  }

  function resetToolForm() {
    setEditingToolId(null);
    setToolForm(emptyToolForm());
  }

  const counts = {
    users: users.length,
    roles: roles.length,
    agents: agents.length,
    tools: tools.length,
    conversations: conversations.length,
    logs: audit.length
  };
  const conversationStats = {
    total: conversations.length,
    active: conversations.filter((item) => !item.archived).length,
    archived: conversations.filter((item) => item.archived).length,
    messages: conversations.reduce((sum, item) => sum + item.message_count, 0)
  };

  if (loading) {
    return <div className="min-h-screen bg-ink-950 px-6 py-8 text-white">Cargando administración...</div>;
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#07111f_0%,_#0d1726_100%)] px-4 py-6 text-ink-100">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-panel backdrop-blur">
          <div className="text-xs uppercase tracking-[0.35em] text-accent-300">Administración</div>
          <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold">Panel interno</h1>
              <p className="mt-2 text-sm text-ink-200">Sesión activa: {userName}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              <SummaryCard label="Usuarios" value={counts.users} onClick={() => setActiveTab("users")} />
              <SummaryCard label="Roles" value={counts.roles} onClick={() => setActiveTab("roles")} />
              <SummaryCard label="Agentes" value={counts.agents} onClick={() => setActiveTab("agents")} />
              <SummaryCard label="Tools" value={counts.tools} onClick={() => setActiveTab("tools")} />
              <SummaryCard label="Auditoría" value={counts.logs} onClick={() => setActiveTab("audit")} />
            </div>
          </div>
          {notice ? <NoticeBanner kind={notice.kind} text={notice.text} /> : null}
        </header>

        <div className="rounded-3xl border border-white/10 bg-white/5 p-4 shadow-panel backdrop-blur">
          <div className="grid gap-3 md:grid-cols-[1fr,220px,auto]">
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">Buscar</div>
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Usuario, agente, herramienta, rol o acción..."
                className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-ink-500 focus:border-accent-400"
              />
            </label>
            <label className="block">
              <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">Estado</div>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as "all" | "active" | "inactive")}
                className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition focus:border-accent-400"
              >
                <option value="all">Todos</option>
                <option value="active">Activos</option>
                <option value="inactive">Inactivos</option>
              </select>
            </label>
            <div className="flex items-end">
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setStatusFilter("all");
                }}
                className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

        <nav className="flex flex-wrap gap-2">
          <TabButton active={activeTab === "overview"} onClick={() => setActiveTab("overview")}>
            Resumen
          </TabButton>
          <TabButton active={activeTab === "users"} onClick={() => setActiveTab("users")}>
            Usuarios
          </TabButton>
          <TabButton active={activeTab === "roles"} onClick={() => setActiveTab("roles")}>
            Roles
          </TabButton>
          <TabButton active={activeTab === "agents"} onClick={() => setActiveTab("agents")}>
            Agentes
          </TabButton>
          <TabButton active={activeTab === "tools"} onClick={() => setActiveTab("tools")}>
            Herramientas
          </TabButton>
          <TabButton active={activeTab === "conversations"} onClick={() => setActiveTab("conversations")}>
            Conversaciones
          </TabButton>
          <TabButton active={activeTab === "audit"} onClick={() => setActiveTab("audit")}>
            Auditoría
          </TabButton>
        </nav>

        {activeTab === "overview" ? (
          <div className="grid gap-6 xl:grid-cols-2">
            <InfoCard
              title="Usuario administrador"
              description="Acceso completo al panel y administración de permisos."
              actionLabel="Ir a usuarios"
              onAction={() => setActiveTab("users")}
            >
              <span className="text-sm text-ink-200">{userName}</span>
            </InfoCard>
            <InfoCard
              title="Asignaciones rápidas"
              description="El panel permite crear y editar usuarios, roles, agentes y herramientas."
              actionLabel="Ir a agentes"
              onAction={() => setActiveTab("agents")}
            >
              <div className="flex flex-wrap gap-2 text-xs text-ink-200">
                <Pill>RBAC</Pill>
                <Pill>Permisos</Pill>
                <Pill>Tools</Pill>
                <Pill>Auditoría</Pill>
              </div>
            </InfoCard>
            <ActionCard title="Crear usuario" onClick={() => setActiveTab("users")} buttonLabel="Abrir formulario" count={counts.users} />
            <ActionCard title="Crear rol" onClick={() => setActiveTab("roles")} buttonLabel="Abrir formulario" count={counts.roles} />
            <ActionCard title="Crear agente" onClick={() => setActiveTab("agents")} buttonLabel="Abrir formulario" count={counts.agents} />
            <ActionCard title="Crear herramienta" onClick={() => setActiveTab("tools")} buttonLabel="Abrir formulario" count={counts.tools} />
            <ActionCard title="Ver conversaciones" onClick={() => setActiveTab("conversations")} buttonLabel="Abrir listado" count={counts.conversations} />
          </div>
        ) : null}

        {activeTab === "users" ? (
          <div className="grid gap-6 xl:grid-cols-[360px,1fr]">
            <FormCard
              title={editingUserId ? "Editar usuario" : "Crear usuario"}
              subtitle="Los roles se asignan al guardar el usuario."
              footer={
                <div className="flex gap-2">
                  <button disabled={saving} onClick={saveUser} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                    {editingUserId ? "Guardar cambios" : "Crear usuario"}
                  </button>
                  <button disabled={saving} onClick={resetUserForm} className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50">
                    Limpiar
                  </button>
                </div>
              }
            >
              <TextInput label="Usuario" value={userForm.username} onChange={(value) => setUserForm({ ...userForm, username: value })} disabled={Boolean(editingUserId)} />
              <TextInput label="Email" value={userForm.email} onChange={(value) => setUserForm({ ...userForm, email: value })} />
              <TextInput label="Contraseña" type="password" value={userForm.password} onChange={(value) => setUserForm({ ...userForm, password: value })} disabled={Boolean(editingUserId)} />
              <div className="grid grid-cols-2 gap-3">
                <TextInput label="Nombre" value={userForm.first_name} onChange={(value) => setUserForm({ ...userForm, first_name: value })} />
                <TextInput label="Apellido" value={userForm.last_name} onChange={(value) => setUserForm({ ...userForm, last_name: value })} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <ToggleField label="Activo" checked={userForm.active} onChange={(checked) => setUserForm({ ...userForm, active: checked })} />
                <ToggleField label="Superadmin" checked={userForm.is_superadmin} onChange={(checked) => setUserForm({ ...userForm, is_superadmin: checked })} />
              </div>
              <MultiSelectField
                label="Roles"
                value={userForm.roleIds.map(String)}
                options={roles.map((role) => ({ label: role.name, value: String(role.id) }))}
                onChange={(values) => setUserForm({ ...userForm, roleIds: values.map(Number) })}
              />
              <div className="flex flex-wrap gap-2">
                {userForm.roleIds.length ? (
                  userForm.roleIds.map((roleId) => {
                    const role = roles.find((item) => item.id === roleId);
                    return (
                      <button
                        key={roleId}
                        type="button"
                        disabled={saving}
                        onClick={() =>
                          setUserForm({
                            ...userForm,
                            roleIds: userForm.roleIds.filter((item) => item !== roleId)
                          })
                        }
                        className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-ink-100 hover:bg-black/30 disabled:opacity-50"
                      >
                        {role?.name ?? `Rol ${roleId}`} x
                      </button>
                    );
                  })
                ) : (
                  <span className="text-xs text-ink-300">Sin roles seleccionados.</span>
                )}
              </div>
              {editingUserId ? (
                <button disabled={saving} onClick={() => void doAssignUserRole()} className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50">
                  Reasignar roles del usuario
                </button>
              ) : null}
            </FormCard>

            <DataTable
              title="Usuarios"
              columns={["Usuario", "Email", "Rol", "Estado", "Tipo", "Acciones"]}
              rows={filteredUsers.map((item) => [
                item.username,
                item.email,
                item.roles.join(", ") || "Sin roles",
                item.active ? "Activo" : "Inactivo",
                item.is_superadmin ? "Superadmin" : "Normal",
                <RowActions
                  key={item.id}
                  onEdit={() => beginEditUser(item)}
                  onToggle={() => void toggleUserActive(item)}
                  onDelete={() => void deleteUser(item)}
                  toggleLabel={item.active ? "Desactivar" : "Activar"}
                />
              ])}
            />
          </div>
        ) : null}

        {activeTab === "roles" ? (
          <div className="grid gap-6 xl:grid-cols-[360px,1fr]">
            <FormCard
              title={editingRoleId ? "Editar rol" : "Crear rol"}
              subtitle="Los roles se usan para permitir agentes y usuarios."
              footer={
                <div className="flex gap-2">
                  <button disabled={saving} onClick={saveRole} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                    {editingRoleId ? "Guardar cambios" : "Crear rol"}
                  </button>
                  <button disabled={saving} onClick={resetRoleForm} className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50">
                    Limpiar
                  </button>
                </div>
              }
            >
              <TextInput label="Nombre" value={roleForm.name} onChange={(value) => setRoleForm({ ...roleForm, name: value })} />
              <TextArea label="Descripción" value={roleForm.description} onChange={(value) => setRoleForm({ ...roleForm, description: value })} rows={4} />
            </FormCard>

            <DataTable
              title="Roles"
              columns={["Nombre", "Descripción", "Acciones"]}
              rows={filteredRoles.map((item) => [
                item.name,
                item.description || "Sin descripción",
                <RowActions key={item.id} onEdit={() => beginEditRole(item)} onDelete={() => void deleteRole(item)} editLabel="Editar rol" onToggle={undefined} />
              ])}
            />
          </div>
        ) : null}

        {activeTab === "agents" ? (
          <div className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-[420px,1fr]">
              <FormCard
                title={editingAgentId ? "Editar agente" : "Crear agente"}
                subtitle="El backend valida los permisos de herramientas."
                footer={
                  <div className="flex gap-2">
                    <button disabled={saving} onClick={saveAgent} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                      {editingAgentId ? "Guardar cambios" : "Crear agente"}
                    </button>
                    <button disabled={saving} onClick={resetAgentForm} className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50">
                      Limpiar
                    </button>
                  </div>
                }
              >
                <TextInput label="Nombre" value={agentForm.name} onChange={(value) => setAgentForm({ ...agentForm, name: value })} />
                <TextInput label="Slug" value={agentForm.slug} onChange={(value) => setAgentForm({ ...agentForm, slug: value })} />
                <TextInput label="Proveedor" value={agentForm.provider} onChange={(value) => setAgentForm({ ...agentForm, provider: value })} />
                <TextInput label="Modelo" value={agentForm.model} onChange={(value) => setAgentForm({ ...agentForm, model: value })} />
                <TextInput label="Temperatura" value={agentForm.temperature} onChange={(value) => setAgentForm({ ...agentForm, temperature: value })} />
                <ToggleField label="Activo" checked={agentForm.active} onChange={(checked) => setAgentForm({ ...agentForm, active: checked })} />
                <TextArea label="Descripción" value={agentForm.description} onChange={(value) => setAgentForm({ ...agentForm, description: value })} rows={3} />
                <TextArea label="System prompt" value={agentForm.system_prompt} onChange={(value) => setAgentForm({ ...agentForm, system_prompt: value })} rows={5} />
              </FormCard>

              <div className="space-y-6">
                <FormCard
                  title="Asignar rol a agente"
                  subtitle="Asocia un rol existente a un agente para habilitarlo."
                  footer={
                    <button disabled={saving} onClick={() => void doAssignAgentRole()} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                      Asignar rol
                    </button>
                  }
                  >
                  <SelectField
                    label="Agente"
                    value={agentRoleTarget}
                    options={agents.map((item) => ({ label: item.name, value: String(item.id) }))}
                    onChange={setAgentRoleTarget}
                  />
                  <SelectField
                    label="Rol"
                    value={agentRoleValue}
                    options={roles.map((item) => ({ label: item.name, value: String(item.id) }))}
                    onChange={setAgentRoleValue}
                  />
                </FormCard>

                {editingAgentId && selectedAgentDetail ? (
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
                    <div className="text-sm text-ink-200">Asignaciones actuales</div>
                    <div className="mt-3 space-y-4">
                      <div>
                        <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">Roles</div>
                        <div className="flex flex-wrap gap-2">
                          {selectedAgentDetail.roles.length ? (
                            selectedAgentDetail.roles.map((role) => (
                              <button
                                key={role.id}
                                disabled={saving}
                                onClick={() => void removeRoleFromSelectedAgent(role.id)}
                                className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-ink-100 hover:bg-black/30 disabled:opacity-50"
                              >
                                {role.name} x
                              </button>
                            ))
                          ) : (
                            <span className="text-xs text-ink-300">Sin roles asignados.</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">Herramientas</div>
                        <div className="flex flex-wrap gap-2">
                          {selectedAgentDetail.tools.length ? (
                            selectedAgentDetail.tools.map((tool) => (
                              <button
                                key={tool.id}
                                disabled={saving}
                                onClick={() => void removeToolFromSelectedAgent(tool.id)}
                                className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs text-ink-100 hover:bg-black/30 disabled:opacity-50"
                              >
                                {tool.name} x
                              </button>
                            ))
                          ) : (
                            <span className="text-xs text-ink-300">Sin herramientas asignadas.</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}

                <DataTable
                  title="Agentes"
                  columns={["Nombre", "Slug", "Roles", "Tools", "Estado", "Acciones"]}
                  rows={filteredAgents.map((item) => [
                    item.name,
                    item.slug,
                    item.roles?.join(", ") || `${item.role_count} rol(es)`,
                    String(item.tool_count),
                    item.active ? "Activo" : "Inactivo",
                    <RowActions
                      key={item.id}
                      onEdit={() => void beginEditAgent(item)}
                      onToggle={() => void toggleAgentActive(item)}
                      onDelete={() => void deleteAgent(item)}
                      toggleLabel={item.active ? "Desactivar" : "Activar"}
                    />
                  ])}
                />
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "tools" ? (
          <div className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-[420px,1fr]">
              <FormCard
                title={editingToolId ? "Editar herramienta" : "Crear herramienta"}
                subtitle="La configuración se guarda como JSON."
                footer={
                  <div className="flex gap-2">
                    <button disabled={saving} onClick={saveTool} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                      {editingToolId ? "Guardar cambios" : "Crear herramienta"}
                    </button>
                    <button disabled={saving} onClick={resetToolForm} className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50">
                      Limpiar
                    </button>
                  </div>
                }
              >
                <TextInput label="Nombre" value={toolForm.name} onChange={(value) => setToolForm({ ...toolForm, name: value })} />
                <TextInput label="Slug" value={toolForm.slug} onChange={(value) => setToolForm({ ...toolForm, slug: value })} />
                <TextInput label="Tipo de tool" value={toolForm.tool_type} onChange={(value) => setToolForm({ ...toolForm, tool_type: value })} />
                <ToggleField label="Activo" checked={toolForm.active} onChange={(checked) => setToolForm({ ...toolForm, active: checked })} />
                <TextArea label="Descripción" value={toolForm.description} onChange={(value) => setToolForm({ ...toolForm, description: value })} rows={3} />
                <TextArea label="Configuración JSON" value={toolForm.configuration} onChange={(value) => setToolForm({ ...toolForm, configuration: value })} rows={8} />
              </FormCard>

              <div className="space-y-6">
                <FormCard
                  title="Asignar herramienta a agente"
                  subtitle="Define qué agente puede usar la herramienta y con qué permiso."
                  footer={
                    <button disabled={saving} onClick={() => void doAssignToolToAgent()} className="rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-50">
                      Asignar herramienta
                    </button>
                  }
                >
                  <SelectField
                    label="Agente"
                    value={assignmentAgentId}
                    options={agents.map((item) => ({ label: item.name, value: String(item.id) }))}
                    onChange={setAssignmentAgentId}
                  />
                  <SelectField
                    label="Herramienta"
                    value={assignmentToolId}
                    options={tools.map((item) => ({ label: item.name, value: String(item.id) }))}
                    onChange={setAssignmentToolId}
                  />
                  <SelectField
                    label="Nivel"
                    value={assignmentPermission}
                    options={[
                      { label: "read", value: "read" },
                      { label: "execute", value: "execute" },
                      { label: "write", value: "write" },
                      { label: "admin", value: "admin" }
                    ]}
                    onChange={setAssignmentPermission}
                  />
                </FormCard>

                <DataTable
                  title="Herramientas"
                  columns={["Nombre", "Slug", "Tipo", "Estado", "Acciones"]}
                  rows={filteredTools.map((item) => [
                    item.name,
                    item.slug,
                    item.tool_type,
                    item.active ? "Activa" : "Inactiva",
                    <RowActions
                      key={item.id}
                      onEdit={() => beginEditTool(item)}
                      onToggle={() => void toggleToolActive(item)}
                      onDelete={() => void deleteTool(item)}
                      toggleLabel={item.active ? "Desactivar" : "Activar"}
                    />
                  ])}
                />
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "conversations" ? (
          <div className="grid gap-6 xl:grid-cols-[380px,1fr]">
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <SummaryCard label="Total" value={conversationStats.total} onClick={() => setConversationArchivedFilter("all")} />
                <SummaryCard label="Archivadas" value={conversationStats.archived} onClick={() => setConversationArchivedFilter("archived")} />
                <SummaryCard label="Activas" value={conversationStats.active} onClick={() => setConversationArchivedFilter("active")} />
                <SummaryCard label="Mensajes" value={conversationStats.messages} onClick={() => setActiveTab("audit")} />
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
                <div className="text-lg font-semibold text-white">Conversaciones</div>
                <div className="mt-1 text-sm text-ink-200">Registro reciente por usuario y agente.</div>
                <div className="mt-4 grid gap-3">
                  <TextInput label="Buscar conversaciones" value={searchQuery} onChange={setSearchQuery} />
                  <TextInput label="Filtrar por usuario" value={conversationUserFilter} onChange={setConversationUserFilter} />
                  <TextInput label="Filtrar por agente" value={conversationAgentFilter} onChange={setConversationAgentFilter} />
                  <div className="grid grid-cols-2 gap-3">
                    <TextInput label="Desde" type="date" value={conversationDateFrom} onChange={setConversationDateFrom} />
                    <TextInput label="Hasta" type="date" value={conversationDateTo} onChange={setConversationDateTo} />
                  </div>
                  <SelectField
                    label="Estado"
                    value={conversationArchivedFilter}
                    options={[
                      { label: "Todas", value: "all" },
                      { label: "Activas", value: "active" },
                      { label: "Archivadas", value: "archived" }
                    ]}
                    onChange={(value) => setConversationArchivedFilter(value as "all" | "active" | "archived")}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      setConversationUserFilter("");
                      setConversationAgentFilter("");
                      setConversationArchivedFilter("all");
                      setConversationDateFrom("");
                      setConversationDateTo("");
                    }}
                    className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800"
                  >
                    Limpiar filtros
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {filteredConversations.length ? (
                  filteredConversations.map((item) => {
                    const isSelected = selectedConversation?.id === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => void selectConversation(item)}
                        className={`w-full rounded-2xl border p-4 text-left transition ${
                          isSelected ? "border-accent-400 bg-accent-500/10" : "border-white/10 bg-white/5 hover:bg-white/10"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold text-white">{item.title}</div>
                            <div className="mt-1 text-xs text-ink-300">
                              {item.user_username} · {item.agent_name}
                            </div>
                          </div>
                          <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-ink-200">
                            {item.message_count} msgs
                          </span>
                        </div>
                      </button>
                    );
                  })
                ) : (
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-sm text-ink-200">Sin conversaciones para mostrar.</div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
                {selectedConversation ? (
                  <>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-lg font-semibold text-white">{selectedConversation.title}</div>
                        <div className="mt-1 text-sm text-ink-200">
                          Usuario: {selectedConversation.user_username} · Agente: {selectedConversation.agent_name}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <Pill>{selectedConversation.archived ? "Archivada" : "Activa"}</Pill>
                          <Pill>{selectedConversation.message_count} mensajes</Pill>
                          <Pill>{selectedConversation.created_at ? new Date(selectedConversation.created_at).toLocaleDateString("es-AR") : "Sin fecha"}</Pill>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={saving}
                          onClick={() => void toggleConversationArchived(selectedConversation)}
                          className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
                        >
                          {selectedConversation.archived ? "Restaurar" : "Archivar"}
                        </button>
                        <button
                          type="button"
                          disabled={saving}
                          onClick={() => void exportConversation(selectedConversation)}
                          className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
                        >
                          Exportar JSON
                        </button>
                        <button
                          type="button"
                          disabled={saving}
                          onClick={() => void deleteConversation(selectedConversation)}
                          className="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm font-semibold text-rose-100 hover:bg-rose-500/20 disabled:opacity-50"
                        >
                          Borrar conversación
                        </button>
                      </div>
                    </div>
                    <div className="mt-4 text-xs uppercase tracking-[0.2em] text-ink-300">Mensajes</div>
                    <div className="mt-4 space-y-3">
                      {conversationMessages.length ? (
                        conversationMessages.map((message) => (
                          <div
                            key={message.id}
                            className={`rounded-2xl border px-4 py-3 ${
                              message.role === "assistant" ? "border-accent-500/20 bg-accent-500/10" : "border-white/10 bg-black/10"
                            }`}
                          >
                            <div className="text-xs uppercase tracking-[0.2em] text-ink-300">{message.role}</div>
                            <div className="mt-2 whitespace-pre-wrap text-sm text-white">{message.content}</div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-ink-200">
                          Esta conversación todavía no tiene mensajes cargados.
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-sm text-ink-200">
                    Seleccioná una conversación para ver los mensajes y opciones de administración.
                  </div>
                )}
              </div>

                <DataTable
                title="Detalle de conversaciones"
                columns={["Título", "Usuario", "Agente", "Mensajes", "Estado", "Fecha", "Acciones"]}
                rows={filteredConversations.map((item) => [
                  item.title,
                  item.user_username,
                  item.agent_name,
                  String(item.message_count),
                  item.archived ? "Archivada" : "Activa",
                  item.created_at ? new Date(item.created_at).toLocaleString("es-AR") : "-",
                  <div className="flex flex-wrap gap-2" key={item.id}>
                    <button
                      type="button"
                      onClick={() => void selectConversation(item)}
                      className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs font-semibold text-white hover:bg-ink-800"
                    >
                      Ver mensajes
                    </button>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void toggleConversationArchived(item)}
                      className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
                    >
                      {item.archived ? "Restaurar" : "Archivar"}
                    </button>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void exportConversation(item)}
                      className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
                    >
                      Exportar
                    </button>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void deleteConversation(item)}
                      className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/20 disabled:opacity-50"
                    >
                      Borrar
                    </button>
                  </div>
                ])}
              />
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={exportFilteredConversations}
                  className="rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm font-semibold text-white hover:bg-ink-800"
                >
                  Exportar listado filtrado
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === "audit" ? (
          <DataTable
            title="Auditoría reciente"
            columns={["Acción", "Estado", "Usuario", "Resumen", "Fecha"]}
            rows={filteredAudit.map((item) => [
              item.action,
              item.status,
              item.user_id ? String(item.user_id) : "-",
              item.request_summary.slice(0, 80),
              new Date(item.created_at).toLocaleString("es-AR")
            ])}
          />
        ) : null}
      </div>
    </div>
  );
}

function NoticeBanner({ kind, text }: Notice) {
  const styles =
    kind === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
      : kind === "error"
        ? "border-rose-500/30 bg-rose-500/10 text-rose-100"
        : "border-sky-500/30 bg-sky-500/10 text-sky-100";
  return <div className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${styles}`}>{text}</div>;
}

function TabButton({
  active,
  onClick,
  children
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-4 py-2 text-sm font-semibold transition ${
        active ? "border-accent-400 bg-accent-500 text-white" : "border-white/10 bg-white/5 text-ink-100 hover:bg-white/10"
      }`}
    >
      {children}
    </button>
  );
}

function SummaryCard({ label, value, onClick }: { label: string; value: number; onClick: () => void }) {
  return (
    <button onClick={onClick} className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3 text-left hover:bg-black/20">
      <div className="text-[11px] uppercase tracking-[0.35em] text-ink-300">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </button>
  );
}

function InfoCard({
  title,
  description,
  actionLabel,
  onAction,
  children
}: {
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
  children: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
      <div className="text-sm text-ink-200">{title}</div>
      <div className="mt-2 text-base text-white">{description}</div>
      <div className="mt-4">{children}</div>
      <button onClick={onAction} className="mt-5 rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600">
        {actionLabel}
      </button>
    </div>
  );
}

function ActionCard({
  title,
  count,
  buttonLabel,
  onClick
}: {
  title: string;
  count: number;
  buttonLabel: string;
  onClick: () => void;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
      <div className="text-sm text-ink-200">{title}</div>
      <div className="mt-3 text-3xl font-semibold">{count}</div>
      <button onClick={onClick} className="mt-5 w-full rounded-xl bg-accent-500 px-4 py-3 text-sm font-semibold text-white hover:bg-accent-600">
        {buttonLabel}
      </button>
    </div>
  );
}

function FormCard({
  title,
  subtitle,
  footer,
  children
}: {
  title: string;
  subtitle: string;
  footer: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-panel backdrop-blur">
      <div className="text-lg font-semibold text-white">{title}</div>
      <div className="mt-1 text-sm text-ink-200">{subtitle}</div>
      <div className="mt-5 space-y-4">{children}</div>
      <div className="mt-5">{footer}</div>
    </div>
  );
}

function DataTable({
  title,
  columns,
  rows
}: {
  title: string;
  columns: string[];
  rows: (string | ReactNode)[][];
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-panel backdrop-blur">
      <div className="border-b border-white/10 px-5 py-4 text-sm font-semibold text-white">{title}</div>
      <div className="overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-xs uppercase tracking-[0.2em] text-ink-300">
            <tr>
              {columns.map((column) => (
                <th key={column} className="px-5 py-3 font-medium">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row, rowIndex) => (
                <tr key={`${title}-${rowIndex}`} className="border-b border-white/5 last:border-b-0">
                  {row.map((cell, cellIndex) => (
                    <td key={`${title}-${rowIndex}-${cellIndex}`} className="px-5 py-3 align-top text-ink-100">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-5 py-6 text-ink-200" colSpan={columns.length}>
                  Sin datos
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RowActions({
  onEdit,
  onToggle,
  onDelete,
  toggleLabel = "Cambiar estado",
  editLabel = "Editar"
}: {
  onEdit: () => void;
  onToggle?: () => void;
  onDelete?: () => void;
  toggleLabel?: string;
  editLabel?: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <button onClick={onEdit} className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs font-semibold text-white hover:bg-ink-800">
        {editLabel}
      </button>
      {onToggle ? (
        <button onClick={onToggle} className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs font-semibold text-white hover:bg-ink-800">
          {toggleLabel}
        </button>
      ) : null}
      {onDelete ? (
        <button onClick={onDelete} className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/20">
          Borrar
        </button>
      ) : null}
    </div>
  );
}

function TextInput({
  label,
  value,
  onChange,
  type = "text",
  disabled = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  disabled?: boolean;
}) {
  return (
    <label className="block">
      <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">{label}</div>
      <input
        disabled={disabled}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-ink-500 focus:border-accent-400"
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  rows = 4
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}) {
  return (
    <label className="block">
      <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">{label}</div>
      <textarea
        rows={rows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-ink-500 focus:border-accent-400"
      />
    </label>
  );
}

function ToggleField({
  label,
  checked,
  onChange
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`rounded-xl border px-4 py-3 text-left text-sm transition ${
        checked ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100" : "border-white/10 bg-ink-900 text-ink-100 hover:bg-ink-800"
      }`}
    >
      {label}: {checked ? "Sí" : "No"}
    </button>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: { label: string; value: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">{label}</div>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition focus:border-accent-400"
      >
        {options.length ? (
          options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))
        ) : (
          <option value="">Sin opciones</option>
        )}
      </select>
    </label>
  );
}

function MultiSelectField({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string[];
  options: { label: string; value: string }[];
  onChange: (values: string[]) => void;
}) {
  return (
    <label className="block">
      <div className="mb-2 text-xs uppercase tracking-[0.2em] text-ink-300">{label}</div>
      <select
        multiple
        value={value}
        onChange={(event) => onChange(Array.from(event.target.selectedOptions).map((option) => option.value))}
        className="h-36 w-full rounded-xl border border-white/10 bg-ink-900 px-4 py-3 text-sm text-white outline-none transition focus:border-accent-400"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <p className="mt-2 text-xs text-ink-300">Podés seleccionar uno o varios roles.</p>
    </label>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1">{children}</span>;
}
