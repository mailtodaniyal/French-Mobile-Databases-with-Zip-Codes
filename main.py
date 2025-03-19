import time
import random
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

def setup_driver():
    options = Options()
    options.add_argument("--headless") 
    options.add_argument(f"user-agent={UserAgent().random}")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_leboncoin(page_url):
    driver = setup_driver()
    driver.get(page_url)
    time.sleep(3) 

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    data = []
    
    listings = soup.find_all("div", class_="sc-1fcmfeb-2") 
    for listing in listings:
        try:
            phone_number = extract_mobile_number(listing)
            address, zip_code = extract_address_zip(listing)

            if phone_number and zip_code:
                data.append({"phone_number": phone_number, "address": address, "zip_code": zip_code})
        except Exception as e:
            print(f"Skipping entry due to error: {e}")

    return data

def extract_mobile_number(listing):
    text = listing.get_text()
    numbers = [num for num in text.split() if num.startswith("06") or num.startswith("07")]
    return numbers[0] if numbers else None

def extract_address_zip(listing):
    address_tag = listing.find("span", class_="sc-1a92hh1-1") 
    if address_tag:
        address = address_tag.get_text()
        zip_code = extract_zip_code(address)
        return address, zip_code
    return None, None

def extract_zip_code(address):
    zip_codes = [part for part in address.split() if part.isdigit() and len(part) == 5]
    return zip_codes[0] if zip_codes else None

def save_to_db(data):
    conn = sqlite3.connect("france_mobile_db.sqlite")
    df = pd.DataFrame(data)
    df.to_sql("mobile_data", conn, if_exists="replace", index=False)
    conn.close()
    print("Data successfully saved to database!")

if __name__ == "__main__":
    leboncoin_url = "https://www.leboncoin.fr/recherche?category=2"  
    print("Scraping mobile data from LeBonCoin...")
    scraped_data = scrape_leboncoin(leboncoin_url)
    
    if scraped_data:
        print(f"Collected {len(scraped_data)} records.")
        save_to_db(scraped_data)
    else:
        print("No valid data found. Try adjusting the scraper settings.")
