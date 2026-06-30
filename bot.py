import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

COLORES_PREDEFINIDOS = {
    "rojo": 0xE74C3C,
    "naranja": 0xE67E22,
    "amarillo": 0xF1C40F,
    "verde": 0x2ECC71,
    "azul": 0x3498DB,
    "morado": 0x9B59B6,
    "rosa": 0xE91E63,
    "turquesa": 0x1ABC9C,
    "gris": 0x95A5A6,
    "negro": 0x23272A,
    "blanco": 0xFFFFFF,
}

NOMBRE_PREFIJO_ROL_COLOR = "color-"

ROLES_GENERALES = {
    "anuncios": {"emoji": "📢", "color": 0x99AAB5},
    "juegos": {"emoji": "🎮", "color": 0x99AAB5},
    "eventos": {"emoji": "📅", "color": 0x99AAB5},
}


def hex_a_color(texto: str):
    texto = texto.strip().lstrip("#")
    if len(texto) == 3:
        texto = "".join([c * 2 for c in texto])
    if len(texto) != 6:
        return None
    try:
        valor = int(texto, 16)
        return discord.Color(valor)
    except ValueError:
        return None


async def obtener_o_crear_rol_color(guild: discord.Guild, color: discord.Color, nombre_base: str):
    nombre_rol = f"{NOMBRE_PREFIJO_ROL_COLOR}{nombre_base}"
    rol_existente = discord.utils.find(
        lambda r: r.name == nombre_rol and r.color.value == color.value, guild.roles
    )
    if rol_existente:
        return rol_existente
    nuevo_rol = await guild.create_role(
        name=nombre_rol,
        color=color,
        reason="Rol de color generado por Tiramisu Pintor",
    )
    return nuevo_rol


async def quitar_roles_color_anteriores(member: discord.Member):
    roles_color = [r for r in member.roles if r.name.startswith(NOMBRE_PREFIJO_ROL_COLOR)]
    if roles_color:
        await member.remove_roles(*roles_color, reason="Cambiando color de usuario")


async def aplicar_color(interaction: discord.Interaction, nombre_color: str, color_obj: discord.Color):
    guild = interaction.guild
    member = interaction.user

    bot_member = guild.get_member(bot.user.id)
    if bot_member.guild_permissions.manage_roles is False:
        await interaction.followup.send(
            "No tengo permisos para gestionar roles en este servidor. Pide a un administrador que me dé el permiso 'Gestionar roles'.",
            ephemeral=True,
        )
        return

    try:
        nuevo_rol = await obtener_o_crear_rol_color(guild, color_obj, nombre_color)

        if bot_member.top_role.position <= nuevo_rol.position:
            await interaction.followup.send(
                "Mi rol necesita estar más arriba que el rol de color en la lista de roles del servidor. Pide a un administrador que suba mi rol.",
                ephemeral=True,
            )
            return

        await quitar_roles_color_anteriores(member)
        await member.add_roles(nuevo_rol, reason="Cambio de color solicitado")

        await interaction.followup.send(
            f"Listo, tu color ahora es **{nombre_color}** ({str(color_obj)}).",
            ephemeral=True,
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "No tengo permisos suficientes para crear o asignar ese rol.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(f"Ocurrió un error al cambiar tu color: {e}", ephemeral=True)


class BotonColor(discord.ui.Button):
    def __init__(self, nombre_color: str, valor_color: int):
        super().__init__(
            label=nombre_color.capitalize(),
            style=discord.ButtonStyle.secondary,
            emoji="🎨",
            custom_id=f"colores_color_{nombre_color}",
        )
        self.nombre_color = nombre_color
        self.valor_color = valor_color

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await aplicar_color(interaction, self.nombre_color, discord.Color(self.valor_color))


class VistaColores(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for nombre_color, valor_color in COLORES_PREDEFINIDOS.items():
            self.add_item(BotonColor(nombre_color, valor_color))


def crear_embed_colores():
    embed = discord.Embed(
        title="Elige tu color",
        description="Haz clic en el botón del color que quieras para tu nombre.",
        color=discord.Color.blurple(),
    )
    lista_colores = "\n".join(
        [f"🎨 **{nombre.capitalize()}**" for nombre in COLORES_PREDEFINIDOS]
    )
    embed.add_field(name="Colores disponibles", value=lista_colores, inline=False)
    embed.set_footer(text="También puedes usar /color con un código hex personalizado")
    return embed


async def obtener_o_crear_rol_general(guild: discord.Guild, nombre_rol: str, color_valor: int):
    rol_existente = discord.utils.find(lambda r: r.name == nombre_rol, guild.roles)
    if rol_existente:
        return rol_existente
    nuevo_rol = await guild.create_role(
        name=nombre_rol,
        color=discord.Color(color_valor),
        reason="Rol generado por Tiramisu Pintor (reaction roll)",
    )
    return nuevo_rol


class BotonRolGeneral(discord.ui.Button):
    def __init__(self, nombre_rol: str, emoji: str, color_valor: int):
        super().__init__(
            label=nombre_rol.capitalize(),
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
            custom_id=f"reaction_roll_rol_{nombre_rol}",
        )
        self.nombre_rol = nombre_rol
        self.color_valor = color_valor

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = interaction.user

        bot_member = guild.get_member(bot.user.id)
        if bot_member.guild_permissions.manage_roles is False:
            await interaction.followup.send(
                "No tengo permisos para gestionar roles en este servidor.", ephemeral=True
            )
            return

        try:
            rol = await obtener_o_crear_rol_general(guild, self.nombre_rol, self.color_valor)

            if bot_member.top_role.position <= rol.position:
                await interaction.followup.send(
                    "Mi rol necesita estar más arriba que este rol en la lista de roles del servidor.",
                    ephemeral=True,
                )
                return

            if rol in member.roles:
                await member.remove_roles(rol, reason="Quitó rol vía reaction roll")
                await interaction.followup.send(
                    f"Se te quitó el rol **{self.nombre_rol.capitalize()}**.", ephemeral=True
                )
            else:
                await member.add_roles(rol, reason="Obtuvo rol vía reaction roll")
                await interaction.followup.send(
                    f"Ahora tienes el rol **{self.nombre_rol.capitalize()}**.", ephemeral=True
                )
        except discord.Forbidden:
            await interaction.followup.send(
                "No tengo permisos suficientes para asignar ese rol.", ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}", ephemeral=True)


class BotonColorReactionRoll(discord.ui.Button):
    def __init__(self, nombre_color: str, valor_color: int):
        super().__init__(
            label=nombre_color.capitalize(),
            style=discord.ButtonStyle.secondary,
            emoji="🎨",
            custom_id=f"reaction_roll_color_{nombre_color}",
        )
        self.nombre_color = nombre_color
        self.valor_color = valor_color

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await aplicar_color(interaction, self.nombre_color, discord.Color(self.valor_color))


class VistaReactionRoll(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for nombre_color, valor_color in COLORES_PREDEFINIDOS.items():
            self.add_item(BotonColorReactionRoll(nombre_color, valor_color))
        for nombre_rol, datos in ROLES_GENERALES.items():
            self.add_item(BotonRolGeneral(nombre_rol, datos["emoji"], datos["color"]))


def crear_embed_reaction_roll():
    embed = discord.Embed(
        title="Panel de roles",
        description="Haz clic en los botones para asignarte roles. Puedes elegir un color y los roles que quieras.",
        color=discord.Color.blurple(),
    )
    lista_colores = "\n".join(
        [f"🎨 **{nombre.capitalize()}**" for nombre in COLORES_PREDEFINIDOS]
    )
    embed.add_field(name="Colores", value=lista_colores, inline=True)
    lista_roles = "\n".join(
        [f"{datos['emoji']} **{nombre.capitalize()}**" for nombre, datos in ROLES_GENERALES.items()]
    )
    embed.add_field(name="Roles", value=lista_roles, inline=True)
    embed.set_footer(text="Haz clic de nuevo en un rol para quitártelo")
    return embed


@bot.event
async def on_ready():
    bot.add_view(VistaColores())
    bot.add_view(VistaReactionRoll())
    await bot.tree.sync()
    print(f"Tiramisu Pintor conectado como {bot.user}")


@bot.tree.command(name="color", description="Cambia el color de tu nombre en el servidor")
@app_commands.describe(
    color_predefinido="Elige un color de la lista",
    color_hex="O escribe un código hex personalizado (ej. #ff5733)",
)
@app_commands.choices(
    color_predefinido=[
        app_commands.Choice(name=nombre.capitalize(), value=nombre)
        for nombre in COLORES_PREDEFINIDOS
    ]
)
async def color(
    interaction: discord.Interaction,
    color_predefinido: app_commands.Choice[str] = None,
    color_hex: str = None,
):
    await interaction.response.defer(ephemeral=True)

    if color_predefinido is None and color_hex is None:
        await interaction.followup.send(
            "Tienes que elegir un color predefinido o escribir un código hex."
        )
        return

    if color_hex is not None:
        color_obj = hex_a_color(color_hex)
        if color_obj is None:
            await interaction.followup.send(
                "Ese código hex no es válido. Usa un formato como `#ff5733` o `ff5733`."
            )
            return
        nombre_color = color_hex.strip().lstrip("#").lower()
    else:
        nombre_color = color_predefinido.value
        color_obj = discord.Color(COLORES_PREDEFINIDOS[nombre_color])

    guild = interaction.guild
    member = interaction.user

    await aplicar_color(interaction, nombre_color, color_obj)


@bot.tree.command(name="colores", description="Muestra un menú con botones para elegir tu color")
async def colores(interaction: discord.Interaction):
    embed = crear_embed_colores()
    vista = VistaColores()
    await interaction.response.send_message(embed=embed, view=vista)


@bot.tree.command(name="reaction_roll", description="Publica el panel fijo de roles (solo administradores)")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_roll(interaction: discord.Interaction):
    embed = crear_embed_reaction_roll()
    vista = VistaReactionRoll()
    await interaction.response.send_message(embed=embed, view=vista)


@reaction_roll.error
async def reaction_roll_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "Solo administradores pueden publicar el panel de roles.", ephemeral=True
        )


@bot.tree.command(name="quitar_color", description="Quita tu color personalizado actual")
async def quitar_color(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    member = interaction.user
    roles_color = [r for r in member.roles if r.name.startswith(NOMBRE_PREFIJO_ROL_COLOR)]
    if not roles_color:
        await interaction.followup.send("No tienes ningún color asignado actualmente.")
        return
    await member.remove_roles(*roles_color, reason="Usuario quitó su color")
    await interaction.followup.send("Tu color ha sido removido.")


if __name__ == "__main__":
    if TOKEN is None:
        print("ERROR: No se encontró la variable de entorno DISCORD_TOKEN")
    else:
        bot.run(TOKEN)
