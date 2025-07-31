import discord
from discord.ext import commands
import re
import random
import json
import os

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel IDs (replace with your actual channel IDs)
COUNTING_CHANNEL_ID = Channel_For_Counting_ID_Here  # Replace with actual counting channel ID
FISHING_CHANNEL_ID = Channel_For_Fishing_ID_Here  # Replace with actual fishing channel ID

# File for persistent data storage
DATA_FILE = "bot_data.json"

# Load data from JSON file
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"counting": {"current_count": 0, "last_user_id": None}, "fish_data": {}}
    return {"counting": {"current_count": 0, "last_user_id": None}, "fish_data": {}}

# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize data
data = load_data()
current_count = data["counting"]["current_count"]
last_user_id = data["counting"]["last_user_id"]
fish_data = data["fish_data"]

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    global current_count, last_user_id
    
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)
    
    # Check if message is in the counting channel
    if message.channel.id == COUNTING_CHANNEL_ID:
        # Remove whitespace and check if message is empty
        content = message.content.strip()
        if not content:
            return
        
        # Check if the same user is counting twice in a row
        if message.author.id == last_user_id:
            await message.add_reaction('❌')
            current_count = 0
            last_user_id = None
            data["counting"]["current_count"] = current_count
            data["counting"]["last_user_id"] = last_user_id
            save_data(data)
            await message.channel.send(f"{message.author.mention}, you can't count twice in a row! Count reset to 0.")
            return
        
        try:
            # First, try to parse as a plain integer
            number = int(content)
        except ValueError:
            # If not an integer, try to evaluate as a math expression
            try:
                # Basic security: only allow digits, basic operators, and parentheses
                if not re.match(r'^[\d\s+\-*/().]+$', content):
                    return  # Ignore if contains invalid characters
                
                # Evaluate the expression safely
                number = eval(content, {"__builtins__": {}}, {"sum": sum})
                if not isinstance(number, (int, float)) or number != int(number):
                    return  # Ignore if result is not an integer
                number = int(number)
            except (SyntaxError, NameError, TypeError, ZeroDivisionError):
                return  # Ignore invalid expressions
        
        # Check if the number is correct
        if number == current_count + 1:
            current_count = number
            last_user_id = message.author.id
            data["counting"]["current_count"] = current_count
            data["counting"]["last_user_id"] = last_user_id
            save_data(data)
            await message.add_reaction('✅')
        else:
            await message.add_reaction('❌')
            current_count = 0
            last_user_id = None
            data["counting"]["current_count"] = current_count
            data["counting"]["last_user_id"] = last_user_id
            save_data(data)
            await message.channel.send(f"{message.author.mention}, wrong number! The next number should be {current_count + 1}. Count reset to 0.")

@bot.command()
async def setcount(ctx, number: int):
    """Admin command to set the current count"""
    if ctx.author.guild_permissions.administrator:
        global current_count, last_user_id
        current_count = number
        last_user_id = None
        data["counting"]["current_count"] = current_count
        data["counting"]["last_user_id"] = last_user_id
        save_data(data)
        await ctx.send(f"Count has been set to {current_count}")
    else:
        await ctx.send("You need administrator permissions to use this command!")

@bot.command()
async def resetcount(ctx):
    """Admin command to reset the count"""
    if ctx.author.guild_permissions.administrator:
        global current_count, last_user_id
        current_count = 0
        last_user_id = None
        data["counting"]["current_count"] = current_count
        data["counting"]["last_user_id"] = last_user_id
        save_data(data)
        await ctx.send("Count has been reset to 0")
    else:
        await ctx.send("You need administrator permissions to use this command!")

@bot.command()
async def fish(ctx):
    """Fishing command to catch random fish in the fishing channel"""
    if ctx.channel.id != FISHING_CHANNEL_ID:
        await ctx.send(f"This command can only be used in the fishing channel!")
        return
    
    # Define fish with their probabilities
    fish_types = [
        ("Common Fish 🐟", 0.61),
        ("Rare Fish 🐠", 0.25),
        ("Epic Fish 🐳", 0.09),
        ("Legendary Fish 🐉", 0.05)
    ]
    
    # Generate random catch
    catch = random.choices(
        [fish[0] for fish in fish_types],
        weights=[fish[1] for fish in fish_types],
        k=1
    )[0]
    
    # Update fish data for the user
    user_id = str(ctx.author.id)
    if user_id not in fish_data:
        fish_data[user_id] = {
            "Common Fish 🐟": 0,
            "Rare Fish 🐠": 0,
            "Epic Fish 🐳": 0,
            "Legendary Fish 🐉": 0
        }
    fish_data[user_id][catch] += 1
    data["fish_data"] = fish_data
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} went fishing and caught a {catch}!")

@bot.command()
async def fishstats(ctx):
    """Display the user's fish catch statistics"""
    user_id = str(ctx.author.id)
    if user_id not in fish_data or not any(fish_data[user_id].values()):
        await ctx.send(f"{ctx.author.mention}, you haven't caught any fish yet!")
        return
    
    stats = f"{ctx.author.mention}'s Fishing Stats:\n"
    for fish, count in fish_data[user_id].items():
        if count > 0:
            stats += f"{fish}: {count}\n"
    await ctx.send(stats)

# Replace 'YOUR_TOKEN_HERE' with your bot token
bot.run('YOUR_TOKEN_HERE')
