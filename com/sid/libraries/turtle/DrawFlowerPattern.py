import turtle

# Create a turtle object
t = turtle.Turtle()
t.speed(10)  # Set the speed of the turtle

# Function to draw a flower pattern
def draw_flower():
    for _ in range(36):   # Repeat 36 times to create a full circle pattern
        t.circle(100)     # Draw a circle
        t.right(10)       # Turn right by 10 degrees

# Draw the flower
draw_flower()

# Close the turtle graphics window
turtle.done()
