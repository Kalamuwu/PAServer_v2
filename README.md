### PAServer_v2
# Multi-function Discord bot
## Based on [Disnake](https://docs.disnake.dev/en/stable/api.html), more specifically [Disnake Slash Commands](https://docs.disnake.dev/en/stable/api.html#slashcommand).

## Config
Configuring for your server will probably not be too straightforward; as this bot is meant for a specific server, a lot of values (IDs, names, etc) are hard-coded

## Cogs
By default, the bot will attempt to load any files in `./cogs` as [Cogs](https://docs.disnake.dev/en/stable/ext/commands/api.html#cogs), and will not attempt to load anything in `./cogs-disabled`. Cogs can be loaded and unloaded with built-in functionality for `/cog load`, `/cog unload`, and `/cog reload`, and *`/cog sync` for updating the discord cache of what the bot can do[^1]*.

[^1]: The old version of this bot, based on DiscordPy, had functionality to sync application commands at-will. I don't know if this is possible with Disnake; maybe it isn't, or maybe I just don't know the right keywords to search the docs for. I'll keep trying to make syncing at-will work.

## In Development
Items checked off have been pushed to features.
[X] Cog loading/unloading
[X] New member verification
[X] Role menus