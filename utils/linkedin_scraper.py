import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib.parse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from dotenv import load_dotenv
load_dotenv()

def read_company_names(company_list, driver):
    company = driver.find_elements(
    By.XPATH, "//div[contains(@class,'artdeco-entity-lockup__subtitle')]//span[normalize-space()]")
    for c in company:
        if c.text:
            company_list.append(c.text)
    return company_list

def read_all_pages(company_list, driver, company_name=""):

    # Go on search page on LinkedIn
    search_term = f"service technician {company_name}"
    url = f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote(search_term)}&origin=TYPEAHEAD_HISTORY"
    driver.get(url)
    # Wait until clickable
    wait = WebDriverWait(driver, 10)
    link = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-results__cluster-bottom-banner a"))
    )
    link.click()
    for i in range(100):

        company_list = read_company_names(company_list, driver)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        # sleep(0.5)
        company_list = read_company_names(company_list, driver)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # sleep(0.5)
        company_list = read_company_names(company_list, driver)

        wait = WebDriverWait(driver, 6)
        try:
            next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'jobs-search-pagination__button--next')]"))
            )
            next_button.click()
            sleep(1)
        except Exception as e:
            print(f"Exiting for loop: {e}")
            break
    return company_list

def scraper(
        companies: list,
        email_address: str = os.environ['EMAIL'],
        password: str = os.environ['PASSWORD']
) -> pd.DataFrame:

    # Go to login page:
    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/login')

    if not email_address or not password:
        raise ValueError("Email address and password must be provided.")

    # Log in to LinkedIn:
    email = driver.find_element(By.ID, "username")
    email.send_keys(email_address)
    password = driver.find_element(By.ID, "password")
    password.send_keys(password)
    password.submit()

    company_list = []

    for c in companies:
        try:
            company_list = read_all_pages(company_list, driver, c)
        except Exception:
            return company_list

    return company_list