import csv
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import pandas as pd

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
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# ✅ Extract Product Description
def extract_description(item):
    """Extract product description using Selenium and BeautifulSoup."""
    try:
        container = item.find_element(By.XPATH, ".//div[contains(@class, 'a-section a-spacing-small puis-padding-left-small puis-padding-right-small')]")
        html = container.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-size-base-plus a-spacing-none a-color-base a-text-normal").get_text(strip=True)
    except:
        return "N/A"

# ✅ Extract Rating
def extract_rating(item):
    """Extract rating using Selenium and BeautifulSoup."""
    try:
        rating_icon = item.find_element(By.XPATH, ".//i[contains(@class, 'a-icon-star-small')]")
        html = rating_icon.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-icon-alt").get_text(strip=True)
    except:
        return "N/A"

# ✅ Extract Total Purchases
def extract_total_purchases(item):
    """Extract total purchases using Selenium and BeautifulSoup."""
    try:
        purchases_element = item.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base s-underline-text')]")
        html = purchases_element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-size-base s-underline-text").get_text(strip=True)
    except:
        return "N/A"

# ✅ Extract Discount Price
def extract_discount_price(item):
    """Extract discount price using Selenium and BeautifulSoup."""
    try:
        discount_element = item.find_element(By.XPATH, ".//span[contains(@class, 'a-price-whole')]")
        html = discount_element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-price-whole").get_text(strip=True)
    except:
        return "N/A"

# ✅ Extract Actual Price
def extract_actual_price(item):
    """Extract actual price using Selenium and BeautifulSoup."""
    try:
        actual_price_element = item.find_element(By.XPATH, ".//span[contains(@class, 'a-offscreen')]")
        html = actual_price_element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-offscreen").get_text(strip=True)
    except:
        return "N/A"

# ✅ Extract Offer Details
def extract_offer(item):
    """Extract offer details using Selenium and BeautifulSoup."""
    try:
        offer_element = item.find_element(By.XPATH, ".//div[contains(@class, 'a-row a-size-base a-color-secondary')]/span")
        html = offer_element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("span", class_="a-size-base a-color-secondary").get_text(strip=True)
    except:
        return "N/A"

# ✅ Main Scraper Function
def scrape_amazon_product_details(search_url):
    """Scrape Amazon product details using separate functions for each attribute."""
    driver = initialize_driver()
    driver.get(search_url)
    
    products = []
    time.sleep(3)  # Allow page to load
    items = driver.find_elements(By.XPATH, "//div[contains(@class, 'a-section a-spacing-base')]")
    
    for item in items:
        product_data = {
            "Product Description": extract_description(item),
            "Rating": extract_rating(item),
            "Total Purchases": extract_total_purchases(item),
            "Discount Price": extract_discount_price(item),
            "Actual Price": extract_actual_price(item),
            "Offer": extract_offer(item)
        }
        products.append(product_data)
    
    driver.quit()
    return products

# URL for Home Textiles category
search_url = "https://www.amazon.in/Home-Textiles/s?k=Home+Textiles"

data = scrape_amazon_product_details(search_url)

if data:
    df = pd.DataFrame(data)
    df.to_csv("amazon_product_details.csv", index=False)
    print("✅ Scraping complete. Data saved to amazon_product_details.csv")
