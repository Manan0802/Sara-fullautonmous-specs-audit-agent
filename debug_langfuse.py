import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST")

print("Checking Langfuse Connection...")
print(f"Host: {host}")

try:
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    is_success = langfuse.auth_check()
    if is_success:
        print("SUCCESS: Langfuse auth check passed.")
    else:
        print("FAILURE: Langfuse auth check returned False.")
except Exception as e:
    print(f"ERROR: Langfuse connection failed with {type(e).__name__}: {str(e)}")
