import disnake
from disnake import ui
from disnake.ext import commands
import typing

from datetime import datetime
import json

from server_logging import make_action, BaseAction

from checks import dev_only, admin_only

class LoggingCog(commands.Cog, name="Logging"):
    """ Handles common action logging (nick change, leaves, etc) and logging-related actions """

    ##TODO set up all sorts of handlers for avatar changes, nick changes, joins
    # and leaves, maybe even edits and deletes? idk just yet, just a bunch of
    # handlers and logging stats

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        def to_embed(self: BaseAction):
            return disnake.Embed(
                description=f"test_value {self.test_value}",
                color=disnake.Color.purple()
            )
        self.DebugAction = make_action(bot, to_embed, required_parameters=["test_value"])

    @commands.slash_command(name="test-log")
    @dev_only()
    async def test_log(self, interaction: disnake.ApplicationCommandInteraction):
        myAction = self.DebugAction(test_value = 15)
        await myAction.audit()


# needed per cog
def setup(bot):
    bot.add_cog(LoggingCog(bot))