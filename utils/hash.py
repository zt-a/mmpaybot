import hmac
import hashlib
import time
from config import ADMIN_SECRET as SECRET_KEY

def generate_hash() -> str:
    interval = int(time.time() // 300)
    msg = str(interval).encode()
    key = SECRET_KEY if isinstance(SECRET_KEY, bytes) else SECRET_KEY.encode()
    hash_bytes = hmac.new(key, msg, hashlib.sha256).digest()
    return hash_bytes.hex()


def verify_hash(provided_hash: str) -> bool:
    current_interval = int(time.time() // 300)
    valid_hashes = []
    for i in (current_interval, current_interval - 1):
        msg = str(i).encode()
        # Если SECRET_KEY - bytes, используем напрямую
        key = SECRET_KEY if isinstance(SECRET_KEY, bytes) else SECRET_KEY.encode()
        valid_hash = hmac.new(key, msg, hashlib.sha256).digest().hex()
        valid_hashes.append(valid_hash)
    return provided_hash in valid_hashes

