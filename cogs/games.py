import disnake
from disnake.ext import commands
from disnake import ui
import typing

import random

class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    
    class RPS:
        class Player:
            def __init__(self, user:disnake.User|None, choice:str):
                self.user = user
                self.name = user.display_name if user is not None else "Computer"
                self.color = user.color if user is not None else disnake.Color.dark_grey()
                self.choice = choice
        @staticmethod
        def parse(character:str) -> str:
            return "🪨" if character == "r" else "📜" if character == "p" else "✂️"
        @classmethod
        def check(cls, player1:Player, player2:Player) -> disnake.Embed:
            if player1.choice == player2.choice:
                title = "Tie game!"
                color = disnake.Color.dark_grey()
            else:
                if   player1.choice == "r":  win = player1 if player2.choice == "s" else player2
                elif player1.choice == "p":  win = player1 if player2.choice == "r" else player2
                else:                        win = player1 if player2.choice == "p" else player2
                title = win.name + " wins!"
                color = win.color
            return disnake.Embed(title=title, color=color) \
                .add_field(name=player1.name, value=cls.parse(player1.choice), inline=True) \
                .add_field(name=player2.name, value=cls.parse(player2.choice), inline=True)

    class TTT:
        class Player:
            def __init__(self, user:disnake.User|None):
                self.user = user
                self.name = user.display_name if user is not None else "Computer"
                self.color = user.color if user is not None else disnake.Color.dark_gray()
        @staticmethod
        def check_single(bitboard:int) -> int:
            """ Returns the bitboard matching the win condition, otherwise 0 if not a win. """
            for i in range(3):  # row bitboard checks
                board = 7 << (3*i)
                if bitboard & board == board: return board
            for i in range(3):  # col bitboard checks
                board = 73 << i
                if bitboard & board == board: return board
            if bitboard & 273 == 273: return 273  # top-left to bottom-right
            if bitboard & 84 == 84: return 84  # top-right to bottom-left
            return 0
        @classmethod
        def game_over(cls, x_bitboard:int, o_bitboard:int, winning_board:int) -> ui.View:
            view = ui.View()
            for i in range(9):
                shift = 256>>i
                style = disnake.ButtonStyle.green if winning_board&shift else disnake.ButtonStyle.gray
                emoji = "❌" if x_bitboard&shift else "⭕" if o_bitboard&shift else "🫙"
                view.add_item(ui.Button(emoji=emoji, style=style, row=i//3, disabled=True))
            return view
        @classmethod
        def game_not_over(cls, x_bitboard:int, o_bitboard:int, is_xs_turn:bool, px_id:int, po_id:int) -> ui.View:
            total_bits = (x_bitboard<<10) | (o_bitboard<<1) | (is_xs_turn&1)
            view = ui.View()
            for i in range(9):
                shift = 256>>i
                if x_bitboard & shift:
                    view.add_item(ui.Button(emoji="❌", disabled=True, style=disnake.ButtonStyle.gray, row=i//3))
                elif o_bitboard & shift:
                    view.add_item(ui.Button(emoji="⭕", disabled=True, style=disnake.ButtonStyle.gray, row=i//3))
                else:
                    view.add_item(ui.Button(emoji="🫙", style=disnake.ButtonStyle.blurple, custom_id=f"tttpl-{hex(total_bits)}-{i}-{hex(px_id)}-{hex(po_id)}", row=i//3))
            return view
        @classmethod
        def parse_bitboard(cls, bitboard:int, x_player:Player, o_player:Player) -> typing.Tuple[disnake.Embed, ui.View]:
            """ The first 9 bytes represent the X board; the next 9 bytes represent the O board; the next bit represents who just went (1 for X, 0 for O). """
            did_x_just_go = bitboard & 1
            o_board = (bitboard & 1022) >> 1
            x_board = (bitboard & 523264) >> 10
            if (board:=cls.check_single(x_board)):
                return (
                    disnake.Embed(
                        title=x_player.name + " wins!",
                        color=x_player.color
                    ), cls.game_over(x_board, o_board, board))
            elif (board:=cls.check_single(o_board)):
                return (
                    disnake.Embed(
                        title=o_player.name + " wins!",
                        color=o_player.color
                    ), cls.game_over(x_board, o_board, board))
            elif x_board|o_board == 511:
                title = "Tie Game!"
                color = disnake.Color.dark_gray()
            else:
                title = f"TicTacToe - {o_player.name if did_x_just_go else x_player.name}'s Turn"
                color = o_player.color if did_x_just_go else x_player.color
            return (
                disnake.Embed(title=title, color=color),
                cls.game_not_over(x_board, o_board, did_x_just_go^1, x_player.id, o_player.id)
            )


    
    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.ApplicationCommandInteraction):
        if interaction.type == disnake.InteractionType.component:

            # RPS vs computer
            if interaction.data["custom_id"].startswith("rpsai-"):
                if interaction.user.id != int(interaction.data["custom_id"][8:],16):
                    await interaction.response.send_message(embed=disnake.Embed(
                        description="🚫 **Only the people who requested the game may play!**",
                        color=disnake.Color.red()
                    ), ephemeral=True)
                else:
                    player = self.RPS.Player(interaction.user, interaction.data["custom_id"][6])
                    ai = self.RPS.Player(None, random.choice(["r","p","s"]))
                    await interaction.message.edit(embed=self.RPS.check(player, ai), view=None)
                    await interaction.response.defer()

            # RPS vs player
            elif interaction.data["custom_id"].startswith("rpspl-"):
                _, p1_choice, p1_id, p2_choice, p2_id = interaction.data["custom_id"].split("-")
                p1_id, p2_id = int(p1_id,16), int(p2_id,16)
                if interaction.user.id not in [p1_id, p2_id]:
                    await interaction.response.send_message(embed=disnake.Embed(
                        description="🚫 **Only the people who requested the game may play!**",
                        color=disnake.Color.red()
                    ), ephemeral=True)
                else:
                    if p2_choice == "a":  # player 1 just chose
                        if interaction.user.id != p1_id:
                            await interaction.response.send_message(embed=disnake.Embed(
                                description="🚫 **It's not your turn!**",
                                color=disnake.Color.red()
                            ), ephemeral=True)
                        else:
                            p2 = interaction.guild.get_member(p2_id)
                            view = ui.View(timeout=30)
                            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="🪨", row=1, custom_id=f"rpspl-{p1_choice}-{p1_id}-r-{p2_id}"))
                            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="📜", row=1, custom_id=f"rpspl-{p1_choice}-{p1_id}-p-{p2_id}"))
                            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="✂️", row=1, custom_id=f"rpspl-{p1_choice}-{p1_id}-s-{p2_id}"))
                            await interaction.message.edit(
                                embed=disnake.Embed(
                                    description=f"{p2.mention}, choose your fighter!",
                                    color=disnake.Color.dark_gray()
                                ), view=view)
                            await interaction.response.defer()
                    else:  # player 2 just chose
                        if interaction.user.id != p2_id:
                            await interaction.response.send_message(embed=disnake.Embed(
                                description="🚫 **It's not your turn!**",
                                color=disnake.Color.red()
                            ), ephemeral=True)
                        else:
                            p1 = self.RPS.Player(interaction.guild.get_member(p1_id), p1_choice)
                            p2 = self.RPS.Player(interaction.guild.get_member(p2_id), p2_choice)
                            await interaction.message.edit(embed=self.RPS.check(p1, p2), view=None)
                            await interaction.response.defer()

            # TTT vs player
            elif interaction.data["custom_id"].startswith("tttpl-"):
                _, board, tile, p1_id, p2_id = interaction.data["custom_id"].split('-')
                board, tile, p1_id, p2_id = int(board,16), int(tile), int(p1_id,16), int(p2_id,16)
                if interaction.user.id not in [p1_id, p2_id]:
                    await interaction.response.send_message(embed=disnake.Embed(
                        description="🚫 **Only the people who requested the game may play!**",
                        color=disnake.Color.red()
                    ), ephemeral=True)
                else:
                    did_x_just_go = board & 1
                    if interaction.user.id != [p2_id, p1_id][did_x_just_go]:
                        await interaction.response.send_message(embed=disnake.Embed(
                            description="🚫 **It's not your turn!**",
                            color=disnake.Color.red()
                        ), ephemeral=True)
                    else:
                        px, po = interaction.guild.get_member(p1_id), interaction.guild.get_member(p2_id)
                        move = 512>>tile
                        move <<= 9*did_x_just_go
                        embed, view = self.TTT.parse_bitboard(board|move, px, po)
                        await interaction.message.edit(embed=embed, view=view)
                        await interaction.response.defer()


    @commands.slash_command(name="games")
    async def games_group(self, i):
        """ Various minigames! """
        pass
    @games_group.sub_command_group(name="vs-computer")
    async def computer_group(self, i):
        """ Play games against the computer! """
        pass
    @games_group.sub_command_group(name="vs-user")
    async def player_group(self, i):
        """ Play games against another user! """
        pass

    @computer_group.sub_command(name="rps")
    async def rps_ai(self, interaction:disnake.ApplicationCommandInteraction):
        """ A simple game of rock-paper-scissors, versus the computer! """
        view = ui.View(timeout=30)
        view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="🪨", row=1, custom_id=f"rpsai-r-{hex(interaction.user.id)}"))
        view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="📜", row=1, custom_id=f"rpsai-p-{hex(interaction.user.id)}"))
        view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="✂️", row=1, custom_id=f"rpsai-s-{hex(interaction.user.id)}"))
        await interaction.response.send_message(
            embed=disnake.Embed(
                description="Choose your fighter!",
                color=disnake.Color.light_grey()
            ), view=view)

    @player_group.sub_command(name="rps")
    async def rps_player(self, interaction:disnake.ApplicationCommandInteraction, against: disnake.User):
        """
        A simple game of rock-paper-scissors, versus another player.

        Parameters
        ----------
        against: :class:`disnake.User`
            The user to play against
        """
        if against.id == interaction.user.id:
            await interaction.response.send_message(embed=disnake.Embed(
                description="🚫 **You cant play yourself, silly!**",
                color=disnake.Color.red()
            ), ephemeral=True)
        else:
            view = ui.View(timeout=30)
            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="🪨", row=1, custom_id=f"rpspl-r-{hex(interaction.user.id)}-a-{hex(against.id)}"))
            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="📜", row=1, custom_id=f"rpspl-p-{hex(interaction.user.id)}-a-{hex(against.id)}"))
            view.add_item(ui.Button(style=disnake.ButtonStyle.green, emoji="✂️", row=1, custom_id=f"rpspl-s-{hex(interaction.user.id)}-a-{hex(against.id)}"))
            await interaction.response.send_message(
                embed=disnake.Embed(
                    description=f"{interaction.user.mention}, choose your fighter!",
                    color=disnake.Color.light_grey()
                ), view=view)

    @player_group.sub_command(name="ttt")
    async def ttt_player(self, interaction:disnake.ApplicationCommandInteraction, against: disnake.User):
        """
        A simple game of tictactoe, versus another player.

        Parameters
        ----------
        against: :class:`disnake.User`
            The user to play against
        """
        if against.id == interaction.user.id:
            await interaction.response.send_message(embed=disnake.Embed(
                description="🚫 **You cant play yourself, silly!**",
                color=disnake.Color.red()
            ), ephemeral=True)
        else:
            view = ui.View()
            for i in range(9):
                view.add_item(ui.Button(emoji="🫙", style=disnake.ButtonStyle.blurple, custom_id=f"tttpl-1-{i}-{hex(interaction.user.id)}-{hex(against.id)}", row=i//3))
            await interaction.response.send_message(embed=disnake.Embed(
                title=f"TicTacToe - {interaction.user.display_name}'s Turn",
                color=interaction.user.color
            ), view=view)



# needed per cog
def setup(bot):
    bot.add_cog(GamesCog(bot))