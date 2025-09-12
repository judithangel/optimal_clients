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
        By.XPATH, "//div[contains(@class,'artdeco-entity-lockup__subtitle')]//span[normalize-space()]")
    for c in company:
        if c.text:
            company_list.append(c.text)
    return company_list

def read_all_pages(company_list, driver, company_name=""):

    # Enter search term into search field
    search_term = f"service technician {company_name}"
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@data-testid="typeahead-input"]'))
    )
    search_input.send_keys(search_term)
    search_input.send_keys(Keys.ENTER)

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
        except Exception:
            print(f"Exiting for loop")
            break
    return company_list

def scraper(
        companies: list[str],
        email_address: str = os.environ['EMAIL'],
        pw: str = os.environ['PASSWORD']
) -> list[str]:

    # Go to login page:
    driver = webdriver.Chrome()
    driver.get('https://www.linkedin.com/login')

    if not email_address or not pw:
        raise ValueError("Email address and password must be provided.")

    # Log in to LinkedIn:
    email = driver.find_element(By.ID, "username")
    email.send_keys(email_address)
    password = driver.find_element(By.ID, "password")
    password.send_keys(pw)
    password.submit()

    company_list = []

    for c in companies:
        try:
            sleep(0.5)
            url = f"https://www.linkedin.com/jobs/"
            driver.get(url)
            sleep(0.25)
            company_list = read_all_pages(company_list, driver, c)
        except Exception:
            print(f"Error with company {c}")

    driver.quit()
    return company_list