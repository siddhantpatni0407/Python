import pywhatkit as kit

# Define the phone number and message
phone_number = "+1234567890"  # Use the full international format, e.g., "+1234567890"
message = "Hello, this is a test handwritten message from Python!"

# Convert the message to handwritten text
handwritten_message_path = "handwritten_message.png"
kit.text_to_handwriting(message, save_to=handwritten_message_path)

# Define the time at which the message should be sent (24-hour format)
hour = 22
minute = 0

# Send the handwritten message as an image
kit.sendwhats_image(phone_number, handwritten_message_path, "Here is your handwritten message!", wait_time=15, tab_close=True)
