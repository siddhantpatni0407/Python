# Python
Python Programming Codes


# automation

1.  AutoWhatsAppMessage.py

#### WhatsApp Message Sender

This Python program allows you to send a WhatsApp message using the `pywhatkit` library.

## Installation

-   Install the required library using pip:

    ```bash
    pip install pywhatkit
    ```
    ```bash
    pip install pywin32
    ```
    ```bash
    pip install pyqrcode
    ```

## Usage

1. Open the `AutoWhatsAppMessage.py` file in a text editor.
2. Define the phone number, message, and the time at which the message should be sent in the script.

    ```python
    import pywhatkit as kit

    # Define the phone number and message
    phone_number = "+1234567890"  # Use the full international format, e.g., "+1234567890"
    message = "Hello, this is a test message from Python!"

    # Define the time at which the message should be sent (24-hour format)
    # In this example, the message will be sent at 18:30
    hour = 18
    minute = 30

    # Send the message
    kit.sendwhatmsg(phone_number, message, hour, minute)
    ```

3. Save the changes and run the script:

    ```bash
    python whatsapp_message_sender.py
    ```

## Notes

- Ensure you are logged into WhatsApp Web on your default browser.
- The `pywhatkit` library requires a stable internet connection.
- The `kit.sendwhatmsg` function schedules the message to be sent at the specified time, so make sure your Python script is running at that time.

## Sending an Immediate Message

If you want to send the message immediately, you can use the `sendwhatmsg_instantly` method instead:

```python
kit.sendwhatmsg_instantly(phone_number, message)
