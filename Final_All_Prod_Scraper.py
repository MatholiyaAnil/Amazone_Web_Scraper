import time
import random
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


def initialize_driver():
    user_agent = random.choice(USER_AGENTS)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")
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
    driver = initialize_driver()
    driver.get(url)
    time.sleep(3)

    category = extract_category_from_url(url)  # Extract category name
    page_count = 0  # Track the number of pages scraped

    # Open CSV file for writing
    filename = f"amazon_products_{category}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Category", "Title", "Rating", "Number of Ratings", "Current Price", "Actual Price (MRP)", "Last Month Purchase", "Price Per Unit\K.g"
                          "Discount", "ASIN"])
        
        while True:  # Scrape until the last page
            page_count += 1  # Increment page count
            print(f"\nScraping Page {page_count}: {driver.current_url}\n" + "="*50)

            product_containers = driver.find_elements(By.XPATH, "//div[@data-asin and @data-component-type='s-search-result']")

            for container in product_containers:
                try:
                    title = container.find_element(By.XPATH, ".//h2/span").text.strip()
                except NoSuchElementException:
                    title = "Not Available"

                try:
                    rating_element = container.find_element(By.XPATH, ".//i[@data-cy='reviews-ratings-slot']")
                    rating_html = rating_element.get_attribute("outerHTML")
                    soup = BeautifulSoup(rating_html, "html.parser")
                    rating_text = soup.find("span", class_="a-icon-alt").text.strip()
                except NoSuchElementException:
                    rating_text = "Not Available"

                try:
                    num_ratings_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 's-underline-text')]")
                    num_ratings = num_ratings_element.text.strip()
                except:
                    num_ratings = "Not Available"

                try:
                    purchase_element = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 'a-color-secondary')]")
                    purchase_text = purchase_element.text.strip()
                    
                    if "bought in past month" in purchase_text:
                        purchase_in_last_month = purchase_text
                    else:
                        purchase_in_last_month = "Not Available"
                except NoSuchElementException:
                    purchase_in_last_month = "Not Available"

                try:
                    price_element = container.find_element(By.XPATH, ".//span[@class='a-price-whole']")
                    current_price = price_element.text.strip()
                except NoSuchElementException:
                    current_price = "Not Available"

                try:
                    price_per_unit_elements = container.find_elements(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 'a-color-secondary')]")
                    price_per_unit_html = price_per_unit_elements[1].get_attribute("outerHTML") if len(price_per_unit_elements) > 1 else "Not found"
                    soup = BeautifulSoup(price_per_unit_html, "html.parser")
                    
                    price_per_unit_element = soup.find("span", class_="a-price a-text-price")
                    price_per_unit = "NA"
                    
                    if price_per_unit_element:
                        price_offscreen = price_per_unit_element.find("span", class_="a-offscreen")
                        if price_offscreen:
                            price_per_unit = price_offscreen.text.strip()
                except Exception:
                    price_per_unit = "NA"

                try:
                    actual_price_html = container.get_attribute("outerHTML")
                    soup = BeautifulSoup(actual_price_html, "html.parser")
                    actual_price_element = soup.find("span", class_="a-price a-text-price", attrs={"data-a-strike": "true"})
                    actual_price = "Not Available"
                    
                    if actual_price_element:
                        actual_price_offscreen = actual_price_element.find("span", class_="a-offscreen")
                        if actual_price_offscreen:
                            actual_price = actual_price_offscreen.text.strip()
                except Exception:
                    actual_price = "Not Available"

                try:
                    discount_element = container.find_element(By.XPATH, ".//span[contains(text(), '% off')]")
                    discount = discount_element.text.strip()
                except NoSuchElementException:
                    discount = "Not Available"

                try:
                    asin = container.get_attribute("data-asin").strip()
                except NoSuchElementException:
                    asin = "Not Available"

                # Save data to CSV
                writer.writerow([category, title, rating_text, num_ratings, current_price, actual_price, purchase_in_last_month, price_per_unit, discount, asin])

                print(f"Title: {title}")
                print(f"Rating: {rating_text}")
                print(f"Number of Ratings: {num_ratings}")
                print(f"Purchase in Last Month: {purchase_in_last_month}")
                print(f"Current Price: ₹{current_price}")
                print(f"Price per Unit: {price_per_unit}")
                print(f"Actual Price: {actual_price}")
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
amazon_url = "https://www.amazon.in/s?k=basmati+rice+1+kg&page=3&crid=3A4JBXYQ1BAE&qid=1740114198&rnid=1741387031&sprefix=Bas%2Caps%2C288&xpid=17hH69vHYw8SI&ref=sr_nr_p_36_0_0&low-price=&high-price="
scrape_amazon_products(amazon_url)