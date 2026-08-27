# Architecture

```mermaid
flowchart LR
  U[Usuario] --> F[Frontend Next.js]
  F --> B[API Backend FastAPI]
  B --> A[Auth / RBAC]
  B --> R[Agent Runtime]
  R --> P[Tool Authorization]
  P --> T[Tool Executor]
  T --> N[n8n]
  T --> M[MCP]
  T --> X[REST API]
  T --> I[Sistema interno]
  R --> L[LLM Provider]
  B --> D[(PostgreSQL)]
  B --> O[Audit Log]
  A --> D
  O --> D
```

## Componentes

- `Frontend`: experiencia de chat y administración.
- `API Backend`: auth, RBAC, conversaciones, chat y admin.
- `Auth/RBAC`: valida usuario, organización y permisos antes de cada operación sensible.
- `Agent Runtime`: orquesta historial, tools y proveedor LLM.
- `Tool Executor`: ejecuta acciones permitidas en backend.
- `PostgreSQL`: persistencia multiempresa.
- `LLM Provider`: capa intercambiable para OpenAI, Anthropic, Google o modelos locales.
- `Audit Log`: trazabilidad de accesos, tools y errores.

