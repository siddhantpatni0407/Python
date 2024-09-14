import pywhatkit as kit

# Define the text to be converted to handwritten text
text = "Hello, this is a handwritten text example from Python!"
output_path = "handwritten_text.png"

# Convert the text to handwritten text and save it as an image
kit.text_to_handwriting(text, save_to=output_path)
