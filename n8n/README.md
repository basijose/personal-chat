# n8n

`get_student` puede salir por n8n cuando la tool tiene configurado un webhook seguro.

## Flujo recomendado

1. Crear un workflow en n8n con trigger `Webhook`.
2. Configurar el webhook para recibir el payload estándar de Personal Chat.
3. Guardar la URL en `N8N_GET_STUDENT_WEBHOOK_URL`.
4. Dejar la tool `get_student` con `tool_type = get_student`.
5. El backend usa n8n si encuentra la URL; si no, usa el mock local.

## Payload que envía Personal Chat

```json
{
  "tool_slug": "get_student",
  "tool_name": "Get Student",
  "organization_id": 1,
  "user_id": 10,
  "inputs": {
    "student_id": "STU-1001",
    "document_number": "30111222",
    "query": "Camila"
  },
  "context": {
    "conversation_id": 55,
    "agent_id": 3,
    "agent_slug": "alumnos"
  }
}
```

## Ejemplo de tool

```json
{
  "name": "Get Student",
  "slug": "get_student",
  "description": "Consulta datos de alumnos con n8n o mock local",
  "tool_type": "get_student",
  "configuration": {
    "webhook_url_env": "N8N_GET_STUDENT_WEBHOOK_URL",
    "timeout_seconds": 10
  },
  "active": true
}
```
