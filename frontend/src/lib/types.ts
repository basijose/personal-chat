export type UserPublic = {
  id: number;
  organization_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  active: boolean;
  is_superadmin: boolean;
  roles: string[];
};

export type Agent = {
  id: number;
  name: string;
  slug: string;
  description: string;
  provider: string;
  model: string;
  temperature: number;
  active: boolean;
  tool_count: number;
  role_count: number;
  roles?: string[];
};

export type Conversation = {
  id: number;
  organization_id: number;
  user_id: number;
  agent_id: number;
  title: string;
  archived: boolean;
  created_at?: string | null;
};

export type ConversationAdmin = {
  id: number;
  organization_id: number;
  user_id: number;
  user_username: string;
  agent_id: number;
  agent_name: string;
  title: string;
  archived: boolean;
  message_count: number;
  created_at?: string | null;
};

export type Message = {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system" | string;
  content: string;
  metadata: Record<string, unknown>;
  created_at?: string | null;
};

export type AdminUser = UserPublic;

export type Role = {
  id: number;
  name: string;
  description: string;
};

export type Tool = {
  id: number;
  name: string;
  slug: string;
  description: string;
  tool_type: string;
  active: boolean;
  configuration: Record<string, unknown>;
};

export type AgentDetail = Omit<Agent, "roles"> & {
  system_prompt: string;
  tools: Tool[];
  roles: Role[];
};

export type AuditLog = {
  id: number;
  organization_id: number | null;
  user_id: number | null;
  agent_id: number | null;
  tool_id: number | null;
  action: string;
  request_summary: string;
  result_summary: string;
  status: string;
  created_at: string;
};

export type AdminUserCreateInput = {
  organization_id?: number;
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  active: boolean;
  is_superadmin: boolean;
  role_ids: number[];
};

export type AdminUserUpdateInput = {
  first_name?: string;
  last_name?: string;
  active?: boolean;
  is_superadmin?: boolean;
  role_ids?: number[] | null;
};

export type RoleCreateInput = {
  name: string;
  description: string;
};

export type RoleUpdateInput = {
  name?: string;
  description?: string;
};

export type AgentCreateInput = {
  name: string;
  slug: string;
  description: string;
  system_prompt: string;
  provider: string;
  model: string;
  temperature: number;
  active: boolean;
};

export type AgentUpdateInput = Partial<AgentCreateInput>;

export type ToolCreateInput = {
  name: string;
  slug: string;
  description: string;
  tool_type: string;
  configuration: Record<string, unknown>;
  active: boolean;
};

export type ToolUpdateInput = Partial<ToolCreateInput>;
