import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import re
import random
import json
import os
import time
import asyncio
import logging

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("Missing DISCORD_TOKEN in .env")

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Reduce noisy gateway warnings that were causing formatting issues in logging
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

# Channel IDs (replace with your actual channel IDs)
COUNTING_CHANNEL_ID = 1396292969182658732 # Replace with actual counting channel ID
FISHING_CHANNEL_ID = 1399585285494276107  # Replace with actual fishing channel ID 


# File for persistent data storage
DATA_FILE = "bot_data.json"
BACKUP_DIR = "backup"

# Global variables for the random fish event
random_fish_event_active = False
random_fish_event_message = None
random_fish_event_start_time = None
random_fish_event_type = None

EVENT_SCHOOL = "school"
EVENT_COMMON_SWARM = "common_swarm"
EVENT_MIXED_HAUL = "mixed_haul"

FISH_EVENTS = {
    EVENT_SCHOOL: {
        "title": "🎣 RANDOM FISH EVENT! 🎣",
        "description": "A school of fish has appeared! The first person to type **`net`** will catch **2-6 random fish**!",
        "reward": "2-6 random fish (based on your rod)",
        "ended": "The fish have swam away! No one caught them in time.",
        "color": 0x00ff00,
    },
    EVENT_COMMON_SWARM: {
        "title": "🐟 COMMON FISH SWARM! 🐟",
        "description": "A huge swarm of common fish has appeared! The first person to type **`net`** will catch **20 Common Fish**!",
        "reward": "20 Common Fish 🐟",
        "ended": "The common fish swarm has moved on! No one caught them in time.",
        "color": 0x87ceeb,
    },
    EVENT_MIXED_HAUL: {
        "title": "✨ TREASURE SCHOOL! ✨",
        "description": "A mixed school of valuable fish has appeared! The first person to type **`net`** will catch **5 Rare, 5 Epic, and 1 Legendary**!",
        "reward": "5 Rare 🐠, 5 Epic 🐳, 1 Legendary 🐉",
        "ended": "The treasure school has swam away! No one caught them in time.",
        "color": 0xffd700,
    },
}

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
                "last_daily_time": {},
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
        "last_daily_time": {},
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

def create_backup_file():
    """Create a timestamped backup of the current in-memory data dict."""
    timestamp = time.strftime('%m_%d_%Y_%H%M', time.localtime())
    backup_filename = f"bot_data_backup_{timestamp}.json"
    # Ensure backup directory exists
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except Exception as e:
        print(f"Failed to create backup directory '{BACKUP_DIR}': {e}")
    full_path = os.path.join(BACKUP_DIR, backup_filename)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return full_path

def prune_old_backups(keep: int = 7):
    """Keep only the most recent 'keep' backup files."""
    try:
        if not os.path.isdir(BACKUP_DIR):
            return
        files = [f for f in os.listdir(BACKUP_DIR) if re.match(r'^bot_data_backup_\d{2}_\d{2}_\d{4}_\d{4}\.json$', f)]
        files_sorted = sorted(
            files,
            key=lambda x: time.strptime(x.replace('bot_data_backup_', '').replace('.json', ''), '%m_%d_%Y_%H%M'),
            reverse=True
        )
        for old in files_sorted[keep:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except Exception as e:
                print(f"Failed to remove old backup {old}: {e}")
    except Exception as e:
        print(f"Error pruning backups: {e}")

# Periodic backup task (weekly)
@tasks.loop(hours=168)
async def backup_data_task():
    try:
        backup_filename = create_backup_file()
        prune_old_backups(keep=7)
        print(f"Backup created: {backup_filename}")
    except Exception as e:
        print(f"Error creating backup: {e}")

# Initialize data
data = load_data()
current_count = data["counting"]["current_count"]
last_user_id = data["counting"]["last_user_id"]
fish_data = data["fish_data"]
user_coins = data["user_coins"]
user_rods = data["user_rods"]
last_fish_time = data["last_fish_time"]
fishing_records = data["records"]
# Ensure new keys exist if loading from an older data file
if "last_daily_time" not in data:
    data["last_daily_time"] = {}

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
        ("Common Fish 🐟", 0.15),
        ("Rare Fish 🐠", 0.21),
        ("Epic Fish 🐳", 0.30),
        ("Legendary Fish 🐉", 0.25),
        ("Ultimate Fish 🦅", 0.09)
    ],
    "SuperbRod": [
        ("Common Fish 🐟", 0.07),
        ("Rare Fish 🐠", 0.11),
        ("Epic Fish 🐳", 0.21),
        ("Legendary Fish 🐉", 0.46),
        ("Ultimate Fish 🦅", 0.15)
    ],
    "MasterRod": [
        ("Common Fish 🐟", 0.05),
        ("Rare Fish 🐠", 0.09),
        ("Epic Fish 🐳", 0.18),
        ("Legendary Fish 🐉", 0.45),
        ("Ultimate Fish 🦅", 0.23)
    ],
    "MythicRod": [
        ("Common Fish 🐟", 0.03),
        ("Rare Fish 🐠", 0.06),
        ("Epic Fish 🐳", 0.14),
        ("Legendary Fish 🐉", 0.42),
        ("Ultimate Fish 🦅", 0.35)
    ],
    "DivineRod": [
        ("Common Fish 🐟", 0.02),
        ("Rare Fish 🐠", 0.04),
        ("Epic Fish 🐳", 0.10),
        ("Legendary Fish 🐉", 0.39),
        ("Ultimate Fish 🦅", 0.45)
    ]
}

# Shop prices (1k, 5k, 10k, 25k, then the same growth: 50k, 100k, 250k)
ROD_PRICES = {
    "NewRod": 1000,
    "SpecialRod": 5000,
    "UltimateRod": 10000,
    "SuperbRod": 25000,
    "MasterRod": 50000,
    "MythicRod": 100000,
    "DivineRod": 250000
}

DOUBLE_CATCH_CHANCE = {
    "NewRod": 0.02,
    "SpecialRod": 0.04,
    "UltimateRod": 0.07,
    "SuperbRod": 0.10,
    "MasterRod": 0.18,
    "MythicRod": 0.21,
    "DivineRod": 0.25,
}

JACKPOT_CHANCE = {
    "SuperbRod": 0.01,
    "MasterRod": 0.015,
    "MythicRod": 0.02,
    "DivineRod": 0.03,
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
    "superb": "SuperbRod",
    "master": "MasterRod",
    "mythic": "MythicRod",
    "divine": "DivineRod",
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
    # Start background tasks only if not already running (handles reconnects/resumes)
    if not random_fish_event_task.is_running():
        random_fish_event_task.start()
    if not backup_data_task.is_running():
        backup_data_task.start()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

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

def award_event_catches(user_id: str, catches: list):
    """Add event catches to inventory and update records."""
    if user_id not in fish_data:
        fish_data[user_id] = {
            "Common Fish 🐟": 0,
            "Rare Fish 🐠": 0,
            "Epic Fish 🐳": 0,
            "Legendary Fish 🐉": 0,
            "Ultimate Fish 🦅": 0
        }

    current_time = time.time()
    fish_to_record = {
        "Common Fish 🐟": "most_common_fish",
        "Rare Fish 🐠": "most_rare_fish",
        "Epic Fish 🐳": "most_epic_fish",
        "Legendary Fish 🐉": "most_legendary_fish",
        "Ultimate Fish 🦅": "most_ultimate_fish"
    }

    for catch in catches:
        fish_data[user_id][catch] += 1
        current_count = fish_data[user_id][catch]
        record_key = fish_to_record.get(catch)
        if record_key and record_key in fishing_records and current_count > fishing_records[record_key]["amount"]:
            fishing_records[record_key] = {
                "user_id": user_id,
                "amount": current_count,
                "date": current_time
            }

    num_fish = len(catches)
    if num_fish > fishing_records["largest_catch"]["amount"]:
        fishing_records["largest_catch"] = {
            "user_id": user_id,
            "amount": num_fish,
            "date": current_time
        }

    data["fish_data"] = fish_data
    data["records"] = fishing_records
    save_data(data)
    return num_fish

async def handle_random_fish_catch(message):
    """Handle the random fish catch when someone says 'net'"""
    global random_fish_event_active, random_fish_event_message, random_fish_event_type

    user_id = str(message.author.id)
    user_rod = user_rods.get(user_id, "BasicRod")
    event_type = random_fish_event_type or EVENT_SCHOOL

    if event_type == EVENT_COMMON_SWARM:
        catches = ["Common Fish 🐟"] * 20
        catch_message = (
            f"🐟 **COMMON FISH SWARM!** 🐟\n{message.author.mention} scooped up **20 Common Fish**!"
        )
    elif event_type == EVENT_MIXED_HAUL:
        catches = (["Rare Fish 🐠"] * 5) + (["Epic Fish 🐳"] * 5) + ["Legendary Fish 🐉"]
        catch_message = (
            f"✨ **TREASURE SCHOOL!** ✨\n{message.author.mention} caught **5 Rare, 5 Epic, and 1 Legendary**!"
        )
    else:
        num_fish = random.randint(2, 6)
        available_fish = []
        fish_weights = []
        for fish_type, weight in RODS[user_rod]:
            available_fish.append(fish_type)
            fish_weights.append(weight)
        catches = random.choices(available_fish, weights=fish_weights, k=num_fish)
        catch_list = ", ".join(catches)
        catch_message = (
            f"🎣 **RANDOM FISH EVENT!** 🎣\n{message.author.mention} caught **{num_fish} fish** "
            f"with their {user_rod}!\n\n**Caught:** {catch_list}"
        )

    award_event_catches(user_id, catches)
    random_fish_event_active = False
    random_fish_event_message = None
    random_fish_event_type = None
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

async def trigger_random_fish_event(event_type: str = None):
    """Trigger a random fish event"""
    global random_fish_event_active, random_fish_event_message, random_fish_event_start_time, random_fish_event_type

    try:
        channel = bot.get_channel(FISHING_CHANNEL_ID)
        if not channel:
            return

        if event_type not in FISH_EVENTS:
            event_type = random.choice(list(FISH_EVENTS.keys()))

        event = FISH_EVENTS[event_type]
        random_fish_event_active = True
        random_fish_event_start_time = time.time()
        random_fish_event_type = event_type

        embed = discord.Embed(
            title=event["title"],
            description=event["description"],
            color=event["color"]
        )
        embed.add_field(name="⏰ Time Limit", value="This event will last for 30 minutes!", inline=False)
        embed.add_field(name="🎣 How to Participate", value="Simply type `net` in this channel!", inline=False)
        embed.add_field(name="🎁 Reward", value=event["reward"], inline=False)

        random_fish_event_message = await channel.send(embed=embed)

        await asyncio.sleep(1800)  # 30 minutes

        if random_fish_event_active:
            random_fish_event_active = False
            random_fish_event_type = None
            embed = discord.Embed(
                title="🎣 FISH EVENT ENDED! 🎣",
                description=event["ended"],
                color=0xff0000
            )
            await channel.send(embed=embed)
            random_fish_event_message = None

    except Exception as e:
        print(f"Error in random fish event: {e}")
        random_fish_event_active = False
        random_fish_event_message = None
        random_fish_event_type = None

@bot.hybrid_command()
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

@bot.hybrid_command(name="help", aliases=["commands"])
async def help_commands(ctx):
    """List all commands."""
    commands_list = [
        "! or /help - Show this command list",
        "! or /menu - Open the fishing button menu",
        "! or /fish - Catch fish (fishing channel only)",
        "! or /fishstats [@user] - Show fishing stats",
        "! or /sellfish <type> <amount> - Sell specific fish",
        "! or /sell <type|all> <amount> - Sell fish (or all)",
        "! or /shop - Show rod shop",
        "! or /buyrod <rod name> - Buy a rod",
        "! or /donate @user <amount> - Donate coins",
        "! or /topfishers - Top fishers leaderboard",
        "! or /topcoins - Richest players leaderboard",
        "! or /toprare - Rare fish leaderboard",
        "! or /leaderboard <fishers|coins|rare> - Category leaderboard",
        "! or /records - Show all-time fishing records",
        "! or /daily - Claim daily coin reward",
        "! or /fishstatus - Check random fish event status",
    ]
    await ctx.send("**Available Commands:**\n" + "\n".join(commands_list))

@bot.hybrid_command()
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

@bot.hybrid_command()
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
    double_catch = random.random() < DOUBLE_CATCH_CHANCE.get(user_rod, 0)
    
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
        if random.random() < JACKPOT_CHANCE.get(user_rod, 0):
            catches = [fish[0] for fish in fish_types]
            catch_message = f"{ctx.author.mention} went fishing with {user_rod} and hit the JACKPOT! 🎉 Caught ALL fish types: {', '.join(catches)}"
        else:
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
async def shop(ctx):
    """Display the fishing shop"""
    shop_message = "🎣 Fishing Shop 🎣\n\n"
    for rod, price in ROD_PRICES.items():
        shop_message += f"{rod} - {price} coins\n"
    shop_message += "\nUse !buyrod rodname to purchase a rod!"
    await ctx.send(shop_message)

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
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

@bot.hybrid_command()
async def daily(ctx):
    """Claim a daily coin reward (25-100 coins), once every 24 hours."""
    user_id = str(ctx.author.id)

    # Initialize coins dict entry if missing
    if user_id not in user_coins:
        user_coins[user_id] = 0

    # Ensure last_daily_time exists in data
    last_daily_time = data.get("last_daily_time", {})
    data["last_daily_time"] = last_daily_time

    now = time.time()
    last_claim = last_daily_time.get(user_id)

    if last_claim is not None:
        elapsed = now - last_claim
        seconds_in_day = 24 * 60 * 60
        if elapsed < seconds_in_day:
            remaining = int(seconds_in_day - elapsed)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            await ctx.send(f"{ctx.author.mention}, you have already claimed your daily reward. Try again in {hours}h {minutes}m {seconds}s.")
            return

    # Grant reward
    reward = random.randint(25, 100)
    user_coins[user_id] += reward
    last_daily_time[user_id] = now

    # Persist
    data["user_coins"] = user_coins
    data["last_daily_time"] = last_daily_time
    save_data(data)

    await ctx.send(f"{ctx.author.mention} claimed their daily reward: {reward} coins! 💰")

@bot.hybrid_command()
@app_commands.describe(event_type="school, common, or mixed. Leave empty for a random event.")
async def triggerfish(ctx, event_type: str = None):
    """Admin command to manually trigger a random fish event"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to trigger fish events!")
        return
    
    global random_fish_event_active
    
    # Check if an event is already active
    if random_fish_event_active:
        await ctx.send("A random fish event is already active! Wait for it to end first.")
        return

    event_map = {
        "school": EVENT_SCHOOL,
        "random": EVENT_SCHOOL,
        "common": EVENT_COMMON_SWARM,
        "swarm": EVENT_COMMON_SWARM,
        "mixed": EVENT_MIXED_HAUL,
        "treasure": EVENT_MIXED_HAUL,
        "haul": EVENT_MIXED_HAUL,
    }
    chosen = None
    if event_type:
        chosen = event_map.get(event_type.lower().strip())
        if chosen is None:
            await ctx.send("Invalid event type. Use `school`, `common`, or `mixed`.")
            return
    
    # Trigger the event
    await ctx.send("🎣 **ADMIN TRIGGERED FISH EVENT!** 🎣\nA fish event is starting now!")
    await trigger_random_fish_event(chosen)

@bot.hybrid_command()
async def stopfish(ctx):
    """Admin command to stop the current random fish event"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to stop fish events!")
        return
    
    global random_fish_event_active, random_fish_event_message, random_fish_event_type
    
    if not random_fish_event_active:
        await ctx.send("No random fish event is currently active.")
        return
    
    # Stop the event
    random_fish_event_active = False
    random_fish_event_message = None
    random_fish_event_type = None
    
    embed = discord.Embed(
        title="🎣 RANDOM FISH EVENT STOPPED! 🎣",
        description="The fish event has been stopped by an administrator.",
        color=0xff0000
    )
    await ctx.send(embed=embed)

@bot.hybrid_command()
async def fishstatus(ctx):
    """Check the status of the random fish event"""
    global random_fish_event_active, random_fish_event_start_time, random_fish_event_type
    
    if random_fish_event_active:
        elapsed_time = int(time.time() - random_fish_event_start_time)
        remaining_time = max(0, 1800 - elapsed_time)  # 30 minutes = 1800 seconds
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        event = FISH_EVENTS.get(random_fish_event_type, FISH_EVENTS[EVENT_SCHOOL])
        
        embed = discord.Embed(
            title="🎣 Random Fish Event Status",
            description=f"**{event['title']}** is currently **ACTIVE**!",
            color=event["color"]
        )
        embed.add_field(name="🎁 Reward", value=event["reward"], inline=False)
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

@bot.hybrid_command()
async def backup(ctx):
    """Admin command to create a manual backup of the bot data"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need administrator permissions to create a backup!")
        return
    try:
        backup_filename = create_backup_file()
        prune_old_backups(keep=7)
        await ctx.send(f"Backup created: `{backup_filename}`")
    except Exception as e:
        await ctx.send(f"Failed to create backup: {e}")


class MenuContext:
    """Lets existing commands reply to a button or dropdown interaction."""

    def __init__(self, interaction, channel):
        self.interaction = interaction
        self.author = interaction.user
        self.channel = channel
        self.guild = interaction.guild

    async def send(self, content=None, *, embed=None):
        kwargs = {}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        if not kwargs:
            kwargs["content"] = "Done."
        if self.interaction.response.is_done():
            return await self.interaction.followup.send(**kwargs)
        return await self.interaction.response.send_message(**kwargs)


_menu_locks = {}


def _menu_lock(user_id):
    lock = _menu_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _menu_locks[user_id] = lock
    return lock


def _is_admin(user):
    return isinstance(user, discord.Member) and user.guild_permissions.administrator


class ConfirmView(discord.ui.View):
    def __init__(self, owner_id, action):
        super().__init__(timeout=30)
        self.owner_id = owner_id
        self.action = action

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Confirmed.", view=self)
        channel = interaction.channel
        if channel is None:
            await interaction.followup.send("I could not find this channel.", ephemeral=True)
            self.stop()
            return
        ctx = MenuContext(interaction, channel)
        # The confirmation already used the interaction response, so post the
        # command result in the channel instead of as a hidden followup.
        async def public_send(content=None, *, embed=None):
            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if embed is not None:
                kwargs["embed"] = embed
            return await channel.send(**kwargs)
        ctx.send = public_send
        try:
            async with _menu_lock(interaction.user.id):
                await self.action(ctx)
        except Exception as e:
            print(f"Menu confirmation failed: {e}")
            await interaction.followup.send(f"That action failed: {e}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Cancelled.", view=self)
        self.stop()


async def _ask_confirm(interaction, prompt, action):
    view = ConfirmView(interaction.user.id, action)
    await interaction.response.send_message(prompt, view=view, ephemeral=True)


class AdminMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    async def interaction_check(self, interaction):
        if not _is_admin(interaction.user):
            await interaction.response.send_message(
                "You need administrator permissions to use this menu.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Reset Count", style=discord.ButtonStyle.danger, row=0)
    async def reset_count(self, interaction, button):
        await _ask_confirm(
            interaction,
            "Reset the counting channel to 0?",
            resetcount.callback,
        )

    @discord.ui.button(label="Stop Event", style=discord.ButtonStyle.danger, row=0)
    async def stop_event(self, interaction, button):
        await _ask_confirm(
            interaction,
            "Stop the active fish event?",
            stopfish.callback,
        )

    @discord.ui.button(label="Backup", style=discord.ButtonStyle.secondary, row=0)
    async def backup_now(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        ctx = MenuContext(interaction, interaction.channel)
        try:
            async with _menu_lock(interaction.user.id):
                await backup.callback(ctx)
        except Exception as e:
            print(f"Menu backup failed: {e}")
            await interaction.followup.send(f"That action failed: {e}", ephemeral=True)

    @discord.ui.select(
        placeholder="Start a fish event",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="School", value="school", description="2-6 fish based on the catcher's rod"),
            discord.SelectOption(label="Common swarm", value="common", description="20 Common Fish"),
            discord.SelectOption(label="Treasure school", value="mixed", description="5 Rare, 5 Epic, and 1 Legendary"),
        ],
        row=1,
    )
    async def start_event(self, interaction, select):
        choice = select.values[0]
        event_ids = {
            "school": EVENT_SCHOOL,
            "common": EVENT_COMMON_SWARM,
            "mixed": EVENT_MIXED_HAUL,
        }
        event_id = event_ids.get(choice)
        if event_id is None:
            await interaction.response.send_message("Unknown event.", ephemeral=True)
            return

        async def launch(ctx):
            global random_fish_event_active
            if random_fish_event_active:
                await ctx.send("A random fish event is already active! Wait for it to end first.")
                return
            await ctx.send("🎣 **ADMIN TRIGGERED FISH EVENT!** 🎣\nA fish event is starting now!")
            asyncio.create_task(trigger_random_fish_event(event_id))

        labels = {"school": "school", "common": "common swarm", "mixed": "treasure school"}
        await _ask_confirm(interaction, f"Start a {labels[choice]} event now?", launch)


class FishingMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=900)
        self.message = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    async def _run(self, interaction, command, *args, **kwargs):
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message("Use this menu in a server channel.", ephemeral=True)
            return
        await interaction.response.defer()
        ctx = MenuContext(interaction, interaction.channel)
        try:
            async with _menu_lock(interaction.user.id):
                await command.callback(ctx, *args, **kwargs)
        except Exception as e:
            print(f"Menu action failed: {e}")
            await interaction.followup.send(f"That action failed: {e}")
        try:
            if interaction.message is not None:
                await interaction.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Fish", style=discord.ButtonStyle.success, row=0)
    async def fish_button(self, interaction, button):
        await self._run(interaction, fish)

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.primary, row=0)
    async def stats_button(self, interaction, button):
        await self._run(interaction, fishstats)

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.primary, row=0)
    async def daily_button(self, interaction, button):
        await self._run(interaction, daily)

    @discord.ui.button(label="Sell All", style=discord.ButtonStyle.secondary, row=0)
    async def sell_all_button(self, interaction, button):
        await self._run(interaction, sell, "all")

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.secondary, row=0)
    async def shop_button(self, interaction, button):
        await self._run(interaction, shop)

    @discord.ui.button(label="Records", style=discord.ButtonStyle.primary, row=1)
    async def records_button(self, interaction, button):
        await self._run(interaction, records)

    @discord.ui.button(label="Event Status", style=discord.ButtonStyle.primary, row=1)
    async def status_button(self, interaction, button):
        await self._run(interaction, fishstatus)

    @discord.ui.button(label="Help", style=discord.ButtonStyle.secondary, row=1)
    async def help_button(self, interaction, button):
        await self._run(interaction, help_commands)

    @discord.ui.button(label="Admin", style=discord.ButtonStyle.danger, row=1)
    async def admin_button(self, interaction, button):
        if not _is_admin(interaction.user):
            await interaction.response.send_message(
                "You need administrator permissions to use this menu.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="Admin menu",
            description="These actions are only visible to you. Reset, stop, and starting an event ask for confirmation.",
            color=0xff5555,
        )
        await interaction.response.send_message(embed=embed, view=AdminMenu(), ephemeral=True)

    @discord.ui.select(
        placeholder="Buy a rod",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=rod, value=rod, description=f"{price:,} coins")
            for rod, price in ROD_PRICES.items()
        ],
        row=2,
    )
    async def buy_rod(self, interaction, select):
        await self._run(interaction, buyrod, rod_name=select.values[0])

    @discord.ui.select(
        placeholder="Leaderboard",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Top fishers", value="fishers"),
            discord.SelectOption(label="Richest players", value="coins"),
            discord.SelectOption(label="Rare fish", value="rare"),
        ],
        row=3,
    )
    async def leaderboard_select(self, interaction, select):
        await self._run(interaction, leaderboard, select.values[0])


def build_menu_embed():
    embed = discord.Embed(
        title="Fishing menu",
        description=(
            "Use the buttons and dropdowns below. Each action uses the person who clicked, "
            "not the person who opened the menu.\n\n"
            "Fish still only works in the fishing channel. Donate, selling a set amount, "
            "and setting the count still need a typed command because they need extra details."
        ),
        color=0x3498db,
    )
    embed.add_field(
        name="Still typed",
        value="`!donate`, `!sell common 5`, `!setcount`, `!setrecord`, and `net` during an event",
        inline=False,
    )
    embed.set_footer(text="This menu turns off after 15 minutes. Run !menu or /menu again.")
    return embed


@bot.hybrid_command(name="menu", aliases=["gui"])
async def menu(ctx):
    """Open a Discord button menu for the fishing commands."""
    if ctx.guild is None:
        await ctx.send("Use this menu in a server channel.")
        return
    view = FishingMenu()
    message = await ctx.send(embed=build_menu_embed(), view=view)
    view.message = message

bot.run(TOKEN)
