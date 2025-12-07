import hmac
import hashlib


def verify_hmac(secret: str, body: bytes, signature: str) -> bool:
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(digest, signature)
    except Exception:
        return False

