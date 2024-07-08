import requests

# URL of the file to download
file_url = "https://example.com/example_file.zip"

# Send a GET request to the URL
response = requests.get(file_url)

# Save the file
with open("downloaded_file.zip", "wb") as f:
    f.write(response.content)

print("File downloaded successfully!")
