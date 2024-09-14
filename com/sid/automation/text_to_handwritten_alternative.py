from PIL import Image, ImageDraw, ImageFont


def text_to_handwriting(text, save_to="handwritten_text.png"):
    # Create a blank image with white background
    img = Image.new('RGB', (800, 600), color='white')

    # Load a handwriting-like font
    font = ImageFont.truetype("fonts/HandwritingFont.ttf", 30)

    # Initialize the drawing context
    d = ImageDraw.Draw(img)

    # Draw the text onto the image
    d.text((10, 10), text, font=font, fill=(0, 0, 0))

    # Save the image
    img.save(save_to)


# Define the text to be converted to handwritten text
text = "Hello, this is a handwritten text example from Python!"
output_path = "handwritten_text.png"

# Convert the text to handwritten text and save it as an image
text_to_handwriting(text, save_to=output_path)
