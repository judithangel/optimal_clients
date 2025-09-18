import streamlit as st
import pandas as pd
import os
from utils.data_chunks import scrape_chunks
from utils.xing_scraper import scraper
from utils.data_cleaning import clean_data, preprocess_company_list, preprocess_scraped_data
from utils.ml_functions import kmeans_clustering, plot_clusters_3d, plot_clusters_2d

st.set_page_config(
    page_title="find(IQ) potential customers",
    page_icon="📞",
    layout="wide"
)

st.title("find(IQ) potential customers")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Update company data", "View company data", "Clustering", "Visualisation"])

with tab1:
    # Current customers
    st.write("Data for the current customers is saved in an Excel file. You can update this data by uploading a new file.")
    current_customers = pd.read_excel('data/customers/Active_Accounts_with_revenue.xlsx')
    if st.button("Update current customers"):
        uploaded_customers = st.file_uploader("Choose an Excel file with current customers", type=["xlsx"])
        if uploaded_customers is not None:
            current_customers = pd.read_excel(uploaded_customers, header=1)
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            current_customers.to_excel(f'data/customers/Active_Accounts_with_revenue_{timestamp}.xlsx', index=False)
            st.success("Customer data updated.")
        else:
            st.write("Please upload an Excel file to proceed.")

    # List of companies to scrape
    st.write("You can either upload a new list of companies or use an existing one.")
    use_existing_file = st.selectbox(
        "Please choose an option",
        options=["Use existing list of companies", "Upload new list of companies"])
    if use_existing_file == "Upload new list of companies":
        st.write("In this case you need to scrape data from Xing, which might take a while.")
        file = st.file_uploader("Choose an Excel file", type=["xlsx"])
        if file is None:
            st.write("Please upload an Excel file to proceed.")
        else:
            df_company_data = pd.read_excel(file, header=1)
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            file_path = f'data/company_data/company_data_{timestamp}.xlsx'
            df_company_data.to_excel(file_path, index=False)
            st.success(f"File uploaded and saved to {file_path}")
    elif use_existing_file == "Use existing list of companies":
        st.write("Choose the excel file you want to use.")
        filenames = os.listdir("data/company_data/")
        xlsx_files = [f for f in filenames if f.endswith('.xlsx')]
        filename = st.selectbox("Select a file", xlsx_files)
        df_company_data = pd.read_excel(f'data/company_data/{filename}', header=1)
        if f"xing_data_{filename}" in os.listdir("data/scraped_data/"):
            st.success(
                f"Scraped data for {filename} is available. \n\nIf you want to update the scraped data, please click the button below. "
                + "Updating might take a while.")
        else:
            st.warning(f"No scraped data for {filename} available")

        path_scraped = f'data/scraped_data/xing_data_{filename}'

    df_company_data = preprocess_company_list(df_company_data, current_customers)

    # Scraping
    if st.button("Scrape data from Xing", help=f"Estimated time to scrape: {len(df_company_data)/100*3.2:.0f} minutes."):
        st.write("Company data will be scraped and saved.")
        scrape_chunks(df_company_data, scraper, path_scraped, 100)
        st.success(f"Company data scraped and saved to {path_scraped}")
    try:
        df_xing_orig = pd.read_excel(path_scraped)
        df_xing = preprocess_scraped_data(df_xing_orig, current_customers)
    except FileNotFoundError:
        st.stop()
    intersection = list(set(df_company_data["lowercase_company"].tolist()).intersection(set(df_xing["lowercase_company"].unique().tolist())))
    df_company_data["Service technician ads"] = 0
    for c in intersection:
        df_company_data.loc[df_company_data["lowercase_company"] == c, "Service technician ads"] = df_xing.loc[df_xing["lowercase_company"] == c, "count"].values[0]
    company_data_selection = df_company_data[df_company_data["Service technician ads"] > 0]
    company_data_selection["Ads per 100 employees"] = company_data_selection["Service technician ads"] / company_data_selection["Employees"] * 100
    company_data_selection = company_data_selection.sort_values(by="Ads per 100 employees", ascending=False).reset_index(drop=True)
    st.write(f"Number of companies with service technician ads: {len(company_data_selection)} \n\n You can view these companies in the 'View company data' tab.")
    df_rest = df_xing_orig[~df_xing_orig["lowercase_company"].isin(intersection)]

with tab2:
    st.subheader("Selection from list of companies  (🔜 📞)")
    st.write("These are the companies out of the excel list that have job advertisements for service technicians or similar positions on Xing.")
    st.dataframe(company_data_selection[["Company", "Annual Revenue (USD)", "Employees", "Industry", "Service technician ads", "Ads per 100 employees"]])
    if st.button("Show additional companies"):
        st.subheader("Additional companies from scraped data")
        st.write("These are the companies that have job advertisements for service technicians or similar positions on Xing but are not included in the excel file of companies.")
        st.dataframe(df_rest[["Company", "count"]].sort_values(by="count", ascending=False).reset_index(drop=True))

with tab3:
    n_clusters = st.selectbox("Select number of clusters", options=[2, 3, 4, 5], index=1)
    if st.button("Perform clustering"):
        st.write("Clustering will be performed on the existing data.")

with tab4:

    st.write("Visualisation of the company data.")
    df_joined = pd.concat([
        company_data_selection[["Company", "Annual Revenue (USD)", "Employees", "Industry"]],
        current_customers[["Company", "Annual Revenue (USD)", "Employees", "Industry"]]
        ], ignore_index=True)
    df_joined["Current customer"] = ["No"] * len(company_data_selection) + ["Yes"] * len(current_customers)

    # Restliche Firmen vom Scraping:
    df_rest = df_xing[~df_xing["lowercase_company"].isin(intersection)]
