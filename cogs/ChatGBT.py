import disnake
import openai
from disnake.ext import commands

tempenv = "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"
class ChatGBT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@commands.slash_command(name = "ChatGBT")
async def ChatGBT(self, inter:disnake.ApplicationCommandInteraction, prompt = ""):
    completion = openai.Completion.create(
    engine=model_engine,
    prompt=prompt,
    max_tokens=1024,
    n=1,
    stop=None,
    temperature=0.5,)
    response = completion.choices[0].text
    print(response)



# needed per cog
def setup(bot):
    bot.add_cog(ChatGBT(bot))