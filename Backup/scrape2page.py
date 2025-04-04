import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup

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
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_amazon_products(url):
    """Scrape product details from the first 2 pages of Amazon search results."""
    driver = initialize_driver()
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load

    current_page = 1
    max_pages = 2  # Stop after 2 pages

    while current_page <= max_pages:
        print(f"\nScraping Page {current_page}...\n" + "="*50)

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

            try:
                actual_price_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-text-price')]")
                actual_price_html = actual_price_element.get_attribute("outerHTML")
                soup = BeautifulSoup(actual_price_html, "html.parser")
                actual_price = soup.find("span", class_="a-offscreen").text.strip()
            except NoSuchElementException:
                actual_price = "Not Available"

            try:
                discount_element = container.find_element(By.XPATH, ".//span[contains(text(), '% off')]")
                discount = discount_element.text.strip()
            except NoSuchElementException:
                discount = "Not Available"

            print(f"Title: {title}")
            print(f"Rating: {rating_text}")
            print(f"Number of Ratings: {num_ratings}")
            print(f"Bought in Past Month: {bought_past_month}")
            print(f"Current Price: ₹{current_price}")
            print(f"Actual Price (MRP): ₹{actual_price}")
            print(f"Discount: {discount}")
            print("-" * 60)

        # Try to find and click the "Next" button
        if current_page < max_pages:
            try:
                next_button = driver.find_element(By.XPATH, "//a[contains(@class, 's-pagination-next')]")
                if "s-pagination-disabled" in next_button.get_attribute("class"):
                    print("\nNo more pages to scrape.\n")
                    break
                next_button.click()
                time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
            except (NoSuchElementException, ElementClickInterceptedException, TimeoutException):
                print("\nNext button not found or cannot be clicked. Stopping pagination.\n")
                break

        current_page += 1

    driver.quit()

# Example: Call the function with an Amazon search URL
amazon_url = "https://www.amazon.in/s?k=bedsheets"
scrape_amazon_products(amazon_url)
