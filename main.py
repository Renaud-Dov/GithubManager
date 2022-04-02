import json

import discord
from discord import app_commands, ui
import requests
from discord.utils import get
from requests.auth import HTTPDigestAuth
import os

import logging

from src.header import get_headers
from src.secrets import create_secret

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


def is_owner():
    async def predicate(interaction: discord.Interaction):
        # check if the user is the owner of the bot
        return interaction.user.id == 208480161421721600

    return app_commands.check(predicate)


@tree.command(name='webhook', guild=discord.Object(id=760808606672093184), description="Add webhook to repo")
@app_commands.describe(repo="Repo to add webhook to")
@is_owner()
async def webhook(interaction: discord.Interaction, repo: str):
    # TODO: Add a check to see if the repo is a valid repo

    # create channel in category id
    category = get(interaction.guild.categories, name="logs")
    channel = await interaction.guild.create_text_channel(name=repo, category=category)
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
            "check_run",
            "check_suite",
            "release",
            "star",
            "fork",
            "workflow_run",
            "workflow_job",
            "package",
            "create",
            "delete"
        ],
        "active": True
    }
    response = requests.post(f"https://api.github.com/repos/Renaud-Dov/{repo}/hooks", headers=headers,
                             data=json.dumps(data))
    if response.status_code == 201:
        await interaction.response.send_message(
            f"Created webhook for {repo} in {channel.mention} (https://github.com/Renaud-Dov/{repo})")
    else:
        await interaction.response.send_message("Error creating webhook for " + repo + response.text)
        # delete the webhook and channel if it failed
        await wb.delete()
        await channel.delete()


@tree.command(guild=discord.Object(id=760808606672093184), name="update", description="Update commands")
async def updateCommands(interaction: discord.Interaction):
    await tree.sync(guild=discord.Object(id=760808606672093184))
    await interaction.response.send_message("Updated commands")


@tree.command(guild=discord.Object(id=760808606672093184), name="add", description="Add/Update secret to repo")
@app_commands.describe(repo="Repo where you want to add/update secret")
@is_owner()
async def addSecret(interaction: discord.Interaction, repo: str):
    await interaction.response.send_modal(AskSecretValue(repo))


@tree.command(guild=discord.Object(id=760808606672093184), name="docker", description="Add Docker credentials to repo")
@is_owner()
async def addDocker(interaction: discord.Interaction, repo: str):
    data = {"DOCKERHUB_USERNAME": "bugbeardov", "DOCKERHUB_TOKEN": os.environ["DOCKERHUB_TOKEN"]}

    for key, value in data.items():
        response = create_secret(repo, key, value)
        if not response.ok:
            await interaction.response.send_message("Error creating secret for " + repo)
            return
    await interaction.response.send_message(
        "Created Docker Credentials (DOCKERHUB_USERNAME,DOCKERHUB_TOKEN) for " + repo)


class AskSecretValue(ui.Modal, title="Add secret"):
    name = ui.TextInput(label='Secret Name', required=True, style=discord.TextStyle.short)
    secret = ui.TextInput(label='Secret value', required=True, style=discord.TextStyle.paragraph)

    def __init__(self, repo: str):
        super().__init__()
        self.title = f"{repo} new secret"
        self.repo = repo

    async def on_submit(self, interaction: discord.Interaction):
        response = create_secret(self.repo, self.name.value, self.secret.value)
        if response.ok:
            await interaction.response.send_message(f"Added secret {self.name} to {self.repo}")
        else:
            await interaction.response.send_message(f"Failed to add secret {self.name} to {self.repo}")


client.run(os.environ.get("DISCORD_TOKEN"))
