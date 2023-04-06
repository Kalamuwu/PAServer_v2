print("Starting server...\n")

import dotenv
dotenv.load_dotenv(".env")

import asyncio
import enum
import os
import sys
import traceback
from datetime import datetime

import disnake
from disnake.ext import commands
import typing

from vars import author_id


intents = disnake.Intents.all()
bot = commands.InteractionBot(activity=disnake.Activity(
                                  type=disnake.ActivityType.watching,
                                  name="/help  |  ver1.1.0-release"),
                              intents=intents,
                              command_sync_flags=commands.CommandSyncFlags.all())

bot.author_id = author_id

from cog_management import get_possible_cogs

@bot.event
async def on_ready():
    print("", datetime.now().strftime('Loaded %d %b %Y %H:%M'),
          f"Username {bot.user}",
          f"User ID  {bot.user.id}",
          sep='\nAPI  ')
    print("API  -- Bot Initialized --\n")


if __name__ == '__main__':
    bot.load_extension("cog_management")  # load special cog_management cog
    bot.load_extension("help.help")       # load special help menu cog
    for cog in get_possible_cogs(refresh=True):
        try: bot.load_extension("cogs."+cog)  # load the rest of the cogs from the `cogs/` folder
        except Exception as e: print(f"ERR  Errorred loading cog {cog}! {e}")
    
    bot.run(os.environ['DISCORD_TOKEN'])
