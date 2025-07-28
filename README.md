# Discord Counting Bot

A Discord bot that manages a counting game in a specified channel. Users take turns posting the next number in sequence (e.g., 1, 2, 3, ...), and the bot ensures rules are followed, accepting both plain numbers and simple math equations (e.g., `2+2` for 4). If a user posts an incorrect number or counts twice in a row, the count resets to 0.

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
   - In the Developer Portal, go to **OAuth2** > **URL Generator**.
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

## Example
- User A: `1` → ✅ (count = 1)
- User B: `2` → ✅ (count = 2)
- User A: `1+2` → ✅ (count = 3, evaluates to 3)
- User A: `4` → ❌ (double count, resets to 0, message: "you can't count twice in a row! Count reset to 0.")
- User B: `2` → ❌ (wrong number, resets to 0, message: "wrong number! The next number should be 1. Count reset to 0.")
- User B: `1` → ✅ (count = 1)

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

## IMPORTANT SECURITY INFO
- **Keep your bot token private**. If exposed, reset it in the Developer Portal and update the script **ASAP**. 
- The bot uses `eval()` for math expressions with restricted input (digits, `+`, `-`, `*`, `/`, parentheses). Avoid modifying the code to allow unsafe inputs.

## Contributing
Feel free to fork this project, add features (e.g., high score tracking, leaderboard), and submit pull requests. Report issues or suggestions via the issues tab.
https://github.com/GartB/Discord-Counting-Py-Bot/issues

## License
This project is unlicensed and provided as-is for personal use. Use at your own risk.
