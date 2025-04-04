import time
import random
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

def scrape_amazon_products(url):
    driver = initialize_driver()
    driver.get(url)
    time.sleep(3)

    product_containers = driver.find_elements(By.XPATH, "//div[@data-asin and @data-component-type='s-search-result']")

    for container in product_containers:
        try:
            title = container.find_element(By.XPATH, ".//h2/span").text.strip()
        except NoSuchElementException:
            title = "Not found"

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
            print(f"Price per Unit HTML: {price_per_unit_html}")
        except Exception:
            price_per_unit = "NA"

        try:
            actual_price_html = container.get_attribute("outerHTML")
            soup = BeautifulSoup(actual_price_html, "html.parser")
            actual_price_element = soup.find("span", class_="a-price a-text-price", attrs={"data-a-strike": "true"})
            actual_price = "Not found"
            
            if actual_price_element:
                actual_price_offscreen = actual_price_element.find("span", class_="a-offscreen")
                if actual_price_offscreen:
                    actual_price = actual_price_offscreen.text.strip()
            print(f"Actual Price HTML: {actual_price_element}")
        except Exception:
            actual_price = "Not found"

        print(f"Title: {title}")
        print(f"Price per Unit: {price_per_unit}")
        print(f"Actual Price: {actual_price}")
        print("-" * 60)

    driver.quit()

amazon_url = "https://www.amazon.in/s?k=diapers+new+born+baby"
scrape_amazon_products(amazon_url)
