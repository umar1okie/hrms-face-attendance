# attendance_ai/utils/crypto.py
import os
import base64
from cryptography.fernet import Fernet, InvalidToken
import json
from django.conf import settings

KEY = os.environ.get("ATTENDANCE_FERNET_KEY") or getattr(settings, "ATTENDANCE_FERNET_KEY", None)
if not KEY:
    raise RuntimeError("Missing ATTENDANCE_FERNET_KEY env var. Generate with: "
                       "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")

fernet = Fernet(KEY.encode() if isinstance(KEY, str) else KEY)

def encrypt_array(arr):
    """
    Accepts a Python list/array (JSON-serializable), returns a base64 string safe for storage.
    """
    blob = json.dumps(arr, separators=(',', ':')).encode()
    token = fernet.encrypt(blob)
    return base64.b64encode(token).decode()

def decrypt_array(enc_str):
    """
    Accepts the stored encrypted base64 string and returns Python object (list).
    """
    if not enc_str:
        return None
    try:
        token = base64.b64decode(enc_str)
        data = fernet.decrypt(token)
        return json.loads(data.decode())
    except (InvalidToken, ValueError):
        # not decryptable — maybe old plain JSON: try to parse as JSON
        try:
            return json.loads(enc_str)
        except Exception:
            return None
