import requests
from bs4 import BeautifulSoup

# URL of the website to scrape
url = "https://example.com"

# Send a GET request to the URL
response = requests.get(url)

# Parse HTML content
soup = BeautifulSoup(response.text, "html.parser")

# Example: Get the title of the website
title = soup.find("title").get_text()

print("Title of the website:", title)
