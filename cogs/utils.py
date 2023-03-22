import discord
from discord import app_commands
from discord.ext import commands

import random

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # @app_commands.command(name="choice", description="Picks a choice, at random.")
    # async def choice(self, interaction: discord.Interaction, args: Tuple[str]):
    #     await interaction.response.send_message(content=f"Found {args}", ephemeral=True)

    randomizer_group = app_commands.Group(name="pick", description="Various randomizer and choice commands")

    @randomizer_group.command(name="user", description="Pick a random N users from the server")
    async def pick_random_user(self, interaction: discord.Interaction, number_to_pick:app_commands.Range[int,1]=1):
        users = random.choices(interaction.guild.members, k=number_to_pick)
        await interaction.response.send_message(embed=discord.Embed(
            description="\n".join(user.mention for user in users),
            color=discord.Color.blue()))



# needed per cog
async def setup(bot):
    await bot.add_cog(UtilsCog(bot))