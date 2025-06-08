import hashlib
import aiohttp
from urllib.parse import quote
from config import \
    CASH_HASH as HASH, \
    CASH_PASS as CASHIER_PASS, \
    CASHDESK_ID, \
    API_URL as BASE_URL, \
    CASH_LOGIN, \
    AUTO_DEPOSIT, \
    AUTO_WITHDRAW


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def get_utc_now():
    from datetime import datetime, timezone
    return datetime.utcnow().strftime("%Y.%m.%d %H:%M:%S")

async def get_balance():
    dt = get_utc_now()
    confirm = md5(f"{CASHDESK_ID}:{HASH}")

    hash_str = f"hash={HASH}&cashierpass={CASHIER_PASS}&dt={dt}"
    step1_sha256 = sha256(hash_str)

    md5_str = f"dt={dt}&cashierpass={CASHIER_PASS}&cashdeskid={CASHDESK_ID}"
    step2_md5 = md5(md5_str)

    sign_input = step1_sha256 + step2_md5
    sign = sha256(sign_input)

    dt_encoded = quote(dt)
    url = f"{BASE_URL}/Cashdesk/{CASHDESK_ID}/Balance?confirm={confirm}&dt={dt_encoded}"

    headers = {
        "sign": sign
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print("Status:", response.status)
            return await response.json()


async def find_user(user_id: int):
    confirm = md5(f"{user_id}:{HASH}")

    hash_str = f"hash={HASH}&userid={user_id}&cashdeskid={CASHDESK_ID}"
    md5_str = f"userid={user_id}&cashierpass={CASHIER_PASS}&hash={HASH}"
    sign = sha256(sha256(hash_str) + md5(md5_str))

    url = f"{BASE_URL}/Users/{user_id}?confirm={confirm}&cashdeskId={CASHDESK_ID}"
    headers = {"sign": sign}
    


    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()


async def deposit_user(user_id: int, summa: int, lang: str = "ru"):
    if AUTO_DEPOSIT:
        return {}
    confirm = md5(f"{user_id}:{HASH}")

    sha1 = sha256(f"hash={HASH}&lng={lang}&userid={user_id}")
    md5_str = md5(f"summa={int(summa)}&cashierpass={CASHIER_PASS}&cashdeskid={CASHDESK_ID}")
    sign = sha256(sha1 + md5_str)

    url = f"{BASE_URL}/Deposit/{user_id}/Add"
    headers = {"sign": sign}
    json_body = {
        "cashdeskId": CASHDESK_ID,
        "lng": lang,
        "summa": int(summa),
        "confirm": confirm
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_body) as response:
            return await response.json()

async def payout_user(user_id: int, code: str, lang: str = "ru"):
    if AUTO_WITHDRAW:
        return {}
    
    confirm = md5(f"{user_id}:{HASH}")

    sha1 = sha256(f"hash={HASH}&lng={lang}&userid={user_id}")
    md5_str = md5(f"code={code}&cashierpass={CASHIER_PASS}&cashdeskid={CASHDESK_ID}")
    sign = sha256(sha1 + md5_str)

    url = f"{BASE_URL}/Deposit/{user_id}/Payout"
    headers = {"sign": sign}
    json_body = {
        "cashdeskId": CASHDESK_ID,
        "lng": lang,
        "code": code,
        "confirm": confirm
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_body) as response:
            return await response.json()
