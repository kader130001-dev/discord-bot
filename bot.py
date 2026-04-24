import discord
from discord.ext import commands
import json, os, asyncio, aiohttp
from collections import defaultdict
from datetime import datetime, timedelta

# ─────────────────────────────────────────
#  CONFIG — MODIFIE ICI
# ─────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
PREFIX = "+"
# ─────────────────────────────────────────

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())
bot.remove_command("help")  # ← ajoute ça

# ══════════════════════════════════════════
#  BASE DE DONNÉES JSON
# ══════════════════════════════════════════
def load(file):
    if not os.path.exists(f"{file}.json"):
        return {}
    with open(f"{file}.json", "r") as f:
        return json.load(f)

def save(file, data):
    with open(f"{file}.json", "w") as f:
        json.dump(data, f, indent=2)

def get_guild(file, guild_id):
    return load(file).get(str(guild_id), {})

def set_guild(file, guild_id, data):
    db = load(file)
    db[str(guild_id)] = data
    save(file, db)

# ══════════════════════════════════════════
#  TRACKERS ANTI-RAID
# ══════════════════════════════════════════
join_tracker    = defaultdict(list)
ban_tracker     = defaultdict(list)
channel_tracker = defaultdict(list)
role_tracker    = defaultdict(list)

def now():
    return datetime.utcnow()

def recent(lst, seconds=10):
    cutoff = now() - timedelta(seconds=seconds)
    return [t for t in lst if t > cutoff]

# ══════════════════════════════════════════
#  TICKETS — SELECT MENU
# ══════════════════════════════════════════
TICKET_CATEGORIES = [
    discord.SelectOption(label="Gestion Abus",    description="Signaler un abus ou comportement inapproprié.", emoji="🚫", value="abus"),
    discord.SelectOption(label="Gestion Staff",   description="Recrutement ou problèmes liés au staff.",       emoji="🔧", value="staff"),
    discord.SelectOption(label="Ticket Question", description="Questions, DM all, fusions, contact owners.",   emoji="📢", value="question"),
    discord.SelectOption(label="Animation",       description="Demandes liées aux animations et événements.",  emoji="🎉", value="animation"),
]
TICKET_TITLES = {
    "abus": "🚫 Gestion Abus",
    "staff": "🔧 Gestion Staff",
    "question": "📢 Ticket Question",
    "animation": "🎉 Animation",
}

class TicketSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Sélectionnez une catégorie de gestion...", options=TICKET_CATEGORIES)

    async def callback(self, interaction: discord.Interaction):
        choix   = self.values[0]
        guild   = interaction.guild
        membre  = interaction.user
        cfg     = get_guild("tickets", guild.id)

        nom = f"ticket-{membre.name}-{choix}".lower().replace(" ", "-")[:32]
        existing = discord.utils.get(guild.text_channels, name=nom)
        if existing:
            return await interaction.response.send_message(f"❌ Ticket déjà ouvert : {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            membre: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        staff_role_id = cfg.get("staff_role")
        if staff_role_id:
            role = guild.get_role(int(staff_role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        cat_id   = cfg.get("category_id")
        category = guild.get_channel(int(cat_id)) if cat_id else None

        channel = await guild.create_text_channel(name=nom, overwrites=overwrites, category=category)

        embed = discord.Embed(
            title=TICKET_TITLES[choix],
            description=(
                f"Bonjour {membre.mention}, bienvenue dans ton ticket.\n\n"
                f"Explique ta demande en détail, le staff te répondra rapidement.\n"
                f"Clique sur 🔒 **Fermer** pour clore le ticket."
            ),
            color=discord.Color.dark_red()
        )
        embed.set_footer(text=f"Crow Bot • {membre}")
        await channel.send(embed=embed, view=TicketActionView())
        if staff_role_id:
            role = guild.get_role(int(staff_role_id))
            if role:
                await channel.send(f"{role.mention} — nouveau ticket !")

        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=True)

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def fermer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fermeture dans 5 secondes...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="✋ Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.edit(topic=f"Pris en charge par {interaction.user}")
        await interaction.response.send_message(f"✅ Pris en charge par {interaction.user.mention}.")

    @discord.ui.button(label="🗑️ Supprimer", style=discord.ButtonStyle.secondary, custom_id="ticket_delete")
    async def supprimer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗑️ Suppression...")
        await interaction.channel.delete()

# ══════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════
@bot.event
async def on_ready():
    bot.add_view(TicketSelectView())
    bot.add_view(TicketActionView())
    await bot.load_extension("cogs.gestion")
    await bot.change_presence(activity=discord.Game(name="+help | Crow Bot"))
    print(f"✅ {bot.user} connecté.")

@bot.event
async def on_member_join(member):
    guild = member.guild

    # --- Blacklist auto-kick ---
    db_bl = load("blacklist").get(str(guild.id), {})
    if str(member.id) in db_bl.get("list", {}):
        try: await member.send(f"❌ Tu es blacklisté du serveur **{guild.name}**.")
        except: pass
        return await member.kick(reason="Blacklist")
    if member.bot and str(member.id) in db_bl.get("bots", []):
        return await member.kick(reason="Bot blacklisté")

    # --- AntiRaid (antitoken) ---
    cfg = get_guild("antiraid", guild.id)
    if cfg.get("antitoken"):
        limit = cfg.get("antitoken_max", 5)
        duree = cfg.get("antitoken_duree", 10)
        join_tracker[guild.id].append(now())
        join_tracker[guild.id] = recent(join_tracker[guild.id], duree)
        if len(join_tracker[guild.id]) >= limit:
            join_tracker[guild.id] = []
            for ch in guild.text_channels:
                try: await ch.set_permissions(guild.default_role, send_messages=False)
                except: pass
            log_id = cfg.get("log_channel")
            if log_id:
                ch = guild.get_channel(int(log_id))
                if ch: await ch.send("🚨 **RAID DÉTECTÉ** — Serveur verrouillé !")

@bot.event
async def on_member_ban(guild, user):
    cfg = get_guild("antiraid", guild.id)
    if not cfg.get("antiban"): return
    limit = cfg.get("antiban_max", 3)
    ban_tracker[guild.id].append(now())
    ban_tracker[guild.id] = recent(ban_tracker[guild.id], 10)
    if len(ban_tracker[guild.id]) >= limit:
        ban_tracker[guild.id] = []
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if not entry.user.bot:
                await punir(guild, entry.user, "Ban massif", cfg)

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    cfg = get_guild("antiraid", guild.id)
    if not cfg.get("antichannel"): return
    channel_tracker[guild.id].append(now())
    channel_tracker[guild.id] = recent(channel_tracker[guild.id], 10)
    if len(channel_tracker[guild.id]) >= cfg.get("antichannel_max", 3):
        channel_tracker[guild.id] = []
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if not entry.user.bot:
                await punir(guild, entry.user, "Suppression massive de salons", cfg)

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    cfg = get_guild("antiraid", guild.id)
    if not cfg.get("antirole"): return
    role_tracker[guild.id].append(now())
    role_tracker[guild.id] = recent(role_tracker[guild.id], 10)
    if len(role_tracker[guild.id]) >= cfg.get("antirole_max", 3):
        role_tracker[guild.id] = []
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if not entry.user.bot:
                await punir(guild, entry.user, "Suppression massive de rôles", cfg)

@bot.event
async def on_webhooks_update(channel):
    guild = channel.guild
    cfg = get_guild("antiraid", guild.id)
    if not cfg.get("antiwebhook"): return
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
        if not entry.user.bot:
            await punir(guild, entry.user, "Création webhook suspecte", cfg)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        await bot.process_commands(message)
        return
    cfg = get_guild("antiraid", message.guild.id)
    if cfg.get("antieveryone") and message.mention_everyone:
        try:
            await message.delete()
            await punir(message.guild, message.author, "@everyone non autorisé", cfg)
        except: pass
    await bot.process_commands(message)

# ══════════════════════════════════════════
#  HELPER PUNITION ANTI-RAID
# ══════════════════════════════════════════
async def punir(guild, member, raison, cfg):
    action = cfg.get("punition", "kick")
    try:
        if action == "ban":    await guild.ban(member, reason=f"[AntiRaid] {raison}")
        elif action == "derank": await member.edit(roles=[], reason=f"[AntiRaid] {raison}")
        else:                  await guild.kick(member, reason=f"[AntiRaid] {raison}")
    except: pass
    log_id = cfg.get("log_channel")
    if log_id:
        ch = guild.get_channel(int(log_id))
        if ch:
            embed = discord.Embed(title="🛡️ AntiRaid", description=f"**Membre :** {member}\n**Raison :** {raison}\n**Action :** {action}", color=discord.Color.red())
            await ch.send(embed=embed)

# ══════════════════════════════════════════
#  COMMANDES TICKETS
# ══════════════════════════════════════════
@bot.command(name="ticket")
@commands.has_permissions(administrator=True)
async def ticket_setup(ctx, sub: str = "setup"):
    if sub != "setup": return
    embed = discord.Embed(title="Crow Ticket", description="Choisissez une option dans le menu ci-dessous.", color=discord.Color.dark_red())
    await ctx.send(embed=embed, view=TicketSelectView())
    await ctx.message.delete()

@bot.command(name="ticketrole")
@commands.has_permissions(administrator=True)
async def ticketrole(ctx, role: discord.Role):
    cfg = get_guild("tickets", ctx.guild.id)
    cfg["staff_role"] = role.id
    set_guild("tickets", ctx.guild.id, cfg)
    await ctx.send(f"✅ Rôle staff : {role.mention}")

@bot.command(name="ticketcategory")
@commands.has_permissions(administrator=True)
async def ticketcategory(ctx, category: discord.CategoryChannel):
    cfg = get_guild("tickets", ctx.guild.id)
    cfg["category_id"] = category.id
    set_guild("tickets", ctx.guild.id, cfg)
    await ctx.send(f"✅ Catégorie : **{category.name}**")

# ══════════════════════════════════════════
#  COMMANDES ANTI-RAID
# ══════════════════════════════════════════
@bot.command(name="secur")
@commands.has_permissions(administrator=True)
async def secur(ctx, mode: str = None):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode is None:
        embed = discord.Embed(title="🛡️ Sécurité", color=discord.Color.blue())
        for k in ["antitoken","antiban","antichannel","antirole","antieveryone","antiwebhook","antibot"]:
            embed.add_field(name=k, value="✅ ON" if cfg.get(k) else "❌ OFF", inline=True)
        return await ctx.send(embed=embed)
    state = mode in ("on", "max")
    for k in ["antitoken","antiban","antichannel","antirole","antieveryone","antiwebhook"]:
        cfg[k] = state
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ Sécurité globale : `{mode}`")

@bot.command(name="antitoken")
@commands.has_permissions(administrator=True)
async def antitoken(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode == "on":    cfg["antitoken"] = True
    elif mode == "off": cfg["antitoken"] = False
    elif "/" in mode:
        nb, d = mode.split("/")
        cfg["antitoken_max"] = int(nb); cfg["antitoken_duree"] = int(d)
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antitoken : `{mode}`")

@bot.command(name="antiban")
@commands.has_permissions(administrator=True)
async def antiban(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode == "on":    cfg["antiban"] = True
    elif mode == "off": cfg["antiban"] = False
    elif "/" in mode:
        nb, d = mode.split("/"); cfg["antiban_max"] = int(nb); cfg["antiban_duree"] = int(d)
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antiban : `{mode}`")

@bot.command(name="antichannel")
@commands.has_permissions(administrator=True)
async def antichannel(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode == "on":    cfg["antichannel"] = True
    elif mode == "off": cfg["antichannel"] = False
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antichannel : `{mode}`")

@bot.command(name="antirole")
@commands.has_permissions(administrator=True)
async def antirole(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode == "on":    cfg["antirole"] = True
    elif mode == "off": cfg["antirole"] = False
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antirole : `{mode}`")

@bot.command(name="antieveryone")
@commands.has_permissions(administrator=True)
async def antieveryone(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    cfg["antieveryone"] = mode == "on"
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antieveryone : `{mode}`")

@bot.command(name="antiwebhook")
@commands.has_permissions(administrator=True)
async def antiwebhook(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    cfg["antiwebhook"] = mode == "on"
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antiwebhook : `{mode}`")

@bot.command(name="antibot")
@commands.has_permissions(administrator=True)
async def antibot(ctx, mode: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    cfg["antibot"] = mode == "on"
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ antibot : `{mode}`")

@bot.command(name="punition")
@commands.has_permissions(administrator=True)
async def punition(ctx, target: str, action: str):
    cfg = get_guild("antiraid", ctx.guild.id)
    cfg["punition"] = action
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send(f"✅ Punition : `{action}`")

@bot.command(name="raidlog")
@commands.has_permissions(administrator=True)
async def raidlog(ctx, mode: str, channel: discord.TextChannel = None):
    cfg = get_guild("antiraid", ctx.guild.id)
    if mode == "on" and channel: cfg["log_channel"] = channel.id
    elif mode == "off": cfg.pop("log_channel", None)
    set_guild("antiraid", ctx.guild.id, cfg)
    await ctx.send("✅ raidlog mis à jour.")

@bot.command(name="clear_webhooks")
@commands.has_permissions(administrator=True)
async def clear_webhooks(ctx):
    count = 0
    for ch in ctx.guild.text_channels:
        try:
            for hook in await ch.webhooks():
                await hook.delete(); count += 1
        except: pass
    await ctx.send(f"✅ {count} webhook(s) supprimé(s).")

# ══════════════════════════════════════════
#  COMMANDES WHITELIST
# ══════════════════════════════════════════
@bot.command(name="wl")
@commands.has_permissions(administrator=True)
async def wl(ctx, membre: discord.Member = None):
    db = get_guild("whitelist", ctx.guild.id)
    wlist = db.get("list", [])
    if membre is None:
        if not wlist: return await ctx.send("📋 Whitelist vide.")
        embed = discord.Embed(title="✅ Whitelist", description="\n".join(f"<@{u}>" for u in wlist), color=discord.Color.green())
        return await ctx.send(embed=embed)
    if str(membre.id) not in wlist: wlist.append(str(membre.id))
    db["list"] = wlist; set_guild("whitelist", ctx.guild.id, db)
    await ctx.send(f"✅ {membre.mention} ajouté à la whitelist.")

@bot.command(name="unwl")
@commands.has_permissions(administrator=True)
async def unwl(ctx, membre: discord.Member):
    db = get_guild("whitelist", ctx.guild.id)
    wlist = db.get("list", [])
    if str(membre.id) in wlist: wlist.remove(str(membre.id))
    db["list"] = wlist; set_guild("whitelist", ctx.guild.id, db)
    await ctx.send(f"✅ {membre.mention} retiré de la whitelist.")

@bot.command(name="clear_wl")
@commands.has_permissions(administrator=True)
async def clear_wl(ctx):
    set_guild("whitelist", ctx.guild.id, {"list": []})
    await ctx.send("✅ Whitelist vidée.")

# ══════════════════════════════════════════
#  COMMANDES BLACKLIST
# ══════════════════════════════════════════
@bot.command(name="bl")
@commands.has_permissions(administrator=True)
async def bl(ctx, membre: discord.Member = None, *, raison: str = "Aucune raison"):
    db = get_guild("blacklist", ctx.guild.id)
    blist = db.get("list", {})
    if membre is None:
        if not blist: return await ctx.send("📋 Blacklist vide.")
        embed = discord.Embed(title="🚫 Blacklist", description="\n".join(f"<@{u}> — {d['raison']}" for u, d in blist.items()), color=discord.Color.red())
        return await ctx.send(embed=embed)
    blist[str(membre.id)] = {"raison": raison}
    db["list"] = blist; set_guild("blacklist", ctx.guild.id, db)
    await ctx.send(f"🚫 {membre.mention} blacklisté. Raison : **{raison}**")

@bot.command(name="blinfo")
@commands.has_permissions(administrator=True)
async def blinfo(ctx, membre: discord.Member):
    db = get_guild("blacklist", ctx.guild.id)
    entry = db.get("list", {}).get(str(membre.id))
    if entry:
        embed = discord.Embed(title=f"🚫 {membre}", description=f"**Raison :** {entry['raison']}", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"✅ {membre.mention} n'est pas blacklisté.")

@bot.command(name="unbl")
@commands.has_permissions(administrator=True)
async def unbl(ctx, membre: discord.Member):
    db = get_guild("blacklist", ctx.guild.id)
    blist = db.get("list", {})
    blist.pop(str(membre.id), None)
    db["list"] = blist; set_guild("blacklist", ctx.guild.id, db)
    await ctx.send(f"✅ {membre.mention} retiré de la blacklist.")

@bot.command(name="clear_bl")
@commands.has_permissions(administrator=True)
async def clear_bl(ctx):
    set_guild("blacklist", ctx.guild.id, {"list": {}, "bots": []})
    await ctx.send("✅ Blacklist vidée.")

@bot.command(name="blbot")
@commands.has_permissions(administrator=True)
async def blbot(ctx, sub: str = "list", membre: discord.Member = None):
    db = get_guild("blacklist", ctx.guild.id)
    bots = db.get("bots", [])
    if sub == "list":
        if not bots: return await ctx.send("📋 Aucun bot blacklisté.")
        embed = discord.Embed(title="🤖 Bots blacklistés", description="\n".join(f"<@{u}>" for u in bots), color=discord.Color.orange())
        return await ctx.send(embed=embed)
    if sub == "add" and membre:
        if str(membre.id) not in bots: bots.append(str(membre.id))
    elif sub == "del" and membre:
        if str(membre.id) in bots: bots.remove(str(membre.id))
    elif sub == "clear":
        bots = []
    db["bots"] = bots; set_guild("blacklist", ctx.guild.id, db)
    await ctx.send(f"✅ blbot `{sub}` effectué.")

# ══════════════════════════════════════════
#  COMMANDES PERMISSIONS
# ══════════════════════════════════════════
@bot.command(name="setperm")
@commands.has_permissions(administrator=True)
async def setperm(ctx, commande: str, cible: discord.Role | discord.Member):
    db = get_guild("permissions", ctx.guild.id)
    allowed = db.get(commande, [])
    if str(cible.id) not in allowed: allowed.append(str(cible.id))
    db[commande] = allowed; set_guild("permissions", ctx.guild.id, db)
    await ctx.send(f"✅ Permission `{commande}` → **{cible.name}**")

@bot.command(name="delperm")
@commands.has_permissions(administrator=True)
async def delperm(ctx, commande: str, cible: discord.Role | discord.Member):
    db = get_guild("permissions", ctx.guild.id)
    allowed = db.get(commande, [])
    if str(cible.id) in allowed: allowed.remove(str(cible.id))
    db[commande] = allowed; set_guild("permissions", ctx.guild.id, db)
    await ctx.send(f"✅ Permission `{commande}` retirée à **{cible.name}**")

@bot.command(name="clearperms")
@commands.has_permissions(administrator=True)
async def clearperms(ctx):
    set_guild("permissions", ctx.guild.id, {})
    await ctx.send("✅ Permissions réinitialisées.")

@bot.command(name="noderank")
@commands.has_permissions(administrator=True)
async def noderank(ctx, action: str, role: discord.Role):
    db = get_guild("permissions", ctx.guild.id)
    nr = db.get("noderank", [])
    if action == "add" and str(role.id) not in nr: nr.append(str(role.id))
    elif action == "del" and str(role.id) in nr: nr.remove(str(role.id))
    db["noderank"] = nr; set_guild("permissions", ctx.guild.id, db)
    await ctx.send(f"✅ noderank `{action}` : **{role.name}**")

@bot.command(name="limitrole")
@commands.has_permissions(administrator=True)
async def limitrole(ctx, action: str, role: discord.Role, nombre: int = 0):
    db = get_guild("permissions", ctx.guild.id)
    limits = db.get("limitrole", {})
    if action == "add": limits[str(role.id)] = nombre
    elif action == "del": limits.pop(str(role.id), None)
    db["limitrole"] = limits; set_guild("permissions", ctx.guild.id, db)
    await ctx.send(f"✅ limitrole `{action}` : **{role.name}**")

@bot.command(name="mainprefix")
@commands.has_permissions(administrator=True)
async def mainprefix(ctx, nouveau: str):
    bot.command_prefix = nouveau
    await ctx.send(f"✅ Préfixe → `{nouveau}`")

@bot.command(name="blrank")
@commands.has_permissions(administrator=True)
async def blrank(ctx, *args):
    db = get_guild("permissions", ctx.guild.id)
    br = db.get("blrank", {})
    if not args:
        embed = discord.Embed(title="🔒 BlRank", description=f"État : {'ON' if br.get('enabled') else 'OFF'}", color=discord.Color.purple())
        return await ctx.send(embed=embed)
    sub = args[0]
    if sub in ("on","off"): br["enabled"] = sub == "on"
    elif sub == "max" and len(args) > 1: br["max"] = int(args[1])
    db["blrank"] = br; set_guild("permissions", ctx.guild.id, db)
    await ctx.send(f"✅ blrank `{sub}`")

# ══════════════════════════════════════════
#  COMMANDES MODÉRATION
# ══════════════════════════════════════════
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, membre: discord.Member, *, raison: str = "Aucune raison"):
    if membre.top_role >= ctx.author.top_role:
        return await ctx.send("❌ Rôle trop haut.")
    await membre.ban(reason=raison)
    embed = discord.Embed(title="🔨 Banni", description=f"{membre.mention}\n**Raison :** {raison}", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, membre: discord.Member, *, raison: str = "Aucune raison"):
    if membre.top_role >= ctx.author.top_role:
        return await ctx.send("❌ Rôle trop haut.")
    await membre.kick(reason=raison)
    embed = discord.Embed(title="👢 Expulsé", description=f"{membre.mention}\n**Raison :** {raison}", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, membre: discord.Member, duree: int = 10, *, raison: str = "Aucune raison"):
    await membre.timeout(timedelta(minutes=duree), reason=raison)
    embed = discord.Embed(title="🔇 Mute", description=f"{membre.mention} — {duree} min\n**Raison :** {raison}", color=discord.Color.greyple())
    await ctx.send(embed=embed)

@bot.command(name="unmute")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, membre: discord.Member):
    await membre.timeout(None)
    await ctx.send(f"✅ {membre.mention} n'est plus muté.")

@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn(ctx, membre: discord.Member, *, raison: str = "Aucune raison"):
    db = get_guild("warns", ctx.guild.id)
    warns = db.get(str(membre.id), [])
    warns.append(raison); db[str(membre.id)] = warns
    set_guild("warns", ctx.guild.id, db)
    embed = discord.Embed(title="⚠️ Warn", description=f"{membre.mention} ({len(warns)} total)\n**Raison :** {raison}", color=discord.Color.yellow())
    await ctx.send(embed=embed)
    try: await membre.send(f"⚠️ Warn sur **{ctx.guild.name}** : {raison}")
    except: pass

@bot.command(name="warns")
async def warns(ctx, membre: discord.Member = None):
    if not membre: membre = ctx.author
    db = get_guild("warns", ctx.guild.id)
    wlist = db.get(str(membre.id), [])
    if not wlist: return await ctx.send(f"✅ {membre.mention} — aucun warn.")
    embed = discord.Embed(title=f"⚠️ Warns — {membre}", description="\n".join(f"`{i+1}.` {w}" for i,w in enumerate(wlist)), color=discord.Color.yellow())
    await ctx.send(embed=embed)

@bot.command(name="clearwarn")
@commands.has_permissions(kick_members=True)
async def clearwarn(ctx, membre: discord.Member):
    db = get_guild("warns", ctx.guild.id)
    db[str(membre.id)] = []; set_guild("warns", ctx.guild.id, db)
    await ctx.send(f"✅ Warns de {membre.mention} effacés.")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user} débanni.")

@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="mp")
@commands.has_permissions(administrator=True)
async def mp(ctx, sub_or_membre=None, *, message: str = None):
    if sub_or_membre == "settings":
        return await ctx.send("⚙️ Paramètres MP.")
    try:
        membre = await commands.MemberConverter().convert(ctx, sub_or_membre)
        if message:
            await membre.send(message)
            await ctx.send(f"✅ MP envoyé à {membre.mention}.")
    except: await ctx.send("❌ Membre introuvable.")

@bot.command(name="modmail")
@commands.has_permissions(administrator=True)
async def modmail(ctx):
    db = get_guild("config", ctx.guild.id)
    db["modmail_channel"] = ctx.channel.id
    set_guild("config", ctx.guild.id, db)
    await ctx.send("✅ Modmail configuré ici.")

@bot.command(name="openmodmail")
@commands.has_permissions(administrator=True)
async def openmodmail(ctx, membre: discord.Member):
    db = get_guild("config", ctx.guild.id)
    ch_id = db.get("modmail_channel")
    if not ch_id: return await ctx.send("❌ Modmail non configuré.")
    ch = ctx.guild.get_channel(int(ch_id))
    if ch:
        embed = discord.Embed(title="📬 Modmail", description=f"Ouvert pour {membre.mention} par {ctx.author.mention}", color=discord.Color.blurple())
        await ch.send(embed=embed)
    await ctx.send(f"✅ Modmail ouvert pour {membre.mention}.")

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, nombre: int = 10):
    await ctx.channel.purge(limit=nombre + 1)
    msg = await ctx.send(f"✅ {nombre} message(s) supprimé(s).")
    await asyncio.sleep(3); await msg.delete()

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Salon verrouillé.")

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Salon déverrouillé.")

# ══════════════════════════════════════════
#  COMMANDES SETTINGS
# ══════════════════════════════════════════
async def fetch_bytes(url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.read()

@bot.command(name="setbotname")
@commands.is_owner()
async def setbotname(ctx, *, nom: str):
    await bot.user.edit(username=nom)
    await ctx.send(f"✅ Nom → **{nom}**")

@bot.command(name="setbotpic")
@commands.is_owner()
async def setbotpic(ctx, lien: str = None):
    url = lien or (ctx.message.attachments[0].url if ctx.message.attachments else None)
    if not url: return await ctx.send("❌ Fournis un lien.")
    data = await fetch_bytes(url)
    await bot.user.edit(avatar=data)
    await ctx.send("✅ Avatar mis à jour.")

@bot.command(name="setservername")
@commands.has_permissions(manage_guild=True)
async def setservername(ctx, *, nom: str):
    await ctx.guild.edit(name=nom)
    await ctx.send(f"✅ Serveur renommé : **{nom}**")

@bot.command(name="setserverpic")
@commands.has_permissions(manage_guild=True)
async def setserverpic(ctx, lien: str = None):
    url = lien or (ctx.message.attachments[0].url if ctx.message.attachments else None)
    if not url: return await ctx.send("❌ Fournis un lien.")
    data = await fetch_bytes(url)
    await ctx.guild.edit(icon=data)
    await ctx.send("✅ Icône serveur mise à jour.")

@bot.command(name="setserverbanner")
@commands.has_permissions(manage_guild=True)
async def setserverbanner(ctx, lien: str = None):
    url = lien or (ctx.message.attachments[0].url if ctx.message.attachments else None)
    if not url: return await ctx.send("❌ Fournis un lien.")
    data = await fetch_bytes(url)
    await ctx.guild.edit(banner=data)
    await ctx.send("✅ Bannière serveur mise à jour.")

@bot.command(name="theme")
@commands.has_permissions(administrator=True)
async def theme(ctx, couleur: str):
    try: c = discord.Color(int(couleur.strip("#"), 16))
    except: return await ctx.send("❌ Couleur invalide. Ex : `+theme #FF0000`")
    db = get_guild("config", ctx.guild.id)
    db["theme"] = couleur.strip("#"); set_guild("config", ctx.guild.id, db)
    await ctx.send(embed=discord.Embed(title="🎨 Thème mis à jour", color=c))

@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def backup(ctx, action: str = "list", nom: str = None):
    db = get_guild("backups", ctx.guild.id)
    if action == "list":
        blist = db.get("list", [])
        if not blist: return await ctx.send("📋 Aucun backup.")
        embed = discord.Embed(title="💾 Backups", description="\n".join(blist), color=discord.Color.blue())
        return await ctx.send(embed=embed)
    elif action == "save":
        nom = nom or f"backup_{len(db.get('list', []))}"
        data = {
            "name": ctx.guild.name,
            "roles": [{"name": r.name, "color": r.color.value, "perms": r.permissions.value} for r in ctx.guild.roles],
            "channels": [{"name": c.name, "type": str(c.type)} for c in ctx.guild.channels],
        }
        saves = db.get("saves", {}); saves[nom] = data
        bl = db.get("list", [])
        if nom not in bl: bl.append(nom)
        db["saves"] = saves; db["list"] = bl
        set_guild("backups", ctx.guild.id, db)
        await ctx.send(f"✅ Backup **{nom}** sauvegardé.")
    elif action == "delete" and nom:
        saves = db.get("saves", {}); saves.pop(nom, None)
        bl = db.get("list", [])
        if nom in bl: bl.remove(nom)
        db["saves"] = saves; db["list"] = bl
        set_guild("backups", ctx.guild.id, db)
        await ctx.send(f"✅ Backup **{nom}** supprimé.")
    elif action == "load" and nom:
        saves = db.get("saves", {})
        data = saves.get(nom)
        if not data: return await ctx.send(f"❌ Backup **{nom}** introuvable.")
        for r in data.get("roles", []):
            if r["name"] == "@everyone": continue
            if not discord.utils.get(ctx.guild.roles, name=r["name"]):
                try: await ctx.guild.create_role(name=r["name"], color=discord.Color(r["color"]))
                except: pass
        await ctx.send(f"✅ Backup **{nom}** chargé.")
    elif action == "show" and nom:
        data = db.get("saves", {}).get(nom)
        if not data: return await ctx.send(f"❌ Backup **{nom}** introuvable.")
        embed = discord.Embed(title=f"💾 {nom}", color=discord.Color.blue())
        embed.add_field(name="Serveur", value=data.get("name","?"))
        embed.add_field(name="Rôles", value=len(data.get("roles",[])))
        embed.add_field(name="Salons", value=len(data.get("channels",[])))
        await ctx.send(embed=embed)

@bot.command(name="invisible")
@commands.is_owner()
async def invisible(ctx):
    await bot.change_presence(status=discord.Status.invisible)
    await ctx.send("✅ Invisible.")

@bot.command(name="remove_activity")
@commands.is_owner()
async def remove_activity(ctx):
    await bot.change_presence(activity=None)
    await ctx.send("✅ Activité retirée.")

@bot.command(name="stream")
@commands.is_owner()
async def stream(ctx, *, msg: str = "Crow Bot"):
    await bot.change_presence(activity=discord.Streaming(name=msg, url="https://twitch.tv/crow"))
    await ctx.send(f"✅ Stream : **{msg}**")

@bot.command(name="serverlist")
@commands.is_owner()
async def serverlist(ctx):
    lines = [f"**{g.name}** `{g.id}` — {g.member_count} membres" for g in bot.guilds]
    embed = discord.Embed(title=f"📋 Serveurs ({len(bot.guilds)})", description="\n".join(lines[:20]), color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="leave")
@commands.is_owner()
async def leave(ctx, guild_id: int = None):
    g = bot.get_guild(guild_id) if guild_id else ctx.guild
    if g: await g.leave()

@bot.command(name="changelogs")
async def changelogs(ctx):
    embed = discord.Embed(title="📋 Crow Bot — Changelogs", description="**v1.0.0** — Première version\n- Tickets\n- AntiRaid\n- WL/BL\n- Permissions\n- Modération\n- Settings", color=discord.Color.dark_red())
    await ctx.send(embed=embed)

@bot.command(name="setlang")
@commands.has_permissions(administrator=True)
async def setlang(ctx, langue: str):
    db = get_guild("config", ctx.guild.id)
    db["lang"] = langue; set_guild("config", ctx.guild.id, db)
    await ctx.send(f"✅ Langue → `{langue}`")

@bot.command(name="getlang")
async def getlang(ctx):
    db = get_guild("config", ctx.guild.id)
    await ctx.send(f"🌍 Langue : `{db.get('lang', 'fr')}`")

# ══════════════════════════════════════════
#  COMMANDES UTILS
# ══════════════════════════════════════════
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong ! **{round(bot.latency*1000)}ms**")

@bot.command(name="info")
async def info(ctx):
    embed = discord.Embed(title="🐦 Crow Bot", color=discord.Color.dark_red())
    embed.add_field(name="Serveurs", value=len(bot.guilds))
    embed.add_field(name="Membres", value=sum(g.member_count for g in bot.guilds))
    embed.add_field(name="Latence", value=f"{round(bot.latency*1000)}ms")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="helpold")
async def helpold(ctx):
    embed = discord.Embed(title="🐦 Crow Bot — Aide", description=f"Préfixe : `{PREFIX}`", color=discord.Color.dark_red())
    embed.add_field(name="🎫 Tickets", value="`+ticket setup` `+ticketrole` `+ticketcategory`", inline=False)
    embed.add_field(name="🛡️ AntiRaid", value="`+secur` `+antitoken` `+antiban` `+antichannel` `+antirole` `+antieveryone` `+antiwebhook` `+punition` `+raidlog` `+clear_webhooks`", inline=False)
    embed.add_field(name="✅ Whitelist", value="`+wl` `+unwl` `+clear_wl`", inline=False)
    embed.add_field(name="🚫 Blacklist", value="`+bl` `+blinfo` `+unbl` `+clear_bl` `+blbot`", inline=False)
    embed.add_field(name="⚙️ Permissions", value="`+setperm` `+delperm` `+clearperms` `+noderank` `+limitrole` `+mainprefix` `+blrank`", inline=False)
    embed.add_field(name="🔨 Modération", value="`+ban` `+kick` `+mute` `+unmute` `+warn` `+warns` `+clearwarn` `+unban` `+say` `+mp` `+modmail` `+clear` `+lock` `+unlock`", inline=False)
    embed.add_field(name="🔧 Settings", value="`+setbotname` `+setbotpic` `+setservername` `+setserverpic` `+setserverbanner` `+theme` `+backup` `+invisible` `+stream` `+serverlist` `+leave` `+setlang` `+changelogs`", inline=False)
    embed.add_field(name="ℹ️ Utils", value="`+ping` `+info` `+help`", inline=False)
    await ctx.send(embed=embed)

# ══════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════

import json
import os

# Charger/sauvegarder les données
PERMS_FILE = "perms_data.json"

def load_perms():
    if os.path.exists(PERMS_FILE):
        with open(PERMS_FILE, "r") as f:
            return json.load(f)
    return {
        "Perm1": "Aucun", "Perm2": "Aucun", "Perm3": "Aucun",
        "Perm4": "Aucun", "Perm5": "Aucun", "Perm6": "Aucun",
        "Perm7": "Aucun", "Perm8": "Aucun", "Perm9": "Aucun"
    }

def save_perms(data):
    with open(PERMS_FILE, "w") as f:
        json.dump(data, f)

# Commande +perms
@bot.command(name="perms")
async def perms(ctx):
    data = load_perms()
    description = ""
    for perm, roles in data.items():
        description += f"**{perm}**\n{roles}\n\n"

    embed = discord.Embed(
        title="🔐 Permissions du serveur",
        description=description,
        color=0x5865F2
    )
    embed.set_footer(text="Voir le +helpall pour voir les commandes auxquelles chaque permission donne accès")
    await ctx.send(embed=embed)

# Commande +set perms <perm> <@role>
@bot.command(name="set")
@commands.has_permissions(administrator=True)
async def set_cmd(ctx, option: str, perm: str, *, roles: str):
    if option.lower() != "perms":
        return

    data = load_perms()

    if perm not in data:
        await ctx.send(f"❌ `{perm}` est invalide. Utilise Perm1, Perm2... Perm9")
        return

    data[perm] = roles
    save_perms(data)

    embed = discord.Embed(
        description=f"✅ **{perm}** mis à jour avec : {roles}",
        color=0x57F287
    )
    await ctx.send(embed=embed)

bot.run(TOKEN)