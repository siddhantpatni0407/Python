import turtle

# Create a turtle object
t = turtle.Turtle()

# Function to draw a square
def draw_square():
    for _ in range(4):
        t.forward(100)  # Move forward by 100 units
        t.right(90)     # Turn right by 90 degrees

# Draw the square
draw_square()

# Close the turtle graphics window
turtle.done()