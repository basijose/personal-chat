# Permissions

## Modelo

- Un usuario puede tener uno o más roles.
- Un agente puede estar asignado a uno o más roles.
- Un usuario puede usar un agente si comparte al menos un rol con ese agente, o si es superadmin.
- Un agente puede invocar una tool solo si esa tool está asociada a ese agente y el backend la autoriza.

## `permission_level`

- `read`
- `execute`
- `write`
- `admin`

En el MVP, la ejecución de tools usa `execute` o superior.

## Flujo de validación

1. El usuario inicia sesión.
2. El backend identifica organización y roles.
3. Se filtran agentes permitidos.
4. Al enviar un mensaje, se valida el agente otra vez.
5. Si el modelo pide una tool, el backend valida la tool antes de ejecutarla.
6. Toda denegación queda auditable.

