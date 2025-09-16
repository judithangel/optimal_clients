import pandas as pd
from collections.abc import Callable
from utils.data_cleaning import clean_data

def scrape_chunks(companies_df: pd.DataFrame, scraper: Callable, path: str, chunk_size: int = 100):
    """
    Scrape data in chunks to manage large lists of companies.

    Args:
        companies (pd.DataFrame): DataFrame containing company names to scrape.
        chunk_size (int): Number of companies to process in each chunk.
        scraper_function (callable): The scraping function to use.

    """
    df = clean_data(companies_df)
    companies = df['Account Name'].sort_values().tolist()
    company_chunks = [companies[i:i + chunk_size] for i in range(0, len(companies), chunk_size)]

    for i in range(len(company_chunks)):
        company_list = scraper(company_chunks[i])

        df_companies = pd.DataFrame(company_list, columns=['company'])
        df_counts = df_companies["company"].value_counts().sort_index().reset_index()

        # Save scraped data to Excel
        try:
            df_counts_start = pd.read_excel(path)
            df_concatenated = pd.concat([df_counts_start, df_counts])
            df_concatenated.to_excel(path, index=False)
        except FileNotFoundError:
            df_counts.to_excel(path, index=False)
        print(f"Chunk {i+1}/{len(company_chunks)} processed and saved.")
