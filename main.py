import discord
from discord.ext import commands
import json
import random
import string
import time
import re  # Import regular expressions module

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Required to access message contents

# Create the bot with a specific prefix and intents
bot = commands.Bot(command_prefix='.', intents=intents)

# Files to store keys, user data, cooldown data, and used keys
KEYS_FILE = 'keys.json'
USERS_FILE = 'users.json'
HWIDS_FILE = 'hwids.json'
COOLDOWNS_FILE = 'cooldowns.json'
USED_KEYS_FILE = 'usedkeys.json'

# Role IDs
BUYER_ROLE_ID = 1272776413908308041  # Replace with your actual Buyer role ID
ADMIN_ROLE_ID = 1272804155433422931  # Role ID that can reset cooldowns

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_json(file_path, data):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def generate_keys(num_keys):
    """Generate a dictionary of keys with a given number of keys."""
    keys = {}
    for _ in range(num_keys):
        key = ''.join(random.choices(string.digits, k=11))
        keys[key] = "Key not redeemed yet"
    return keys

def generate_hwid(user_id):
    """Generate a unique HWID for a user in the format @<HWID>."""
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"@{user_id}-{random_suffix}"

def redeem_key_without_hwid(key, user_id):
    """Redeem a key for a user but without storing the HWID initially."""
    keys = load_json(KEYS_FILE)
    users = load_json(USERS_FILE)
    used_keys = load_json(USED_KEYS_FILE)

    if key in keys:
        if keys[key] == "Key not redeemed yet":
            # Assign the key to the user but do not store HWID yet
            keys[key] = {
                "redeemed_by": f"@{user_id}",
                "hwid": None  # HWID will be added later
            }
            users[user_id] = key

            # Add the key to used keys
            used_keys.append(key)
            save_json(USED_KEYS_FILE, used_keys)

            # Save updated data
            save_json(KEYS_FILE, keys)
            save_json(USERS_FILE, users)

            return True
        else:
            return False  # Key already redeemed
    return False  # Key does not exist

def update_key_hwid_after_confirmation(key, hwid):
    """Update the HWID for a redeemed key after confirmation by user 1273044266347663395."""
    keys = load_json(KEYS_FILE)

    if key in keys:
        if isinstance(keys[key], dict):
            current_hwid = keys[key].get('hwid')
            if current_hwid is None:  # HWID only updated if not already set
                keys[key]['hwid'] = hwid
                save_json(KEYS_FILE, keys)
                return True
    return False

def is_buyer(ctx):
    """Check if the user has the 'Buyer' role."""
    role = discord.utils.get(ctx.guild.roles, id=BUYER_ROLE_ID)
    return role in ctx.author.roles

def is_admin(ctx):
    """Check if the user has the admin role."""
    role = discord.utils.get(ctx.guild.roles, id=ADMIN_ROLE_ID)
    return role in ctx.author.roles

def buyer_required():
    """Decorator to require the 'Buyer' role."""
    def predicate(ctx):
        return is_buyer(ctx)
    return commands.check(predicate)

def admin_required():
    """Decorator to require the admin role."""
    def predicate(ctx):
        return is_admin(ctx)
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')

@bot.event
async def on_message(message):
    # Check if the message author is the user with the specific ID
    if str(message.author.id) == '1273044266347663395':
        # Respond with "Understood, copied"
        await message.channel.send("Understood, copied")

        # Define regex patterns to match the details
        user_pattern = re.compile(r'User:\s*(\S+)')
        client_id_pattern = re.compile(r'Client ID:\s*([\w-]+)')
        script_key_pattern = re.compile(r'Script Key:\s*(\S+)')

        # Find matches in the message content
        user_match = user_pattern.search(message.content)
        client_id_match = client_id_pattern.search(message.content)
        script_key_match = script_key_pattern.search(message.content)

        # Extract data if matches are found
        if user_match and client_id_match and script_key_match:
            user = user_match.group(1)
            client_id = client_id_match.group(1)
            script_key = script_key_match.group(1)

            # Check if the key is already redeemed and hwid needs to be added
            keys = load_json(KEYS_FILE)
            key_data = keys.get(script_key)

            if key_data and key_data.get("hwid") is None:
                # Add HWID to the key after confirmation
                if update_key_hwid_after_confirmation(script_key, client_id):
                    await message.channel.send(f"HWID for key {script_key} has been updated.")
                else:
                    await message.channel.send(f"Key {script_key} already has a HWID or is not valid.")

    # Process other commands
    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    """Responds with a greeting."""
    await ctx.send('Hello!')

@bot.command()
@buyer_required()
async def clear(ctx, amount: int):
    """Deletes a specified number of messages."""
    if amount < 1 or amount > 100:
        await ctx.send('Please provide a number between 1 and 100.')
        return

    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f'Deleted: {len(deleted)} messages.', delete_after=5)

@bot.command()
@buyer_required()
async def hwid(ctx):
    """Returns a unique HWID for the user."""
    user_id = str(ctx.author.id)
    user_hwids = load_json(HWIDS_FILE)

    # Check if the user already has an HWID
    if user_id not in user_hwids:
        # Generate and store a new HWID for the user
        hwid = generate_hwid(user_id)
        user_hwids[user_id] = hwid
        save_json(HWIDS_FILE, user_hwids)
    else:
        # Retrieve the existing HWID
        hwid = user_hwids[user_id]

    await ctx.send(f'Your HWID is: {hwid}')

@bot.command()
@buyer_required()
async def resethwid(ctx):
    """Resets the HWID for the user."""
    user_id = str(ctx.author.id)
    user_hwids = load_json(HWIDS_FILE)
    cooldowns = load_json(COOLDOWNS_FILE)

    current_time = time.time()

    if user_id in cooldowns:
        last_used_time = cooldowns[user_id]
        elapsed_time = current_time - last_used_time
        cooldown_period = 86400  # 1 day in seconds

        if elapsed_time < cooldown_period:
            remaining_time = cooldown_period - elapsed_time
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            cooldown_message = (
                f"{ctx.author.mention}, you need to wait {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds "
                "before using this command again."
            )
            await ctx.send(cooldown_message)
            return

    # Update cooldown timestamp
    cooldowns[user_id] = current_time
    save_json(COOLDOWNS_FILE, cooldowns)

    # Reset HWID in the keys and user data
    keys = load_json(KEYS_FILE)
    if user_id in keys:
        key = keys[user_id]
        if isinstance(key, dict):
            key['hwid'] = None  # Remove HWID for the key

    # Generate and store a new HWID for the user
    new_hwid = generate_hwid(user_id)
    user_hwids[user_id] = new_hwid
    save_json(HWIDS_FILE, user_hwids)

    await ctx.send(f'Your HWID has been reset. New HWID is: {new_hwid}')

@bot.command()
@admin_required()
async def resetcooldown(ctx, user: discord.Member):
    """Allows an admin to reset the cooldown for a specified user."""
    cooldowns = load_json(COOLDOWNS_FILE)

    if str(user.id) in cooldowns:
        del cooldowns[str(user.id)]
        save_json(COOLDOWNS_FILE, cooldowns)
        await ctx.send(f'Cooldown for {user.mention} has been reset.')
    else:
        await ctx.send(f'{user.mention} does not have a cooldown record.')

@resetcooldown.error
async def resetcooldown_error(ctx, error):
    """Handles errors for the resetcooldown command."""
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")

@bot.command()
@buyer_required()
async def redeemkey(ctx, key: str):
    """Command to redeem a key."""
    user_id = str(ctx.author.id)
    user_hwids = load_json(HWIDS_FILE)

    keys = load_json(KEYS_FILE)

    # Check if the key exists
    if key not in keys:
        await ctx.send(f'Key {key} does not exist.')
        return

    # Check if the key is already redeemed
    key_data = keys[key]
    if key_data != "Key not redeemed yet":
        await ctx.send(f'Failed to redeem key {key}. It may be invalid or already used.')
        return

    # Redeem the key but do not store the HWID yet
    if redeem_key_without_hwid(key, user_id):
        await ctx.send(f'Key {key} successfully redeemed! Awaiting HWID confirmation.')
    else:
        await ctx.send(f'Failed to redeem key {key}. It may be invalid or already used.')

@bot.command()
@admin_required()
async def keyinfo(ctx, key: str):
    """Admin command to view details of a specific key."""
    keys = load_json(KEYS_FILE)

    if key in keys:
        key_data = keys[key]
        if isinstance(key_data, dict):
            redeemed_by = key_data["redeemed_by"]
            hwid = key_data["hwid"]
            hwid_status = hwid if hwid else "Not yet confirmed"
            await ctx.send(f'Key: {key}\nRedeemed by: {redeemed_by}\nHWID: {hwid_status}')
        else:
            await ctx.send(f'Key: {key} has not been redeemed yet.')
    else:
        await ctx.send(f'Key {key} does not exist.')

@bot.command()
@admin_required()
async def genkey(ctx, num_keys: int):
    """Admin command to generate keys and store them in keys.json."""
    if num_keys < 1:
        await ctx.send('Please specify a positive number of keys to generate.')
        return

    # Load existing keys from the file
    keys = load_json(KEYS_FILE)

    # Generate new keys
    new_keys = generate_keys(num_keys)
    keys.update(new_keys)

    # Save updated keys to the file
    save_json(KEYS_FILE, keys)

    await ctx.send(f'Successfully generated {num_keys} keys.')

@bot.command()
@admin_required()
async def viewusedkeys(ctx):
    """Admin command to view all used keys."""
    used_keys = load_json(USED_KEYS_FILE)
    if not used_keys:
        await ctx.send('No keys have been used yet.')
        return

    # Format the keys into a string with each key on a new line
    used_keys_str = '\n'.join(used_keys)
    await ctx.send(f'Used keys:\n{used_keys_str}')

# Initialize keys and used keys if needed
if not load_json(KEYS_FILE):
    keys = generate_keys(10)  # Generate 10 keys as an example
    save_json(KEYS_FILE, keys)

if not load_json(USED_KEYS_FILE):
    save_json(USED_KEYS_FILE, [])  # Initialize with an empty list

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run("MTI3MzAyODg1ODkzNzA4MTg3OA.G10cYe.TvM6eKcaayg3kWICrI5sgFjJMiPeBt3Cp0pAPs")
