import streamlit as st
import time
import random
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup
from urllib.parse import urlencode

# User agents to prevent bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def initialize_driver():
    """Initialize Selenium WebDriver with anti-bot detection measures."""
    user_agent = random.choice(USER_AGENTS)
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(5)
    return driver

def build_amazon_url(product_name, page=1):
    """Build Amazon search URL for a given product name and page number."""
    base_url = "https://www.amazon.in/s"
    params = {"k": product_name, "page": page}
    return f"{base_url}?{urlencode(params)}"

def scrape_amazon_products(url, max_pages, category):
    driver = initialize_driver()
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@data-asin and @data-component-type='s-search-result']")))
    except TimeoutException:
        st.error("Timeout while waiting for the page to load. Please try again.")
        driver.quit()
        return

    scraped_data = []
    page_count = 0

    while page_count < max_pages:
        page_count += 1
        st.write(f"Scraping Page {page_count}: {driver.current_url}")

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
                num_ratings = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 's-underline-text')]").text.strip()
            except NoSuchElementException:
                num_ratings = "Not Available"

            try:
                purchase_text = container.find_element(By.XPATH, ".//span[contains(@class, 'a-size-base') and contains(@class, 'a-color-secondary')]").text.strip()
                purchase_in_last_month = purchase_text if "bought in past month" in purchase_text else "Not Available"
            except NoSuchElementException:
                purchase_in_last_month = "Not Available"

            try:
                current_price = container.find_element(By.XPATH, ".//span[@class='a-price-whole']").text.strip()
            except NoSuchElementException:
                current_price = "Not Available"
            
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
                discount = container.find_element(By.XPATH, ".//span[contains(text(), '% off')]").text.strip()
            except NoSuchElementException:
                discount = "Not Available"

            try:
                asin = container.get_attribute("data-asin").strip()
            except NoSuchElementException:
                asin = "Not Available"
            
            scraped_data.append([category, title, rating_text, num_ratings, current_price, actual_price, price_per_unit, purchase_in_last_month, discount, asin])

        # Handle pagination
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 's-pagination-next')]"))
            )
            if "s-pagination-disabled" in next_button.get_attribute("class"):
                break
            next_button.click()
            WebDriverWait(driver, random.uniform(2, 4)).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-asin and @data-component-type='s-search-result']"))
            )
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            break

    driver.quit()
    
    df = pd.DataFrame(scraped_data, columns=["Category", "Title", "Rating", "Number of Ratings", "Current Price", "Actual Price", "Price Per Unit", "Last Month Purchase", "Discount", "ASIN"])
    st.dataframe(df)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV", data=csv, file_name="amazon_products.csv", mime="text/csv", key="download_csv")
    st.success("Scraping completed!")

# Streamlit UI
st.title("🛒 Amazon Product Scraper")
st.markdown("#### Search for products on Amazon and scrape product details!")

search_input = st.text_input("Enter product name OR URL (e.g., bedsheets, curtains, towels)")
category_input = ""

if "amazon.in" in search_input:
    category_input = st.text_input("Enter category name")
    page_option = 1  # Force single-page scrape for URL
else:
    page_option = st.selectbox("Select number of pages to scrape", [1, 3, "All"])
    category_input = search_input

if st.button("Start Scraping"):
    if search_input:
        with st.spinner("Scraping data... This may take some time."):
            url = search_input if "amazon.in" in search_input else build_amazon_url(search_input)
            max_pages = 1 if "amazon.in" in search_input else (999 if page_option == "All" else page_option)
            scrape_amazon_products(url, max_pages, category_input)
    else:
        st.error("Please enter a valid product name or Amazon URL")
