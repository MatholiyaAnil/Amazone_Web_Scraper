import time
import random
import pandas as pd
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

def initialize_driver():
    """Initialize the WebDriver with anti-detection options."""
    user_agent = random.choice(USER_AGENTS)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")  # Change to False if you want to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_asin(url):
    """Extract ASIN from Amazon product URL."""
    try:
        return url.split("/dp/")[1].split("/")[0]
    except IndexError:
        return "N/A"

def scrape_amazon_product(driver, url):
    """Scrape product details including actual price and discount."""
    driver.get(url)
    
    try:
        # Wait for the page to load
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "productTitle")))

        # Extract page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract ASIN from URL
        asin = extract_asin(url)

        # Extract Product Title
        title_element = soup.find("span", id="productTitle")
        title = title_element.text.strip() if title_element else "N/A"

        # Extract Final Price (Selling Price)
        price_element = soup.find("span", class_="a-price-whole")
        price = f"₹{price_element.text.strip()}" if price_element else "N/A"

        # Extract Actual Price (Original Price Before Discount)
        price_section_html = driver.page_source
        price_soup = BeautifulSoup(price_section_html, "html.parser")
        mrp_element = price_soup.find("span", {"class": "a-price a-text-price", "data-a-strike": "true"})
        actual_price = mrp_element.find("span", class_="a-offscreen").text.strip() if mrp_element else "N/A"

        # Extract Discount Percentage
        discount_element = soup.find("span", class_="a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage")
        discount = discount_element.text.strip() if discount_element else "N/A"

        # Extract Rating
        rating_element = soup.find("span", class_="a-icon-alt")
        rating = rating_element.text.strip() if rating_element else "N/A"

        # Extract Number of Reviews
        reviews_element = soup.find("span", id="acrCustomerReviewText")
        num_reviews = reviews_element.text.strip() if reviews_element else "N/A"

        # Extract Product Attributes (Material, Colour, Brand, Manufacturer, Pattern)
        attributes = {}
        table = soup.find("table", id="productDetails_techSpec_section_1")
        if table:
            for row in table.find_all("tr"):
                key_element = row.find("th", class_="prodDetSectionEntry")
                value_element = row.find("td", class_="prodDetAttrValue")
                if key_element and value_element:
                    attributes[key_element.text.strip()] = value_element.text.strip()

        product_data = {
            "ASIN": asin,
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
        print(f"Error fetching details for {url}: {e}")
        return None

def process_csv(input_csv, output_csv):
    """Read CSV with URLs, scrape data, and save results to a new CSV."""
    df = pd.read_csv(input_csv)

    if "URL" not in df.columns:
        print("CSV file must have a column named 'URL'")
        return

    driver = initialize_driver()  # Initialize WebDriver once

    product_data_list = []
    for url in df["URL"]:
        print(f"Scraping: {url}")
        product_data = scrape_amazon_product(driver, url)
        if product_data:
            product_data_list.append(product_data)
        time.sleep(random.uniform(2, 5))  # Random delay to avoid detection

    driver.quit()  # Quit WebDriver after all URLs are processed

    # Save results to CSV
    output_df = pd.DataFrame(product_data_list)
    output_df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")

# Example Usage
input_csv = "input_urls.csv"  # User uploads this file
output_csv = "scraped_amazon_data.csv"  # Output file
process_csv(input_csv, output_csv)
