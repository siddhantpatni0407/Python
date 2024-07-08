import pywhatkit as kit

# Define the email details
receiver_email = "siddhantpatni04@gmail.com"
subject = "Test Email from Python"
message = "Hello, this is a test email sent from Python using pywhatkit!"

# Replace with your email and App Password
sender_email = "siddhant4patni@gmail.com"
app_password = "wlalfdf fdfdgil nkndfb fetn"

# Send the email
kit.send_mail(sender_email, app_password, subject, message, receiver_email)
