from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Defined here, separately from app.py, so both app.py and api.py
# can import the same limiter instance without creating a circular import.
limiter = Limiter(key_func=get_remote_address)