import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")
PREFIX = "+"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    COGS = [
        "cogs.gestion",
        "cogs.utils",
        "cogs.logs",
        "cogs.tickets",
        "cogs.antiraid"
        "cogs.embed"
    ]
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog chargé : {cog}")
        except Exception as e:
            print(f"❌ Erreur sur {cog} : {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="le serveur"))
    print(f"✅ {bot.user} connecté.")

bot.run(TOKEN)
