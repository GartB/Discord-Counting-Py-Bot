import discord
from discord.ext import commands
import re
import random
import json
import os
import time

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
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {
                "counting": {"current_count": 0, "last_user_id": None},
                "fish_data": {},
                "user_coins": {},
                "user_rods": {},
                "last_fish_time": {}
            }
    return {
        "counting": {"current_count": 0, "last_user_id": None},
        "fish_data": {},
        "user_coins": {},
        "user_rods": {},
        "last_fish_time": {}
    }

# Save data to JSON file
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Initialize data
data = load_data()
current_count = data["counting"]["current_count"]
last_user_id = data["counting"]["last_user_id"]
fish_data = data["fish_data"]
user_coins = data["user_coins"]
user_rods = data["user_rods"]
last_fish_time = data["last_fish_time"]

# Rod definitions with fish probabilities
RODS = {
    "BasicRod": [
        ("Common Fish 🐟", 0.61),
        ("Rare Fish 🐠", 0.25),
        ("Epic Fish 🐳", 0.09),
        ("Legendary Fish 🐉", 0.05)
    ],
    "NewRod": [
        ("Common Fish 🐟", 0.47),
        ("Rare Fish 🐠", 0.33),
        ("Epic Fish 🐳", 0.11),
        ("Legendary Fish 🐉", 0.09)
    ],
    "SpecialRod": [
        ("Common Fish 🐟", 0.37),
        ("Rare Fish 🐠", 0.21),
        ("Epic Fish 🐳", 0.27),
        ("Legendary Fish 🐉", 0.15)
    ],
    "UltimateRod": [
        ("Common Fish 🐟", 0.18),
        ("Rare Fish 🐠", 0.24),
        ("Epic Fish 🐳", 0.30),
        ("Legendary Fish 🐉", 0.25),
        ("Ultimate Fish 🦅", 0.03)
    ]
}

# Shop prices
ROD_PRICES = {
    "NewRod": 1000,
    "SpecialRod": 5000,
    "UltimateRod": 10000
}

# Fish selling prices
FISH_PRICES = {
    "Common Fish 🐟": 10,
    "Rare Fish 🐠": 25,
    "Epic Fish 🐳": 50,
    "Legendary Fish 🐉": 100,
    "Ultimate Fish 🦅": 500
}

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
    
    user_id = str(ctx.author.id)
    
    # Check cooldown (3 minutes = 180 seconds)
    if user_id in last_fish_time:
        time_since_last_fish = time.time() - last_fish_time[user_id]
        if time_since_last_fish < 180:
            remaining = int(180 - time_since_last_fish)
            await ctx.send(f"{ctx.author.mention}, you need to wait {remaining} seconds before fishing again!")
            return
    
    # Get user's rod or default BasicRod
    user_rod = user_rods.get(user_id, "BasicRod")
    fish_types = RODS[user_rod]
    
    # Check for double catch chance (only for NewRod and above)
    double_catch = False
    if user_rod != "BasicRod":
        # 2% chance for double catch with better rods
        double_catch = random.random() < 0.02
    
    # Generate random catch(es)
    if double_catch:
        # Catch two fish
        catches = random.choices(
            [fish[0] for fish in fish_types],
            weights=[fish[1] for fish in fish_types],
            k=2
        )
        catch_message = f"{ctx.author.mention} went fishing with {user_rod} and caught **TWO FISH**! 🎣\n{catches[0]} and {catches[1]}!"
    else:
        # Catch one fish
        catches = [random.choices(
            [fish[0] for fish in fish_types],
            weights=[fish[1] for fish in fish_types],
            k=1
        )[0]]
        catch_message = f"{ctx.author.mention} went fishing with {user_rod} and caught a {catches[0]}!"
    
    # Update fish data for the user
    if user_id not in fish_data:
        fish_data[user_id] = {
            "Common Fish 🐟": 0,
            "Rare Fish 🐠": 0,
            "Epic Fish 🐳": 0,
            "Legendary Fish 🐉": 0,
            "Ultimate Fish 🦅": 0
        }
    
    # Add all catches to inventory
    for catch in catches:
        fish_data[user_id][catch] += 1
    
    last_fish_time[user_id] = time.time()
    
    data["fish_data"] = fish_data
    data["last_fish_time"] = last_fish_time
    save_data(data)
    
    await ctx.send(catch_message)

@bot.command()
async def fishstats(ctx):
    """Display the user's fish catch statistics"""
    user_id = str(ctx.author.id)
    
    # Always show basic user info
    stats = f"{ctx.author.mention}'s Fishing Stats:\n"
    stats += f"Coins: {user_coins.get(user_id, 0)} 💰\n"
    stats += f"Current Rod: {user_rods.get(user_id, 'BasicRod')}\n"
    
    # Show fish stats only if they have caught fish
    if user_id in fish_data and any(fish_data[user_id].values()):
        stats += "\nFish Caught:\n"
        for fish, count in fish_data[user_id].items():
            if count > 0:
                stats += f"{fish}: {count}\n"
    else:
        stats += "\nNo fish caught yet! Use !fish to start fishing!"
    
    await ctx.send(stats)

@bot.command()
async def sellfish(ctx, fish_type: str, amount: int = 1):
    """Sell fish for coins"""
    user_id = str(ctx.author.id)
    
    # Map simple fish names to full fish names with emojis
    fish_name_mapping = {
        "common": "Common Fish 🐟",
        "rare": "Rare Fish 🐠", 
        "epic": "Epic Fish 🐳",
        "legendary": "Legendary Fish 🐉",
        "ultimate": "Ultimate Fish 🦅",
        "common fish": "Common Fish 🐟",
        "rare fish": "Rare Fish 🐠",
        "epic fish": "Epic Fish 🐳", 
        "legendary fish": "Legendary Fish 🐉",
        "ultimate fish": "Ultimate Fish 🦅"
    }
    
    # Convert input to lowercase for easier matching
    fish_type_lower = fish_type.lower()
    
    # Get the full fish name with emoji
    if fish_type_lower in fish_name_mapping:
        full_fish_name = fish_name_mapping[fish_type_lower]
    else:
        # If not found in mapping, try the original input
        full_fish_name = fish_type
    
    if user_id not in fish_data or full_fish_name not in FISH_PRICES:
        await ctx.send(f"{ctx.author.mention}, invalid fish type or you haven't caught any fish! Valid types: Common, Rare, Epic, Legendary, Ultimate")
        return
    
    if amount <= 0:
        await ctx.send(f"{ctx.author.mention}, please specify a valid amount to sell!")
        return
    
    if fish_data[user_id].get(full_fish_name, 0) < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have enough {full_fish_name} to sell!")
        return
    
    # Update fish and coins
    fish_data[user_id][full_fish_name] -= amount
    if user_id not in user_coins:
        user_coins[user_id] = 0
    user_coins[user_id] += FISH_PRICES[full_fish_name] * amount
    
    data["fish_data"] = fish_data
    data["user_coins"] = user_coins
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} sold {amount} {full_fish_name} for {FISH_PRICES[full_fish_name] * amount} coins!")

@bot.command()
async def sell(ctx, fish_type: str, amount: int = 1):
    """Sell fish for coins (shorthand for sellfish)"""
    user_id = str(ctx.author.id)
    
    # Map simple fish names to full fish names with emojis
    fish_name_mapping = {
        "common": "Common Fish 🐟",
        "rare": "Rare Fish 🐠", 
        "epic": "Epic Fish 🐳",
        "legendary": "Legendary Fish 🐉",
        "ultimate": "Ultimate Fish 🦅",
        "common fish": "Common Fish 🐟",
        "rare fish": "Rare Fish 🐠",
        "epic fish": "Epic Fish 🐳", 
        "legendary fish": "Legendary Fish 🐉",
        "ultimate fish": "Ultimate Fish 🦅"
    }
    
    # Convert input to lowercase for easier matching
    fish_type_lower = fish_type.lower()
    
    # Get the full fish name with emoji
    if fish_type_lower in fish_name_mapping:
        full_fish_name = fish_name_mapping[fish_type_lower]
    else:
        # If not found in mapping, try the original input
        full_fish_name = fish_type
    
    if user_id not in fish_data or full_fish_name not in FISH_PRICES:
        await ctx.send(f"{ctx.author.mention}, invalid fish type or you haven't caught any fish! Valid types: Common, Rare, Epic, Legendary, Ultimate")
        return
    
    if amount <= 0:
        await ctx.send(f"{ctx.author.mention}, please specify a valid amount to sell!")
        return
    
    if fish_data[user_id].get(full_fish_name, 0) < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have enough {full_fish_name} to sell!")
        return
    
    # Update fish and coins
    fish_data[user_id][full_fish_name] -= amount
    if user_id not in user_coins:
        user_coins[user_id] = 0
    user_coins[user_id] += FISH_PRICES[full_fish_name] * amount
    
    data["fish_data"] = fish_data
    data["user_coins"] = user_coins
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} sold {amount} {full_fish_name} for {FISH_PRICES[full_fish_name] * amount} coins!")

@bot.command()
async def shop(ctx):
    """Display the fishing shop"""
    shop_message = "🎣 Fishing Shop 🎣\n\n"
    for rod, price in ROD_PRICES.items():
        shop_message += f"{rod} - {price} coins\n"
    shop_message += "\nUse !buyrod <rod_name> to purchase a rod!"
    await ctx.send(shop_message)

@bot.command()
async def buyrod(ctx, *, rod_name: str):
    """Buy a fishing rod from the shop"""
    user_id = str(ctx.author.id)
    
    if rod_name not in ROD_PRICES:
        await ctx.send(f"{ctx.author.mention}, invalid rod type! Available rods: {', '.join(ROD_PRICES.keys())}")
        return
    
    user_coins[user_id] = user_coins.get(user_id, 0)
    if user_coins[user_id] < ROD_PRICES[rod_name]:
        await ctx.send(f"{ctx.author.mention}, you need {ROD_PRICES[rod_name]} coins to buy {rod_name}!")
        return
    
    # Update user rod and coins
    user_coins[user_id] -= ROD_PRICES[rod_name]
    user_rods[user_id] = rod_name
    
    data["user_coins"] = user_coins
    data["user_rods"] = user_rods
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} purchased {rod_name} for {ROD_PRICES[rod_name]} coins!")

@bot.command()
async def donate(ctx, member: discord.Member, amount: int):
    """Donate coins to another player"""
    user_id = str(ctx.author.id)
    target_id = str(member.id)
    
    # Prevent donating to yourself
    if user_id == target_id:
        await ctx.send(f"{ctx.author.mention}, you can't donate to yourself!")
        return
    
    # Check if user has enough coins
    if user_id not in user_coins or user_coins[user_id] < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have enough coins to donate {amount} coins!")
        return
    
    if amount <= 0:
        await ctx.send(f"{ctx.author.mention}, please specify a valid amount to donate!")
        return
    
    # Transfer coins
    user_coins[user_id] -= amount
    if target_id not in user_coins:
        user_coins[target_id] = 0
    user_coins[target_id] += amount
    
    data["user_coins"] = user_coins
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} donated {amount} coins to {member.mention}! 💰")

# Replace 'YOUR_TOKEN_HERE' with your bot token
bot.run('YOUR_TOKEN_HERE')
