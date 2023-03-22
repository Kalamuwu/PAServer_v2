import disnake
from disnake import app_commands
from disnake.ext import commands
from disnake import ui

import typing

game_names = {
    "Treasure Wars":     "tw",
    "SkyWars Standard":  "sws",
    "SkyWars Kits":      "swk",
    "Block Party":       "bp",
    "Capture the Flag":  "ctf",
    "DeathRun":          "dr",
    "Hide n Seek":       "hs",
    "Murder Mystery":    "mm",
}
games = {}
for k,v in game_names.items(): games[v] = 0
pending_votes = {
    # userid: { 3: code_1st, 2: code_2nd, 1: code_3rd }
}

class TempCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.Interaction):
        global games, pending_votes
        if interaction.type == disnake.InteractionType.component:
            # check if user exists
            if interaction.user.id not in pending_votes: pending_votes[interaction.user.id] = {}
            if interaction.data['custom_id'][0:8] == "gamevote":
                if interaction.data['custom_id'] == "gamevote-submit":
                    # check for duplicates
                    for pts,code in pending_votes[interaction.user.id].items():
                        for pts2,code2 in pending_votes[interaction.user.id].items():
                            if pts != pts2 and code == code2:
                                # duplicate
                                return await interaction.response.send_message(
                                    embed=disnake.Embed(
                                        title="Vote Failure",
                                        description="**You can't vote for the same game twice!**",
                                        color=disnake.Color.red()
                                    )
                                , ephemeral=True)
                    try:  # check for missing
                        for i in range(1,4): pending_votes[interaction.user.id][i]
                    except KeyError:
                        # missing
                        print("missing", i)
                        return await interaction.response.send_message(
                            embed=disnake.Embed(
                                title="Vote Failure",
                                description="**You haven't voted for at least one rank!**",
                                color=disnake.Color.red()
                            )
                        , ephemeral=True)
                    else:
                        # tally points
                        for pts in range(1,4):
                            games[pending_votes[interaction.user.id][pts]] += pts
                        return await interaction.response.send_message(embed=disnake.Embed(
                            description="**✅ Submitted voting results!**",
                            color=disnake.Color.green()
                        ), ephemeral=True)
                else:
                    pts = int(interaction.data['custom_id'][9])
                    pending_votes[interaction.user.id][pts] = interaction.data['values'][0]
                    return await interaction.response.send_message(embed=disnake.Embed(
                        description="✅ Registered selection",
                        color=disnake.Color.green()
                    ), delete_after=2, ephemeral=True)

    
    game_vote_command_group = app_commands.Group(name="gamevote", description="Commands relating to ranked-choice game voting.")

    @game_vote_command_group.command(name="vote", description="Rank your top 3 game choices.")
    async def vote_for_top_3(self, i: disnake.Interaction):
        global game_names
        view = ui.View()
        options = [ disnake.SelectOption(label=k, value=v) for k,v in game_names.items() ]
        view.add_item(ui.Select(options=options, placeholder="First Choice",  custom_id="gamevote-3"))
        view.add_item(ui.Select(options=options, placeholder="Second Choice", custom_id="gamevote-2"))
        view.add_item(ui.Select(options=options, placeholder="Third Choice",  custom_id="gamevote-1"))
        view.add_item(ui.Button(label="Submit", style=disnake.ButtonStyle.green, custom_id="gamevote-submit"))
        await i.response.send_message(
            embed=disnake.Embed(
                title="Game Vote",
                description="Rank your top 3 game choices",
                color=disnake.Color.purple()
            ), view=view, ephemeral=True)
    
    @game_vote_command_group.command(name="check", description="Check the current voted game.")
    async def check(self, i: disnake.Interaction):
        global games, game_names
        await i.response.send_message(embed=disnake.Embed(
            title="Current Voting Stats",
            description='> '+'\n> '.join([f"{name}  **`{games[code]}`**" for name,code in game_names.items()]),
            color=disnake.Color.blue()
        ))
    
    @game_vote_command_group.command(name="reset", description="Resets the game voting scores.")
    async def reset(self, i: disnake.Interaction):
        global games, pending_votes
        for k in games.keys(): games[k] = 0
        pending_votes = {}
        await i.response.send_message(embed=disnake.Embed(
            description="**✅ Reset game votes**",
            color=disnake.Color.green()
        ))


# needed per cog
async def setup(bot):
    await bot.add_cog(TempCog(bot))