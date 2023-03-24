import disnake
from disnake.ext import commands
import typing

import random

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # @commands.slash_command(name="choice", description="Picks a choice, at random.")
    # async def choice(self, interaction: disnake.ApplicationCommandInteraction, args: Tuple[str]):
    #     await interaction.response.send_message(content=f"Found {args}", ephemeral=True)

    @commands.slash_command(name="pick")
    async def randomizer_group(self, interaction: disnake.ApplicationCommandInteraction):
        """ Various randomizer and choice commands """
        pass

    @randomizer_group.sub_command(name="user", description="")
    async def pick_random_user(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        number_to_pick: int = 1
      ):
        """
        Pick a random N users from the server (default 1 user).

        Parameters
        ----------
        number_to_pick: :class:`int`
            The number of users to randomly select. Default 1
        """
        users = random.choices(interaction.guild.members, k=n)
        await interaction.response.send_message(embed=disnake.Embed(
            description="\n".join(user.mention for user in users),
            color=disnake.Color.blue()))
    
    # @randomizer_group.sub_command(name="number", description="Picks a random number from the given range.")
    # async def pick_random_from_range(self, interaction: disnake.ApplicationCommandInteraction, low:int=0, high:int=10):
    #     rand = random.randint(min(low, high), max(high, low))
    #     await interaction.response.send_message(embed=disnake.Embed(
    #         description=f"Your number: **{rand}**",
    #         color=disnake.Color.blue()))



# needed per cog
def setup(bot):
    bot.add_cog(UtilsCog(bot))