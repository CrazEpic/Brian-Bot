import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
from zoneinfo import ZoneInfo
import json
import os
import asyncio

DATA_FILE = "daily_config.json"

DEFAULT_CONFIG = {
    "timezone": "America/Chicago",
    "hour": 0,
    "channel_id": None,
    "counter": 0,
    "last_run_date": None,
    "running": False,
}


class DailyScheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = self.load_data()
        self.scheduler.start()

    def cog_unload(self):
        self.scheduler.cancel()

    # -----------------------
    # Data Handling
    # -----------------------

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_guild_config(self, guild_id: int, channel_id_for_create: int):
        guild_id = str(guild_id)
        if guild_id not in self.config:
            self.config[guild_id] = DEFAULT_CONFIG.copy()
            self.config[guild_id]["channel_id"] = channel_id_for_create
            self.save_data()
        return self.config[guild_id]

    # -----------------------
    # Background Scheduler
    # -----------------------

    @tasks.loop(hours=1)
    async def scheduler(self):
        for guild_id, data in self.config.items():
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            if not data["channel_id"]:
                continue

            if not data["running"]:
                continue

            tz = ZoneInfo(data["timezone"])
            now = datetime.datetime.now(tz)

            if now.hour == data["hour"]:
                today_str = now.date().isoformat()

                channel = guild.get_channel(data["channel_id"])
                if not channel:
                    continue

                count_str = f"{data['counter']:03d}"
                await channel.send(f"Day {count_str}")

                data["counter"] += 1
                data["last_run_date"] = today_str
                self.save_data()

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        seconds_until_hour = 3600 - (now.minute * 60 + now.second)
        await asyncio.sleep(seconds_until_hour)

    # -----------------------
    # Slash Commands
    # -----------------------

    @app_commands.command(
        name="hello_world",
        description="A simple command to test the bot's responsiveness.",
    )
    async def hello_world(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello, World!", ephemeral=True)

    @app_commands.command(
        name="display_info", description="Display current settings and counter."
    )
    async def display_info(self, interaction: discord.Interaction):
        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        tz = ZoneInfo(data["timezone"])
        last_run_date = data["last_run_date"]
        now = datetime.datetime.now(tz)
        next_run_time = now.replace(
            hour=data["hour"], minute=0, second=0, microsecond=0
        )
        if now >= next_run_time:
            next_run_time += datetime.timedelta(days=1)
        current_channel = interaction.guild.get_channel(data["channel_id"])
        embed = discord.Embed(title="Daily Counter Info", color=discord.Color.blue())
        embed.add_field(
            name="Current Channel",
            value=current_channel.mention if current_channel else "Not Set",
            inline=False,
        )
        embed.add_field(
            name="Current Counter", value=f"{data['counter']:03d}", inline=False
        )
        embed.add_field(name="Timezone", value=data["timezone"], inline=False)
        embed.add_field(name="Daily Time", value=f"{data['hour']:02d}:00", inline=False)
        embed.add_field(
            name="Running", value="Yes" if data["running"] else "No", inline=False
        )
        unix_timestamp = int(next_run_time.timestamp())
        embed.add_field(
            name="Last Run Date",
            value=last_run_date if last_run_date else "Never",
            inline=False,
        )
        embed.add_field(
            name="Next Run Time",
            value=f"<t:{unix_timestamp}:F>\n(<t:{unix_timestamp}:R>)"
            if data["running"]
            else "N/A",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="set_channel", description="Set the channel for the daily counter."
    )
    async def set_channel(self, interaction: discord.Interaction):
        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        data["channel_id"] = interaction.channel_id
        self.save_data()

        await interaction.response.send_message(
            "This channel has been set for the daily counter.", ephemeral=True
        )

    @app_commands.command(
        name="start_count", description="Start daily counter in this channel."
    )
    async def start_count(self, interaction: discord.Interaction):
        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        if not data["channel_id"] == interaction.channel_id:
            await interaction.response.send_message(
                "This command can only be used in the channel where the counter is active.",
                ephemeral=True,
            )
            return
        if data["running"]:
            await interaction.response.send_message(
                "The counter is already running in this channel.", ephemeral=True
            )
            return
        data["running"] = True
        self.save_data()

        await interaction.response.send_message(
            "Daily counter started in this channel.", ephemeral=True
        )

    @app_commands.command(
        name="stop_count", description="Stop daily counter in this channel."
    )
    async def stop_count(self, interaction: discord.Interaction):
        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        if not data["channel_id"] == interaction.channel_id:
            await interaction.response.send_message(
                "This command can only be used in the channel where the counter is active.",
                ephemeral=True,
            )
            return
        if not data["running"]:
            await interaction.response.send_message(
                "The counter is not currently running in this channel.", ephemeral=True
            )
            return
        data["running"] = False
        self.save_data()

        await interaction.response.send_message(
            "Daily counter stopped in this channel.", ephemeral=True
        )

    TIMEZONE_CHOICES = [
        app_commands.Choice(name="Eastern (EST/EDT)", value="America/New_York"),
        app_commands.Choice(name="Central (CST/CDT)", value="America/Chicago"),
        app_commands.Choice(name="Mountain (MST/MDT)", value="America/Denver"),
        app_commands.Choice(name="Pacific (PST/PDT)", value="America/Los_Angeles"),
        app_commands.Choice(name="Alaska (AKST/AKDT)", value="America/Anchorage"),
        app_commands.Choice(name="Hawaii (HST)", value="Pacific/Honolulu"),
    ]

    @app_commands.command(name="set_timezone", description="Set the timezone.")
    @app_commands.choices(timezone=TIMEZONE_CHOICES)
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        try:
            ZoneInfo(timezone)
        except Exception:
            await interaction.response.send_message(
                "Invalid timezone. Use IANA format like `America/New_York`.",
                ephemeral=True,
            )
            return

        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        if not data["channel_id"] == interaction.channel_id:
            await interaction.response.send_message(
                "This command can only be used in the channel where the counter is active.",
                ephemeral=True,
            )
            return
        data["timezone"] = timezone
        self.save_data()

        await interaction.response.send_message(
            f"Timezone set to `{timezone}`.", ephemeral=True
        )

    @app_commands.command(name="set_time", description="Set daily send time.")
    @app_commands.describe(hour="0-23")
    async def set_time(self, interaction: discord.Interaction, hour: int):
        if not (0 <= hour <= 23):
            await interaction.response.send_message(
                "Invalid time values.", ephemeral=True
            )
            return

        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        if not data["channel_id"] == interaction.channel_id:
            await interaction.response.send_message(
                "This command can only be used in the channel where the counter is active.",
                ephemeral=True,
            )
            return
        data["hour"] = hour
        self.save_data()

        await interaction.response.send_message(
            f"Daily time set to {hour:02d}:00.", ephemeral=True
        )

    @app_commands.command(name="reset_count", description="Reset the counter to 000.")
    async def reset_count(self, interaction: discord.Interaction):
        data = self.get_guild_config(interaction.guild_id, interaction.channel_id)
        if not data["channel_id"] == interaction.channel_id:
            await interaction.response.send_message(
                "This command can only be used in the channel where the counter is active.",
                ephemeral=True,
            )
            return
        if not data["running"]:
            await interaction.response.send_message(
                "The counter is not currently running in this channel.", ephemeral=True
            )
            return
        data["counter"] = 0
        self.save_data()

        await interaction.response.send_message("Counter reset to 000.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyScheduler(bot))
