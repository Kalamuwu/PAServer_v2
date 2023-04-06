import disnake
from disnake.ext import commands

import enum
import os
import typing
import os
import enum

from checks import dev_only

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
        def __init__(self, head:str, comment:str, emoji:str, log_type:str, color:disnake.Color):
            self.head = head
            self.comment = comment
            self.emoji = emoji
            self.log_type = log_type
            self.color = color
        
        def to_embed(self) -> disnake.Embed:
            print(repr(self))
            return disnake.Embed(
                description=str(self),
                color=self.color
            )
        
        def __str__(self):
            """ Returns formatting for a disnake.Embed """
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
        return cls.EmbedFormat(head, comment, '🧪', "DBG", disnake.Color.blue())
        
    @classmethod
    def OK(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '✅', "SUC", disnake.Color.green())
    
    @classmethod
    def WARNING(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '⚠️', "WRN", disnake.Color.yellow())

    @classmethod
    def ERROR(cls, head:str, comment:str="") -> EmbedFormat:
        return cls.EmbedFormat(head, comment, '🚫', "ERR", disnake.Color.red())


class CogManagementCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot


    def __do_on_single_cog(self, i: disnake.ApplicationCommandInteraction, cog: str, ac: CogAction) -> EmbedFormatter.EmbedFormat:
        if cog not in get_possible_cogs():
            raise commands.ExtensionNotFound(f"The cog `{cog}` was not found!")
        
        cog = "cogs." + cog
        if ac == CogAction.LOAD:
            if cog in self.bot.extensions:
                return EmbedFormatter.WARNING(f"`{cog}` already loaded; skipping")
            try:
                self.bot.load_extension(cog)
                return EmbedFormatter.OK(f"Loaded `{cog}`")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        elif ac == CogAction.UNLOAD:
            if cog not in self.bot.extensions:
                return EmbedFormatter.WARNING(f"{cog} not loaded!")
            try:
                self.bot.unload_extension(cog)
                return EmbedFormatter.OK(f"Unloaded `{cog}`")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        elif ac == CogAction.RELOAD:
            if cog in self.bot.extensions:
                self.bot.unload_extension(cog)
            try:
                self.bot.load_extension(cog)
                return EmbedFormatter.OK(f"Reloaded {cog}")
            except commands.ExtensionError as e:
                return EmbedFormatter.ERROR(f"`{cog}` had an error loading:", comment=f"\n> ```{e}```")
        
        else: raise ValueError(f"Unknown action `{ac}`!")


    async def __do_on_cog_set(self, i: disnake.ApplicationCommandInteraction, cog: str, ac: CogAction) -> bool:
        extensions = get_possible_cogs()  # so this is only called once
        if cog == 'all':  # tries on all cogs
            text = ""
            colors = set()
            for extension in extensions:
                resp = self.__do_on_single_cog(i, extension, ac)
                text += str(resp)
                colors.add(resp.color)
            if len(text) and len(colors):
                if   disnake.Color.red() in colors:     color = disnake.Color.red()
                elif disnake.Color.yellow() in colors:  color = disnake.Color.yellow()
                elif disnake.Color.green() in colors:   color = disnake.Color.green()
                else:                                   color = disnake.Color.blue()
                print(repr(resp))
                await i.response.send_message(
                    embed=disnake.Embed(
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
                    resp = self.__do_on_single_cog(i, c, ac)
                    await i.response.send_message(embed=resp.to_embed(), ephemeral=True)
                    return True
            # no cog found
            embed = EmbedFormatter.ERROR(f"Unknown cog `{cog}`")
            await i.response.send_message(embed=embed, ephemeral=True)
            return False
    

    @staticmethod
    async def do_cog_autocomplete(interaction: disnake.ApplicationCommandInteraction, current: str):
        return ["all"] + [cog for cog in get_possible_cogs() if current.lower() in cog.lower()]

    @commands.slash_command(name="cog")
    @dev_only()
    async def __cog_modification_command_group(self, interaction: disnake.ApplicationCommandInteraction):
        """ Commands relating to the loading, unloading, and reloading of cogs attached to the bot. """
        pass

    @__cog_modification_command_group.sub_command(name="load")
    async def do_cog_load(self, i: disnake.ApplicationCommandInteraction, cog: str = commands.Param(autocomplete=do_cog_autocomplete)):
        """
        Loads an unloaded cog. Use 'all' to load all cogs.

        Parameters
        ----------
        cog: :class:`str`
            The name of the cog to load
        """
        await self.__do_on_cog_set(i, cog, CogAction.LOAD)

    @__cog_modification_command_group.sub_command(name="unload")
    async def do_cog_unload(self, i: disnake.ApplicationCommandInteraction, cog: str = commands.Param(autocomplete=do_cog_autocomplete)):
        """
        Unloads a loaded cog. Use 'all' to unload all cogs.

        Parameters
        ----------
        cog: :class:`str`
            The name of the cog to unload
        """
        await self.__do_on_cog_set(i, cog, CogAction.UNLOAD)

    @__cog_modification_command_group.sub_command(name="reload")
    async def do_cog_reload(self, i: disnake.ApplicationCommandInteraction, cog: str = commands.Param(autocomplete=do_cog_autocomplete)):
        """
        Reloads a cog. Use 'all' to reload all cogs.

        Parameters
        ----------
        cog: :class:`str`
            The name of the cog to reload
        """
        await self.__do_on_cog_set(i, cog, CogAction.RELOAD)

    @__cog_modification_command_group.sub_command(name="list")
    async def do_cog_list(self, i: disnake.ApplicationCommandInteraction, refresh_cached_list: bool = True):
        """
        Lists all loaded and unloaded cogs.

        Parameters
        ----------
        refresh_cached_list: :class:`bool`
            Whether or not to refresh the internally-cached list
        """
        loaded = []
        unloaded = []
        cogs = get_possible_cogs(refresh=refresh_cached_list)
        for cog in cogs:
            if 'cogs.'+cog in self.bot.extensions.keys():
                loaded.append(cog)
            else:
                unloaded.append(cog)
        disabled = [file[:-3] for file in os.listdir('./cogs-disabled') if file.endswith(".py")]
        text = ""
        if len(loaded):   text += "\n**Loaded:**\n> `"   + '`\n> `'.join(loaded)   + '`\n'
        if len(unloaded): text += "\n**Unloaded:**\n> `" + '`\n> `'.join(unloaded) + '`\n'
        if len(disabled): text += "\n**Disabled:**\n> `" + '`\n> `'.join(disabled) + '`\n'
        await i.response.send_message(embed=disnake.Embed(
            description=text if len(text) else "\n🚫 **No cogs found!**\n",
            color=disnake.Color.green() if len(text) else disnake.color.red()
        ), ephemeral=True)


# needed per cog
def setup(bot):
    bot.add_cog(CogManagementCog(bot))