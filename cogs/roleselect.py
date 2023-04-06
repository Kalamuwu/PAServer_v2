import disnake
from disnake.ext import commands
from disnake import ui
import typing

# class RoleSelect(ui.Select):
#     def __init__(self, custom_id:str, options:typing.List[disnake.SelectOption], only_one:bool=False, allow_empty:bool=True, placeholder:str="Select"):
#         """ Initialize a new RoleSelect handler """
#         custom_id = "rolemenu-" + custom_id
#         if allow_empty: options.append(disnake.SelectOption(label="None", value="0"))
#         super().__init__(placeholder=placeholder, options=options, custom_id=custom_id, max_values=1 if only_one else len(options))
#     async def callback(self, interaction: disnake.ApplicationCommandInteraction): pass  # handled in on_interaction below

class RoleSelectCog(commands.Cog, name='RoleSelect Cog'):
    """ This cog handles role select interactions """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    known_rolemenus = {
        "color_roles": [899376611814670376, 899376914333040701, 899376964937322566, 899377152728903711, 899378077317091378, 899377212153815041, 899377291510050846, 899377342756044810, 899377501137150012, 899378012204707851, 899377632473415721, 899377900233588746, 899377826376056882],
        "pronouns":    [899371117666521178, 899371152877711441, 899371185329037322, 899371222083731508, 899371302614343731, 957976015207014410, 899372444735905843, 899401124031914044, 957976073231011840],
        "pings": [957985234136227890, 957985334157799524],
        "dms": [957985376922927135, 957985444568641566],
        "graduation_year": [899383365382320149, 899383402074083359, 899383430406602782, 998406336180146220],
        "vent": [903681643548672020],
        "lgbt": [1039151271371874314],
        "server_pings": [900006786013224970, 900006978926039070, 904931272445554698]
    }

    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.ApplicationCommandInteraction):
        if interaction.type == disnake.InteractionType.component:
            if interaction.data['custom_id'][0:9] == "rolemenu-":
                _, label = interaction.data['custom_id'].split('-')
                if label not in self.known_rolemenus:
                    raise ValueError(f"Unknown rolemenu {label}! Something has gone wrong!")
                print("DEV  Received data from rolemenu", label)
                roles  = [int(i) for i in self.known_rolemenus[label]]
                uroles = [r.id for r in interaction.user.roles]
                vroles = [int(r) for r in interaction.data['values']]
                text = ""
                for ri in roles:
                    ro = interaction.guild.get_role(ri)
                    if ro is not None:
                        if ri not in uroles and ri in vroles:
                            text += f"✅ Gave role {ro.mention}\n"
                            await interaction.user.add_roles(ro)
                        elif ri in uroles and ri not in vroles:
                            text += f"✅ Removed role {ro.mention}\n"
                            await interaction.user.remove_roles(ro)
                    else:
                        text += f"Could not find role {ri}, something has gone wrong!"
                if text != "":
                    await interaction.response.send_message(
                        embed=disnake.Embed(
                            description="\n"+text,
                            color=disnake.Color.green()
                        ), ephemeral=True)
                else:
                    await interaction.response.send_message(
                        embed=disnake.Embed(
                            description="\n⚠️ No new roles to grant or revoke!\n",
                            color=disnake.Color.yellow()
                        ), ephemeral=True)
    

    ## EXAMPLE command to create a role menu
    # @commands.slash_command(name="generate-rolemenu")
    # async def make_rolemenu(self, interaction: disnake.ApplicationCommandInteraction):
    #     options = [
    #         disnake.SelectOption(label="Vent channel access", value="903681643548672020"),
    #     ]
    #     options2 = [
    #         disnake.SelectOption(label="LGBTQ :D", value="1039151271371874314")
    #     ]
    #     view = ui.View()
    #     view.add_item(RoleSelect(options=options, custom_id="vent", only_one=True, allow_empty=True, placeholder="Vent channel access"))
    #     view.add_item(RoleSelect(options=options2, custom_id="lgbt", only_one=True, allow_empty=True, placeholder="🌈❓"))
    #     await interaction.channel.send(embed=disnake.Embed(
    #         title="Other Roles",
    #         color=disnake.Color.from_rgb(0, 0, 0)
    #     ), view=view)
    #     await interaction.response.send_message("Created rolemenu.", delete_after=5, ephemeral=True)


# needed per cog
def setup(bot):
    bot.add_cog(RoleSelectCog(bot))