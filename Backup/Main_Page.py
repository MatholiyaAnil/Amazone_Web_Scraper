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
import re

# Define user agents to avoid detection
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
    options.add_argument("--headless")  # Set to False if you want to see browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_amazon(url):
    """Scrape product details from Amazon search results page."""
    driver = initialize_driver()
    driver.get(url)
    time.sleep(3)  # Allow time for page to load

    product_containers = driver.find_elements(By.XPATH, "//div[@data-asin][@role='listitem']")

    for container in product_containers:
        try:
            # Extract ASIN
            asin = container.get_attribute("data-asin").strip() if container.get_attribute("data-asin") else "Not found"

            # Extract title
            title = container.find_element(By.XPATH, ".//h2/span").text.strip()
        except NoSuchElementException:
            title = "Not found"

        try:
            # Extract rating
            rating_element = container.find_element(By.XPATH, ".//i[@data-cy='reviews-ratings-slot']")
            rating_html = rating_element.get_attribute("outerHTML")

            # Parse rating HTML with BeautifulSoup
            soup = BeautifulSoup(rating_html, "html.parser")
            rating_text = soup.find("span", class_="a-icon-alt").text.strip()
        except NoSuchElementException:
            rating_text = "Not found"

        try:
            # Extract number of ratings
            num_ratings_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 's-underline-text')]")
            num_ratings = num_ratings_element.text.strip()
        except NoSuchElementException:
            num_ratings = "Not found"

        try:
            # Extract "bought in past month" information
            bought_past_month_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 'a-color-secondary')]")
            bought_past_month = bought_past_month_element.text.strip()
        except NoSuchElementException:
            bought_past_month = "NA"

        try:
            # Extract current price
            price_element = container.find_element(By.XPATH, ".//span[@class='a-price-whole']")
            current_price = price_element.text.strip()
        except NoSuchElementException:
            current_price = "Not Available"

        try:
            # Extract actual price (strike-through price)
            actual_price_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-text-price')]")
            actual_price_html = actual_price_element.get_attribute("outerHTML")

            # Parse actual price HTML with BeautifulSoup
            soup = BeautifulSoup(actual_price_html, "html.parser")
            actual_price = soup.find("span", class_="a-offscreen").text.strip()
        except NoSuchElementException:
            actual_price = "Not Available"

        try:
            # Extract discount percentage
            discount_element = container.find_element(By.XPATH, ".//span[contains(text(), '% off')]")
            discount = discount_element.text.strip()
        except NoSuchElementException:
            discount = "Not Available"

        # Print extracted details
        print(f"ASIN: {asin}")
        print(f"Title: {title}")
        print(f"Rating: {rating_text}")
        print(f"Number of Ratings: {num_ratings}")
        print(f"Bought in Past Month: {bought_past_month}")
        print(f"Current Price: ₹{current_price}")
        print(f"Actual Price (MRP): ₹{actual_price}")
        print(f"Discount: {discount}")
        print("-" * 60)

    driver.quit()

# Example Amazon search URL
amazon_url = "https://www.amazon.in/s?k=home+textile+products"
scrape_amazon(amazon_url)