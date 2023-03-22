### PAServer_v2
# Multi-function Discord bot
## Based on [DiscordPy](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html), more specifically [DiscordPy Application Commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html#application-commands).

## Config
Configuring for your server will probably not be too straightforward; as this bot is meant for a specific server, a lot of values (IDs, names, etc) are hard-coded

## Cogs
By default, the bot will attempt to load any files in `./cogs` as [Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#cogs), and will not attempt to load anything in `./cogs-disabled`. Cogs can be loaded and unloaded with built-in functionality for `/cog load`, `/cog unload`, and `/cog reload`, and `/cog sync` for updating the discord cache of what the bot can do[^1].

[^1]: See [discord.app_commands.CommandTree.sync](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.CommandTree.sync) for more -- tl;dr Discord doesn't notice any new application commands until you sync the command tree. Restarting the bot has the same effect, since it syncs on bot startup, but this is not reccommended for quick development because there's a chance you'll get ratelimited.
