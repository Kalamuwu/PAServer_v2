import discord
from discord import app_commands
from discord.ext import commands
import os, requests, typing

from vars import author_id


class DevCog(commands.Cog, name="Developer Commands"):
    """Developer and testing commands"""
    def __init__(self, bot):
        self.bot = bot
    
    def dev_only():
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id == 594154260271464458
        return app_commands.check(predicate)
    
    def bot_author_only():
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id == author_id
        return app_commands.check(predicate)

    # @commands.command(name='pastebin', aliases=['file'])
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

    @app_commands.command(name="channelinfo", description="Get the current channel deve info (channel name and ID)")
    async def get_curr_channel_id(self, i: discord.Interaction):
        await i.response.send_message(f"Channel name: `{i.channel}`\nChannel id: `{i.channel_id}`", ephemeral=True)


# needed per cog
async def setup(bot):
    await bot.add_cog(DevCog(bot))
