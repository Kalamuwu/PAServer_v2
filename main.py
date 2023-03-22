print("Starting server...\n")

import dotenv
dotenv.load_dotenv(".env")

import os
import sys
import asyncio
import typing
import traceback
import enum
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from vars import author_id


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=commands.when_mentioned,
                   help_command=None,
                   activity=discord.Activity(
                       type=discord.ActivityType.watching,
                       name="/help  |  ver0.1.0-stable"),
                   intents=intents)

bot.author_id = author_id

##
##  Cog management
##

from cog_management import get_possible_cogs

@bot.event
async def on_ready():
    # display loaded
    print("", datetime.now().strftime('Loaded %d %b %Y %H:%M'),
          f"Username {bot.user}",
          f"User ID  {bot.user.id}",
          sep='\nAPI  ')
    # sync commands
    await bot.tree.sync()
    print("-- Bot Initialized --\n")


if __name__ == '__main__':
    from cog_management import get_possible_cogs
    async def load_extensions():
        await bot.load_extension("cog_management")  # load special cog_management cog
        for cog in get_possible_cogs(refresh=True):
            try: await bot.load_extension("cogs."+cog)  # load the rest of the cogs from the `cogs/` fodler
            except: print(f"ERR  Errorred loading cog {cog}!")
    asyncio.run(load_extensions())

    from keep_alive import keep_alive
    keep_alive()
    bot.run(os.environ['DISCORD_TOKEN'])
