import ipaddress


def validate_analyse_input(data):
    """
    Validates and cleans the JSON payload for POST /api/analyse.
    Returns (cleaned_entry, errors). If errors is non-empty, the
    caller should return a 400 response and ignore cleaned_entry.
    """
    errors = []

    ip_address = data.get("ip_address", "")
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        errors.append(f"'{ip_address}' is not a valid IP address")

    username = data.get("username", "")
    if not isinstance(username, str) or not username.strip():
        errors.append("username must be a non-empty string")

    status = data.get("status", "")
    if status not in ("Failed", "Accepted"):
        errors.append("status must be either 'Failed' or 'Accepted'")

    try:
        hour = int(data.get("hour"))
        if not (0 <= hour <= 23):
            errors.append("hour must be between 0 and 23")
    except (TypeError, ValueError):
        errors.append("hour must be a whole number between 0 and 23")
        hour = None

    try:
        failed_attempts = int(data.get("failed_attempts", 1))
        if failed_attempts < 0:
            errors.append("failed_attempts cannot be negative")
    except (TypeError, ValueError):
        errors.append("failed_attempts must be a whole number")
        failed_attempts = None

    try:
        port = int(data.get("port", 22))
        if not (1 <= port <= 65535):
            errors.append("port must be between 1 and 65535")
    except (TypeError, ValueError):
        errors.append("port must be a whole number between 1 and 65535")
        port = None

    if errors:
        return None, errors

    cleaned = {
        "timestamp"      : data.get("timestamp", ""),
        "ip_address"     : ip_address,
        "username"       : username,
        "status"         : status,
        "failed_attempts": failed_attempts,
        "port"           : port,
        "hour"           : hour,
    }
    return cleaned, []