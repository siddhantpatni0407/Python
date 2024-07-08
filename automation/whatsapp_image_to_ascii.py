import pywhatkit as kit

# Define the phone number and image path
phone_number = "+917276369171"  # Use the full international format, e.g., "+1234567890"
image_path = "C:/Users/Siddhant Patni/Pictures/Siya.JPG"


# Convert the image to ASCII art
ascii_art = kit.image_to_ascii_art(image_path)

# Define the time at which the message should be sent (24-hour format)
hour = 00
minute = 27

# Send the ASCII art as a message
kit.sendwhatmsg(phone_number, ascii_art, hour, minute)
