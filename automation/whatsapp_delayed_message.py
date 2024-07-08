import pywhatkit as kit
import time

# Define the phone number and message
phone_number = "+1234567890"  # Use the full international format, e.g., "+1234567890"
message = "Hello, this is a test message from Python!"

# Define the delay in seconds
delay = 30

# Wait for the specified delay
time.sleep(delay)

# Send the message
kit.sendwhatmsg_instantly(phone_number, message)
