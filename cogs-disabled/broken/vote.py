import disnake
from disnake import app_commands
from disnake.ext import commands
from disnake import ui

import typing
import uuid

from vars import admin_id, giveaway_id

class MetaModal(ui.Modal):
    name =     ui.TextInput(label="Vote title",                                required=True,  custom_id="name")
    question = ui.TextInput(label="Vote question",                             required=True,  custom_id="question")
    # time =     ui.TextInput(label="Vote time (sec) -- blank or 0 for endless", required=False, custom_id="time")
    def __init__(self):
        super().__init__(title="Create Vote", custom_id=f"vote-meta")

class OptionsModal(ui.Modal):
    option1 = ui.TextInput(label="Option 1",            required=True,  custom_id="option1")
    option2 = ui.TextInput(label="Option 2",            required=True,  custom_id="option2")
    option3 = ui.TextInput(label="Option 3 (optional)", required=False, custom_id="option3")
    option4 = ui.TextInput(label="Option 4 (optional)", required=False, custom_id="option4")
    option5 = ui.TextInput(label="Option 5 (optional)", required=False, custom_id="option5")
    def __init__(self, vote_id):
        super().__init__(title="Create Vote - Options", custom_id=f"vote-create-{vote_id}")

active_votes = {
    # vote_id: { message_id, channel_id, options[], time_left }
}
pending_votes = {
    # vote_id: { interaction, title, question, time }
}
class Vote:
    global active_votes

    def __init__(self, interaction: disnake.Interaction, name:str, question:str, time:int):
        self.name = name
        self.question = question
        self.time = time
    
    @staticmethod
    def from_interaction(interaction:disnake.Interaction):
        pass

class VoteCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
    
    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.Interaction):
        global active_votes, pending_votes
        if interaction.type == disnake.InteractionType.modal_submit:
            if interaction.data['custom_id'][0:4] == "vote":

                if interaction.data['custom_id'][5:9] == "meta":
                    # parse input
                    title =    interaction.data['components'][0]['components'][0]['value']
                    question = interaction.data['components'][1]['components'][0]['value']
                    time =     interaction.data['components'][2]['components'][0]['value']
                    try: time = int(float(time))
                    except ValueError: time = 0
                    # generate unique vote id
                    uid = uuid.uuid4().hex
                    # make embed
                    embed = disnake.Embed(
                        title="Configuring Vote",
                        description="I received the following metadata:\n",
                        color=disnake.Color.blue()
                    )
                    embed.add_field(name="Title",    value=title)
                    embed.add_field(name="Question", value=question)
                    embed.add_field(name="Time",     value=(time if time > 0 else "Endless"))
                    embed.set_footer(text=f"Vote UUID {uid}")
                    # set up time options
                    options = [
                        disnake.SelectOption(label="Endless", value="0"),
                        disnake.SelectOption(label="10 sec",  value="10"),
                        disnake.SelectOption(label="30 sec",  value="30"),
                        disnake.SelectOption(label="2 min",   value="120"),
                        disnake.SelectOption(label="5 min",   value="300"),
                        disnake.SelectOption(label="15 min",  value="900"),
                        disnake.SelectOption(label="1 hour",  value="3600"),
                    ]
                    if interaction.user.get_role(admin_id) or interaction.user.get_role(giveaway_id):
                        options += [  # longer timing options for admin and giveaway mods
                            disnake.SelectOption(label="1 day",  value="86400"),
                            disnake.SelectOption(label="2 days", value="172800"),
                            disnake.SelectOption(label="3 days", value="259200"),
                            disnake.SelectOption(label="5 days", value="432000"),
                            disnake.SelectOption(label="7 days", value="604800")
                        ]
                    # make buttons and time select menu
                    view = ui.View()
                    view.add_item(ui.Button(label="Make with up/downvote (standard)", custom_id=f"vote-standard-{uid}"))
                    view.add_item(ui.Button(label="Make with custom options", custom_id=f"vote-custom-{uid}"))
                    # add to pending and send
                    pending_votes[uid] = { 'interaction': interaction, 'title': title, 'question': question, 'time': time }
                    await interaction.response.send_message(embed=embed, view=view)
                
                elif interaction.data['custom_id'][5:11] == "create":
                    # parse data
                    vote_id = int(interaction.data['custom_id'].split('-')[-1])
                    title, question, time = pending_votes[vote_id]
                    options = [ c['components'][0]['value'] for c in interaction.data['components'] ]
                    await interaction.response.send_message(f"metadata `{title}`, `{question}`, `{time}` sec\noptions `{options}`")
                
        elif interaction.type == disnake.InteractionType.component:
            if interaction.data['custom_id'][0:4] == "vote":
                _, typ, vote_id = interaction.data['custom_id'].split('-')
                print(pending_votes[vote_id])
                title = pending_votes[vote_id]['title']
                question = pending_votes[vote_id]['question']
                time = pending_votes[vote_id]['time']
                past_interaction = pending_votes[vote_id]['interaction']
                await past_interaction.edit_original_response(
                    embed=disnake.Embed(
                        title="Created Vote",
                        description="You may dismiss this message now.",
                        color=disnake.Color.green()
                    ), view=None)
                # custom options - prompt modal
                if typ == "custom":
                    await interaction.response.send_modal(OptionsModal(vote_id))
                # standard vote; create with up and downvotes
                elif typ == "standard":
                    await interaction.response.send_message(f"created {vote_id} as a standard vote", ephemeral=True)
                    del pending_votes[vote_id]


    vote_command_group = app_commands.Group(name="vote", description="Commands relating to creating and finishing votes.")

    @vote_command_group.command(name="create", description="Create a new vote.")
    async def create_vote(self, interaction: disnake.Interaction):
        await interaction.response.send_modal(MetaModal())



# needed per cog
async def setup(bot):
    await bot.add_cog(VoteCog(bot))