import turtle

# Create a turtle object
t = turtle.Turtle()
t.speed(10)  # Set the speed of the turtle

# Function to draw a spiral
def draw_spiral():
    for i in range(100):
        t.forward(i * 5)  # Move forward increasing distance
        t.right(45)       # Turn right by 45 degrees

# Draw the spiral
draw_spiral()

# Close the turtle graphics window
turtle.done()
