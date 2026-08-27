# API

## Auth

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Agents and chat

- `GET /api/agents`
- `GET /api/agents/{agent_id}`
- `GET /api/conversations`
- `POST /api/conversations`
- `GET /api/conversations/{conversation_id}/messages`
- `POST /api/chat`

## Admin

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/roles`
- `POST /api/admin/roles`
- `PATCH /api/admin/roles/{role_id}`
- `POST /api/admin/users/{user_id}/roles/{role_id}`
- `GET /api/admin/agents`
- `POST /api/admin/agents`
- `PATCH /api/admin/agents/{agent_id}`
- `POST /api/admin/agents/{agent_id}/roles/{role_id}`
- `GET /api/admin/tools`
- `POST /api/admin/tools`
- `PATCH /api/admin/tools/{tool_id}`
- `POST /api/admin/agents/{agent_id}/tools/{tool_id}`
- `GET /api/admin/audit`

