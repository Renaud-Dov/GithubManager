import discord
from discord import Embed


def BasicEmbed(title: str = None, description: str = None, color: discord.Colour = discord.Color.blue()):
    embed = Embed(title=title, description=description, color=color)
    embed.set_footer(text="Made with ❤️ by Bugbear")
    return embed
