import discord
from discord.ext import commands
from datetime import timedelta, datetime
from discord.ui import Button, View
from googlesearch import search
import json
import os

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
                f'{prefix}ping - Responds with Pong! And latency in ms',
                f'{prefix}kick @user [reason] - Kicks the mentioned user with an optional reason.',
                f'{prefix}ban @user [reason] - Bans the mentioned user with an optional reason.',
                f'{prefix}unban [user#1234] - Unbans a user using their username and discriminator.',
                f'{prefix}timeout [@user] [duration in minutes] [reason] - Times out the mentioned user for a specified duration with an optional reason.',
                f'{prefix}untimeout [@user] - Removes timeout from the mentioned user.',
                f'{prefix}purge [number] - Deletes the specified number of messages in the channel.',
                f'{prefix}mute @user [reason] - Mutes the mentioned user.',
                f'{prefix}unmute [@user] - Unmutes the mentioned user.',
                f'{prefix}slowmode [seconds] - Sets slowmode in the current channel.',
                f'{prefix}lock - Locks the current channel.',
                f'{prefix}unlock - Unlocks the current channel.',
                f'{prefix}say [message] - Makes the bot say the message you provide.',
                f'{prefix}serverinfo - Get server info/stats.',
                f'{prefix}userinfo - Get user info/stats.',
                f'{prefix}embedsend title:<title>;description:<description>;[color:<hex_code>;author_name:<name>;footer_text:<text>;image:<url>;field1_name:<name>;field1_value:<value>] - Creates a fully customizable embed with optional fields, author, footer, and images.'
                
            ]

            # Create the embed
            embed = discord.Embed(title="Here are my commands:", color=discord.Color.blue())
            embed.description = "\n".join(commands_list)

            # Send the embed
            await message.channel.send(embed=embed)

        await bot.process_commands(message)

log_channel = None  # Initialize log channel

@bot.command(name='setlogchannel')
@commands.has_permissions(administrator=True)
async def setlogchannel(ctx, channel: discord.TextChannel):
    """Sets the channel to log events."""
    global log_channel
    log_channel = channel
    await ctx.send(f"Log channel set to {channel.mention}")
    
    # Dictionary to store AFK users and their messages
afk_users = {}

@bot.command()
async def afk(ctx, *, message: str = "AFK"):
    """Set yourself as AFK with an optional message."""
    afk_users[ctx.author.id] = message
    await ctx.send(f"{ctx.author.mention} is now AFK: {message}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if the user is returning from AFK
    if message.author.id in afk_users:
        del afk_users[message.author.id]
        await message.channel.send(f"Welcome back, {message.author.mention}! You are no longer AFK.")

    # Check if the message mentions an AFK user
    for mention in message.mentions:
        if mention.id in afk_users:
            await message.channel.send(f"{mention.mention} is AFK: {afk_users[mention.id]}")

    await bot.process_commands(message)
    
@bot.command(name='google')
async def google_search(ctx, *, query: str):
    """
    Searches Google for the given query and displays links and image results.
    """
    search_results = list(search(query, num_results=8))  # Get top 8 search results
    
    # Create an embed to show the search results
    embed = discord.Embed(title=f"Google Search Results for: {query}", color=discord.Color.blurple())
    
    # Add image results if available
    image_results = search(f"{query} images", num_results=3)
    image_urls = "\n".join(image_results) if image_results else "No image results found."
    
    embed.add_field(name="Top Links", value="\n".join(search_results), inline=False)
    embed.add_field(name="Image Results", value=image_urls, inline=False)
    
    # Send the embed
    await ctx.send(embed=embed)
    
    # File to store user data
DATA_FILE = "user_data.json"

# Load user data from the file
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save user data to the file
def save_user_data():
    with open(DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Load data into memory
users = load_user_data()

# Helper function to get user data
def get_user_data(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "wallet": 0,
            "bank": 0,
            "last_daily": None,
            "investments": 0,
        }
    return users[str(user_id)]

# Command: Daily reward
@bot.command()
async def daily(ctx):
    user_data = get_user_data(ctx.author.id)
    now = datetime.utcnow()

    if user_data["last_daily"]:
        last_daily = datetime.fromisoformat(user_data["last_daily"])
        if now - last_daily < timedelta(days=1):
            remaining_time = timedelta(days=1) - (now - last_daily)
            await ctx.send(f"You've already claimed your daily reward. Try again in {remaining_time}.")
            return

    user_data["wallet"] += 100
    user_data["last_daily"] = now.isoformat()
    save_user_data()
    await ctx.send(f"{ctx.author.mention} claimed their daily 100 coins!")
  
 # Command: Do a job
@bot.command()
async def job(ctx):
    user_data = get_user_data(ctx.author.id)
    earnings = 50  # Flat job earnings
    user_data["wallet"] += earnings
    save_user_data()
    await ctx.send(f"{ctx.author.mention} did a job and earned {earnings} coins!")

# Command: Deposit money to bank
@bot.command()
async def deposit(ctx, amount: int):
    user_data = get_user_data(ctx.author.id)

    if amount <= 0:
        await ctx.send("Amount must be greater than zero.")
        return

    if user_data["wallet"] < amount:
        await ctx.send("You don't have enough money in your wallet.")
        return

    user_data["wallet"] -= amount
    user_data["bank"] += amount
    save_user_data()
    await ctx.send(f"{ctx.author.mention} deposited {amount} coins to the bank!")

# Command: Withdraw money from bank
@bot.command()
async def withdraw(ctx, amount: int):
    user_data = get_user_data(ctx.author.id)

    if amount <= 0:
        await ctx.send("Amount must be greater than zero.")
        return

    if user_data["bank"] < amount:
        await ctx.send("You don't have enough money in the bank.")
        return

    user_data["bank"] -= amount
    user_data["wallet"] += amount
    save_user_data()
    await ctx.send(f"{ctx.author.mention} withdrew {amount} coins from the bank!")

# Command: Invest money
@bot.command()
async def invest(ctx, amount: int):
    user_data = get_user_data(ctx.author.id)

    if amount <= 0:
        await ctx.send("Amount must be greater than zero.")
        return

    if user_data["wallet"] < amount:
        await ctx.send("You don't have enough money to invest.")
        return

    user_data["wallet"] -= amount
    user_data["investments"] += amount
    save_user_data()
    await ctx.send(f"{ctx.author.mention} invested {amount} coins!")

# Command: Check investments
@bot.command()
async def investments(ctx):
    user_data = get_user_data(ctx.author.id)
    if user_data["investments"] > 0:
        profit = user_data["investments"] * 1.2  # 20% profit
        user_data["wallet"] += profit
        user_data["investments"] = 0
        save_user_data()
        await ctx.send(f"{ctx.author.mention} claimed their investment returns of {profit} coins!")
    else:
        await ctx.send("You don't have any active investments.")

# Command: Check balance
@bot.command()
async def balance(ctx):
    user_data = get_user_data(ctx.author.id)
    wallet = user_data["wallet"]
    bank = user_data["bank"]
    await ctx.send(f"{ctx.author.mention}, Wallet: {wallet} coins, Bank: {bank} coins.")

# Command: Shop
@bot.command()
async def shop(ctx):
    shop_items = {
        "item1": {"name": "Laptop", "price": 500},
        "item2": {"name": "Phone", "price": 300},
        "item3": {"name": "Headphones", "price": 150},
    }
    shop_list = "\n".join([f"{key}: {item['name']} - {item['price']} coins" for key, item in shop_items.items()])
    await ctx.send(f"Shop:\n{shop_list}")

# Command: Buy from the shop
@bot.command()
async def buy(ctx, item_id):
    shop_items = {
        "item1": {"name": "Laptop", "price": 500},
        "item2": {"name": "Phone", "price": 300},
        "item3": {"name": "Headphones", "price": 150},
    }

    user_data = get_user_data(ctx.author.id)

    if item_id not in shop_items:
        await ctx.send("Invalid item ID.")
        return

    item = shop_items[item_id]
    if user_data["wallet"] < item["price"]:
        await ctx.send("You don't have enough money to buy this item.")
        return

    user_data["wallet"] -= item["price"]
    save_user_data()
    await ctx.send(f"{ctx.author.mention} bought {item['name']} for {item['price']} coins!")
  
@bot.command(name='embedsend')
async def custom_embed(ctx, *, options):
    """
    Create a customizable embed with optional fields, author, footer, and image.
    Pass options in the format: key:value;key:value.
    """
    # Split options into key-value pairs
    options = options.split(";")
    embed_kwargs = {}

    for option in options:
        try:
            key, value = option.split(":", 1)
            embed_kwargs[key.strip().lower()] = value.strip()
        except ValueError:
            await ctx.send(f"Invalid format for option: `{option}`. Use `key:value` format.")
            return

    # Extract main variables with defaults
    title = embed_kwargs.get("title", "Default Title")
    description = embed_kwargs.get("description", "Default Description")
    color = discord.Color.blue()  # Default color
    if "color" in embed_kwargs:
        try:
            color = discord.Color(int(embed_kwargs["color"].lstrip("#"), 16))  # Hex to int
        except ValueError:
            await ctx.send("Invalid color format. Use a hex code like #3498db.")
            return

    # Create the embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    # Optional: Author
    if "author_name" in embed_kwargs:
        embed.set_author(
            name=embed_kwargs["author_name"],
            url=embed_kwargs.get("author_url"),
            icon_url=embed_kwargs.get("author_icon")
        )

    # Optional: Footer
    if "footer_text" in embed_kwargs:
        embed.set_footer(
            text=embed_kwargs["footer_text"],
            icon_url=embed_kwargs.get("footer_icon")
        )

    # Optional: Thumbnail
    if "thumbnail" in embed_kwargs:
        embed.set_thumbnail(url=embed_kwargs["thumbnail"])

    # Optional: Image
    if "image" in embed_kwargs:
        embed.set_image(url=embed_kwargs["image"])

    # Optional: Fields
    for i in range(1, 26):  # Discord allows up to 25 fields
        field_name = embed_kwargs.get(f"field{i}_name")
        field_value = embed_kwargs.get(f"field{i}_value")
        if field_name and field_value:
            inline = embed_kwargs.get(f"field{i}_inline", "true").lower() == "true"
            embed.add_field(name=field_name, value=field_value, inline=inline)

    # Send the embed
    await ctx.send(embed=embed)  
    
@bot.command(name="ping")
async def ping(ctx):
    """Shows the bot's latency."""
    latency = round(bot.latency * 1000)  # Convert latency to milliseconds
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms")
    
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

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: int, *, reason="No reason provided"):
    # Ensure `timed_out_until` is correctly calculated
    duration_seconds = duration * 60  # Convert minutes to seconds
    timeout_until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
    
    try:
        await member.edit(timed_out_until=timeout_until, reason=reason)
        await ctx.send(f'Timed out {member.mention} for {duration} minute(s). Reason: {reason}')
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to timeout the user: {e}")

@bot.command(name='setuptickets')
@commands.has_permissions(administrator=True)
async def setuptickets(ctx, role: discord.Role):
    """Sets up a ticket panel where tickets are controlled by a specified role."""

    embed = discord.Embed(
        title="🎫 Ticket Support",
        description="Click the button below to create a ticket. A staff member will assist you shortly.",
        color=discord.Color.blurple()
    )

    button = Button(label="Create Ticket", style=discord.ButtonStyle.green)

    async def button_callback(interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category(name="Tickets")

        existing_ticket = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{interaction.user.name.lower().replace(' ', '-')}"
        )
        if existing_ticket:
            await interaction.response.send_message(
                "You already have an open ticket!", ephemeral=True
            )
            return

        ticket_channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True
        )

        close_button = Button(label="Close Ticket", style=discord.ButtonStyle.red)

        async def close_callback(interaction_close: discord.Interaction):
            if interaction_close.user == interaction.user or role in interaction_close.user.roles:
                await ticket_channel.delete()
            else:
                await interaction_close.response.send_message(
                    "Only the ticket creator or a staff member can close this ticket.", ephemeral=True
                )

        close_button.callback = close_callback
        close_view = View()
        close_view.add_item(close_button)

        await ticket_channel.send(
            f"{interaction.user.mention}, a staff member will assist you shortly. "
            f"{role.mention}, use the button below to close the ticket when resolved.",
            view=close_view
        )

    button.callback = button_callback
    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)      
        
# Command to remove timeout from a user
@bot.command(name='untimeout')
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.edit(timed_out_until=None)
    await ctx.send(f'Removed timeout from {member.mention}')

    # Command to bulk delete messages in a channel
@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int):
    """
    Purges a specified number of messages in the current channel.
    Usage: ;purge <number_of_messages>
    """
    if limit <= 0:
        await ctx.send("Please specify a number greater than 0.", delete_after=5)
        return

    try:
        # Bulk delete messages (Discord handles rate limits more effectively with `purge`)
        deleted = await ctx.channel.purge(limit=limit + 1)  # Include the command message
        confirmation = await ctx.send(f"✅ Purged {len(deleted) - 1} messages.")  # Exclude the command itself
        await confirmation.delete(delay=5)  # Auto-delete confirmation after 5 seconds
    except discord.HTTPException as e:
        await ctx.send(f"❌ An error occurred: {str(e)}", delete_after=10)
    
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
@bot.command(name='setverify')
@commands.has_permissions(administrator=True)
async def setverify(ctx):
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