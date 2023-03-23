import disnake

from disnake.ext import commands
import os, requests, typing

from vars import author_id


class DevCog(commands.Cog, name="Developer Commands"):
    """Developer and testing commands"""
    def __init__(self, bot):
        self.bot = bot
    
    ## TODO i dont think these are the same in disnake
    # def dev_only():
    #     def predicate(interaction: disnake.ApplicationCommandInteraction) -> bool:
    #         return interaction.user.id == 594154260271464458
    #     return commands.check(predicate)
    # 
    # def bot_author_only():
    #     def predicate(interaction: disnake.ApplicationCommandInteraction) -> bool:
    #         return interaction.user.id == author_id
    #     return commands.check(predicate)

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
    async def get_curr_channel_id(self, i: disnake.ApplicationCommandInteraction):
        """ Get the current channel developer info (channel name and ID). """
        await i.response.send_message(f"Channel name: `{i.channel}`\nChannel id: `{i.channel_id}`", ephemeral=True)


# needed per cog
def setup(bot):
    bot.add_cog(DevCog(bot))
