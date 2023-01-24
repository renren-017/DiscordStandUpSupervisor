import os
import discord
import datetime
import pytz
import requests
import asyncio
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()

tz = pytz.timezone('Asia/Bishkek')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_SERVER_NAME = os.getenv("DISCORD_SERVER_NAME")
CHANNEL_ID = os.getenv("CHANNEL_ID")
start = datetime.datetime(year=2023, month=1, day=24, hour=8, minute=0, second=0, tzinfo=tz)
end = datetime.datetime(year=2023, month=1, day=24, hour=16, minute=31, second=0, tzinfo=tz)

intents = discord.Intents.all()


class Client(discord.Client):

    def __init__(self, token, server_name):
        super().__init__(intents=intents)

        self._token = token
        self._guild_name = server_name

    def run(self, *args, **kwargs):
        super().run(self._token)


client = Client(DISCORD_TOKEN, DISCORD_SERVER_NAME)

wrote_standup = set()


async def get_non_admins(channel):
    non_admin_members = []
    for member in channel.members:
        # if not any(role.permissions.administrator for role in member.roles):
        #     non_admin_members.append(member)
        if member.name != 'StandUpSupervisor':
            non_admin_members.append(member)
    return non_admin_members


async def seconds_until(hours, minutes):
    given_time = datetime.time(hours, minutes)
    now = datetime.datetime.now().astimezone(tz)
    future_exec = datetime.datetime.combine(now, given_time).astimezone(tz)
    if (future_exec - now).days < 0:
        future_exec = datetime.datetime.combine(now + datetime.timedelta(days=1), given_time).astimezone(tz) # days always >= 0

    return (future_exec - now).total_seconds()


@client.event
async def on_message(message):
    if message.author.name == 'StandUpSupervisor':
        return
    timestamp = message.created_at.replace(tzinfo=pytz.utc).astimezone(tz)

    if not (start < timestamp < end):
        return

    if message.content.startswith('#standup'):
        wrote_standup.add(message.author)


@tasks.loop(hours=24)
async def send_message():
    while True:
        await asyncio.sleep(await seconds_until(15, 20))
        channel = client.get_channel(int(CHANNEL_ID))
        members = set(await get_non_admins(channel))
        members.difference_update(wrote_standup)

        await channel.send(f"{''.join(list(map(lambda x: x.mention, members)))} didn't write standup")
        await asyncio.sleep(60)


@client.event
async def on_ready():
    send_message.start()

client.run()
