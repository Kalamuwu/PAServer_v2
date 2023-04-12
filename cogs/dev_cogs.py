import disnake
from disnake.ext import commands
import typing

import os
import requests

from vars import author_id
from checks import dev_only


class DevCog(commands.Cog, name="Developer Commands"):
    """Developer and testing commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## TODO might add this back later? idk
    # @commands.slash_command(name='pastebin', aliases=['file'])
    # async def pastebin(self, ctx, *args):
    #     args, flags = disassemble(' '.join(args))
    #     # creates a new PasteBin
    #     res = requests.post('https://pastebin.com/api/api_post.php',
    #                         data={
    #                             'api_dev_key':
    #                             os.environ['PASTEBIN_TOKEN'],
    #                             'api_option':
    #                             'paste',
    #                             'api_paste_code':
    #                             ' '.join(args),
    #                             'api_paste_name':
    #                             f'{ctx.message.author.display_name}\'s Paste'
    #                         })
    #     res = res.content.decode('utf-8')
    #     print(res)
    #     if 'https://pastebin.com' not in res:
    #         await ctx.send(f'Bad request; error:  `{res}`')
    #     else:
    #         await ctx.send(res)

    @commands.slash_command(name="channelinfo")
    @dev_only()
    async def get_curr_channel_id(self, i: disnake.ApplicationCommandInteraction):
        """ Get the current channel developer info (channel name and ID). """
        await i.response.send_message(f"Channel name: `{i.channel}`\nChannel id: `{i.channel_id}`\nGuild id: `{i.guild_id}`", ephemeral=True)


# needed per cog
def setup(bot):
    bot.add_cog(DevCog(bot))
