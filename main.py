import json
from typing import Optional

import discord
from discord import app_commands, ui
import requests
from discord.utils import get
import os

import logging

from src.Embed import BasicEmbed
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


def generate_secret():
    # generate a secret key made of 16 random bytes
    secret = os.urandom(16)
    secret = secret.hex()
    return secret


def getConfigRules(type_event):
    if type_event == "push":
        with open("example2.txt", "r") as file:
            return file.read()
    elif type_event == "check":
        with open("example.txt", "r") as file:
            return file.read()


@tree.command(name='wb', guild=discord.Object(id=760808606672093184), description="Add update webhook to repo")
@app_commands.describe(repo="Repo to add webhook to")
@app_commands.describe(type="type of trigger, either 'push' or 'check'")
@app_commands.describe(webhook="Name of webhook, optional")
@is_owner()
async def updater_webhook(interaction: discord.Interaction, repo: str, type: str, webhook: Optional[str] = None):
    if type != "push" and type != "check":
        await interaction.response.send_message(
            BasicEmbed(title="Error", description="Type must be either 'push' or 'check'"))
        return
    if webhook is None:
        webhook = repo

    url = f"https://wb.bugbear.fr/hooks/{webhook}"
    secret = generate_secret()
    response = push_webhook(repo, url, secret)
    if response.status_code != 201:
        await interaction.response.send_message(
            f"Error creating webhook for {repo} (code {response.status_code}) : ```{response.text}```")
    else:
        embed = BasicEmbed(title="Webhook created", description=f"Webhook created for {repo}",
                           color=discord.Color.green())
        embed.add_field(name="Repository", value=f"https://github.com/Renaud-Dov/{repo}")
        embed.add_field(name="Webhook", value=f"https://wb.bugbear.fr/hooks/{webhook}")
        await interaction.response.send_message(embed=embed)
        file_config = getConfigRules(type).replace("{name}", webhook).replace("{secret}", secret)
        await interaction.user.send("```json\n" + file_config + "\n```")


def push_webhook(repo: str, url: str, secret: Optional[str]):
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
    if secret:
        data["config"]["secret"] = secret
    return requests.post(f"https://api.github.com/repos/Renaud-Dov/{repo}/hooks", headers=headers,
                         data=json.dumps(data))


@tree.command(name='webhook', guild=discord.Object(id=760808606672093184), description="Add webhook to repo")
@app_commands.describe(repo="Repo to add webhook to")
@app_commands.describe(channel="Channel to add webhook to (if not specified, will create a new one in logs category)")
@is_owner()
async def add_webhook(interaction: discord.Interaction, repo: str, channel: Optional[discord.TextChannel] = None):
    if channel is None:
        category = get(interaction.guild.categories, name="logs")
        _channel = await interaction.guild.create_text_channel(name=repo, category=category)
    else:
        _channel = channel
    try:
        wb = await _channel.create_webhook(name=repo)
    except discord.errors.Forbidden:
        await interaction.response.send_message("I don't have permission to create webhooks in this channel")
        return
    except discord.errors.HTTPException:
        await interaction.response.send_message("I failed creating a webhook for the repo")
        return

    url = wb.url + "/github"
    response = push_webhook(repo,url)
    if response.status_code == 201:
        embed = BasicEmbed(title="Webhook created", description=f"Webhook created for {repo}",
                           color=discord.Color.green())
        embed.add_field(name="Channel", value=f"{_channel.mention}")
        embed.add_field(name="Repository", value=f"https://github.com/Renaud-Dov/{repo}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Error creating webhook for " + repo + response.text)
        # delete the webhook and channel if it failed
        await wb.delete()
        if channel is None:
            await _channel.delete()


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

    embed = BasicEmbed(title="Created Docker Credentials", description="Docker credentials created for " + repo,
                       color=discord.Color.green())
    embed.add_field(name="Repository", value=f"https://github.com/Renaud-Dov/{repo}")
    await interaction.response.send_message(embed=embed)


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
            embed = BasicEmbed(title="Created secret", description=f"Secret created for {self.repo}",
                               color=discord.Color.green())
            embed.add_field(name="Repository", value=f"https://github.com/Renaud-Dov/{self.repo}")
            await interaction.response.send_message(embed=embed)
            await interaction.response.send_message(f"Added secret {self.name} to {self.repo}")
        else:
            await interaction.response.send_message(f"Failed to add secret {self.name} to {self.repo}")


@tree.command(guild=discord.Object(id=760808606672093184), name="rerun", description="Rerun the last job workflow")
@app_commands.describe(repo="Repo where you want to rerun the last job")
@app_commands.describe(id="Run id to rerun. If not specified, the last run will be rerun")
@is_owner()
async def rerun(interaction: discord.Interaction, repo: str, id: Optional[int]):
    response1 = requests.get(f"https://api.github.com/repos/Renaud-Dov/{repo}/actions/runs", headers=get_headers())
    if not response1.ok:
        await interaction.response.send_message("Error getting runs for " + repo)
        return
    data = response1.json()
    if data["total_count"] == 0:
        await interaction.response.send_message("No runs found for " + repo)
        return
    if id is None:
        run_id = data["workflow_runs"][0]["id"]
    else:
        # filter runs to find the one with the run_number equal to id
        run_id = next(filter(lambda x: x["run_number"] == id, data["workflow_runs"]))["id"]
    response = requests.post(f"https://api.github.com/repos/Renaud-Dov/{repo}/actions/runs/{run_id}/rerun",
                             headers=get_headers())
    if response.ok:
        embed = BasicEmbed(title="Rerun workflow", description=f"Rerun workflow for {repo}",
                           color=discord.Color.green())
        embed.add_field(name="Repository", value=f"https://github.com/Renaud-Dov/{repo}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"Error rerunning run {run_id}")


client.run(os.environ.get("DISCORD_TOKEN"))
