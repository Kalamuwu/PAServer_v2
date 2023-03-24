import disnake
from disnake.ext import commands
from disnake import ui
import typing

import random
import time
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from vars import otp_email_html, otp_email_text, author_id, verified_role

active_otps = []
async def send_otp(interaction: disnake.ApplicationCommandInteraction, userid:str) -> bool:
    global active_otps
    # Generate code
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    otp = "".join(random.choice(chars) for i in range(8))
    # os.environ variables for security
    sender = os.environ["EMAIL_ADDR"]
    password = os.environ["EMAIL_PSW"]
    # Set up MIME message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Server Verification OTP"
    message["From"] = "pinkerton.bot@gmail.com"
    message["To"] = f"{userid}@pinkertonacademy.org"
    # Add HTML/plain-text parts to MIMEMultipart message - the email client will try to render the last part first
    text = otp_email_text.replace("!name", interaction.user.name).replace("!otp", otp)
    html = otp_email_html.replace("!name", interaction.user.name).replace("!otp", otp)
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))
    # Send email
    with smtplib.SMTP_SSL("smtp.sendgrid.net", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, message["To"], message.as_string())
    print(f"Email sent to {message['To']}")
    # Register OTP pair
    active_otps.append({'otp': otp, 'userid': userid, 'time': time.time()})
    print("active OTPs: ", active_otps)
    return True


class UserOTPModal(ui.Modal):
    userid = ui.TextInput(label="6-digit student ID", custom_id="userid", placeholder="123456", min_length=6,max_length=6, required=True)
    otp_response = ui.TextInput(label="OTP code", custom_id="otp_response", min_length=8,max_length=8, required=True)
    def __init__(self):
        super().__init__(title="User Verification", custom_id="verification-otp")

# class UserIDModal(ui.Modal):
#     userid = ui.TextInput(label="6-digit student ID", custom_id="userid", placeholder="123456", min_length=6,max_length=6, required=True)
#     def __init__(self):
#         super().__init__(title="User Verification", custom_id="verification-id")

class UserVerificationCog(commands.Cog, name='User Verification'):
    """ This cog handles user verification """
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.Cog.listener("on_interaction")
    async def on_interaction(self, interaction: disnake.ApplicationCommandInteraction):
        global active_otps
        if interaction.type == disnake.InteractionType.component:
            if interaction.data['custom_id'][0:17] == "verification-send":  # "send otp code" button
                role = interaction.guild.get_role(verified_role)
                if role in interaction.user.roles:
                    await interaction.response.send_message(
                        embed=disnake.Embed(
                            description="🚫 **You're already verified!**",
                            color=disnake.Color.red()
                        ), ephemeral=True)
                else:
                    await interaction.response.send_modal(ui.Modal(
                        title="User Verification",
                        custom_id="verification-id",
                        components=[ui.TextInput(
                            label="6-digit student ID", custom_id="userid",
                            placeholder="123456", required=True,
                            min_length=6, max_length=6
                        )]
                    ))
            elif interaction.data['custom_id'][0:18] == "verification-input":  # "input otp code" button
                role = interaction.guild.get_role(verified_role)
                if role in interaction.user.roles:
                    await interaction.response.send_message(
                        embed=disnake.Embed(
                            description="🚫 **You're already verified!**",
                            color=disnake.Color.red()
                        ), ephemeral=True)
                else:
                    await interaction.response.send_modal(ui.Modal(
                        title="User Verification",
                        custom_id="verification-otp",
                        components=[ui.TextInput(
                            label="6-digit student ID", custom_id="userid",
                            placeholder="123456", required=True,
                            min_length=6, max_length=6,
                        ), ui.TextInput(
                            label="OTP code", custom_id="otp_response",
                            placeholder="abcd1234", required=True,
                            min_length=8, max_length=8
                        )]
                    ))
        
        elif interaction.type == disnake.InteractionType.modal_submit:
            # "send otp code" response
            if interaction.data['custom_id'][0:15] == "verification-id":
                userid = int(interaction.data['components'][0]['components'][0]['value'])
                suc = await send_otp(interaction, int(userid))
                if suc:
                    embed = disnake.Embed(
                        description="✅ **Check your email for your OTP code!**\n\n",
                        color=disnake.Color.green())
                    embed.set_footer(text="Note: You have 5 minutes to enter your OTP before it expires. Click *\"Input OTP Pair\"* above to input your code.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(
                        embed=disnake.Embed(
                            description="🚫 **An error occurred: please contact the bot developer!**",
                            color=disnake.Color.red()
                        ), ephemeral=True)
            
            # "input otp code" response
            elif interaction.data['custom_id'][0:16] == "verification-otp":
                userid = int(interaction.data['components'][0]['components'][0]['value'])
                otp =       (interaction.data['components'][1]['components'][0]['value'])
                id_match = False
                for i in range(len(active_otps)-1, -1, -1):  # walk backwards to allow for removing OTP pairs without skipping the next one
                    otp_pair = active_otps[i]
                    print("considering", otp_pair)
                    if time.time() - otp_pair['time'] > 300:  # otp code expired! remove it and continue
                        active_otps.pop(i)
                        print("  otp pair timed out")
                        continue
                    elif otp_pair['userid'] == userid:  # otp code is for this user ID
                        print("  id match found")
                        id_match = True
                        if otp_pair['otp'] == otp:
                            print("  otp match found")
                            role = interaction.guild.get_role(verified_role)
                            await interaction.user.add_roles(role)
                            await interaction.response.send_message(
                                embed=disnake.Embed(
                                    description="✅ **You've been verified!**\nWelcome to the server!",
                                    color=disnake.Color.red()
                                ), ephemeral=True)
                            active_otps.pop(i)
                        return
                
                if id_match:  # has not returned -- otp pair found, but not correctly entered
                    embed = disnake.Embed(
                        description=f"🚫 **Incorrect OTP code!** Try entering your code again, or press the \"Send OTP code\" button above again to create a new one.\n",
                        color=disnake.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:  # hasnt returned -- no otp pair for this user id found
                    embed = disnake.Embed(
                        description=f"⚠️ **You have not activated any OTPs!** Press the button \"Send OTP code\" above to create one.\n",
                        color=disnake.Color.yellow())
                    embed.set_footer(text="Note: You may have already requested an OTP; in which case this means the 5-minute timer has expired. Please request a new OTP and try verification again.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)

    ## EXAMPLE command to set up an OTP input
    # @commands.slash_command(name="generate-otp-input")
    # async def make_otppair(self, interaction: disnake.ApplicationCommandInteraction):
    #     view = ui.View()
    #     view.add_item(ui.Button(custom_id=f"verification-send",  label="Send OTP code"))
    #     view.add_item(ui.Button(custom_id=f"verification-input", label="Input OTP Pair"))
    #     await interaction.channel.send(
    #         embed=disnake.Embed(
    #             description="**Click \"Send OTP code\" to start the verification process.** You will be asked for your user ID, and will be sent an email containing a code that is valid for 5 minutes.\n" +
    #                         "When you receive your code, click \"Input OTP Pair\" to input this code and check if it is valid. If it is, welcome to the server! If not, please try generating a new OTP and starting over.",
    #             color=disnake.Color.blue()
    #         ), view=view)
    #     await interaction.response.send_message("Created", ephemeral=True)


# needed per cog
def setup(bot):
    bot.add_cog(UserVerificationCog(bot))