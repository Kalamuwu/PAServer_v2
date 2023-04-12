import disnake
from disnake.ext import commands
from disnake import ui
import typing

import json

from checks import dev_only

class HelpCog(commands.Cog, name="Help Commands"):
    help_data = []
    help_data_flattened = {}
    num_listings_per_page = 6
    
    """ Help commands, help menu, and help subcommands """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        res = self.__class__.load_command_data()
        if not res["error"]:
            self.__class__.help_data = res["data"]["object"]
            self.__class__.help_data_flattened = res["data"]["commands"]
        else:
            raise commands.ExtensionError(message=f"CRIT Couldn't load help data with error {res['error']}")
            
    
    @classmethod
    def generate_page_buttons(cls, curr_page: int) -> ui.View:
        last_page = len(cls.help_data_flattened) // cls.num_listings_per_page
        return ui.View() \
            .add_item(ui.Button(
                emoji="⬅️",
                style=disnake.ButtonStyle.grey if curr_page==0 else disnake.ButtonStyle.blurple,
                custom_id="helppage-disabled1" if curr_page==0 else f"helppage-{curr_page-1}",
                disabled=(curr_page == 0),
                row=1)) \
            .add_item(ui.Button(
                emoji="🏠",
                style=disnake.ButtonStyle.grey if curr_page==0 else disnake.ButtonStyle.blurple,
                custom_id=f"helppage-disabled2" if curr_page==0 else "helppage-home",
                disabled=(curr_page == 0),
                row=1)) \
            .add_item(ui.Button(
                emoji="➡️",
                style=disnake.ButtonStyle.grey if curr_page==last_page else disnake.ButtonStyle.blurple,
                custom_id="helppage-disabled3" if curr_page==last_page else f"helppage-{curr_page+1}",
                disabled=(curr_page == last_page),
                row=1))
    
    @classmethod
    def generate_help_page_n(cls, page: int) -> disnake.Embed:
        embed = disnake.Embed(
            title=f"Help - Page {page+1} of {len(cls.help_data_flattened)//cls.num_listings_per_page+1}",
            color=disnake.Color.blue())
        flat = list(cls.help_data_flattened.values())
        for i in range(page*cls.num_listings_per_page, min((page+1)*cls.num_listings_per_page, len(cls.help_data_flattened))):
            data = flat[i]
            embed.add_field(name=data["command"], value=data["description"], inline=False)
        return embed
    
    @classmethod
    def load_command_data(self) -> dict:
        """
        Parses `help/help.json` into:
          (I)  an object representing the command tree
          (II) a 1D list of all commands and groups
        
        -----
        
        help/help.json formatting specs:
        
        help.json represents List[Union[command, command_group]]
        
        struct argument = {
            name: str,
            description: str,
            type: str,
            optional: bool
        }
        struct command = {
            type: "command",
            command: str,
            description: str,
            syntax: str,
            category: str,
            admin_only: bool,
            args: argument[]
        }
        struct command_group = {
            type: "group",
            command: str,
            description: str,
            category: str,
            admin_only: bool,
            subcommands: command[]
        }
        """
        try:
            with open("help/help.json", 'r') as file:
                data = json.load(file)
                flattened_commands = {}
                to_parse_base = [d for d in data]
                while len(to_parse_base):
                    sub = to_parse_base.pop(0)
                    if sub["type"] == "group":
                        for i,subsub in enumerate(sub["subcommands"]):
                            sub["subcommands"][i]["command"] = sub["command"] + ' ' + subsub["command"]
                        to_parse_base = sub["subcommands"] + to_parse_base
                        name = sub["command"]
                        sub["command"] = "(group) `" + sub["command"] + '`'
                    else:
                        name = sub["command"]
                        sub["command"] = '`' + sub["command"] + '`'
                    flattened_commands[name] = { "command": sub["command"], "description": sub["description"] }
                return { "data": {"object": data, "commands": flattened_commands}, "error": False }
        except KeyError as e:
            print("ERR  Couldn't load help data; malformed!", e)
            return { "data": e, "error": True }
        except Exception as e:
            print("ERR  Couldn't load help data; error is:", e)
            return { "data": e, "error": True }
    
    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.ApplicationCommandInteraction):
        if interaction.type == disnake.InteractionType.component:
            if interaction.data["custom_id"].startswith("helppage-"):
                help_page_num = interaction.data["custom_id"].split("-")[1]
                help_page_num = 0 if help_page_num == "home" else int(help_page_num)
                embed = self.__class__.generate_help_page_n(help_page_num)
                view = self.__class__.generate_page_buttons(help_page_num)
                await interaction.response.defer()
                await interaction.message.edit(embed=embed, view=view)
    
    @commands.slash_command(name="reload-help")
    @dev_only()
    async def reload_help_data(self, interaction: disnake.ApplicationCommandInteraction):
        res = self.load_command_data()
        if res["error"]:
            print("HELP Errored loading -- error:", res["data"])
            await interaction.response.send_message(
                embed=disnake.Embed(
                    description=f"🚫 **Error loading command data! Please contact the developer!**",
                    color=disnake.Color.red()
                ))
        else:
            self.__class__.help_data = res["data"]["object"]
            self.__class__.help_data_flattened = res["data"]["commands"]
            print("HELP loaded new help data:\n", self.__class__.help_data)
            await interaction.response.send_message(
                embed=disnake.Embed(
                    description="✅ **Reloaded command help data**",
                    color=disnake.Color.green()
                ))
    
    @classmethod
    def _find_in_list(cls, command_list:list, name:str) -> dict:
        for cmd in command_list:
            if cmd["command"] == f"`{name}`" or cmd["command"] == f"(group) `{name}`":
                return cmd
        raise KeyError(f"Command or group `{name}` not found in list `{command_list}`!")
    
    @classmethod
    def format_help_for_command(cls, command_string: str) -> disnake.Embed:
        """ Formats the loaded help data into a `disnake.Embed` for command `command_string`. """
        *pregroups, cmd = command_string.split(" ")
        curr_group = cls.help_data
        for i in range(len(pregroups)):
            curr_group = cls._find_in_list(curr_group, ' '.join(pregroups[0:i+1]))["subcommands"]
        cmd = cls._find_in_list(curr_group, command_string)
        fmt_arg = lambda arg: f"**Param `{arg['name']}`**\n> " + arg['description'].replace('\n', '\n> ') + ("\n> *Optional.*" if arg["optional"] else "\n> *Required.*")
        if cmd["type"] == "command":
            return disnake.Embed(
                title=f"Help for command `{command_string}`",
                description=f"**Command**\t{cmd['command']}\n" +
                            f"**Syntax**\t`{cmd['syntax']}`\n" +
                            f"**Description**\t{cmd['description']}\n\n" +
                            f"**Category**\t*{cmd['category'].title()}*\n" +
                            ("**Admin-only** Yes\n\n" if cmd["admin_only"] else "\n") +
                            ('\n\n'.join(fmt_arg(arg) for arg in cmd["args"])),
                color=disnake.Color.blue())
        else:
            return disnake.Embed(
                title=f"Help for group `{command_string}`",
                description=f"**Command**\t{cmd['command']}\n" +
                            f"**Description**\t{cmd['description']}\n\n" +
                            f"**Category**\t*{cmd['category'].title()}*\n" +
                            ("**Admin-only** Yes\n\n" if cmd["admin_only"] else "\n") +
                            ('\n'.join(f"**Subcommand `{sub['command']}`**" for sub in cmd["subcommands"])),
                color=disnake.Color.blue())

    @commands.slash_command(name="help")
    async def get_help_for_string(self, interaction: disnake.ApplicationCommandInteraction, command_name=commands.Param(default=None)):
        """ Basic help for command `command_name`. If no argument is supplied, this gives a command overview. """
        if command_name is None:
            embed = self.__class__.generate_help_page_n(0)
            view = self.__class__.generate_page_buttons(0)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            if command_name not in self.__class__.help_data_flattened:
                return await interaction.response.send_message(
                    embed=disnake.Embed(
                        description=f"🚫 **Command `{command_name}` not found!**",
                        color=disnake.Color.red()
                    ))
            await interaction.response.send_message(embed=self.__class__.format_help_for_command(command_name))



# needed per cog
def setup(bot):
    bot.add_cog(HelpCog(bot))
