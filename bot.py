import discord
from discord.ext import commands
import asyncio
from discord.ext.commands import Bot


startup_extensions = ["Music"]
bot = commands.Bot("!")
class Main_Commands():
    def __init__(self, bot):
        self.bot = bot

@bot.event
async def on_ready():
    print ("Name of bot is: " + bot.user.name)
    print ("You can invite bot with command !inviteme")
    print (".............................................")
    print ("ERRORS:")
@bot.command(pass_context=True)
async def inviteme(ctx):
    """Gives bots invite link..."""
    embed=discord.Embed(color=0x000000)
    embed.add_field(name="You can invite me with this link:", value="https://discordapp.com/api/oauth2/authorize?client_id={}&permissions=0&scope=bot".format(bot.user.id), inline=True)
    await bot.say(embed=embed)

if __name__ == "__main__":  
    for extention in startup_extensions:
        try:
            bot.load_extension(extention)
        except Exception as e:
                exc = "{}: {}".format(type(e).__name__, e)
                print("NEDELA !!!!!!!! --{}\n{}".format(extention, exc))
fh = open("token.txt", "r")
a = fh.read()
bot.run(a)
