import disnake
from disnake.ext import commands
import typing

import os
import requests

from vars import author_id
from checks import author_only


class FollowMeCog(commands.Cog, name="FollowMe Commands"):
    """ Makes the bot do what I say. """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command(name="followme")
    @author_only()
    async def follow_me_group(self, i):
        """ Do what I say >:) """
        pass

    @follow_me_group.sub_command(name="reply")
    async def reply(self, interaction: disnake.ApplicationCommandInteraction, string: str, reply_id = commands.Param(large=True)):
        """
        Says the given string.

        Parameters
        ----------
        string :class:`str`
            This is the string the bot will say.
        reply_id :class:`int`
            The message ID to reply to.
        """
        reply_message = interaction.channel.get_partial_message(reply_id)
        try:
            await reply_message.reply(string)
        except disnake.HTTPException as e:
            await interaction.response.send_message(f"Invalid message ID {reply_id}!")
        else:
            await interaction.response.defer()
            await interaction.delete_original_response()

    @follow_me_group.sub_command(name="say")
    async def say(self, interaction: disnake.ApplicationCommandInteraction, string: str):
        """
        Says the given string.

        Parameters
        ----------
        string :class:`str`
            This is the string the bot will say.
        """
        await interaction.channel.send(string)
        await interaction.response.defer()
        await interaction.delete_original_response()
    
    @follow_me_group.sub_command(name="react")
    async def react(self, interaction: disnake.ApplicationCommandInteraction, emoji: str, message_id = commands.Param(large=True)):
        """
        Says the given string.

        Parameters
        ----------
        emoji :class:`str`
            This is the string the bot will say.
        message_id :class:`int`
            The message ID to reply to.
        """
        react_message = interaction.channel.get_partial_message(message_id)
        try:
            await react_message.add_reaction(emoji)
        except disnake.HTTPException as e:
            await interaction.response.send_message(f"Invalid message ID `{message_id}` or emoji `{emoji}`!")
        else:
            await interaction.response.defer()
            await interaction.delete_original_response()


# needed per cog
def setup(bot):
    bot.add_cog(FollowMeCog(bot))
