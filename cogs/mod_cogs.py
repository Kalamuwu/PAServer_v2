import discord
from discord import app_commands
from discord.ext import commands

class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def getinfo(self, user: discord.Member) -> discord.Embed:
        embed = discord.Embed(
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

    @app_commands.command(name="whois", description="Gathers information about a specific user.")
    async def whois(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(embed=self.getinfo(user))

    @app_commands.command(name="whoami", description="Gathers information about you. Alias to running /whois on yourself.")
    async def whoami(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.getinfo(interaction.user))


# needed per cog
async def setup(bot):
    await bot.add_cog(ModCog(bot))