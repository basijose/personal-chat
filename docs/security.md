# Security

## Principios

- El prompt no otorga permisos.
- El backend valida identidad, organización, rol y tool antes de cada ejecución.
- Los secretos no viajan al frontend.
- Las herramientas se ejecutan en backend o en conectores controlados.

## Amenazas relevantes

- Escalada de privilegios por prompt injection.
- Acceso cruzado entre organizaciones.
- Exposición accidental de API keys o secretos.
- Ejecución de SQL arbitrario.
- Abuso de tools por agentes no autorizados.
- Mensajes demasiado grandes o maliciosos.

## Controles implementados

- JWT con cookie httpOnly.
- Hash PBKDF2 para contraseñas.
- CORS configurable.
- Validación de inputs con Pydantic.
- Scope por `organization_id`.
- Protección de rutas admin.
- Permisos de herramientas validados en backend.
- Auditoría sin secretos.
- Timeout en integraciones n8n.

## Pendientes de endurecimiento

- Rotación de secretos.
- SSO enterprise.
- Rate limiting y antifraude más fino.
- SCA/secret scanning en CI.
- Filtros de contenido y policy engine más detallado.

