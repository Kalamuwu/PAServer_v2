import disnake
from disnake import ui
from disnake.ext import commands
import typing

from datetime import datetime

class BaseAction:
    """ Parent action class """

    alerts_channel = 1093591960431906837
    logging_channel = 907779740713254942

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.timestamp = datetime.now()
    
    def get_channel(self, **kwargs) -> disnake.TextChannel:
        raise ValueError("Cannot be used on base class!")
    
    def to_embed(self, **kwargs) -> disnake.Embed:
        raise ValueError("Cannot be used on base class!")
    
    async def audit(self, **kwargs) -> None:
        raise ValueError("Cannot be used on base class!")


def make_action(bot: commands.InteractionBot, to_embed: typing.Callable[[], disnake.Embed], required_parameters = list(), optional_parameters = dict(), important: bool = False):
    class Action(BaseAction):
        def __init__(self, **kwargs):
            super().__init__(bot)
            for req in set(required_parameters):
                if req not in kwargs:
                    raise ValueError(f"Missing required param {req}")
                setattr(self, req, kwargs[req])
            for opt,placeholder in optional_parameters.items():
                if opt not in kwargs or kwargs[opt] is None:
                    setattr(self, opt, placeholder)
                else:
                    setattr(self, opt, kwargs[opt])
        async def audit(self):
            embed = self.to_embed()
            if embed is not None:
                await self.get_channel().send(embed=embed)
            else:
                print("ERR  Could not generate embed!")
    Action.to_embed = to_embed
    Action.bot = bot
    
    def alert_channel(self: Action):
        return self.bot.get_channel(BaseAction.alerts_channel)
    def log_channel(self: Action):
        return self.bot.get_channel(BaseAction.logging_channel)
    Action.get_channel = alert_channel if important else log_channel
    
    return Action
