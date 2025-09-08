import discord
from discord.ext import commands, tasks
import re
import random
import json
import os
import time
import asyncio

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel IDs (replace with your actual channel IDs)
COUNTING_CHANNEL_ID = Channel_For_Counting_ID_Here  # Replace with actual counting channel ID
FISHING_CHANNEL_ID = Channel_For_Fishing_ID_Here  # Replace with actual fishing channel ID

# File for persistent data storage
DATA_FILE = "bot_data.json"

# Global variables for the random fish event
random_fish_event_active = False
random_fish_event_message = None
random_fish_event_start_time = None

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
                "last_fish_time": {},
                "records": {
                    "largest_catch": {"user_id": None, "amount": 0, "date": None},
                    "most_common_fish": {"user_id": None, "amount": 0, "date": None},
                    "most_rare_fish": {"user_id": None, "amount": 0, "date": None},
                    "most_epic_fish": {"user_id": None, "amount": 0, "date": None},
                    "most_legendary_fish": {"user_id": None, "amount": 0, "date": None},
                    "most_ultimate_fish": {"user_id": None, "amount": 0, "date": None},
                    "biggest_sale": {"user_id": None, "amount": 0, "fish_type": None, "date": None},
                    "longest_streak": {"user_id": None, "days": 0, "date": None}
                }
            }
    return {
        "counting": {"current_count": 0, "last_user_id": None},
        "fish_data": {},
        "user_coins": {},
        "user_rods": {},
        "last_fish_time": {},
        "records": {
            "largest_catch": {"user_id": None, "amount": 0, "date": None},
            "most_common_fish": {"user_id": None, "amount": 0, "date": None},
            "most_rare_fish": {"user_id": None, "amount": 0, "date": None},
            "most_epic_fish": {"user_id": None, "amount": 0, "date": None},
            "most_legendary_fish": {"user_id": None, "amount": 0, "date": None},
            "most_ultimate_fish": {"user_id": None, "amount": 0, "date": None},
            "biggest_sale": {"user_id": None, "amount": 0, "fish_type": None, "date": None},
            "longest_streak": {"user_id": None, "days": 0, "date": None}
        }
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
fishing_records = data["records"]

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

# Case-insensitive rod name normalization and lookup
def normalize_rod_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.casefold())

# Map various user inputs to canonical rod keys
ROD_NAME_LOOKUP = {normalize_rod_name(k): k for k in ROD_PRICES.keys()}
ROD_NAME_LOOKUP.update({
    # Also accept short forms without the word "rod"
    "new": "NewRod",
    "special": "SpecialRod",
    "ultimate": "UltimateRod",
})

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
    # Start the random fish event task
    random_fish_event_task.start()

@bot.event
async def on_message(message):
    global current_count, last_user_id, random_fish_event_active, random_fish_event_message
    
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Check for "net" command during random fish event
    if (random_fish_event_active and 
        message.channel.id == FISHING_CHANNEL_ID and 
        message.content.lower().strip() == "net"):
        
        await handle_random_fish_catch(message)
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

async def handle_random_fish_catch(message):
    """Handle the random fish catch when someone says 'net'"""
    global random_fish_event_active, random_fish_event_message
    
    user_id = str(message.author.id)
    
    # Get user's rod or default BasicRod
    user_rod = user_rods.get(user_id, "BasicRod")
    
    # Determine number of fish to catch (2-6)
    num_fish = random.randint(2, 6)
    
    # Get available fish types based on user's rod
    available_fish = []
    fish_weights = []
    
    for fish_type, weight in RODS[user_rod]:
        available_fish.append(fish_type)
        fish_weights.append(weight)
    
    # Catch the fish
    catches = random.choices(available_fish, weights=fish_weights, k=num_fish)
    
    # Update fish data for the user
    if user_id not in fish_data:
        fish_data[user_id] = {
            "Common Fish 🐟": 0,
            "Rare Fish 🐠": 0,
            "Epic Fish 🐳": 0,
            "Legendary Fish 🐉": 0,
            "Ultimate Fish 🦅": 0
        }
    
    # Add all catches to inventory and check for records
    current_time = time.time()
    for catch in catches:
        fish_data[user_id][catch] += 1
        
        # Check for individual fish type records
        current_count = fish_data[user_id][catch]
        
        # Map fish names to record keys
        fish_to_record = {
            "Common Fish 🐟": "most_common_fish",
            "Rare Fish 🐠": "most_rare_fish", 
            "Epic Fish 🐳": "most_epic_fish",
            "Legendary Fish 🐉": "most_legendary_fish",
            "Ultimate Fish 🦅": "most_ultimate_fish"
        }
        
        record_key = fish_to_record.get(catch)
        
        if record_key and record_key in fishing_records and current_count > fishing_records[record_key]["amount"]:
            fishing_records[record_key] = {
                "user_id": user_id,
                "amount": current_count,
                "date": current_time
            }
    
    # Check for largest catch record
    if num_fish > fishing_records["largest_catch"]["amount"]:
        fishing_records["largest_catch"] = {
            "user_id": user_id,
            "amount": num_fish,
            "date": current_time
        }
    
    data["fish_data"] = fish_data
    data["records"] = fishing_records
    save_data(data)
    
    # Create catch message
    catch_list = ", ".join(catches)
    catch_message = f"🎣 **RANDOM FISH EVENT!** 🎣\n{message.author.mention} caught **{num_fish} fish** with their {user_rod}!\n\n**Caught:** {catch_list}"
    
    # End the event
    random_fish_event_active = False
    random_fish_event_message = None
    
    await message.channel.send(catch_message)

@tasks.loop(hours=1)  # Check every hour
async def random_fish_event_task():
    """Background task to trigger random fish events"""
    global random_fish_event_active, random_fish_event_message, random_fish_event_start_time
    
    # Don't start a new event if one is already active
    if random_fish_event_active:
        return
    
    # Random chance to trigger event (roughly every 2-8 hours)
    # Since we check every hour, we need a 1/3 to 1/8 chance per hour
    if random.random() < 0.15:  # ~15% chance per hour = roughly every 6-7 hours on average
        await trigger_random_fish_event()

async def trigger_random_fish_event():
    """Trigger a random fish event"""
    global random_fish_event_active, random_fish_event_message, random_fish_event_start_time
    
    try:
        channel = bot.get_channel(FISHING_CHANNEL_ID)
        if not channel:
            return
        
        random_fish_event_active = True
        random_fish_event_start_time = time.time()
        
        # Create the event message
        embed = discord.Embed(
            title="🎣 RANDOM FISH EVENT! 🎣",
            description="A school of fish has appeared! The first person to type **`net`** will catch **2-6 random fish**!",
            color=0x00ff00
        )
        embed.add_field(name="⏰ Time Limit", value="This event will last for 30 minutes!", inline=False)
        embed.add_field(name="🎣 How to Participate", value="Simply type `net` in this channel!", inline=False)
        embed.add_field(name="🎣 Fish Types", value="All fish types are available (except Ultimate Fish unless you have Ultimate Rod)!", inline=False)
        
        random_fish_event_message = await channel.send(embed=embed)
        
        # Set a timer to end the event after 30 minutes
        await asyncio.sleep(1800)  # 30 minutes (30 * 60 = 1800 seconds)
        
        # End the event if it's still active
        if random_fish_event_active:
            random_fish_event_active = False
            embed = discord.Embed(
                title="🎣 RANDOM FISH EVENT ENDED! 🎣",
                description="The fish have swam away! No one caught them in time.",
                color=0xff0000
            )
            await channel.send(embed=embed)
            random_fish_event_message = None
            
    except Exception as e:
        print(f"Error in random fish event: {e}")
        random_fish_event_active = False
        random_fish_event_message = None

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
    
    # Check for double catch chance (different chances for different rods)
    double_catch = False
    if user_rod == "NewRod":
        # 2% chance for double catch with NewRod
        double_catch = random.random() < 0.02
    elif user_rod == "SpecialRod":
        # 4% chance for double catch with SpecialRod
        double_catch = random.random() < 0.04
    elif user_rod == "UltimateRod":
        # 7% chance for double catch with UltimateRod
        double_catch = random.random() < 0.07
    
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
    
    # Add all catches to inventory and check for records
    current_time = time.time()
    for catch in catches:
        fish_data[user_id][catch] += 1
        
        # Check for individual fish type records
        current_count = fish_data[user_id][catch]
        
        # Map fish names to record keys
        fish_to_record = {
            "Common Fish 🐟": "most_common_fish",
            "Rare Fish 🐠": "most_rare_fish", 
            "Epic Fish 🐳": "most_epic_fish",
            "Legendary Fish 🐉": "most_legendary_fish",
            "Ultimate Fish 🦅": "most_ultimate_fish"
        }
        
        record_key = fish_to_record.get(catch)
        
        if record_key and record_key in fishing_records and current_count > fishing_records[record_key]["amount"]:
            fishing_records[record_key] = {
                "user_id": user_id,
                "amount": current_count,
                "date": current_time
            }
    
    # Check for largest catch record (double catches)
    if len(catches) > 1 and len(catches) > fishing_records["largest_catch"]["amount"]:
        fishing_records["largest_catch"] = {
            "user_id": user_id,
            "amount": len(catches),
            "date": current_time
        }
    
    last_fish_time[user_id] = current_time
    
    data["fish_data"] = fish_data
    data["last_fish_time"] = last_fish_time
    data["records"] = fishing_records
    save_data(data)
    
    await ctx.send(catch_message)

@bot.command()
async def fishstats(ctx, member: discord.Member = None):
    """Display the user's fish catch statistics. Use !fishstats @user to see another user's stats."""
    # If no member is mentioned, use the command author
    if member is None:
        member = ctx.author
    
    user_id = str(member.id)
    
    # Always show basic user info
    stats = f"{member.mention}'s Fishing Stats:\n"
    stats += f"Coins: {user_coins.get(user_id, 0)} 💰\n"
    stats += f"Current Rod: {user_rods.get(user_id, 'BasicRod')}\n"
    
    # Calculate total worth of current fish inventory
    total_worth = 0
    if user_id in fish_data:
        for fish_name, count in fish_data[user_id].items():
            if count > 0 and fish_name in FISH_PRICES:
                total_worth += FISH_PRICES[fish_name] * count
    stats += f"Inventory Worth: {total_worth} coins\n"
    
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
    
    # Handle "sell all" command
    if fish_type.lower() == "all":
        if user_id not in fish_data:
            await ctx.send(f"{ctx.author.mention}, you haven't caught any fish yet!")
            return
        
        total_coins = 0
        sold_fish = []
        
        # Sell all fish the user has
        for fish_name, count in fish_data[user_id].items():
            if count > 0 and fish_name in FISH_PRICES:
                fish_value = FISH_PRICES[fish_name] * count
                total_coins += fish_value
                sold_fish.append(f"{count} {fish_name}")
                fish_data[user_id][fish_name] = 0
        
        if total_coins == 0:
            await ctx.send(f"{ctx.author.mention}, you don't have any fish to sell!")
            return
        
        # Update coins
        if user_id not in user_coins:
            user_coins[user_id] = 0
        user_coins[user_id] += total_coins
        
        # Check for biggest sale record
        if total_coins > fishing_records["biggest_sale"]["amount"]:
            fishing_records["biggest_sale"] = {
                "user_id": user_id,
                "amount": total_coins,
                "fish_type": "All Fish",
                "date": time.time()
            }
        
        data["fish_data"] = fish_data
        data["user_coins"] = user_coins
        data["records"] = fishing_records
        save_data(data)
        
        sold_message = f"{ctx.author.mention} sold all fish for {total_coins} coins!\nSold: {', '.join(sold_fish)}"
        await ctx.send(sold_message)
        return
    
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
    sale_amount = FISH_PRICES[full_fish_name] * amount
    
    if user_id not in user_coins:
        user_coins[user_id] = 0
    user_coins[user_id] += sale_amount
    
    # Check for biggest sale record
    if sale_amount > fishing_records["biggest_sale"]["amount"]:
        fishing_records["biggest_sale"] = {
            "user_id": user_id,
            "amount": sale_amount,
            "fish_type": full_fish_name,
            "date": time.time()
        }
    
    data["fish_data"] = fish_data
    data["user_coins"] = user_coins
    data["records"] = fishing_records
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} sold {amount} {full_fish_name} for {sale_amount} coins!")

@bot.command()
async def shop(ctx):
    """Display the fishing shop"""
    shop_message = "🎣 Fishing Shop 🎣\n\n"
    for rod, price in ROD_PRICES.items():
        shop_message += f"{rod} - {price} coins\n"
    shop_message += "\nUse !buyrod rodname to purchase a rod!"
    await ctx.send(shop_message)

@bot.command()
async def buyrod(ctx, *, rod_name: str):
    """Buy a fishing rod from the shop"""
    user_id = str(ctx.author.id)
    
    normalized = normalize_rod_name(rod_name)
    canonical_rod_name = ROD_NAME_LOOKUP.get(normalized)
    if not canonical_rod_name:
        await ctx.send(f"{ctx.author.mention}, invalid rod type! Available rods: {', '.join(ROD_PRICES.keys())}")
        return
    
    user_coins[user_id] = user_coins.get(user_id, 0)
    if user_coins[user_id] < ROD_PRICES[canonical_rod_name]:
        await ctx.send(f"{ctx.author.mention}, you need {ROD_PRICES[canonical_rod_name]} coin(s) to buy {canonical_rod_name}!")
        return
    
    # Update user rod and coins
    user_coins[user_id] -= ROD_PRICES[canonical_rod_name]
    user_rods[user_id] = canonical_rod_name
    
    data["user_coins"] = user_coins
    data["user_rods"] = user_rods
    save_data(data)
    
    await ctx.send(f"{ctx.author.mention} purchased {canonical_rod_name} for {ROD_PRICES[canonical_rod_name]} coins!")

@bot.command()
async def donate(ctx, member: discord.Member, amount: int):
    """Donate coin(s) to another player"""
    user_id = str(ctx.author.id)
    target_id = str(member.id)
    
    # Prevent donating to yourself
    if user_id == target_id:
        await ctx.send(f"{ctx.author.mention}, you can't donate to yourself!")
        return
    
    # Check if user has enough coins
    if user_id not in user_coins or user_coins[user_id] < amount:
        await ctx.send(f"{ctx.author.mention}, you don't have enough coin(s) to donate {amount} coin(s)!")
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
    
    await ctx.send(f"{ctx.author.mention} donated {amount} coin(s) to {member.mention}! 💰")

@bot.command()
async def topfishers(ctx):
    """Show top 10 players by total fish caught"""
    # Calculate total fish for each user
    user_totals = {}
    for user_id, fish_counts in fish_data.items():
        total_fish = sum(fish_counts.values())
        if total_fish > 0:
            user_totals[user_id] = total_fish
    
    if not user_totals:
        await ctx.send("No one has caught any fish yet!")
        return
    
    # Sort by total fish caught (descending)
    sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Create leaderboard message
    leaderboard = "🏆 **Top Fishers Leaderboard** 🏆\n\n"
    
    for i, (user_id, total_fish) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.display_name
        except:
            username = f"User {user_id}"
        
        # Add medal emojis for top 3
        if i == 1:
            rank = "🥇"
        elif i == 2:
            rank = "🥈"
        elif i == 3:
            rank = "🥉"
        else:
            rank = f"{i}."
        
        leaderboard += f"{rank} **{username}** - {total_fish} fish\n"
    
    await ctx.send(leaderboard)

@bot.command()
async def topcoins(ctx):
    """Show top 10 richest players"""
    if not user_coins:
        await ctx.send("No one has any coins yet!")
        return
    
    # Sort by coins (descending)
    sorted_users = sorted(user_coins.items(), key=lambda x: x[1], reverse=True)
    
    # Create leaderboard message
    leaderboard = "💰 **Richest Players Leaderboard** 💰\n\n"
    
    for i, (user_id, coins) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.display_name
        except:
            username = f"User {user_id}"
        
        # Add medal emojis for top 3
        if i == 1:
            rank = "🥇"
        elif i == 2:
            rank = "🥈"
        elif i == 3:
            rank = "🥉"
        else:
            rank = f"{i}."
        
        leaderboard += f"{rank} **{username}** - {coins} coins\n"
    
    await ctx.send(leaderboard)

@bot.command()
async def toprare(ctx):
    """Show top 10 players by rare fish caught (Epic, Legendary, Ultimate)"""
    # Calculate rare fish totals for each user
    user_rare_totals = {}
    rare_fish_types = ["Epic Fish 🐳", "Legendary Fish 🐉", "Ultimate Fish 🦅"]
    
    for user_id, fish_counts in fish_data.items():
        rare_total = sum(fish_counts.get(fish_type, 0) for fish_type in rare_fish_types)
        if rare_total > 0:
            user_rare_totals[user_id] = rare_total
    
    if not user_rare_totals:
        await ctx.send("No one has caught any rare fish yet!")
        return
    
    # Sort by rare fish caught (descending)
    sorted_users = sorted(user_rare_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Create leaderboard message
    leaderboard = "🌟 **Rare Fish Hunters Leaderboard** 🌟\n\n"
    
    for i, (user_id, rare_total) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.display_name
        except:
            username = f"User {user_id}"
        
        # Add medal emojis for top 3
        if i == 1:
            rank = "🥇"
        elif i == 2:
            rank = "🥈"
        elif i == 3:
            rank = "🥉"
        else:
            rank = f"{i}."
        
        leaderboard += f"{rank} **{username}** - {rare_total} rare fish\n"
    
    await ctx.send(leaderboard)

@bot.command()
async def leaderboard(ctx, category: str = "fishers"):
    """Show leaderboards. Categories: fishers, coins, rare"""
    category = category.lower()
    
    if category in ["fishers", "fish", "topfishers"]:
        await topfishers(ctx)
    elif category in ["coins", "money", "topcoins"]:
        await topcoins(ctx)
    elif category in ["rare", "rare_fish", "toprare"]:
        await toprare(ctx)
    else:
        await ctx.send("Available leaderboard categories: `fishers`, `coins`, `rare`\n"
                      "Examples: `!leaderboard fishers`, `!leaderboard coins`, `!leaderboard rare`")

@bot.command()
async def records(ctx):
    """Display all-time fishing records"""
    records_message = "🏆 **All-Time Fishing Records** 🏆\n\n"
    
    # Helper function to format record
    async def format_record(record_name, record_data, value_key="amount"):
        if record_data["user_id"] is None:
            return f"**{record_name}**: No record set yet\n"
        
        try:
            user = await bot.fetch_user(int(record_data["user_id"]))
            username = user.display_name
        except:
            username = f"User {record_data['user_id']}"
        
        value = record_data[value_key]
        date_str = ""
        if record_data["date"]:
            date_str = f" on {time.strftime('%Y-%m-%d', time.localtime(record_data['date']))}"
        
        return f"**{record_name}**: {username} - {value}{date_str}\n"
    
    # Display each record
    records_message += await format_record("Largest Single Catch", fishing_records["largest_catch"])
    records_message += await format_record("Most Common Fish", fishing_records["most_common_fish"])
    records_message += await format_record("Most Rare Fish", fishing_records["most_rare_fish"])
    records_message += await format_record("Most Epic Fish", fishing_records["most_epic_fish"])
    records_message += await format_record("Most Legendary Fish", fishing_records["most_legendary_fish"])
    records_message += await format_record("Most Ultimate Fish", fishing_records["most_ultimate_fish"])
    
    # Special formatting for biggest sale
    if fishing_records["biggest_sale"]["user_id"] is None:
        records_message += "**Biggest Single Sale**: No record set yet\n"
    else:
        try:
            user = await bot.fetch_user(int(fishing_records["biggest_sale"]["user_id"]))
            username = user.display_name
        except:
            username = f"User {fishing_records['biggest_sale']['user_id']}"
        
        fish_type = fishing_records["biggest_sale"]["fish_type"]
        amount = fishing_records["biggest_sale"]["amount"]
        date_str = ""
        if fishing_records["biggest_sale"]["date"]:
            date_str = f" on {time.strftime('%Y-%m-%d', time.localtime(fishing_records['biggest_sale']['date']))}"
        
        records_message += f"**Biggest Single Sale**: {username} - {amount} coins ({fish_type}){date_str}\n"
    
    records_message += await format_record("Longest Fishing Streak", fishing_records["longest_streak"], "days")
    
    await ctx.send(records_message)

@bot.command()
async def setrecord(ctx, record_type: str, member: discord.Member, value: int):
    """Admin command to manually set records"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to set records!")
        return
    
    record_type = record_type.lower()
    user_id = str(member.id)
    current_time = time.time()
    
    # Map record types to their keys
    record_mapping = {
        "largest_catch": "largest_catch",
        "most_common": "most_common_fish",
        "most_rare": "most_rare_fish", 
        "most_epic": "most_epic_fish",
        "most_legendary": "most_legendary_fish",
        "most_ultimate": "most_ultimate_fish",
        "biggest_sale": "biggest_sale",
        "streak": "longest_streak"
    }
    
    if record_type not in record_mapping:
        await ctx.send(f"Invalid record type! Available types: {', '.join(record_mapping.keys())}")
        return
    
    record_key = record_mapping[record_type]
    
    # Set the record
    if record_type == "biggest_sale":
        fishing_records[record_key] = {
            "user_id": user_id,
            "amount": value,
            "fish_type": "Manual Set",
            "date": current_time
        }
    elif record_type == "streak":
        fishing_records[record_key] = {
            "user_id": user_id,
            "days": value,
            "date": current_time
        }
    else:
        fishing_records[record_key] = {
            "user_id": user_id,
            "amount": value,
            "date": current_time
        }
    
    data["records"] = fishing_records
    save_data(data)
    
    await ctx.send(f"Record set! {member.mention} now holds the record for {record_type} with {value}!")

@bot.command()
async def triggerfish(ctx):
    """Admin command to manually trigger a random fish event"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to trigger fish events!")
        return
    
    global random_fish_event_active
    
    # Check if an event is already active
    if random_fish_event_active:
        await ctx.send("A random fish event is already active! Wait for it to end first.")
        return
    
    # Trigger the event
    await ctx.send("🎣 **ADMIN TRIGGERED FISH EVENT!** 🎣\nA random fish event is starting now!")
    await trigger_random_fish_event()

@bot.command()
async def stopfish(ctx):
    """Admin command to stop the current random fish event"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to stop fish events!")
        return
    
    global random_fish_event_active, random_fish_event_message
    
    if not random_fish_event_active:
        await ctx.send("No random fish event is currently active.")
        return
    
    # Stop the event
    random_fish_event_active = False
    random_fish_event_message = None
    
    embed = discord.Embed(
        title="🎣 RANDOM FISH EVENT STOPPED! 🎣",
        description="The fish event has been stopped by an administrator.",
        color=0xff0000
    )
    await ctx.send(embed=embed)

@bot.command()
async def fishstatus(ctx):
    """Check the status of the random fish event"""
    global random_fish_event_active, random_fish_event_start_time
    
    if random_fish_event_active:
        elapsed_time = int(time.time() - random_fish_event_start_time)
        remaining_time = max(0, 1800 - elapsed_time)  # 30 minutes = 1800 seconds
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        
        embed = discord.Embed(
            title="🎣 Random Fish Event Status",
            description="A random fish event is currently **ACTIVE**!",
            color=0x00ff00
        )
        embed.add_field(name="⏰ Time Remaining", value=f"{minutes}m {seconds}s", inline=False)
        embed.add_field(name="🎣 How to Participate", value="Type `net` in this channel!", inline=False)
    else:
        embed = discord.Embed(
            title="🎣 Random Fish Event Status",
            description="No random fish event is currently active.",
            color=0x808080
        )
        embed.add_field(name="🎣 Next Event", value="Random events occur every 2-8 hours automatically.", inline=False)
    
    await ctx.send(embed=embed)

# Replace 'YOUR_TOKEN_HERE' with your bot token
bot.run('YOUR_TOKEN_HERE')
