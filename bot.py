#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Free Fire Account Creator Bot - بوت إنشاء حسابات فري فاير
Developer: Yacine Dz
Version: 3.0
"""

import os
import sys
import json
import time
import random
import string
import hashlib
import threading
import subprocess
import base64
import codecs
import re
import logging
from datetime import datetime
from urllib.parse import unquote
from io import BytesIO

import requests
import urllib3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = "8422372449:AAGZxNXJzli5pQvCJeh_rygqhAhn9dtwoPM"
ADMIN_ID = 6936293942
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# إعدادات الإنشاء
ReGiOn = "IND"
NiCkNaMe = "yacinedev"
PaSsWoRd = "yacinedev"
ToTaL = 100
ThReAdS = 50
GhOsT = False
AuToAcT = True

# ============================================================
# ENCRYPTION KEYS
# ============================================================

aEsKeY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
aEsIv = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
cLiEnTsEcReT = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

rEgIoNlAnG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th",
    "BD": "bn", "PK": "ur", "TW": "zh", "EUROPE": "fr", "RU": "ru",
    "NA": "na", "SAC": "es", "BR": "pt", "SG": "ms", "US": "us"
}
rEgIoNlIsT = ["IND", "ID", "TH", "ME", "EUROPE", "VN", "BD", "PK", "TW", "RU", "NA", "SAC", "BR", "SG", "US"]

nIcKXoR = b'1e5898ccb8dfdd921f9bdea848768b64a201'

INDIAN_CARRIERS = ["Jio", "Airtel", "Vodafone Idea", "BSNL", "MTNL", "Reliance Jio", "Bharti Airtel", "Vi"]
INDIAN_CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad"]
INDIAN_DEVICES = ["Asus ASUS_AI2401_A", "Samsung SM-G998B", "OnePlus 9 Pro", "Xiaomi Mi 11", "Google Pixel 6"]

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# GLOBAL VARIABLES
# ============================================================

tor_process = None
session_pool = []
SESSION_POOL_SIZE = 50
IP_ROTATION_INTERVAL = 15
ACCOUNT_COUNTER_FOR_IP_ROTATION = 0
created_accounts = []
is_running = False
stop_flag = False

# ============================================================
# TOR FUNCTIONS
# ============================================================

def start_tor():
    global tor_process
    try:
        subprocess.run(['pkill', '-9', 'tor'], capture_output=True, check=False)
        time.sleep(0.5)
        tor_process = subprocess.Popen(
            ['tor'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        for i in range(10):
            time.sleep(0.5)
            result = subprocess.run(['pgrep', '-x', 'tor'], capture_output=True)
            if result.returncode == 0:
                return True
        return False
    except:
        return False

def renew_tor_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 9051))
        s.send(b'AUTHENTICATE ""\r\n')
        s.send(b'SIGNAL NEWNYM\r\n')
        s.send(b'QUIT\r\n')
        s.close()
        time.sleep(1)
        return True
    except:
        return False

def get_proxies():
    return {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

# ============================================================
# SESSION POOL
# ============================================================

def init_session_pool():
    global session_pool
    for _ in range(SESSION_POOL_SIZE):
        session = requests.Session()
        session.proxies.update(get_proxies())
        session.verify = False
        session.timeout = 10
        session_pool.append(session)

def get_pool_session():
    return random.choice(session_pool)

# ============================================================
# PROTOBUF FUNCTIONS
# ============================================================

def FF(value):
    out = []
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def GayRena(field_num, value):
    if isinstance(value, int):
        tag = (field_num << 3) | 0
        return FF(tag) + FF(value)
    elif isinstance(value, str):
        data = value.encode('utf-8')
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(data)) + data
    elif isinstance(value, bytes):
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(value)) + value
    elif isinstance(value, dict):
        sub_payload = xPro(value)
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(sub_payload)) + sub_payload
    else:
        raise TypeError(f"Unsupported type for field {field_num}: {type(value)}")

def xPro(fields_dict):
    payload = b''
    for key, value in fields_dict.items():
        field_num = int(key)
        if isinstance(value, list):
            if value and all(isinstance(v, int) for v in value):
                packed = b''.join(FF(v) for v in value)
                tag = (field_num << 3) | 2
                payload += FF(tag) + FF(len(packed)) + packed
            else:
                for elem in value:
                    payload += GayRena(field_num, elem)
        else:
            payload += GayRena(field_num, value)
    return payload

def Noob(packet):
    cipher = AES.new(aEsKeY, AES.MODE_CBC, aEsIv)
    pad_len = 16 - (len(packet) % 16)
    if pad_len == 0:
        pad_len = 16
    plaintext_padded = packet + bytes([pad_len]) * pad_len
    return cipher.encrypt(plaintext_padded)

def Pro(data):
    from google.protobuf.internal.decoder import _DecodeVarint, _DecodeVarint32
    pos = 0
    length = len(data)
    fields = {}
    while pos < length:
        key, pos = _DecodeVarint(data, pos)
        field_num = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            value, pos = _DecodeVarint(data, pos)
        elif wire_type == 2:
            size, pos = _DecodeVarint32(data, pos)
            raw = data[pos:pos+size]
            pos += size
            try:
                value = Pro(raw)
            except:
                try:
                    value = raw.decode('utf-8')
                except:
                    value = raw.hex()
        elif wire_type == 5:
            value = int.from_bytes(data[pos:pos+4], "little")
            pos += 4
        elif wire_type == 1:
            value = int.from_bytes(data[pos:pos+8], "little")
            pos += 8
        else:
            raise Exception(f"Unsupported wire type: {wire_type}")
        if field_num in fields:
            if not isinstance(fields[field_num], list):
                fields[field_num] = [fields[field_num]]
            fields[field_num].append(value)
        else:
            fields[field_num] = value
    return fields

# ============================================================
# API FUNCTIONS
# ============================================================

def RoFl(session, password):
    url = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
    payload = {"app_id": 100067, "client_type": 2, "password": password, "source": 2}
    json_body = json.dumps(payload, separators=(',', ':'))
    data_to_sign = cLiEnTsEcReT + json_body
    signature = hashlib.sha256(data_to_sign.encode()).hexdigest()
    headers = {
        "User-Agent": "GarenaMSDK/4.0.39(FRL-AN00a ;Android 10;nu;HK;)",
        "Authorization": f"Signature {signature}",
        "Content-Type": "application/json; charset=utf-8"
    }
    resp = session.post(url, data=json_body, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            return str(data["data"]["uid"])
        else:
            raise Exception(f"Register failed: {data}")
    else:
        resp.raise_for_status()
        raise Exception(f"Unexpected response: {resp.text}")

def yEet(length=6, chars=string.ascii_uppercase + string.digits + "-_."):
    return ''.join(random.choice(chars) for _ in range(length))

def pWe():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "0.0.0.0"

def sUs():
    return "GarenaMSDK/4.0.39(FRL-AN00a ;Android 10;nu;HK;)"

def bRuH():
    return "okhttp/3.12.1"

def fInE(original):
    keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
                 0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
    encoded = ""
    for i in range(len(original)):
        orig_byte = ord(original[i])
        key_byte = keystream[i % len(keystream)]
        result_byte = orig_byte ^ key_byte
        encoded += chr(result_byte)
    return encoded

def yAy(s):
    return ''.join(c if 32 <= ord(c) <= 126 else f'\\u{ord(c):04x}' for c in s)

def nOp(nick_b64):
    if not nick_b64:
        return ""
    try:
        decoded_bytes = base64.b64decode(nick_b64)
        key_len = len(nIcKXoR)
        xored = bytes([decoded_bytes[i] ^ nIcKXoR[i % key_len] for i in range(len(decoded_bytes))])
        return xored.decode('utf-8', errors='ignore')
    except:
        return nick_b64

def wOw(func, session, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(session, *args, **kwargs)
        except:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.5)
    return None

def hAhA(session, password):
    return RoFl(session, password)

def lMaO(session, uid, password):
    url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "client_id":100067, "client_secret":cLiEnTsEcReT, "client_type":2,
        "password":password, "response_type":"token", "uid":uid
    }
    headers = {"User-Agent": sUs(), "Content-Type": "application/json"}
    resp = session.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Token grant failed: {data}")
    return data["data"]["access_token"], data["data"]["open_id"]

def gG(session, name, access_token, open_id, region, is_ghost=False):
    url = "https://loginbp.ggpolarbear.com/MajorRegister"
    exp_digits = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    num = random.randint(1,99999)
    exp = ''.join(exp_digits[d] for d in f"{num:05d}")
    name = name[:7] + exp
    lang_code = "pt" if is_ghost else rEgIoNlAnG.get(region.upper(), "en")
    encoded_result = fInE(open_id)
    field_unicode = yAy(encoded_result)
    field_bytes = codecs.decode(field_unicode, 'unicode_escape').encode('latin1')
    fields_dict = {
        "1": name, "2": access_token, "3": open_id,
        "5": 102000007, "6": 4, "7": 1, "13": 1,
        "14": field_bytes, "15": lang_code, "16": 2
    }
    plaintext = xPro(fields_dict)
    encrypted_payload = Noob(plaintext)
    headers = {
        "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
        "Host": "loginbp.ggpolarbear.com", "ReleaseVersion": "OB54",
        "User-Agent": bRuH(), "X-GA": "v1 1", "X-Unity-Version": "2018.4."
    }
    resp = session.post(url, headers=headers, data=encrypted_payload, timeout=15)
    resp.raise_for_status()
    return Pro(resp.content)

def nIcE(session, access_token, open_id, region, lang_code):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = pWe()
    if region.upper() == "IND":
        device_model = random.choice(INDIAN_DEVICES)
        carrier = random.choice(INDIAN_CARRIERS)
        city = random.choice(INDIAN_CITIES)
    else:
        device_model = "Asus ASUS_AI2401_A"
        carrier = "GrameenPhone"
        city = "Dhaka"
    gpu = "Adreno (TM) 640"
    
    def qT(n):
        out = []
        while True:
            b = n & 0x7F
            n >>= 7
            if n: b |= 0x80
            out.append(b)
            if not n: break
        return bytes(out)
    
    def zZ(f, v):
        return qT((f << 3) | 0) + qT(v)
    
    def xX(f, v):
        data = v.encode() if isinstance(v, str) else v
        return qT((f << 3) | 2) + qT(len(data)) + data
    
    fields = {
        3: now_str,
        4: "free fire",
        5: 1,
        7: "1.126.5",
        8: "Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20220128.171448)",
        9: "Handheld",
        10: carrier,
        11: "WIFI",
        17: gpu,
        18: "OpenGL ES 3.0",
        19: "Google|4645e530-e790-4be2-ae7c-6f64d1259603",
        20: ip,
        21: lang_code,
        22: open_id,
        23: 4,
        24: "Handheld",
        25: device_model,
        26: region.upper(),
        29: access_token,
        33: carrier,
        34: "WIFI",
        37: "7428b253defc164018c604a1ebbfebdf",
        73: "/data/app/com.dts.freefireth-1/lib/arm",
        75: "H4c322aeb56444feaa151d1ea91a8f7f2|/data/app/com.dts.freefireth-1/base.apk",
        76: 2,
        78: 2,
        79: 2,
        83: "OpenGLES2",
        85: city,
        87: "android",
        88: "KqsHTywQqGHMgPbDY9P2mhkxXj/beObk/TFNpmgaucQwxyLu9hA478WEQCV0Mgaz9UivYUPpKNwPzgZhvDhSsUDMAFY=",
        90: '{"cur_rate":null,"support_etc2":false}',
        97: 1,
        98: 1,
        99: "4",
        100: "4"
    }
    
    packet = b''
    for f, v in fields.items():
        if isinstance(v, int): 
            packet += zZ(f, v)
        elif isinstance(v, str): 
            packet += xX(f, v)
        elif isinstance(v, bytes): 
            packet += xX(f, v)
    
    encrypted = Noob(packet)
    headers = {
        "Accept-Encoding": "gzip", 
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded", 
        "Expect": "100-continue",
        "ReleaseVersion": "OB54", 
        "User-Agent": bRuH(),
        "X-GA": "v1 1", 
        "X-Unity-Version": "2018.4."
    }
    resp = session.post(url, headers=headers, data=encrypted, timeout=15)
    resp.raise_for_status()
    decoded = Pro(resp.content)
    jwt_token = decoded.get(8)
    if isinstance(jwt_token, list):
        jwt_token = jwt_token[0] if jwt_token else None
    return decoded, jwt_token

def dUdE(session, region_code, jwt_token):
    url = "https://loginbp.ggpolarbear.com/ChooseRegion"
    if region_code.upper() == "CIS":
        region_code = "ru"
    else:
        region_code = region_code.upper()
    fields_dict = {"1": region_code}
    plaintext = xPro(fields_dict)
    encrypted_payload = Noob(plaintext)
    headers = {
        "Accept-Encoding": "gzip", "Authorization": f"Bearer {jwt_token}",
        "Connection": "Keep-Alive", "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue", "ReleaseVersion": "OB54",
        "User-Agent": bRuH(), "X-GA": "v1 1", "X-Unity-Version": "2018.4."
    }
    resp = session.post(url, headers=headers, data=encrypted_payload, timeout=10)
    return resp.status_code == 200

def bYe(session, jwt_token, client_url):
    url = f"https://{client_url}/GetLoginData"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = pWe()
    device_model = random.choice(INDIAN_DEVICES)
    carrier = random.choice(INDIAN_CARRIERS)
    city = random.choice(INDIAN_CITIES)
    gpu = "Adreno (TM) 640"
    open_id = "24adf2d6806cf61bd95d4cd3b57a0bd9"
    
    def qT(n):
        out = []
        while True:
            b = n & 0x7F
            n >>= 7
            if n: b |= 0x80
            out.append(b)
            if not n: break
        return bytes(out)
    
    def zZ(f, v):
        return qT((f << 3) | 0) + qT(v)
    
    def xX(f, v):
        data = v.encode() if isinstance(v, str) else v
        return qT((f << 3) | 2) + qT(len(data)) + data
    
    fields = {
        3: now_str,
        4: "free fire",
        5: 1,
        7: "1.126.5",
        8: "Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20220128.171448)",
        9: "Handheld",
        10: carrier,
        11: "WIFI",
        17: gpu,
        18: "OpenGL ES 3.0",
        19: "Google|4645e530-e790-4be2-ae7c-6f64d1259603",
        20: ip,
        21: "en",
        22: open_id,
        23: 4,
        24: "Handheld",
        25: device_model,
        26: "IND",
        29: jwt_token,
        33: carrier,
        34: "WIFI",
        37: "7428b253defc164018c604a1ebbfebdf",
        73: "/data/app/com.dts.freefireth-1/lib/arm",
        75: "H4c322aeb56444feaa151d1ea91a8f7f2|/data/app/com.dts.freefireth-1/base.apk",
        83: "OpenGLES2",
        85: city,
        87: "android",
        88: "KqsHT8nWdkA7u/m7k8vg2H5FgrCGa4lfww3nHBGRHRPwDFV4LyCj8sT23O/P6K06qC3MOLZRThwWwul+g2goHwtQJy8=",
        90: '{"cur_rate":null,"support_etc2":false}'
    }
    
    packet = b''
    for f, v in fields.items():
        if isinstance(v, int): 
            packet += zZ(f, v)
        elif isinstance(v, str): 
            packet += xX(f, v)
        elif isinstance(v, bytes): 
            packet += xX(f, v)
    
    encrypted_payload = Noob(packet)
    
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': f"Bearer {jwt_token}",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB54"
    }
    
    try:
        resp = session.post(url, headers=headers, data=encrypted_payload, timeout=10)
        return resp.status_code == 200
    except:
        return False

def hElLo(jwt_token):
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None, None
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        lock_region = data.get("lock_region") or data.get("noti_region")
        raw_nick = data.get("nickname")
        if raw_nick:
            nickname = nOp(raw_nick)
        else:
            nickname = ""
        return lock_region, nickname
    except:
        return None, None

# ============================================================
# ACCOUNT CREATOR CLASS
# ============================================================

class FreeFireAccountCreator:
    def __init__(self, region, nickname_prefix, password_prefix, auto_activate, total_target, ghost=False):
        self.region = region
        self.nickname_prefix = nickname_prefix[:7]
        self.password_prefix = password_prefix.upper()
        self.auto_activate = auto_activate
        self.total_target = total_target
        self.ghost = ghost
        self.created_count = 0
        self.accounts = []
        self.stop = False
        self.lock = threading.Lock()
        self.saved_uids = set()

    def gEnPaSs(self):
        r1 = yEet(6)
        r2 = yEet(6)
        plain = f"{self.password_prefix}_{r1}-VAIBHAV{r2}"
        return plain, plain

    def create_account(self):
        if self.stop:
            return None
        
        session = get_pool_session()
        try:
            store_pass, api_pass = self.gEnPaSs()
            uid = wOw(hAhA, session, api_pass)
            
            if uid in self.saved_uids:
                return None
            
            access_token, open_id = wOw(lMaO, session, uid, api_pass)
            reg_resp = wOw(gG, session, self.nickname_prefix, access_token, open_id, self.region, self.ghost)
            account_id = reg_resp.get(3)
            if not account_id:
                raise Exception("No account_id")
            account_id = str(account_id)
            lang_code = rEgIoNlAnG.get(self.region, "en") if not self.ghost else "pt"
            login_resp, jwt_token = wOw(nIcE, session, access_token, open_id, self.region, lang_code)
            if not jwt_token:
                raise Exception("No JWT")
            lock_region, nickname = hElLo(jwt_token)
            if not nickname:
                nickname = self.nickname_prefix
            
            need_lock = False
            final_jwt = jwt_token
            client_url = None
            
            if not self.ghost:
                if lock_region and lock_region not in (None, 'None', '..', ''):
                    if lock_region != self.region.upper():
                        need_lock = True
                else:
                    need_lock = True
                if need_lock:
                    dUdE(session, self.region, jwt_token)
                    login_resp2, jwt_token2 = wOw(nIcE, session, access_token, open_id, self.region, lang_code)
                    if jwt_token2:
                        final_jwt = jwt_token2
                        lock_region2, nickname2 = hElLo(jwt_token2)
                        if nickname2:
                            nickname = nickname2
                        lock_region = lock_region2
                last_resp = login_resp2 if need_lock and 'login_resp2' in locals() else login_resp
                client_url_raw = last_resp.get(10)
                if isinstance(client_url_raw, str):
                    client_url = client_url_raw
                elif isinstance(client_url_raw, list):
                    client_url = client_url_raw[0] if client_url_raw else None
                if client_url and client_url.startswith("https://"):
                    client_url = client_url[8:]
                if not client_url:
                    if self.region.upper() == "IND":
                        client_url = "client.ind.freefiremobile.com"
                    elif self.region.upper() in ["BR","US","NA","SAC"]:
                        client_url = "client.us.freefiremobile.com"
                    else:
                        client_url = "clientbp.ggpolarbear.com"
            else:
                client_url = "clientbp.ggpolarbear.com"
                lock_region = "GHOST"
            
            activated = False
            if self.auto_activate and final_jwt and client_url and not self.ghost:
                activated = wOw(bYe, session, final_jwt, client_url)
            
            final_region = lock_region if lock_region and not self.ghost else "GHOST"
            stored_password = store_pass
            
            acc = {
                "nickname": nickname,
                "game_uid": account_id,
                "region": final_region,
                "uid": str(uid),
                "password": stored_password,
                "activated": activated
            }
            
            self.saved_uids.add(uid)
            return acc
        except:
            return None

    def run(self, callback=None):
        self.stop = False
        self.created_count = 0
        self.accounts = []
        
        start_tor()
        time.sleep(1)
        init_session_pool()
        
        while self.created_count < self.total_target and not self.stop:
            acc = self.create_account()
            if acc:
                self.created_count += 1
                self.accounts.append(acc)
                if callback:
                    callback(acc)
            else:
                time.sleep(0.1)
        
        return self.accounts

# ============================================================
# TELEGRAM BOT HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ هذا البوت للأدمن فقط!")
        return
    
    text = """
🔥 **Free Fire Account Creator Bot** 🔥

📌 **الأوامر المتاحة:**

/create [عدد] - بدء إنشاء حسابات
/stop - إيقاف الإنشاء
/status - عرض حالة الإنشاء
/export - تصدير الحسابات
/regions - عرض المناطق المتاحة
/setregion [المنطقة] - تغيير المنطقة
/setnick [الاسم] - تغيير بادئة الاسم
/setpass [الباسورد] - تغيير بادئة الباسورد

📌 **المناطق المتاحة:**
IND, ID, TH, ME, EUROPE, VN, BD, PK, TW, RU, NA, SAC, BR, SG, US

👨‍💻 **Developer:** Yacine Dz
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_running, stop_flag, created_accounts
    
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if is_running:
        await update.message.reply_text("⏳ عملية إنشاء جارية بالفعل!")
        return
    
    count = int(context.args[0]) if context.args and context.args[0].isdigit() else 10
    if count > 500:
        await update.message.reply_text("⚠️ الحد الأقصى 500 حساب في المرة الواحدة!")
        return
    
    is_running = True
    stop_flag = False
    created_accounts = []
    
    status_msg = await update.message.reply_text(f"🚀 بدء إنشاء {count} حساب...\n⏳ جاري التنفيذ...")
    
    def callback(acc):
        created_accounts.append(acc)
    
    creator = FreeFireAccountCreator(ReGiOn, NiCkNaMe, PaSsWoRd, AuToAcT, count, GhOsT)
    
    def run_creator():
        creator.run(callback)
        global is_running
        is_running = False
    
    import threading
    thread = threading.Thread(target=run_creator)
    thread.start()
    
    # تحديث الحالة كل 5 ثواني
    while is_running:
        await asyncio.sleep(5)
        try:
            await status_msg.edit_text(
                f"🚀 جاري إنشاء الحسابات...\n"
                f"✅ تم إنشاء: {len(created_accounts)}/{count}\n"
                f"⏳ الوقت: {datetime.now().strftime('%H:%M:%S')}"
            )
        except:
            pass
    
    # إرسال النتائج
    if created_accounts:
        # حفظ في ملف
        folder = "GEN/GHOST" if GhOsT else f"GEN/{ReGiOn}"
        os.makedirs(folder, exist_ok=True)
        txt_path = os.path.join(folder, f"Accounts-{ReGiOn}.txt")
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            for acc in created_accounts:
                f.write(f"BOT = {acc['game_uid']} | UiD = {acc['uid']} | PassWord = {acc['password']} | NamE = {acc['nickname']} | ReGioN = {acc['region']}\n")
        
        # إرسال الملف
        with open(txt_path, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f, filename=f"accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
                caption=f"✅ تم إنشاء {len(created_accounts)} حساب بنجاح!"
            )
        
        # إرسال أول 5 حسابات كعينة
        sample = ""
        for i, acc in enumerate(created_accounts[:5]):
            sample += f"{i+1}. UID: {acc['uid']} | Pass: {acc['password']}\n"
        await update.message.reply_text(f"📋 عينة من الحسابات:\n{sample}")
    else:
        await update.message.reply_text("❌ لم يتم إنشاء أي حساب!")

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_flag, is_running
    
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if is_running:
        stop_flag = True
        is_running = False
        await update.message.reply_text("⏹ تم إيقاف عملية الإنشاء!")
    else:
        await update.message.reply_text("❌ لا توجد عملية إنشاء جارية!")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    status = "🟢 جاري" if is_running else "🔴 متوقف"
    await update.message.reply_text(
        f"📊 **حالة البوت**\n\n"
        f"الحالة: {status}\n"
        f"تم إنشاء: {len(created_accounts)}\n"
        f"المنطقة: {ReGiOn}\n"
        f"بادئة الاسم: {NiCkNaMe}\n"
        f"إجمالي الـ Tor: {len(session_pool)}\n"
        f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode="Markdown"
    )

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    folder = "GEN/GHOST" if GhOsT else f"GEN/{ReGiOn}"
    txt_path = os.path.join(folder, f"Accounts-{ReGiOn}.txt")
    
    if os.path.exists(txt_path):
        with open(txt_path, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f, filename=f"accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
                caption="📁 جميع الحسابات المحفوظة"
            )
    else:
        await update.message.reply_text("❌ لا توجد حسابات محفوظة!")

async def cmd_regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    text = "🌍 **المناطق المتاحة:**\n"
    for region in rEgIoNlIsT:
        text += f"▪️ {region}\n"
    text += f"\nالمنطقة الحالية: **{ReGiOn}**"
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_setregion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ReGiOn
    
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /setregion IND")
        return
    
    region = context.args[0].upper()
    if region in rEgIoNlIsT:
        ReGiOn = region
        await update.message.reply_text(f"✅ تم تغيير المنطقة إلى: {ReGiOn}")
    else:
        await update.message.reply_text(f"❌ منطقة غير صالحة!\nالمناطق المتاحة: {', '.join(rEgIoNlIsT)}")

async def cmd_setnick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global NiCkNaMe
    
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /setnick Vaibhav")
        return
    
    NiCkNaMe = context.args[0][:7]
    await update.message.reply_text(f"✅ تم تغيير بادئة الاسم إلى: {NiCkNaMe}")

async def cmd_setpass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global PaSsWoRd
    
    user_id = update.effective_user.id
    if str(user_id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Admin only!")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /setpass Vaibhav")
        return
    
    PaSsWoRd = context.args[0].upper()
    await update.message.reply_text(f"✅ تم تغيير بادئة الباسورد إلى: {PaSsWoRd}")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ============================================================
# MAIN
# ============================================================

import asyncio

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ قم بتعيين BOT_TOKEN في الكود!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("create", cmd_create))
    application.add_handler(CommandHandler("stop", cmd_stop))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("export", cmd_export))
    application.add_handler(CommandHandler("regions", cmd_regions))
    application.add_handler(CommandHandler("setregion", cmd_setregion))
    application.add_handler(CommandHandler("setnick", cmd_setnick))
    application.add_handler(CommandHandler("setpass", cmd_setpass))
    
    print("🚀 Free Fire Account Creator Bot started!")
    print(f"👨‍💻 Developer: Yacine Dz")
    print(f"📍 Region: {ReGiOn}")
    print(f"📝 Nickname: {NiCkNaMe}")
    print(f"🔑 Password: {PaSsWoRd}")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")

if __name__ == "__main__":
    main()
