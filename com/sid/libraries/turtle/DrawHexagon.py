import turtle

# Create a turtle object
t = turtle.Turtle()

# Function to draw a hexagon
def draw_hexagon():
    for _ in range(6):
        t.forward(100)  # Move forward by 100 units
        t.right(60)     # Turn right by 60 degrees (hexagon angle)

# Draw the hexagon
draw_hexagon()

# Close the turtle graphics window
turtle.done()
