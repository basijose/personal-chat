# Personal Chat

Portal corporativo de inteligencia artificial con experiencia tipo chat, autenticación interna, RBAC, agentes, auditoría y herramientas controladas desde backend.

## Qué incluye este MVP

- Login con usuario/email y contraseña hasheada.
- JWT en cookie httpOnly para sesión local.
- RBAC por roles de usuario y roles de agente.
- Runtime de agentes con abstracción de proveedor LLM.
- Modo demo sin `OPENAI_API_KEY`.
- Tools mock funcionales para alumnos, pagos y presentismo.
- Panel `/admin` para superadministradores.
- Auditoría básica de login, conversación y tool execution.
- Docker Compose con PostgreSQL, backend y frontend.
- Alembic y seed reproducible.

## Arquitectura resumida

- Frontend: Next.js, TypeScript, React, Tailwind CSS.
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic.
- DB: PostgreSQL.
- IA: `OpenAIProvider` o `MockLLMProvider`.
- Integraciones: `ToolExecutor`, n8n webhook, estructura MCP.

## Requisitos

- Python 3.11+
- Node 18+.
- Docker y Docker Compose, si querés levantar todo en contenedores.

## Configuración

1. Copiá `.env.example` a `.env`.
2. Ajustá `DATABASE_URL`, `JWT_SECRET`, `NEXT_PUBLIC_API_BASE_URL` y, si corresponde, `OPENAI_API_KEY`.
3. Para demo local, podés dejar `OPENAI_API_KEY` vacío. El sistema usa `MockLLMProvider`.
4. `BACKEND_CORS_ORIGINS` ya incluye `localhost` y `127.0.0.1` por defecto, así el frontend funciona si lo abrís en cualquiera de las dos URLs.

## Levantar con Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Flujo de ramas en GitHub

Este repositorio está preparado para trabajar con dos ramas de entorno:

- `testing`: validación y pruebas.
- `production`: salida estable.

El CI de GitHub Actions corre en ambas ramas y en pull requests apuntadas a esas ramas.

Ver [docs/deployment.md](./docs/deployment.md) para el flujo recomendado de promoción.

## Levantar en una sola terminal

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1
```

- Limpia la base SQLite demo local.
- Levanta backend y frontend en background.
- Muestra salida combinada en una sola terminal.

## Migraciones

```bash
cd backend
alembic upgrade head
```

## Seed

```bash
cd backend
python -m scripts.seed
```

## Login demo

Usuarios seed:

- `admin`
- `docente`
- `administracion`
- `rrhh`

Contraseña demo:

- valor de `DEMO_SEED_PASSWORD`
- por defecto en `.env.example`: `Demo1234!`

## Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
```

## Estructura

- `backend/` backend FastAPI.
- `frontend/` app Next.js.
- `docs/` documentación técnica.
- `agents/` notas y futuros artefactos de agentes.
- `integrations/` integración con sistemas externos.
- `mcp-servers/` base para servidores MCP.
- `n8n/` ejemplos de webhooks.
- `scripts/` utilidades generales.
- `tests/` apuntes y material de pruebas.

## Crear un nuevo agente

1. Crear el `Agent` en `/api/admin/agents`.
2. Crear o reutilizar roles.
3. Asignar roles al agente.
4. Crear y asignar tools autorizadas.
5. Definir `system_prompt`, `provider`, `model` y `temperature`.

## Crear una nueva herramienta

1. Crear el `Tool` en `/api/admin/tools`.
2. Definir `tool_type` y `configuration`.
3. Si la tool necesita secreto, referenciar una variable de entorno o secret manager.
4. Asignar la tool al agente con `permission_level`.

## Conectar n8n

1. Definí un webhook en n8n.
2. Guardá la URL en `N8N_SAMPLE_WEBHOOK_URL` o en una referencia segura por tool.
3. Creá una herramienta con `tool_type = n8n_webhook`.
4. La ejecución se hace desde backend y no expone secretos al frontend.

## Próximos pasos

- Integración real con OpenAI function calling más granular.
- Conectores SQL controlados por vistas o servicios intermedios.
- UI de administración más avanzada.
- Integración MCP real para herramientas externas.
- SSO con Entra ID, Google Workspace o LDAP.
