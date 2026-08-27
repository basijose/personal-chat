# MCP servers

Este MVP deja preparada la estructura para futuros servidores MCP.

## Enfoque

- Cada servidor MCP debe quedar aislado del backend principal.
- El backend sigue siendo el punto de autorización.
- Las tools MCP deben registrarse como capacidades permitidas y no como acceso libre.

## Estado del MVP

- Se documenta la estructura.
- No se bloquea la aplicación principal con una implementación MCP compleja.
- El backend ya puede llamar a un bridge externo compatible con MCP usando `provider = mcp`.

## Siguiente paso sugerido

- Agregar un servidor MCP de alumnos con herramientas de consulta controladas.
- Publicar un bridge HTTP que traduzca `agent.generate` a un servidor MCP real.
