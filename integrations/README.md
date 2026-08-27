# Integrations

Este directorio reúne documentación y conectores preparados para producción.

## REST / agente externo

Personal Chat puede hablar con un agente externo configurando un agente con:

- `provider = rest`
- `model =` cualquier identificador útil para el servicio externo

Variables de entorno:

- `EXTERNAL_AGENT_REST_URL`
- `EXTERNAL_AGENT_REST_API_KEY`

## MCP / agente externo

Para MCP se usa el mismo patrón, pero el proveedor llama a un bridge compatible con MCP.

Variables de entorno:

- `EXTERNAL_AGENT_MCP_URL`
- `EXTERNAL_AGENT_MCP_API_KEY`

## n8n

`get_student` puede usar n8n si la tool tiene `webhook_url` o `webhook_url_env`.

Variable recomendada:

- `N8N_GET_STUDENT_WEBHOOK_URL`

## SQL controlado

Las consultas SQL siguen pasando por servicios autorizados, nunca por SQL arbitrario del modelo.
