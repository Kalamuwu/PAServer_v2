import disnake
from disnake.ext import commands
import typing

def author_only():
    async def predicate(ctx):
        return ctx.author.id == author_id
    return commands.check(predicate)

def dev_only():
    return commands.check(commands.has_role(929569069806534656).predicate)

def admin_only():
    # order of checks: dev -> admin -> off_duty_admin -> trial_admin
    return commands.check(commands.has_role(929569069806534656).predicate) or \
           commands.check(commands.has_role(907303043467444275).predicate) or \
           commands.check(commands.has_role(908833495277797396).predicate) or \
           commands.check(commands.has_role(903262332447232002).predicate)