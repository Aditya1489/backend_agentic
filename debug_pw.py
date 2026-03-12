from app.core import config
import os

pw = config.INITIAL_USER_PASSWORD
print(f"Password: '{pw}'")
print(f"Length: {len(pw)}")
print(f"Bytes: {pw.encode('utf-8')}")
print(f"Bytes Length: {len(pw.encode('utf-8'))}")

from app.core.security import get_password_hash
try:
    hashed = get_password_hash(pw)
    print("Hashing successful")
except Exception as e:
    print(f"Hashing failed: {e}")
