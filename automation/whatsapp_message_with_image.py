import pywhatkit as kit

# Define the phone number, message, and image path
phone_number = "+917276369171"  # Use the full international format, e.g., "+1234567890"
message = "Hello, this is a test message with an image from Python!"
image_path = "C:/Users/Siddhant Patni/Pictures/Siya.JPG"

# Define the time at which the message should be sent (24-hour format)
hour = 6
minute = 7

# Send the message with the image
kit.sendwhats_image(phone_number, image_path, message, wait_time=15, tab_close=True)