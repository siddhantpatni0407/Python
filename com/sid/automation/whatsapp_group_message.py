import pywhatkit as kit

# Define the group ID and message
group_id = "your-group-id"  # Get this ID from the group URL
message = "Hello everyone, this is a test message from Python!"

# Define the time at which the message should be sent (24-hour format)
hour = 19
minute = 0

# Send the message to the group
kit.sendwhatmsg_to_group(group_id, message, hour, minute)
