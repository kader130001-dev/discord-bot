import discord
from discord.ext import commands
import os
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} a ete kick !")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member} a ete banni !")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"Role ajoute a {member} !")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def delrole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"Role retire a {member} !")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"{amount} messages supprimes !", delete_after=3)
@bot.command()
@commands.has_permissions(manage_channels=True)
async def hide(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send("Les membres ne voyent plus ce salon !")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unhide(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send("Les membres voyent à nouveau ce salon !")
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ! 🏓 {round(bot.latency * 1000)}ms")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Les membres ne peuvent plus parler 🔒")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Les membres peuvent à nouveau parler 🔓")
    
@bot.command()
@commands.has_permissions(manage_roles=True)
async def derank(ctx, member: discord.Member):
    roles = [role for role in member.roles if role != ctx.guild.default_role]
    await member.remove_roles(*roles)
    await ctx.send(f"{member.mention} a été derank !")
@bot.command()
async def commandes(ctx):
    embed = discord.Embed(title="📋 Commandes disponibles", color=0x00bfff)
    embed.add_field(name="+ping", value="Voir la latence du bot", inline=False)
    embed.add_field(name="+lock", value="Verrouiller le salon", inline=False)
    embed.add_field(name="+unlock", value="Déverrouiller le salon", inline=False)
    embed.add_field(name="+userinfo [@membre]", value="Voir les infos d'un membre", inline=False)
    embed.add_field(name="+derank [@membre]", value="Retirer tous les rôles d'un membre", inline=False)
    embed.add_field(name="+help", value="Voir les commandes disponibles", inline=False)
    embed.set_footer(text="Préfixe : +")
    await ctx.send(embed=embed)
    @bot.command()
    
@commands.has_permissions(administrator=True)
async def backup(ctx):
    guild = ctx.guild
    backup_data = {"salons": [], "roles": []}
    
    for role in guild.roles:
        if role.name != "@everyone":
            backup_data["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "permissions": role.permissions.value
            })
    
    for channel in guild.channels:
        backup_data["salons"].append({
            "name": channel.name,
            "type": str(channel.type)
        })
    
    import json
    data_str = json.dumps(backup_data)
    await ctx.author.send(f"**Backup ID:**\n```{data_str}```")
    await ctx.send("✅ Backup envoyé en MP ! Garde le code pour +restore")

@bot.command()
@commands.has_permissions(administrator=True)
async def restore(ctx, *, data: str):
    import json
    guild = ctx.guild
    backup_data = json.loads(data)
    
    for role_data in backup_data["roles"]:
        await guild.create_role(
            name=role_data["name"],
            colour=discord.Colour(role_data["color"]),
            permissions=discord.Permissions(role_data["permissions"])
        )
    
    for channel_data in backup_data["salons"]:
        if channel_data["type"] == "text":
            await guild.create_text_channel(channel_data["name"])
        elif channel_data["type"] == "voice":
            await guild.create_voice_channel(channel_data["name"])
    
    await ctx.send("✅ Restore terminé !")
bot.run(os.environ["TOKEN"])


