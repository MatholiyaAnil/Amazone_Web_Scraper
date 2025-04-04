import time
import random
import csv
import re
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
    """Scrape all pages of Amazon search results and save to CSV."""
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

        while True:  # Scrape until the last page
            page_count += 1  # Increment page count
            print(f"\nScraping Page {page_count}: {driver.current_url}\n" + "="*50)

            # Extract all product containers
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

                # ✅ Extract Correct "M.R.P" Using BeautifulSoup
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

                # Save data to CSV
                writer.writerow([category, title, rating_text, num_ratings, bought_past_month, current_price, actual_price, discount, asin])

                print(f"Category: {category}")
                print(f"Title: {title}")
                print(f"Rating: {rating_text}")
                print(f"Number of Ratings: {num_ratings}")
                print(f"Bought in Past Month: {bought_past_month}")
                print(f"Current Price: ₹{current_price}")
                print(f"Actual Price (MRP): ₹{actual_price}")  # ✅ Correctly Extracted MRP
                print(f"Discount: {discount}")
                print(f"ASIN: {asin}")
                print("-" * 60)

            # Try to find and click the "Next" button
            try:
                next_button = driver.find_element(By.XPATH, "//a[contains(@class, 's-pagination-next')]")
                if "s-pagination-disabled" in next_button.get_attribute("class"):
                    print("\n✅ Reached last page. Stopping pagination.\n")
                    break  # Exit loop when no more pages
                next_button.click()
                time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
            except (NoSuchElementException, TimeoutException):
                print("\n🚫 Next button not found. Stopping pagination.\n")
                break  # Exit loop when "Next" button is not found

    driver.quit()
    print(f"\n✅ Scraping completed! Total pages scraped: {page_count}")
    print(f"✅ Data saved to '{filename}' successfully!\n")

# Example: Call the function with an Amazon search URL
amazon_url = "https://www.amazon.in/bedsheet"
scrape_amazon_products(amazon_url)
