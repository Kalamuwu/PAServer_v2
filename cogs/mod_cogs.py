import disnake
from disnake.ext import commands
import typing

class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def getinfo(self, user: disnake.Member) -> disnake.Embed:
        embed = disnake.Embed(
            title=user.display_name,
            description=f'{user.name}#{user.discriminator}',
            color=user.color)
        embed.set_thumbnail(url=user.display_avatar)
        embed.add_field(
            name="Registered",
            value=user.created_at.strftime("%b %d %Y %H:%M:%S"),
            inline=True)
        try:
            embed.add_field(
                name="Joined",
                value=user.joined_at.strftime("%b %d %Y %H:%M:%S"),
                inline=True)
        except: pass
        embed.add_field(
            name="Roles",
            value='\n'.join(role.mention for role in user.roles),
            inline=False)
        embed.set_footer(text=f"ID:  {user.id}\nis_bot  {user.bot}")
        return embed

    @commands.slash_command(name="whois")
    async def whois(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member):
        """
        Gathers information about a specific user.

        Parameters
        ----------
        user: :class:`disnake.User`
            The user to gather information on
        """
        await interaction.response.send_message(embed=self.getinfo(user))

    @commands.slash_command(name="whoami")
    async def whoami(self, interaction: disnake.ApplicationCommandInteraction):
        """ Gathers information about you. Alias to running /whois on yourself. """
        await interaction.response.send_message(embed=self.getinfo(interaction.user))


# needed per cog
def setup(bot):
    bot.add_cog(ModCog(bot))