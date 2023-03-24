import disnake
import openai
from disnake.ext import commands

tempenv = "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"
class ChatGBT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot





# needed per cog
def setup(bot):
    bot.add_cog(ChatGBT(bot))