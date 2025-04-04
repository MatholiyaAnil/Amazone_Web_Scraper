import time
import random
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup

# Define a list of user agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

CSV_FILE = "Amazone_Product_Page.csv"

def initialize_driver():
    """Initialize the WebDriver with anti-detection options."""
    user_agent = random.choice(USER_AGENTS)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_amazon_product(url):
    """Scrape product details including actual price and discount."""
    driver = initialize_driver()
    driver.get(url)
    
    try:
        # Wait for the page to load
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "productTitle")))

        # Extract page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract Product Title
        title_element = soup.find("span", id="productTitle")
        title = title_element.text.strip() if title_element else "N/A"

        # Extract Final Price (Selling Price)
        price_element = soup.find("span", class_="a-price-whole")
        price = f"₹{price_element.text.strip()}" if price_element else "N/A"

        # Extract Actual Price (Original Price Before Discount)
        actual_price_element = soup.find("span", class_="a-price a-text-price")
        if actual_price_element:
            actual_price = actual_price_element.find("span", class_="a-offscreen")
            actual_price = actual_price.text.strip() if actual_price else "N/A"
        else:
            actual_price = "N/A"

        # Extract Discount Percentage
        discount_element = soup.find("span", class_="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage")
        discount = discount_element.text.strip() if discount_element else "N/A"

        # Extract Rating
        rating_element = soup.find("span", class_="a-icon-alt")
        rating = rating_element.text.strip() if rating_element else "N/A"

        # Extract Number of Reviews
        reviews_element = soup.find("span", id="acrCustomerReviewText")
        num_reviews = reviews_element.text.strip() if reviews_element else "N/A"

        # Extract Product Attributes from Container 2 (Material, Colour, Brand, Manufacturer, Pattern)
        attributes = {}
        table = soup.find("table", id="productDetails_techSpec_section_1")

        if table:
            for row in table.find_all("tr"):
                key_element = row.find("th", class_="prodDetSectionEntry")
                value_element = row.find("td", class_="prodDetAttrValue")

                if key_element and value_element:
                    key = key_element.text.strip()
                    value = value_element.text.strip()
                    attributes[key] = value

        product_data = {
            "Title": title,
            "Product URL": url,
            "Rating": rating,
            "Number of Reviews": num_reviews,
            "Final Price": price,
            "Actual Price": actual_price,
            "Discount Percentage": discount,
            "Material": attributes.get("Material", "N/A"),
            "Colour": attributes.get("Colour", "N/A"),
            "Brand": attributes.get("Brand", "N/A"),
            "Manufacturer": attributes.get("Manufacturer", "N/A"),
            "Pattern": attributes.get("Pattern", "N/A"),
        }

        return product_data

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error fetching details: {e}")
        return None

    finally:
        driver.quit()

def save_to_csv(data, filename=CSV_FILE):
    """Save product data to a CSV file."""
    file_exists = os.path.isfile(filename)
    
    df = pd.DataFrame([data])
    
    # If file exists, append without writing header
    df.to_csv(filename, mode='a', index=False, header=not file_exists)
    print(f"Data saved to {filename}")

# Example Usage
url = "https://www.amazon.in/dp/B0BSGWPBJ1"
product_details = scrape_amazon_product(url)
if product_details:
    save_to_csv(product_details)
