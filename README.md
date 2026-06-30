# Tiramisu Pintor - Bot de colores para Discord

## Variables de entorno necesarias en Railway

- `DISCORD_TOKEN`: el token de tu bot (lo obtienes en https://discord.com/developers/applications)

## Permisos requeridos en el servidor

El bot necesita el permiso **Manage Roles** (Gestionar roles), y su rol debe estar
ubicado por encima de cualquier rol de color en la lista de roles del servidor.

## Comandos disponibles

- `/color color_predefinido:<nombre>` — asigna un color de la lista predefinida
- `/color color_hex:<codigo>` — asigna un color personalizado (ej. `#ff5733`)
- `/quitar_color` — quita el color asignado actualmente
