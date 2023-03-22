import typing
import os
import enum

import discord
from discord import app_commands
from discord.ext import commands

__global_cogs = []  # cog list caching
def get_possible_cogs(refresh=False) -> typing.List[str]:
    global __global_cogs
    if refresh or len(__global_cogs)==0:
        cogs = []
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                cogs.append(file[:-3])  # strip ".py"
        __global_cogs = cogs
        return cogs
    else: return __global_cogs


class CogAction(enum.Enum):
    NOOP   = 0b00
    LOAD   = 0b01
    UNLOAD = 0b10
    RELOAD = 0b11
    
    @staticmethod
    def format_error(e: commands.ExtensionFailed) -> str:
        """ Returns the formatted string containing the error. """
        print(e)
        _, err = str(e).split(": ", 2)
        return "> " + err.replace('\n', "\n> ")


class EmbedFormatter():
    class EmbedFormat():
        def __init__(self, head:str, comment:str, emoji:str, log_type:str, color:discord.Color):
            self.head = head
            self.comment = comment
            self.emoji = emoji
            self.log_type = log_type
            self.color = color
        
        def to_embed(self) -> discord.Embed:
            print(repr(self))
            return discord.Embed(
                description=str(self),
                color=self.color
            )
        
        def __str__(self):
            """ Returns formatting for a discord.Embed """
            s = f"\n{self.emoji} **{self.head}**\n"
            if self.comment != "":
                s += self.comment + '\n'
            return s
        def __repr__(self):
            """ Returns formatting for output logging """
            s = f"{self.log_type}  {self.head}"
            if self.comment != "":
                s += self.comment.replace('\n', "\n     ")
            return s
    
    @classmethod
    def DEBUG(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '🧪', "DBG", discord.Color.blue())
        
    @classmethod
    def OK(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '✅', "SUC", discord.Color.green())
    
    @classmethod
    def WARNING(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '⚠️', "WRN", discord.Color.yellow())

    @classmethod
    def ERROR(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '🚫', "ERR", discord.Color.red())


class CogManagementCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot


    async def __do_on_single_cog(self, i: discord.Interaction, cog: str, ac: CogAction) -> EmbedFormatter.EmbedFormat:
        if cog not in get_possible_cogs():
            raise commands.ExtensionNotFound(f"The cog `{cog}` was not found!")
        
        cog = "cogs." + cog
        if ac == CogAction.LOAD:
            if cog in self.bot.extensions:
                return EmbedFormatter.WARNING(f"`{cog}` already loaded; skipping")
            try:
                await self.bot.load_extension(cog)
                return EmbedFormatter.OK(f"Loaded `{cog}`")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        elif ac == CogAction.UNLOAD:
            if cog not in self.bot.extensions:
                return EmbedFormatter.WARNING(f"{cog} not loaded!")
            try:
                await self.bot.unload_extension(cog)
                return EmbedFormatter.OK(f"Unloaded `{cog}`")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        elif ac == CogAction.RELOAD:
            if cog in self.bot.extensions:
                await self.bot.unload_extension(cog)
            try:
                await self.bot.load_extension(cog)
                return EmbedFormatter.OK(f"Reloaded {cog}")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        else: raise ValueError(f"Unknown action `{ac}`!")


    async def __do_on_cog_set(self, i: discord.Interaction, cog: str, ac: CogAction) -> bool:
        extensions = get_possible_cogs()  # so this is only called once
        if cog == 'all':  # tries on all cogs
            text = ""
            colors = set()
            for extension in extensions:
                resp = await self.__do_on_single_cog(i, extension, ac)
                text += str(resp)
                colors.add(resp.color)
            if len(text) and len(colors):
                if   discord.Color.red() in colors:     color = discord.Color.red()
                elif discord.Color.yellow() in colors:  color = discord.Color.yellow()
                elif discord.Color.green() in colors:   color = discord.Color.green()
                else:                                   color = discord.Color.blue()
                print(repr(resp))
                await i.response.send_message(
                    embed=discord.Embed(
                        description=text,
                        color=color
                    ), ephemeral=True)
                return True
            else:
                embed = EmbedFormatter.ERROR("No cogs found!").to_embed()
                await i.response.send_message(embed=embed, ephemeral=True)
                return False
        else:  # tries on single cog, passed as e.x. `dev_cogs` or `cogs.dev_cogs`
            for c in [cog, "cogs."+cog]:
                if c in extensions:
                    resp = await self.__do_on_single_cog(i, c, ac)
                    await i.response.send_message(embed=resp.to_embed(), ephemeral=True)
                    return True
        # no cog found
        embed = EmbedFormatter.ERROR(f"Unknown cog `{cog}`")
        await i.response.send_message(embed=embed, ephemeral=True)
        return False


    @app_commands.autocomplete()
    async def do_cog_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in get_possible_cogs()
            if current.lower() in cog.lower()
        ] + [app_commands.Choice(name="all", value="all")]

    __cog_modification_command_group = app_commands.Group(name="cog", description="Commands relating to the loading, unloading, and reloading of cogs attached to the bot.")

    @__cog_modification_command_group.command(name="load",    description="Loads an unloaded cog. Use 'all' to reload all cogs.")
    @app_commands.autocomplete(cog=do_cog_autocomplete)
    async def do_cog_load(self, i: discord.Interaction, cog: str):
        await self.__do_on_cog_set(i, cog, CogAction.LOAD)

    @__cog_modification_command_group.command(name="unload",  description="Unloads a loaded cog. Use 'all' to reload all cogs.")
    @app_commands.autocomplete(cog=do_cog_autocomplete)
    async def do_cog_unload(self, i: discord.Interaction, cog: str):
        await self.__do_on_cog_set(i, cog, CogAction.UNLOAD)

    @__cog_modification_command_group.command(name="reload",  description="Reloads a cog. Use 'all' to reload all cogs.")
    @app_commands.autocomplete(cog=do_cog_autocomplete)
    async def do_cog_reload(self, i: discord.Interaction, cog: str):
        await self.__do_on_cog_set(i, cog, CogAction.RELOAD)

    @__cog_modification_command_group.command(name="list",    description="Lists all loaded and unloaded cogs.")
    async def do_cog_list(self, i: discord.Interaction, refresh_cached_list:bool=True):
        loaded = []
        unloaded = []
        cogs = get_possible_cogs(refresh=refresh_cached_list)
        for cog in cogs:
            if cog in self.bot.extensions:
                loaded.append(cog)
            else:
                unloaded.append(cog)
        text = ""
        if len(loaded):   text += "\n**Loaded:**\n> `"   + '`\n> `'.join(loaded)   + '`\n'
        if len(unloaded): text += "\n**Unloaded:**\n> `" + '`\n> `'.join(unloaded) + '`\n'
        await i.response.send_message(embed=discord.Embed(
            description=text if len(text) else "\n🚫 **No cogs found!**\n",
            color=discord.Color.green() if len(text) else discord.color.red()
        ), ephemeral=True)


    @__cog_modification_command_group.command(name="sync",    description="Re-sync the bot application commands.")
    async def do_cog_sync(self, i: discord.Interaction):
        try:
            await i.response.defer()
            print("SYNC  Starting command sync")
            await self.bot.tree.sync()
            print("SYNC  Finished command sync")
        except Exception as e:
            es = '> ' + str(e).replace('\n', '\n> ')
            embed = EmbedFormatter.ERROR("An error occurred:", comment=es)
            await i.followup.send(embed=embed.to_embed(), ephemeral=True)
        else:
            embed = EmbedFormatter.OK("Application commands synced successfully")
            await i.followup.send(embed=embed.to_embed(), ephemeral=True)

    # bot.tree.add_command(cog_modification_command_group)



# needed per cog
async def setup(bot):
    await bot.add_cog(CogManagementCog(bot))