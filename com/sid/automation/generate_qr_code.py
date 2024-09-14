import pyqrcode

# Define the data for QR code
data = "https://www.google.com"

# Generate QR code
qr = pyqrcode.create(data)

# Save QR code as SVG file
qr.svg("qr_code.svg", scale=8)
