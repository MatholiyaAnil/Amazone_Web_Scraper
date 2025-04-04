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
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_amazon_category(url):
    """Scrape product details from an Amazon category/search page."""
    driver = initialize_driver()
    driver.get(url)
    
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        product_list = []
        products = soup.find_all("div", class_="s-result-item")
        
        for product in products:
            # Extract Title
            title_element = product.find("span", class_="a-text-normal")
            title = title_element.text.strip() if title_element else "N/A"
            
            # Extract Product URL
            link_element = product.find("a", class_="a-link-normal")
            product_url = "https://www.amazon.in" + link_element["href"] if link_element else "N/A"
            
            # Extract Final Price
            price_element = product.find("span", class_="a-price-whole")
            price = f"₹{price_element.text.strip()}" if price_element else "N/A"
            
            # Extract Actual Price (Original Price Before Discount)
            actual_price_element = product.find("span", class_="a-price a-text-price")
            if actual_price_element:
                actual_price = actual_price_element.find("span", class_="a-offscreen")
                actual_price = actual_price.text.strip() if actual_price else "N/A"
            else:
                actual_price = "N/A"
            
            # Extract Discount Percentage
            discount_element = product.find("span", class_="a-size-base a-color-price")
            discount = discount_element.text.strip() if discount_element else "N/A"
            
            # Extract Rating
            rating_element = product.find("span", class_="a-icon-alt")
            rating = rating_element.text.strip() if rating_element else "N/A"
            
            # Extract Number of Reviews
            reviews_element = product.find("span", class_="a-size-base s-underline-text")
            num_reviews = reviews_element.text.strip() if reviews_element else "N/A"
            
            product_data = {
                "Title": title,
                "Product URL": product_url,
                "Rating": rating,
                "Number of Reviews": num_reviews,
                "Final Price": price,
                "Actual Price": actual_price,
                "Discount Percentage": discount,
            }
            product_list.append(product_data)
            
        return product_list
    
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error fetching category page details: {e}")
        return []
    
    finally:
        driver.quit()

# Example Usage
url = "https://www.amazon.in/Home-Textiles/s?k=Home+Textiles"
category_products = scrape_amazon_category(url)
if category_products:
    df = pd.DataFrame(category_products)
    df.to_csv("amazon_category_products.csv", index=False)
    print("Scraped data saved to amazon_category_products.csv")
