def identifier_keys(email=None, phone=None):
    if email:
        return f"otp:email:{email}", f"user:email:{email}"
    if phone:
        return f"otp:phone:{phone}", f"user:phone:{phone}"
    return None, None

