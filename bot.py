from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    server.serve_forever()

Thread(target=run_server, daemon=True).start()

import discord
from discord.ext import commands
import os
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} a ete kick !")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_id: int, *, reason=None):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"🔨 {user} a été banni ! Raison : {reason or 'Aucune'}")
    except discord.NotFound:
        await ctx.send("❌ Utilisateur introuvable !")
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de bannir cet utilisateur !")
        
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
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    if overwrite.view_channel == False:
        await ctx.send("❌ Ce salon est déjà caché !")
        return
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
    await ctx.send("🔒 Les membres ne voient plus ce salon !")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unhide(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    if overwrite.view_channel == True:
        await ctx.send("❌ Ce salon est déjà visible !")
        return
    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
    await ctx.send("🔓 Les membres voient à nouveau ce salon !")
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
    await ctx.send(f"{member.mention} **a été derank** !")

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📋 Commandes disponibles",
        description="Préfixe : **+**",
        color=0x2b2d31
    )
    embed.add_field(name="🛡️ Modération", value="`+ban` `+unban` `+kick` `+derank`\n`+banlist` `+clear`", inline=False)
    embed.add_field(name="🔒 Salons", value="`+hide` `+unhide` `+lock` `+unlock`\n`+renew`", inline=False)
    embed.add_field(name="👥 Rôles", value="`+addrole` `+delrole`", inline=False)
    embed.add_field(name="📊 Infos", value="`+serverinfo` `+ping` `+snipe`", inline=False)
    embed.add_field(name="🎫 Autre", value="`+embed`", inline=False)
    embed.set_footer(text="Tape +help <commande> pour plus d'infos")
    await ctx.send(embed=embed)
    
@commands.has_permissions(manage_channels=True)
async def renew(ctx):
    channel = ctx.channel
    position = channel.position
    overwrites = channel.overwrites
    new_channel = await channel.clone(reason="Renew par commande")
    await new_channel.edit(position=position, overwrites=overwrites)
    await channel.delete()

@bot.command()
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    bans = [entry async for entry in ctx.guild.bans()]
    if not bans:
        await ctx.send("✅ Aucun membre banni sur ce serveur !")
        return
    liste = "\n".join([f"🔨 {entry.user} (ID: {entry.user.id})" for entry in bans])
    embed = discord.Embed(title="📋 Liste des bannis", description=liste, color=0xff0000)
    await ctx.send(embed=embed)
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Questions Serveur", description="Si vous avez une question concernant le serveur.", emoji="⚖️"),
            discord.SelectOption(label="Gestion Staff", description="Devenir staff, réclamer un rankup ou récupérer des rôles.", emoji="👥"),
            discord.SelectOption(label="Gestion Abus", description="En cas de conflit ou problème avec un staff/membre.", emoji="🕵️"),
            discord.SelectOption(label="Gestion Coins", description="En cas de problème du bot coins.", emoji="🪙"),
            discord.SelectOption(label="Gestion Animation", description="Devenir animateur.", emoji="🎭"),
            discord.SelectOption(label="Community Manager", description="Contacter les community managers.", emoji="💻"),
        ]
        super().__init__(placeholder="Veuillez faire un choix.", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ Ticket **{self.values[0]}** créé !", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.command()
@commands.has_permissions(manage_channels=True)
async def embed(ctx):
    embed = discord.Embed(title="🎫 Support", description="Veuillez faire un choix.", color=0x2b2d31)
    await ctx.send(embed=embed, view=TicketView())
    
@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    vocal = sum(1 for m in guild.members if m.voice)
    streaming = sum(1 for m in guild.members if m.voice and m.voice.self_stream)
    actifs = sum(1 for m in guild.members if m.activity)
    mutes = sum(1 for m in guild.members if m.voice and m.voice.self_mute)

    embed = discord.Embed(title=f"{guild.name} 🏰 Statistiques !", color=0x2b2d31)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
    embed.add_field(name="", value=f"*Membres:* **{total:,}**\n*En ligne:* **{online:,}**\n*En vocal:* **{vocal:,}**\n*En stream:* **{streaming:,}**\n*Actifs:* **{actifs:,}**\n*Mute:* **{mutes:,}**", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ {user} a été débanni !")
    except discord.NotFound:
        await ctx.send("❌ Utilisateur introuvable ou pas banni !")
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de débannir cet utilisateur !")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.reply("Mon préfixe est **+** !")
    await bot.process_commands(message)
    
snipe_data = {}

@bot.listen()
async def on_message_delete(message):
    if message.author.bot:
        return
    snipe_data[message.channel.id] = {
        "content": message.content if message.content else "*(image/fichier)*",
        "author": message.author,
        "time": message.created_at
    }

@bot.command()
async def snipe(ctx):
    data = snipe_data.get(ctx.channel.id)
    if not data:
        await ctx.send("❌ Aucun message supprimé récemment !")
        return
    embed = discord.Embed(
        description=data["content"],
        color=0x2b2d31,
        timestamp=data["time"]
    )
    embed.set_author(name=data["author"], icon_url=data["author"].display_avatar.url)
    embed.set_footer(text=f"Supprimé dans #{ctx.channel.name}")
    await ctx.send(embed=embed)
    
warn_data = {}

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    import datetime
    duration = datetime.timedelta(hours=1)
    await member.timeout(duration, reason=reason)
    embed = discord.Embed(title="🔇 Membre muet", color=0xff4444)
    embed.add_field(name="👤 Membre", value=member.mention, inline=True)
    embed.add_field(name="⏱️ Durée", value="1 heure", inline=True)
    embed.add_field(name="📝 Raison", value=reason or "Aucune", inline=False)
    embed.set_footer(text=f"Par {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    embed = discord.Embed(title="🔊 Membre unmute", color=0x44ff44)
    embed.add_field(name="👤 Membre", value=member.mention, inline=True)
    embed.set_footer(text=f"Par {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    if member.id not in warn_data:
        warn_data[member.id] = []
    warn_data[member.id].append(reason or "Aucune")
    total = len(warn_data[member.id])
    embed = discord.Embed(title="⚠️ Avertissement", color=0xffaa00)
    embed.add_field(name="👤 Membre", value=member.mention, inline=True)
    embed.add_field(name="🔢 Total warns", value=f"`{total}`", inline=True)
    embed.add_field(name="📝 Raison", value=reason or "Aucune", inline=False)
    embed.set_footer(text=f"Par {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def warnlist(ctx, member: discord.Member):
    warns = warn_data.get(member.id, [])
    if not warns:
        await ctx.send(f"✅ **{member}** n'a aucun avertissement !")
        return
    liste = "\n".join([f"`{i+1}.` {w}" for i, w in enumerate(warns)])
    embed = discord.Embed(title=f"📋 Avertissements de {member}", description=liste, color=0xffaa00)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Total : {len(warns)} warn(s)")
    await ctx.send(embed=embed)
    
bot.run(os.environ["TOKEN"])

