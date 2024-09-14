import turtle

# Create a turtle object
t = turtle.Turtle()

# Function to draw a star
def draw_star():
    for _ in range(5):
        t.forward(150)  # Move forward by 150 units
        t.right(144)    # Turn right by 144 degrees (star angle)

# Draw the star
draw_star()

# Close the turtle graphics window
turtle.done()