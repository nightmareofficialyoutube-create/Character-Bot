import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Your Discord User ID
OWNER_ID = 553648435018989588

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# Current character application
applicants = {}
character_name = ""
character_role = ""
character_minimum = 1

# Current public application panel
panel_message = None


def get_application_message():
    if applicants:
        applicant_list = "\n".join(
            f"<@{user_id}> {'🎤' if has_mic else '❌'}"
            for user_id, has_mic in applicants.items()
        )
    else:
        applicant_list = "No applicants yet."

    return (
        f"🎭 **{character_name}**\n"
        f"{character_role}\n\n"
        f"**Applicants: {len(applicants)}/{character_minimum}**\n"
        f"**Minimum applicants: {character_minimum}**\n\n"
        f"{applicant_list}"
    )


async def update_panel():
    global panel_message

    if panel_message is not None:
        try:
            await panel_message.edit(
                content=get_application_message(),
                view=CharacterView()
            )
        except discord.NotFound:
            panel_message = None


class MicView(discord.ui.View):
    def __init__(self, applicant_id):
        super().__init__(timeout=300)
        self.applicant_id = applicant_id

    @discord.ui.button(
        label="Yes",
        style=discord.ButtonStyle.green,
        emoji="🎤"
    )
    async def mic_yes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id != self.applicant_id:
            await interaction.response.send_message(
                "This application belongs to another player.",
                ephemeral=True
            )
            return

        applicants[interaction.user.id] = True

        await interaction.response.edit_message(
            content="Application submitted.",
            view=None
        )

        await update_panel()

    @discord.ui.button(
        label="No",
        style=discord.ButtonStyle.red
    )
    async def mic_no(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id != self.applicant_id:
            await interaction.response.send_message(
                "This application belongs to another player.",
                ephemeral=True
            )
            return

        applicants[interaction.user.id] = False

        await interaction.response.edit_message(
            content="Application submitted.",
            view=None
        )

        await update_panel()


class CharacterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="APPLY",
        style=discord.ButtonStyle.green
    )
    async def apply(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id in applicants:
            await interaction.response.send_message(
                "You have already applied for this character.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Do you have a mic?",
            view=MicView(interaction.user.id),
            ephemeral=True
        )

    @discord.ui.button(
        label="LEAVE APPLICATION",
        style=discord.ButtonStyle.red
    )
    async def leave_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id not in applicants:
            await interaction.response.send_message(
                "You are not currently applying for this character.",
                ephemeral=True
            )
            return

        applicants.pop(interaction.user.id)

        await interaction.response.send_message(
            "You have left the character application.",
            ephemeral=True
        )

        await update_panel()


@bot.event
async def on_ready():
    print(f"Character Bot is online als {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as error:
        print(f"Sync error: {error}")


@bot.tree.command(
    name="character",
    description="Create a character application"
)
async def character(
    interaction: discord.Interaction,
    name: str,
    role: str,
    minimum_applicants: int
):
    global applicants
    global character_name
    global character_role
    global character_minimum
    global panel_message

    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "You do not have permission to create character applications.",
            ephemeral=True
        )
        return

    if minimum_applicants < 1:
        await interaction.response.send_message(
            "Minimum applicants must be at least 1.",
            ephemeral=True
        )
        return

    applicants = {}
    character_name = name
    character_role = role
    character_minimum = minimum_applicants

    await interaction.response.send_message(
        get_application_message(),
        view=CharacterView()
    )

    panel_message = await interaction.original_response()


bot.run(TOKEN)