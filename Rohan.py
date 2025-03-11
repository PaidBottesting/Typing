import time
import random
import threading
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Bot Token & Owner ID
BOT_TOKEN = "7898888817:AAHfJQUBpUyxj2LS0v6XZ-ufQok262RPJ70"
OWNER_ID = 1866961136  # Replace with your Telegram user ID

# Global Variables
active_attacks = {}
banned_users = set()
admins = set()
group_access = {}
redeem_codes = {}  # Stores generated codes

bot = Bot(BOT_TOKEN)

# Command: /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /help to see available commands.")

# Command: /attack <ip> <port> <duration>
def attack(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in banned_users:
        update.message.reply_text("You are banned from using this bot.")
        return
    
    if len(context.args) != 3:
        update.message.reply_text("Usage: /attack <IP> <Port> <Duration>")
        return

    ip, port, duration = context.args
    duration = int(duration)

    update.message.reply_text(f"Attack started on {ip}:{port} for {duration} seconds.")
    
    attack_end_time = datetime.now() + timedelta(seconds=duration)
    active_attacks[user_id] = attack_end_time

    # Real-time timer update
    msg = update.message.reply_text(f"Attack ends in {duration} seconds.")
    for remaining in range(duration, 0, -1):
        time.sleep(1)
        try:
            msg.edit_text(f"Attack ends in {remaining} seconds.")
        except:
            pass

    msg.edit_text("Attack finished! Please send a game screenshot for verification.")

    # Wait for feedback (2 minutes)
    context.job_queue.run_once(check_feedback, 120, context={"user_id": user_id})

# Check feedback
def check_feedback(context: CallbackContext):
    user_id = context.job.context["user_id"]
    if user_id in active_attacks:
        banned_users.add(user_id)
        del active_attacks[user_id]
        bot.send_message(user_id, "You are banned for not providing feedback!")

# Handle user feedback (Photo)
def handle_feedback(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in active_attacks:
        del active_attacks[user_id]
        update.message.reply_text("Feedback received! Thank you.")

# Command: /unban <user_id>
def unban(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /unban <user_id>")
        return

    user_id = int(context.args[0])
    if user_id in banned_users:
        banned_users.remove(user_id)
        bot.send_message(user_id, "You have been unbanned.")
        update.message.reply_text(f"User {user_id} has been unbanned.")
    else:
        update.message.reply_text("User is not banned.")

# Command: /banned_users
def banned_users_list(update: Update, context: CallbackContext):
    if not banned_users:
        update.message.reply_text("No banned users.")
    else:
        update.message.reply_text("\n".join([str(user) for user in banned_users]))

# Command: /add_admin <user_id>
def add_admin(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /add_admin <user_id>")
        return

    user_id = int(context.args[0])
    admins.add(user_id)
    update.message.reply_text(f"User {user_id} is now an admin.")

# Command: /remove_admin <user_id>
def remove_admin(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /remove_admin <user_id>")
        return

    user_id = int(context.args[0])
    if user_id in admins:
        admins.remove(user_id)
        update.message.reply_text(f"User {user_id} is no longer an admin.")
    else:
        update.message.reply_text("User is not an admin.")

# Command: /generate_code
def generate_code(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if user_id != OWNER_ID and user_id not in admins:
        update.message.reply_text("Only admins and the owner can generate redeem codes.")
        return

    code = f"Rohan-{random.randint(1000, 9999)}"
    redeem_codes[code] = chat_id  # Store code for this group/private chat

    update.message.reply_text(f"Generated Code: `{code}` (Use /redeem {code})", parse_mode="Markdown")

# Command: /redeem <code>
def redeem(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Usage: /redeem <code>")
        return

    code = context.args[0]
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if code not in redeem_codes:
        update.message.reply_text("Invalid or expired redeem code.")
        return

    if redeem_codes[code] == chat_id:
        if chat_id < 0:  # Group chat
            group_access[chat_id] = True
            update.message.reply_text("Redeem code applied! All group members have access.")
        else:  # Private chat
            update.message.reply_text("Redeem code applied! You now have access.")
        
        del redeem_codes[code]  # Remove the code after use
    else:
        update.message.reply_text("This code is not valid for this chat.")

# Command: /help
def help_command(update: Update, context: CallbackContext):
    help_text = """Available Commands:
/start - Start the bot
/attack <IP> <Port> <Duration> - Launch an attack
/unban <user_id> - Unban a user
/banned_users - List banned users
/add_admin <user_id> - Add an admin
/remove_admin <user_id> - Remove an admin
/generate_code - Generate a redeem code (Admins only)
/redeem <code> - Redeem access code
/help - Show this message"""
    update.message.reply_text(help_text)

# Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("attack", attack))
    dp.add_handler(CommandHandler("unban", unban))
    dp.add_handler(CommandHandler("banned_users", banned_users_list))
    dp.add_handler(CommandHandler("add_admin", add_admin))
    dp.add_handler(CommandHandler("remove_admin", remove_admin))
    dp.add_handler(CommandHandler("generate_code", generate_code))  # New
    dp.add_handler(CommandHandler("redeem", redeem))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.photo, handle_feedback))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
