import discord
from discord.ext import commands
import re

# Initialize bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Channel ID for counting (replace with your channel ID)
COUNTING_CHANNEL_ID = Channel_For_Counting_ID_Here  # Replace with actual channel ID
current_count = 0
last_user_id = None

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
            await message.add_reaction('✅')
        else:
            await message.add_reaction('❌')
            current_count = 0
            last_user_id = None
            await message.channel.send(f"{message.author.mention}, wrong number! The next number should be {current_count + 1}. Count reset to 0.")

@bot.command()
async def setcount(ctx, number: int):
    """Admin command to set the current count"""
    if ctx.author.guild_permissions.administrator:
        global current_count, last_user_id
        current_count = number
        last_user_id = None
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
        await ctx.send("Count has been reset to 0")
    else:
        await ctx.send("You need administrator permissions to use this command!")

# Replace 'YOUR_TOKEN_HERE' with your bot token. Do not remove the ''s >:/ or else
bot.run('YOUR_TOKEN_HERE')
