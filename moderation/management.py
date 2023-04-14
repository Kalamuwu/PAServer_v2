import disnake
from disnake import ui
from disnake.ext import commands
from disnake.ext import tasks
import typing

from dateutil import parser as dateparser
from datetime import datetime, timedelta
import json

from checks import admin_only
from vars import verified_role
from server_logging import make_action, BaseAction

def parseTimeOffset(string: str) -> datetime:
    current = 0
    delta = {string:0 for string in ["weeks", "days", "hours", "minutes", "seconds"]}
    def setTo(string):
        if delta[string]:
            raise ValueError("Invalid time string")
        delta[string] = current
    for i,c in enumerate(string.lower()):
        if c == ' ': continue  # skip spaces
        if c.isnumeric():
            current *= 10
            current += int(c)
        else:
            if   c == 'w':  setTo("weeks")
            elif c == 'd':  setTo("days")
            elif c == 'h':  setTo("hours")
            elif c == 'm':  setTo("minutes")
            elif c == 's':  setTo("seconds")
            else: raise ValueError(f"Invalid time code '{c}'")
            current = 0
    return datetime.now() + timedelta(**delta)

def parseTime(timestring: str) -> datetime:
    try:
        time = parseTimeOffset(timestring)
    except ValueError as e1:
        try:
            time = dateparser.parse(timestring)
        except dateparser.ParserError as e2:
            raise ValueError(f"Invalid time string '{timestring}'")
    return time

class ModActionUserFromId:
    """ Simple meta class, for passing a user not within the guild to a ModAction """
    def __init__(self, id: int):
        self.id = id
        self.display_name = str(id)
        self.color = disnake.Color.dark_gray()
        self.avatar = None
        self.dm_channel = None
    async def create_dm(self): return None

class ActionSet:
    @staticmethod
    def mod_audit_embed(self: BaseAction, is_dm: bool = False, timer_expired: bool = False):
        r = " Timer expired" if timer_expired else ("\n> " + (self.reason.replace('\n', '\n> ') if self.reason is not None else "None"))
        desc = "Done on "
        if not timer_expired: desc += f"{self.author.mention}'s authority, on "
        desc += f"<t:{int(self.timestamp.timestamp())}:f>\n\n**Reason:**{r}\n"
        if self.does_expire: desc += f"\n\n**Expires** {self.expires}"
        try: desc += eval('f"""' + self.extra_text + '"""')
        except AttributeError: pass
        embed = disnake.Embed(
            title=f"{self.what_happened.title()} user {self.victim.display_name}",
            description=desc,
            color=self.color
        )
        if not is_dm: embed.set_footer(text=f"Victim ID: {self.victim.id}").set_thumbnail(self.victim.avatar)
        return embed

    @classmethod
    def make_mod_action(cls, bot: commands.InteractionBot, what_happened: str, color: disnake.Color, extra_required_parameters=list(), extra_optional_parameters=dict(), does_expire: bool = True):
        extra_optional_parameters["reason"] = None
        if does_expire: extra_optional_parameters["expires"] = None
        for p in ["author", "victim"]:
            if p not in extra_required_parameters:
                extra_required_parameters.append(p)
        Action = make_action(bot, cls.mod_audit_embed, required_parameters=extra_required_parameters, optional_parameters=extra_optional_parameters, important=True)
        Action.what_happened = what_happened
        Action.does_expire = does_expire
        Action.color = color
        async def dm_user(self: BaseAction, user: typing.Union[disnake.Member, ModActionUserFromId], embed: disnake.Embed):
            if isinstance(user, ModActionUserFromId):
                user = await self.bot.get_or_fetch_user(user.id)
            if user is not None and isinstance(user, (disnake.Member, disnake.User)):
                dmc = user.dm_channel  # try grabbing existing dm channel
                if dmc is None:
                    dmc = await user.create_dm()  # create new dm channel
                if dmc is not None:
                    await dmc.send(embed=embed)
                else:
                    print(f"ERR  Could not DM user about {self.what_happened}; could not open or create DM channel")
            else:
                print(f"ERR  Could not DM user about {self.what_happened}; could not find user {user.id} (type {type(user)})")
        Action.dm_user = dm_user
        async def audit(self: BaseAction, response: disnake.InteractionResponse = None, timer_expired: bool = False) -> bool:
            # print correct reason
            if not timer_expired:
                print(f"ADMN  {self.author.display_name} {self.what_happened.lower()} user {self.victim.display_name}, reason:", self.reason)
            else:
                print(f"ADMN  Timer expired; {self.what_happened.lower()} user {self.victim.display_name}")
            # send in channel and in alerts
            if (embed:=self.to_embed(timer_expired = timer_expired)) is not None:
                await self.get_channel().send(embed=embed)
                if response is not None:
                    await response.send_message(embed=embed)
            else:
                print("ERR  Could not generate channel embed!")
            # dm user
            if (embed:=self.to_embed(timer_expired = timer_expired, is_dm = True)) is not None:
                await self.dm_user(self.victim, embed)
            else:
                print("ERR  Could not generate DM embed!")
        Action.audit = audit
        return Action

    def __init__(self, bot: commands.InteractionBot, typ: str, what_happened_string: str, role_id: int, color: disnake.Color, uncolor: disnake.Color, does_expire: bool = True):
        self.typ = typ
        res = self.load_data()
        if res["error"]:
            print(f"CRIT  Could not load {typ} data, error: {res['data']}")
        else:
            self.data = res['data']
        self.what_happened_string = what_happened_string
        self.role_id = role_id
        self.action = self.__class__.make_mod_action(bot, what_happened_string, color, does_expire=does_expire)
        self.undo_action = self.__class__.make_mod_action(bot, "Un"+what_happened_string.lower(), uncolor, does_expire=False)
    
    def load_data(self) -> dict:
        try:
            with open(f"moderation/{self.typ}.json", 'r') as file:
                data = json.load(file)
                return { "data": data, "error": False }
        except FileNotFoundError as fnfe:
            with open(f"moderation/{self.typ}.json", 'w') as file:
                file.write("[]")
                return { "data": [], "error": False }
        except Exception as e:
            return { "data": e, "error": True }
    
    def dump_data(self) -> None:
        with open(f"moderation/{self.typ}.json", 'w') as file:
            json.dump(self.data, file, indent=4)
    
    def find(self, userid: int):
        for d in self.data:
            if d["userid"] == userid:
                return d
        return None

    def add(self, userid: int, reason: str, expires: datetime = None):
        self.data.append({
            "userid": userid,
            "reason": reason,
            "expires": int(expires.timestamp()) if expires is not None else None,
            "when": int(datetime.now().timestamp())
        })
    
    def remove(self, userid: int):
        for i,d in enumerate(self.data):
            if d["userid"] == userid:
                return self.data.pop(i)
        return None

class BansCog(commands.Cog, name="Ban Management Cog"):
    """ Handles ban commands and ban list """

    num_listings_per_page = 4
    alerts_channel = 1093591960431906837

    lists = {}

    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.__class__.lists = {
            "ban": ActionSet(bot, "ban", "Banned", 1093592734880763984, disnake.Color.red(), disnake.Color.yellow()),
            "mute": ActionSet(bot, "mute", "Muted", 899677826393980949, disnake.Color.green(), disnake.Color.blue())
        }
        self.list_ticker.start()
    
    def cog_unload(self):
        self.list_ticker.cancel()

    @tasks.loop(seconds=5.0)
    async def list_ticker(self):
        cur = datetime.now().timestamp()
        for name,lst in self.__class__.lists.items():
            changed = False
            for i in range(len(lst.data)-1,-1,-1):
                if lst.data[i]["expires"] is not None and lst.data[i]["expires"] < cur:
                    changed = True
                    # fetch affected user, if possible
                    guild = self.bot.get_guild(899311529764192296)
                    user = guild.get_member(lst.data[i]["userid"])
                    if user is None: user = ModActionUserFromId(lst.data[i]["userid"])
                    # create action group
                    ticked_ac = lst.undo_action(author = None, victim = user, reason = "Timer expired", auto=True)
                    # remove this action's role
                    if isinstance(user, disnake.Member):
                        rmed_role = False
                        for role in user.roles:
                            if role.id == lst.role_id:
                                rmed_role = True
                                await user.remove_roles(role, reason=f"Timer for this action expired")
                        if not rmed_role: print(f"ERR  Could not take role {ticked_ac.role_id}; user does not have it!")
                    # audit undo action
                    await ticked_ac.audit(timer_expired=True)
                    # commit undo action
                    lst.data.pop(i)
            if changed: lst.dump_data()

    @list_ticker.before_loop
    async def wait_for_bot_ready_before_ticker(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        for typ,acset in self.__class__.lists.items():
            if (data:=acset.find(member.id)):
                expires = f"<t:{data['expires']}:f>" if data['expires'] else "Never"
                when = f"<t:{data['when']}:f>" if data['when'] else "Unknown"
            await self.bot.get_channel(self.__class__.alerts_channel).send(embed=disnake.Embed(
                title=f"{acset.what_happened_string} user joined!",
                description=f"**{acset.what_happened_string} for:**\n" + \
                            f"> {data['reason']}\n\n**Expires** {expires}\n" + \
                            f"**{acset.what_happened_string} on** {when}"
            ))
            await acset.apply_role(member)
    
    @classmethod
    def generate_page_buttons(cls, typ: str, curr_page: int) -> ui.View:
        last_page = len(cls.lists[typ].data) // cls.num_listings_per_page
        return ui.View() \
            .add_item(ui.Button(
                emoji="⬅️",
                style=disnake.ButtonStyle.grey if curr_page==0 else disnake.ButtonStyle.blurple,
                custom_id=f"mod{typ}list-disabled1" if curr_page==0 else f"mod{typ}list-{curr_page-1}",
                disabled=(curr_page == 0),
                row=1)) \
            .add_item(ui.Button(
                emoji="🏠",
                style=disnake.ButtonStyle.grey if curr_page==0 else disnake.ButtonStyle.blurple,
                custom_id=f"mod{typ}list-disabled2" if curr_page==0 else f"mod{typ}list-home",
                disabled=(curr_page == 0),
                row=1)) \
            .add_item(ui.Button(
                emoji="➡️",
                style=disnake.ButtonStyle.grey if curr_page==last_page else disnake.ButtonStyle.blurple,
                custom_id=f"mod{typ}list-disabled3" if curr_page==last_page else f"mod{typ}list-{curr_page+1}",
                disabled=(curr_page == last_page),
                row=1))
    
    @classmethod
    def generate_list_page_n(cls, typ: str, page: int) -> disnake.Embed:
        lst = cls.lists[typ].data
        if len(lst) == 0:
            return disnake.Embed(description=f"No {typ}s to show", color=disnake.Color.blue())
        embed = disnake.Embed(
            title=f"{typ.title()}s - Page {page+1} of {len(lst)//cls.num_listings_per_page+1}",
            color=disnake.Color.blue())
        for i in range(page*cls.num_listings_per_page, min((page+1)*cls.num_listings_per_page, len(lst))):
            subdata = lst[i]
            text = f"**Reason:**\n> {subdata['reason']}\n" + \
                   f"**Expires** <t:{subdata['expires'] if subdata['expires'] is not None else 'Never'}:f>\n" + \
                   f"**Occurred** <t:{subdata['when']}:f>"
            embed.add_field(name=subdata["userid"], value=text, inline=False)
        return embed
    
    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.ApplicationCommandInteraction):
        if interaction.type == disnake.InteractionType.component:
            if interaction.data["custom_id"].startswith("mod"):
                typ, page_num = interaction.data["custom_id"].split("-")
                typ = typ[3:-4]
                page_num = 0 if page_num == "home" else int(page_num)
                embed = self.__class__.generate_page_n(typ, page_num)
                view = self.__class__.generate_page_buttons(typ, page_num)
                await interaction.response.defer()
                await interaction.message.edit(embed=embed, view=view)
    
    @commands.slash_command(name="mod")
    @admin_only()
    async def mod_group(self, i):
        """ Moderator action commands """
        pass
    
    @mod_group.sub_command(name="list")
    async def list_type(self, interaction: disnake.ApplicationCommandInteraction, what_to_list: typing.Literal["ban", "mute"]):
        """ Lists all current actions of a certain type (e.x. list bans, mutes, etc). """
        if what_to_list not in self.__class__.lists:
            await interaction.response.send_message(embed=disnake.Embed(
                description=f"🚫 **Invalid action type `{what_to_list}`!**",
                color=disnake.Color.red()
            ), ephemeral=True)
        embed = self.__class__.generate_list_page_n(what_to_list, 0)
        view = self.__class__.generate_page_buttons(what_to_list, 0)
        await interaction.response.send_message(embed=embed, view=view)
    
    @mod_group.sub_command(name="ban")
    async def ban(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, reason:str = commands.Param(default=None), expires:str = commands.Param(default=None)):
        """
        Bans given user.

        Parameters
        ----------
        user: :class:`disnake.Member`
            The user to ban.
        reason: :class:`str`
            The reason behind the ban.
        expires: :class:`str`
            The date that this ban will be lifted. Pass datetimes (e.x. Jan 5 2:00) or offsets (e.x. 1d8h)
        """
        if expires is not None:
            try:
                expires = parseTime(expires)
            except ValueError as e:
                return await interaction.response.send_message(
                    embed=disnake.Embed(
                        description=f"🚫 **Invalid time string or offset!**",
                        color=disnake.Color.red()
                    ), ephemeral=True)
        banAc = self.__class__.lists["ban"]
        # affect user
        await user.remove_roles(interaction.guild.get_role(verified_role), reason="User was banned! See alerts page for more details")
        await user.add_roles(interaction.guild.get_role(banAc.role_id), reason="User was banned! See alerts page for more details")
        # commit ban to database
        banAc.add(user.id, reason, expires)
        banAc.dump_data()
        # alert ban
        reasonstr = "None" if reason is None else reason.replace('\n', '\n> ')
        expirystr = "Never" if expires is None else f"<t:{int(expires.timestamp())}:f>"
        ac = banAc.action(author = interaction.user, victim = user, reason = reasonstr, expires = expirystr)
        await ac.audit(response=interaction.response)
    
    @mod_group.sub_command(name="unban")
    async def unban(self, interaction: disnake.ApplicationCommandInteraction, id:int = commands.Param(large=True), reason:str = commands.Param(default=None)):
        """
        Removes a user from the ban list.

        Parameters
        ----------
        id: :class:`int`
            The user ID of the member to unban.
        reason: :class:`str`
            The reason behind the unban.
        """
        banAc = self.__class__.lists["ban"]
        res = banAc.remove(id)
        if res is not None:
            # fetch and affect user (if in server)
            user = await self.bot.get_or_fetch_user(id)
            if user is not None:
                await user.remove_roles(interaction.guild.get_role(banAc.role_id), reason=f"User was unbanned! See alerts page for more details")
            else: user = ModActionUserFromId(id)
            # commit unban to database
            banAc.dump_data()
            # alert for unban
            reasonstr = "None" if reason is None else reason.replace('\n', '\n> ')
            ac = banAc.undo_action(author = interaction.user, victim = user, reason = reason)
            await ac.audit(response=interaction.response)
        else:
            await interaction.response.send_message(
                embed=disnake.Embed(
                    description=f"⚠️ **User is not banned!**",
                    color=disnake.Color.yellow()
                ).set_footer(text=f"ID: {id}"))

    @mod_group.sub_command(name="mute")
    async def mute(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member, reason:str = commands.Param(default=None), expires:str = commands.Param(default=None)):
        """
        Mutes given user.

        Parameters
        ----------
        user: :class:`disnake.Member`
            The user to mute.
        reason: :class:`str`
            The reason behind the mute.
        expires: :class:`str`
            The date that this mute will be lifted. Pass datetimes (e.x. Jan 5 2:00) or offsets (e.x. 1d8h)
        """
        if expires is not None:
            try:
                expires = parseTime(expires)
            except ValueError as e:
                return await interaction.response.send_message(
                    embed=disnake.Embed(
                        description=f"🚫 **Invalid time string or offset!**",
                        color=disnake.Color.red()
                    ), ephemeral=True)
        muteAc = self.__class__.lists["mute"]
        # affect user
        await user.add_roles(interaction.guild.get_role(muteAc.role_id), reason="User was muted! See alerts page for more details")
        # commit ban to database
        muteAc.add(user.id, reason, expires)
        muteAc.dump_data()
        # alert ban
        reasonstr = "None" if reason is None else reason.replace('\n', '\n> ')
        expirystr = "Never" if expires is None else f"<t:{int(expires.timestamp())}:f>"
        ac = muteAc.action(author = interaction.user, victim = user, reason = reasonstr, expires = expirystr)
        await ac.audit(response=interaction.response)
        
    @mod_group.sub_command(name="unmute")
    async def unmute(self, interaction: disnake.ApplicationCommandInteraction, id:int = commands.Param(large=True), reason:str = commands.Param(default=None)):
        """
        Removes a user from the mute list.

        Parameters
        ----------
        id: :class:`int`
            The user ID of the member to unmute.
        reason: :class:`str`
            The reason behind the unmute.
        """
        muteAc = self.__class__.lists["mute"]
        res = muteAc.remove(id)
        if res is not None:
            # fetch and affect user (if in server)
            user = await self.bot.get_or_fetch_user(id)
            if user is not None:
                await user.remove_roles(interaction.guild.get_role(muteAc.role_id), reason=f"User was unbanned! See alerts page for more details")
            else: user = ModActionUserFromId(id)
            # commit unban to database
            muteAc.dump_data()
            # alert for unban
            reasonstr = "None" if reason is None else reason.replace('\n', '\n> ')
            ac = muteAc.undo_action(author = interaction.user, victim = user, reason = reason)
            await ac.audit(response=interaction.response)
        else:
            await interaction.response.send_message(
                embed=disnake.Embed(
                    description=f"⚠️ **User is not muted!**",
                    color=disnake.Color.yellow()
                ).set_footer(text=f"ID: {id}"))

    @commands.slash_command(name="simulate-user-join")
    async def simulate_join(self, i: disnake.ApplicationCommandInteraction, user: disnake.Member):
        await i.response.send_message(f"Simulating user join {user.display_name} (ID {user.id})", ephemeral=True)
        await self.on_member_join(user)



# needed per cog
def setup(bot):
    bot.add_cog(BansCog(bot))