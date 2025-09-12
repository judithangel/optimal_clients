import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib.parse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep
from dotenv import load_dotenv
load_dotenv()

def read_company_names(company_list, driver):
    company = driver.find_elements(
        By.CSS_SELECTOR,
        'p[class*="job-teaser-list-item-styles__Company"]')
    for c in company:
        if c.text:
            company_list.append(c.text)
    return company_list

def job_search(company_list, driver, company_name=""):

    # Enter search term into search field
    search_term = f"service technician {company_name}"
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'keywords-input'))
    )
    search_input.send_keys(search_term)
    search_input.send_keys(Keys.ENTER)

    sleep(1.5)
    company_list = read_company_names(company_list, driver)
    wait = WebDriverWait(driver, 8)
    clear_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label,'Clear')]"))
    )
    clear_button.click()
    return company_list

def scraper(
        companies: list[str],
        email_address: str = os.environ['EMAIL'],
        pw: str = os.environ['PASSWORD']
) -> list[str]:

    driver = webdriver.Chrome()
    driver.maximize_window()
    company_list = []

    url = "https://www.xing.com/jobs/search"
    driver.get(url)
    sleep(2)
    wait = WebDriverWait(driver, 8)
    driver.find_element(By.CSS_SELECTOR, "#usercentrics-root").shadow_root.find_element(By.CSS_SELECTOR, 'button[data-testid="uc-accept-all-button"]').click()
    for c in companies:
        try:
            sleep(0.25)
            # url = f"https://www.linkedin.com/jobs/"
            company_list = job_search(company_list, driver, c)
        except Exception:
            print(f"Error with company {c}")

    driver.quit()
    return company_list