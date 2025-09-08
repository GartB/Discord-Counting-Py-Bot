<img width="102" height="102" alt="Counting Bot Icon" src="https://github.com/user-attachments/assets/83254584-eb72-41b7-a486-2fca19fbf07d" /> 

# Discord Counting+ Bot 

A Discord bot that manages a counting game in a specified channel. Users take turns posting the next number in sequence (e.g., 1, 2, 3, ...), and the bot ensures rules are followed, accepting both plain numbers and simple math equations (e.g., `2+2` for 4). If a user posts an incorrect number or counts twice in a row, the count resets to 0. It also includes a fishing mechanic with various commands and random fish events.

## Features
- Monitors a designated channel for counting.
- Accepts plain integers (e.g., `4`) or math expressions (e.g., `2+2`, `3*5`) that evaluate to the correct number.
- Reacts with ✅ for correct counts and ❌ for incorrect ones.
- Resets the count to 0 if a user:
  - Posts the wrong number (e.g., `5` when expecting `4`).
  - Counts twice in a row.
- Ignores non-numeric messages or invalid equations.
- Admin commands:
  - `!setcount <number>`: Sets the current count (admin only).
  - `!resetcount`: Resets the count to 0 (admin only).
- Fishing mechanic with multiple commands and random fish events.

## Requirements
- Python 3.8 or higher
- `discord.py` library (`pip install discord.py`)
- A Discord bot token
- A Discord server where you have **Manage Server** permissions

## Setup Instructions

1. **Install Python**:
   - Ensure Python 3.8+ is installed. Download from [python.org](https://www.python.org/downloads/) if needed.
   - Verify with: `python --version` or `py --version`.

2. **Install discord.py**:
   - Run the following command in your terminal or command prompt:
     ```bash
     pip install discord.py
     ```
   - If using a specific Python version, use: `py -3 -m pip install discord.py`.

3. **Create a Discord Bot**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new application, add a bot, and copy the bot token.
   - In the **Bot** tab, enable the **Message Content Intent** under **Privileged Gateway Intents**.

4. **Invite the Bot to Your Server**:
   - In the Developer ⟟ Developer Portal, go to **OAuth2** > **URL Generator**.
   - Select the `bot` scope and the following permissions:
     - View Channels
     - Send Messages
     - Add Reactions
   - Copy the generated URL, open it in a browser, and invite the bot to your server.

5. **Configure the Bot**:
   - Open `counting_bot_with_math.py` in a text editor.
   - Replace `YOUR_TOKEN_HERE` with your bot token (without quotes).
   - Replace `YOUR_CHANNEL_ID_HERE` with the ID of the counting channel:
     - Enable Developer Mode in Discord (User Settings > Appearance > Developer Mode).
     - Right-click the channel and select **Copy ID**.

6. **Run the Bot**:
   - Save the script in your project directory (e.g., `C:\Users\YourNameHere\Desktop\counting`).
   - Open a terminal or command prompt, navigate to the directory, and run:
     ```bash
     cd C:\Users\YourNameHere\Desktop\counting
     py counting_bot_with_math.py
     ```
   - The bot should log in and display: `Bot is ready! Logged in as <BotName>`.

## Usage
- **Counting**:
  - In the designated channel, users take turns posting the next number (e.g., `1`, `2`, `3`, ...).
  - Math expressions like `2+2` or `3*5` are accepted if they evaluate to the correct number.
  - Correct counts get a ✅ reaction; incorrect counts or rule violations (e.g., same user counting twice) get a ❌ reaction and reset the count to 0.
- **Admin Commands**:
  - `!setcount <number>`: Sets the current count to `<number>` (requires administrator permissions).
  - `!resetcount`: Resets the count to 0 (requires administrator permissions).
- **Rules**:
  - The next number must be one more than the current count (e.g., if current is 3, next is 4).
  - The same user cannot count twice in a row.
  - Non-numeric messages or invalid equations are ignored.
  - Mistakes (wrong number or double counting) reset the count to 0.

## Fishing Commands
- `!fish`: Cast your rod and catch a fish.
- `!sell <type|all> [amount]`: Shorthand for selling fish; supports selling all.  
  Examples: `!sell rare 3`, `!sell all`
- `!shop`: Show available rods and prices.  
  Example: `!shop`
- `!buyrod <rodname>`: Buy a rod. Rods: NewRod, SpecialRod, UltimateRod. Short names allowed: new, special, ultimate.  
  Examples: `!buyrod NewRod`, `!buyrod special`, `!buyrod ultimate`
- `!fishstats [@user]`: Show your (or mentioned user’s) stats, including inventory worth.  
  Examples: `!fishstats`, `!fishstats @User`
- `!topfishers`: Top 10 by total fish caught.  
  Example: `!topfishers`
- `!topcoins`: Top 10 by coins.  
  Example: `!topcoins`
- `!toprare`: Top 10 by rare fish (Epic, Legendary, Ultimate).  
  Example: `!toprare`
- `!leaderboard <category>`: Leaderboards; categories: fishers, coins, rare.  
  Examples: `!leaderboard fishers`, `!leaderboard coins`, `!leaderboard rare`
- `!records`: Show all-time fishing records (largest catch, most of each type, biggest sale, streak).  
  Example: `!records`
- **Admin only**:
  - `!setrecord <type> @user <value>`: Set a record manually. Types: largest_catch, most_common, most_rare, most_epic, most_legendary, most_ultimate, biggest_sale, streak.  
    Examples: `!setrecord largest_catch @User 5`, `!setrecord biggest_sale @User 1200`, `!setrecord streak @User 7`
  - `!triggerfish`: Manually trigger a random fish event.  
    Example: `!triggerfish`
  - `!stopfish`: Stop the current random fish event.  
    Example: `!stopfish`
- **Event status**:
  - `!fishstatus`: Check if a random fish event is active and time remaining.  
    Example: `!fishstatus`

## Random Fish Events
- Events occur randomly. By default: checked every hour with a 15% chance to start.
- Expected frequency: about once every 6–7 hours on average (random, so can vary).
- Duration: each event lasts 30 minutes.
- Admins can start one anytime with `!triggerfish`.
- To change frequency: adjust the 0.15 value in the hourly check on line 312.
- **Participation**: Type `net` in the fishing channel during an active event to catch 2–6 fish.

## Fish Selling & Donation Commands
**Fish Selling Commands**: 
- `!sellfish <fish_type> <amount>`
- `!sell all`

### Available Fish Types:
You can sell fish using multiple formats - the bot is smart enough to understand different ways to type the fish names:
| Fish Type | Command Examples |
|-----------|------------------|
| Common Fish | `!sellfish common 5`<br>`!sellfish "Common Fish 🐟" 5` |
| Rare Fish | `!sellfish rare 3`<br>`!sellfish "Rare Fish 🐠" 3` |
| Epic Fish | `!sellfish epic 2`<br>`!sellfish "Epic Fish 🐳" 2` |
| Legendary Fish | `!sellfish legendary 1`<br>`!sellfish "Legendary Fish 🐉" 1` |
| Ultimate Fish | `!sellfish ultimate 1`<br>`!sellfish "Ultimate Fish 🦅" 1` |
| all | `!sell all` <br> `Sells all owned fish` |

### Fish Selling Prices:
- 🐟 Common Fish: 10 coins each
- 🐠 Rare Fish: 25 coins each
- 🐳 Epic Fish: 50 coins each
- 🐉 Legendary Fish: 100 coins each
- 🦅 Ultimate Fish: 500 coins each

### Examples:
- `!sellfish common 10` → Sells 10 Common Fish for 100 coins
- `!sellfish rare 5` → Sells 5 Rare Fish for 125 coins
- `!sellfish epic 2` → Sells 2 Epic Fish for 100 coins
- `!sellfish legendary 1` → Sells 1 Legendary Fish for 100 coins

## Donation Command: `!donate`
### Usage:
- `!donate @user <amount>`

### Features:
- ✅ Transfer coins between players
- ❌ Cannot donate to yourself
- Validates you have enough coins
- Shows confirmation message

### Examples:
- `!donate @PlayerName 100` → Donates 100 coins to PlayerName
- `!donate @Friend 500` → Donates 500 coins to Friend
- `!donate @NewPlayer 50` → Donates 50 coins to NewPlayer

### Success Message:
- `@YourName donated 100 coins to @PlayerName! 💰`

### Error Messages:
- `You can't donate to yourself!` - When trying to donate to yourself
- `You don't have enough coins to donate 1000 coins!` - When you don't have enough coins
- `Please specify a valid amount to donate!` - When amount is 0 or negative

## IMPORTANT SECURITY INFO
- **Keep your bot token private**. If exposed, reset it in the Developer Portal and update the script **ASAP**. 
- The bot uses `eval()` for math expressions with restricted input (digits, `+`, `-`, `*`, `/`, parentheses). Avoid modifying the code to allow unsafe inputs.

## Troubleshooting
- **Bot not responding**:
  - Verify the bot token is correct and hasn’t been reset.
  - Ensure the **Message Content Intent** is enabled in the Developer Portal.
  - Check that the bot has permissions to view channels, send messages, and add reactions in the counting channel.
  - Confirm the `COUNTING_CHANNEL_ID` matches the correct channel ID.
- **ModuleNotFoundError: No module named 'discord'**:
  - Install `discord.py` using `pip install discord.py`.
- **PrivilegedIntentsRequired error**:
  - Enable the **Message Content Intent** in the Developer Portal.
- **Other errors**:
  - Check the terminal for error messages and share them for assistance.

## Contributing
Feel free to fork this project, add features (e.g., high score tracking, leaderboard), and submit pull requests. Report issues or suggestions via the issues tab.
https://github.com/GartB/Discord-Counting-Py-Bot/issues

## License
This project is unlicensed and provided as-is for personal use. Use at your own risk.
