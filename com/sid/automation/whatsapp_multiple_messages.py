import pywhatkit as kit
import time

# Define the phone number and message
phone_number = "+917276369171"  # Use the full international format, e.g., "+1234567890"
message = "Hello, this is a test message from Python!"

# Define the number of messages to send and the interval between messages
num_messages = 5
interval = 10  # Interval in seconds

# Send the messages
for _ in range(num_messages):
    kit.sendwhatmsg_instantly(phone_number, message)
    time.sleep(interval)
