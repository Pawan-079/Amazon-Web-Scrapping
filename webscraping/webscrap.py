from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

import time
import json
import os

# Load environment variables from .env file
load_dotenv()

# Setup WebDriver for Microsoft Edge
edge_driver_path = r"C:\Users\ASUS\edgedriver_win64\msedgedriver.exe"  # Update with the path to your msedgedriver.exe
service = Service(edge_driver_path)
driver = webdriver.Edge(service=service)
wait = WebDriverWait(driver, 10)

# Amazon login function
def login_amazon(username, password):
    driver.get("https://www.amazon.in/ap/signin?openid.pape.max_auth_age=900&openid.return_to=https%3A%2F%2Fwww.amazon.in%2Fgp%2Fyourstore%2Fhome%3Fpath%3D%252Fgp%252Fyourstore%252Fhome%26signIn%3D1%26useRedirectOnSuccess%3D1%26action%3Dsign-out%26ref_%3Dnav_AccountFlyout_signout&openid.assoc_handle=inflex&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "ap_email")))
        email_input.send_keys(username)
        driver.find_element(By.ID, "continue").click()

        password_input = wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
        password_input.send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()
    except TimeoutException:
        print("Login failed. Check your credentials or captcha.")

# Scrape category data
def scrape_category(url, category_name, output_dir, max_products=1500):
    driver.get(url)
    products = []
    product_count = 0

    while product_count < max_products:
        try:
            items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".zg-grid-general-faceout")))
            for item in items:
                try:
                    product_name = item.find_element(By.CSS_SELECTOR, ".p13n-sc-truncate").text
                    product_price = item.find_element(By.CSS_SELECTOR, ".p13n-sc-price").text
                    discount = item.find_element(By.CSS_SELECTOR, ".p13n-discount").text if "discount" in item.text.lower() else "N/A"
                    rating = item.find_element(By.CSS_SELECTOR, ".a-icon-alt").text
                    sold_by = item.find_element(By.CSS_SELECTOR, ".p13n-seller-details").text if "sold by" in item.text.lower() else "N/A"
                    ship_from = item.find_element(By.CSS_SELECTOR, ".p13n-shipping").text if "ship from" in item.text.lower() else "N/A"

                    # Ensure discount is greater than 50%
                    if "50%" in discount or "more" in discount:
                        product = {
                            "Category Name": category_name,
                            "Product Name": product_name,
                            "Price": product_price,
                            "Discount": discount,
                            "Rating": rating,
                            "Ship From": ship_from,
                            "Sold By": sold_by
                        }
                        products.append(product)
                        product_count += 1
                        if product_count >= max_products:
                            break
                except NoSuchElementException:
                    continue

            # Click next page
            next_button = driver.find_element(By.CSS_SELECTOR, ".zg-pagination-next")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(3)
            else:
                break
        except TimeoutException:
            print(f"Failed to load products for category {category_name}.")
            break

    # Save products to JSON
    with open(os.path.join(output_dir, f"{category_name}_products.json"), "w") as f:
        json.dump(products, f, indent=4)

    print(f"Scraped {len(products)} products from category {category_name}.")

# Main script
def main():
    # Load credentials from .env file
    AMAZON_EMAIL = os.getenv("AMAZON_EMAIL")
    AMAZON_PASSWORD = os.getenv("AMAZON_PASSWORD")

    if not AMAZON_EMAIL or not AMAZON_PASSWORD:
        print("Error: AMAZON_EMAIL and AMAZON_PASSWORD must be set in the .env file.")
        return

    # Create output directory
    output_dir = "amazon_best_sellers"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Login to Amazon
    login_amazon(AMAZON_EMAIL, AMAZON_PASSWORD)

    # URLs for categories
    category_urls = {
        "Kitchen": "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
        "Shoes": "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
        "Computers": "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
        "Electronics": "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0"
        # Add more categories as needed
    }

    for category_name, url in category_urls.items():
        scrape_category(url, category_name, output_dir)

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()
