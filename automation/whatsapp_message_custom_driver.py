import pywhatkit as kit
from selenium import webdriver

# Define the phone number and message
phone_number = "+1234567890"  # Use the full international format, e.g., "+1234567890"
message = "Hello, this is a test message from Python with a custom WebDriver!"

# Create a custom WebDriver instance
driver = webdriver.Chrome(executable_path='path/to/chromedriver')

# Define the time at which the message should be sent (24-hour format)
hour = 23
minute = 0

# Send the message using the custom WebDriver
kit.sendwhatmsg(phone_number, message, hour, minute, 20, 20, True, 2, driver)
