from PIL import Image, ImageFilter

# Open an image file
image_path = "C:/Users/Siddhant Patni/Pictures/Siya.JPG"
img = Image.open(image_path)

# Apply a blur filter
blurred_img = img.filter(ImageFilter.BLUR)

# Save the blurred image
blurred_img.save("blurred_image.jpg")


