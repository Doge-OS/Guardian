import discord
from discord.ext import commands
import datetime
from discord.ui import Button, View

# Define the intents your bot will use
intents = discord.Intents.default()
intents.messages = True  # Ensure the bot can receive message events
intents.guilds = True
intents.message_content = True  # Required to read message content

# Create an instance of a bot with a custom prefix and intents
bot = commands.Bot(command_prefix=';', intents=intents)

# Event that runs when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=f"This server is protected by Guardian 🛡️"
        )
    )
    
    # Event that runs when the bot is mentioned
    @bot.event
    async def on_message(message):
        if bot.user.mentioned_in(message):
            prefix = bot.command_prefix
            commands_list = [
                f'{prefix}ping - Responds with Pong!',
                f'{prefix}kick @user [reason] - Kicks the mentioned user with an optional reason.',
                f'{prefix}ban @user [reason] - Bans the mentioned user with an optional reason.',
                f'{prefix}unban user#1234 - Unbans a user using their username and discriminator.',
                f'{prefix}timeout @user [duration in minutes] [reason] - Times out the mentioned user for a specified duration with an optional reason.',
                f'{prefix}untimeout @user - Removes timeout from the mentioned user.',
                f'{prefix}purge [number] - Deletes the specified number of messages in the channel.',
                f'{prefix}mute @user [reason] - Mutes the mentioned user.',
                f'{prefix}unmute @user - Unmutes the mentioned user.',
                f'{prefix}slowmode [seconds] - Sets slowmode in the current channel.',
                f'{prefix}lock - Locks the current channel.',
                f'{prefix}unlock - Unlocks the current channel.',
                f'{prefix}say [message] - Makes the bot say the message you provide.',
                f'{prefix}setwelcome [message] [title] [photo (optional)] [author (optional)] [footer (optional)] - Customizes the welcome message, title, photo, author, and footer for when a new member joins.',
                f'{prefix}serverinfo - Get server info/stats.'
                
            ]

            # Create the embed
            embed = discord.Embed(title="Here are my commands:", color=discord.Color.blue())
            embed.description = "\n".join(commands_list)

            # Send the embed
            await message.channel.send(embed=embed)

        await bot.process_commands(message)

log_channel = None  # Initialize log channel

@bot.command(name='setlogchannel')
async def setlogchannel(ctx, channel: discord.TextChannel):
    """Sets the channel to log events."""
    global log_channel
    log_channel = channel
    await ctx.send(f"Log channel set to {channel.mention}")

# Command to ping the bot
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def serverinfo(ctx):
    server = ctx.guild
    text_channels = len(server.text_channels)
    voice_channels = len(server.voice_channels)
    category_channels = len(server.categories)
    
    embed = discord.Embed(title=f"Server Info: {server.name}", color=discord.Color.blue())
    embed.add_field(name="Owner", value=server.owner, inline=False)
    embed.add_field(name="Member Count", value=server.member_count, inline=False)
    embed.add_field(name="Role Count", value=len(server.roles), inline=False)
    embed.add_field(name="Channels", 
                    value=f"Text: {text_channels}, Voice: {voice_channels}, Categories: {category_channels}", 
                    inline=False)
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    embed.set_footer(text=f"ID: {server.id} | Server Created: {server.created_at.strftime('%B %d, %Y')}")
    
    await ctx.send(embed=embed)    
    
# Command to kick a user
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.mention} for {reason}')

# Command to ban a user
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention} for {reason}')

# Command to unban a user
@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member_name.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return

    await ctx.send(f'Member {member_name}#{member_discriminator} not found')

# Command to timeout a user
@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: int, *, reason=None):
    duration_seconds = duration * 60  # Convert minutes to seconds
    await member.edit(timed_out_until=discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds), reason=reason)
    await ctx.send(f'Timed out {member.mention} for {duration} minutes for {reason}')

# Command to remove timeout from a user
@bot.command(name='untimeout')
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.edit(timed_out_until=None)
    await ctx.send(f'Removed timeout from {member.mention}')

# Command to purge messages in a channel
@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int):
    await ctx.channel.purge(limit=limit + 1)  # +1 to account for the command message itself
    await ctx.send(f'Purged {limit} messages.')

# Command to mute a user
@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")  # Ensure this role exists
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")

        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f'Muted {member.mention} for {reason}.')

# Command to unmute a user
@bot.command(name='unmute')
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'Unmuted {member.mention}.')
    else:
        await ctx.send(f'{member.mention} is not muted.')

# Command to get user information
@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member):
    embed = discord.Embed(title="User Info", color=discord.Color.blue())
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Discriminator", value=f"#{member.discriminator}", inline=True)
    embed.add_field(name="User ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)

    await ctx.send(embed=embed)

# Command to say something
@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.send(message)

@bot.event
async def on_message_delete(message):
    """Logs deleted messages."""
    if log_channel:  # Check if log channel is set
        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Author**: {message.author}\n**Content**: {message.content}",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Message deleted at {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    """Logs edited messages."""
    if log_channel:  # Check if log channel is set
        embed = discord.Embed(
            title="Message Edited",
            description=f"**Author**: {before.author}\n**Before**: {before.content}\n**After**: {after.content}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Message edited at {after.edited_at.strftime('%Y-%m-%d %H:%M:%S')}")
        await log_channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    """Logs when a member joins the server."""
    if log_channel:  # Check if log channel is set
        embed = discord.Embed(
            title="Member Joined",
            description=f"**Member**: {member.mention}\n**Joined At**: {member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}",
            color=discord.Color.green()
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    """Logs when a member is banned."""
    if log_channel:
        embed = discord.Embed(
            title="Member Banned",
            description=f"**User**: {user.mention}\n**Banned By**: {guild.me.mention}",
            color=discord.Color.red()
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    """Logs when a member is unbanned."""
    if log_channel:
        embed = discord.Embed(
            title="Member Unbanned",
            description=f"**User**: {user.mention}",
            color=discord.Color.green()
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_member_kick(member):
    """Logs when a member is kicked."""
    if log_channel:
        embed = discord.Embed(
            title="Member Kicked",
            description=f"**User**: {member.mention}\n**Kicked By**: {member.guild.me.mention}",
            color=discord.Color.orange()
        )
        await log_channel.send(embed=embed)
        
@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    """Locks the channel, preventing members from sending messages."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 This channel has been locked.")

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """Unlocks the channel, allowing members to send messages."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 This channel has been unlocked.")
    
@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    """Sets the slow mode delay in the current channel."""
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slow mode is now set to {seconds} seconds in this channel.")   
    
    # Global variables for customizable welcome message settings
welcome_photo_url = None  # Default is no photo
welcome_message = "Welcome to the server, {user}!"  # Default welcome message
welcome_author = "Server Team"  # Default author name
welcome_title = "Welcome!"  # Default title
welcome_footer = None  # Default no footer

# Command to customize the welcome settings
@bot.command(name="setwelcome")
@commands.has_permissions(administrator=True)
async def set_welcome(ctx, message: str, title: str, photo: str = None, author: str = None, footer: str = None):
    global welcome_photo_url, welcome_message, welcome_author, welcome_title, welcome_footer
    welcome_message = message
    welcome_title = title
    if photo:
        welcome_photo_url = photo
    if author:
        welcome_author = author
    if footer:
        welcome_footer = footer
    await ctx.send("Welcome message settings have been updated.")

# Event for welcoming new members
@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title=welcome_title,
        description=welcome_message.format(user=member.mention),
        color=discord.Color.blue()
    )
    if welcome_author:
        embed.set_author(name=welcome_author)
    if welcome_photo_url:
        embed.set_thumbnail(url=welcome_photo_url)
    if welcome_footer:
        embed.set_footer(text=welcome_footer)

    # Send the welcome message in a specific channel (replace "general" with your channel name)
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(embed=embed)
        
# The verification logic when button is clicked
class VerifyButton(View):
    def __init__(self, member):
        super().__init__(timeout=None)  # Timeout is None so the button remains interactable
        self.member = member

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.member:
            # Here, you can implement the logic to verify the user.
            # For now, let's send a message confirming verification
            await interaction.response.send_message(f"**{self.member.display_name}** has been successfully verified!", ephemeral=True)
            # Add the 'Verified' role (you can modify this role based on your needs)
            verified_role = discord.utils.get(self.member.guild.roles, name="Verified")
            if verified_role:
                await self.member.add_roles(verified_role)
        else:
            await interaction.response.send_message("You are not allowed to click this button.", ephemeral=True)

# The command to send an embed with the verify button
@bot.command(name='send_verify')
async def send_verify(ctx):
    # Send the embed to the channel with a button
    embed = discord.Embed(
        title="Verification Required",
        description="This server requires you to verify yourself to get access to the server, verify by clicking on the verify button below.",
        color=discord.Color.blue()
    )

    # Send the embed and attach the button view
    view = VerifyButton(ctx.author)
    await ctx.send(embed=embed, view=view)
    
# Run the bot with the token
bot.run('TOKEN_HERE')