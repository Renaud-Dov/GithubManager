import discord
from discord import app_commands
import requests
import os

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print("Bot is ready!")

    await tree.sync(guild=discord.Object(id=760808606672093184))




@tree.command(name='webhook')
@app_commands.describe(channel="Channel to send webhook to")
@app_commands.describe(repo="Repo to add webhook to")
async def webhook(interaction: discord.Interaction, channel: discord.TextChannel, repo: str):
    # TODO: Add a check to see if the repo is a valid repo

    # create a webhook for the repo
    try:
        wb = await channel.create_webhook(name=repo)
    except discord.errors.Forbidden:
        await interaction.response.send_message("I don't have permission to create webhooks in this channel")
        return
    except discord.errors.HTTPException:
        await interaction.response.send_message("I failed creating a webhook for the repo")
        return

    url = wb.url + "/github"
    headers = get_headers()
    data = {
        "name": "web",
        "config": {
            "url": url,
            "content_type": "json"
        },
        "events": [
            "pull_request",
            "push",
            "pull_request_review_comment",
            "issue_comment",
            "issues",
            "commit_comment",
        ],
        "active": True
    }
    response = requests.post(f"https://api.github.com/repos/Renaud-Dov/{repo}/hooks", headers=headers, data=data)
    if response.status_code == 201:
        await interaction.response.send_message(f"Created webhook for {repo} (https://github.com/Renaud-Dov/{repo})")
    else:
        await interaction.response.send_message("Error creating webhook for " + repo)


def get_headers():
    return {
        "Authorization": "Basic " + os.environ['GITHUB_TOKEN'],
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/x-www-form-urlencoded"
    }


@tree.command(guild=discord.Object(id=760808606672093184), name="update", description="Update commands")
async def updateCommands(interaction: discord.Interaction):
    await tree.sync(guild=discord.Object(id=760808606672093184))
    await interaction.response.send_message("Updated commands")


client.run(os.environ.get("DISCORD_TOKEN"))
