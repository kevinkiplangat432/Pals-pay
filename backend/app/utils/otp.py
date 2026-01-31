import random

def generate_otp():
    return str(random.randint(100000, 999999)) # Generate a 6-digit OTP