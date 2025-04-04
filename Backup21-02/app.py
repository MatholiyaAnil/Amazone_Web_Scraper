import time
import random
import csv
import re
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

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
    options.add_argument("--headless")  # Set to False if you want to see the browser
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_category_from_url(url):
    """Extracts product category from the Amazon search URL."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'k' in query_params:
        return query_params['k'][0]  # Extract category name
    return "Unknown"

def scrape_amazon_products(url):
    """Scrape Amazon search results and save to CSV."""
    driver = initialize_driver()
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load

    category = extract_category_from_url(url)  # Extract category name
    page_count = 0  # Track the number of pages scraped

    # Open CSV file for writing
    filename = f"amazon_products_{category}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Category", "Title", "Rating", "Number of Ratings", "Bought in Past Month", 
                         "Current Price", "Actual Price (MRP)", "Discount", "ASIN"])

        while True:
            page_count += 1
            st.write(f"Scraping Page {page_count}: {driver.current_url}")
            
            product_containers = driver.find_elements(By.XPATH, "//div[@data-asin and @data-component-type='s-search-result']")

            for container in product_containers:
                try:
                    title = container.find_element(By.XPATH, ".//h2/span").text.strip()
                except NoSuchElementException:
                    title = "Not found"

                try:
                    rating_element = container.find_element(By.XPATH, ".//i[@data-cy='reviews-ratings-slot']")
                    rating_html = rating_element.get_attribute("outerHTML")
                    soup = BeautifulSoup(rating_html, "html.parser")
                    rating_text = soup.find("span", class_="a-icon-alt").text.strip()
                except NoSuchElementException:
                    rating_text = "Not found"

                try:
                    num_ratings_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 's-underline-text')]")
                    num_ratings = num_ratings_element.text.strip()
                except NoSuchElementException:
                    num_ratings = "Not found"

                try:
                    bought_past_month_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 'a-color-secondary')]")
                    bought_past_month = bought_past_month_element.text.strip()
                except NoSuchElementException:
                    bought_past_month = "NA"

                try:
                    price_element = container.find_element(By.XPATH, ".//span[@class='a-price-whole']")
                    current_price = price_element.text.strip()
                except NoSuchElementException:
                    current_price = "Not Available"

                try:
                    price_section_html = container.get_attribute("outerHTML")
                    soup = BeautifulSoup(price_section_html, "html.parser")
                    mrp_element = soup.find("span", {"class": "a-price a-text-price", "data-a-strike": "true"})
                    actual_price = mrp_element.find("span", class_="a-offscreen").text.strip() if mrp_element else "Not Available"
                except NoSuchElementException:
                    actual_price = "Not Available"

                try:
                    discount_element = container.find_element(By.XPATH, ".//span[contains(text(), '% off')]")
                    discount = discount_element.text.strip()
                except NoSuchElementException:
                    discount = "Not Available"

                try:
                    asin = container.get_attribute("data-asin").strip()
                except NoSuchElementException:
                    asin = "Not found"

                writer.writerow([category, title, rating_text, num_ratings, bought_past_month, current_price, actual_price, discount, asin])

            try:
                next_button = driver.find_element(By.XPATH, "//a[contains(@class, 's-pagination-next')]")
                if "s-pagination-disabled" in next_button.get_attribute("class"):
                    break
                next_button.click()
                time.sleep(random.uniform(2, 4))
            except (NoSuchElementException, TimeoutException):
                break

    driver.quit()
    st.write(f"Scraping completed! Total pages scraped: {page_count}")
    st.download_button("Download CSV", data=open(filename, "rb").read(), file_name=filename, mime="text/csv")

st.title("Amazon Product Scraper")
product_query = st.text_input("Enter product name:")
if st.button("Scrape"):
    amazon_url = f"https://www.amazon.in/s?k={product_query}"
    scrape_amazon_products(amazon_url)
