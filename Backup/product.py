import requests
from bs4 import BeautifulSoup

# Define the Amazon product URL
url = "https://www.amazon.in/dp/B0BSGWPBJ1"  # Replace with your product URL

# Set User-Agent to avoid bot detection
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

# Fetch the page content
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract Product Title
    title_element = soup.find("span", id="productTitle")
    title = title_element.text.strip() if title_element else "N/A"

    # Extract Price
    price_element = soup.find("span", class_="a-offscreen")
    price = price_element.text.strip() if price_element else "N/A"

    # Extract Rating
    rating_element = soup.find("span", class_="a-icon-alt")
    rating = rating_element.text.strip() if rating_element else "N/A"

    # Extract Number of Reviews
    reviews_element = soup.find("span", id="acrCustomerReviewText")
    num_reviews = reviews_element.text.strip() if reviews_element else "N/A"

    # Extract Product URL
    product_url = url  # The same URL used for the request

    # Print extracted details
    product_data = {
        "Title": title,
        "Product URL": product_url,
        "Rating": rating,
        "Number of Reviews": num_reviews,
        "Price": price,
    }

    for key, value in product_data.items():
        print(f"{key}: {value}")
else:
    print(f"Failed to fetch page, status code: {response.status_code}")
