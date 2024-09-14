import turtle

# Create a turtle object
t = turtle.Turtle()

# Set up the screen and background color
turtle.bgcolor("white")
t.penup()  # Don't draw when turtle moves
t.goto(-200, 0)  # Move the turtle to the starting position

# Set the font and size
font = ("Arial", 48, "normal")

# The text to be written
text = "Siya Patni"

# Function to write each character one by one
def write_text_one_by_one(text):
    for char in text:
        t.write(char, font=font)  # Write the character
        t.forward(50)  # Move turtle forward by 50 units to write next character
        turtle.delay(200)  # Slight delay for better visibility of character writing

# Write the name "Siya Patni" one character at a time
write_text_one_by_one(text)

# Hide the turtle
t.hideturtle()

# Keep the window open until clicked
turtle.done()
