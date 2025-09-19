import streamlit as st
import pandas as pd
import os
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from utils.data_chunks import scrape_chunks
from utils.xing_scraper import scraper
from utils.data_cleaning import clean_data, preprocess_company_list, preprocess_scraped_data
from utils.ml_functions import kmeans_clustering, plot_clusters_2d, violin_plots

st.set_page_config(
    page_title="find(IQ) potential customers",
    page_icon="📞",
    layout="wide"
)

st.title("find(IQ) potential customers")
st.session_state["file_saved"] = False
st.session_state["continue"] = False
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
            filename = f"company_data_{timestamp}.xlsx"
            file_path = f'data/company_data/{filename}'
            if st.session_state["file_saved"] == False:
                df_company_data.to_excel(file_path, index=False)
                st.session_state["file_saved"] = True
            st.success(f"File uploaded and saved to {file_path}")
    elif use_existing_file == "Use existing list of companies":
        st.write("Choose the excel file you want to use.")
        filenames = os.listdir("data/company_data/")
        xlsx_files = [f for f in filenames if f.endswith('.xlsx')]
        filename = st.selectbox("Select a file", xlsx_files)
        df_company_data = pd.read_excel(f'data/company_data/{filename}', header=1)
        if not "Last Modified Date" in df_company_data.columns:
            df_company_data = pd.read_excel(f'data/company_data/{filename}')
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
        st.session_state["continue"] = True
    except FileNotFoundError:
        st.warning("No scraped data available yet. Please scrape data from Xing.")
    # Find intersection between company data and Xing data
    if st.session_state["continue"]:
        intersection = list(set(df_company_data["lowercase_company"].tolist()).intersection(set(df_xing["lowercase_company"].unique().tolist())))
        df_company_data["Service technician ads"] = 0
        for c in intersection:
            df_company_data.loc[df_company_data["lowercase_company"] == c, "Service technician ads"] = df_xing.loc[df_xing["lowercase_company"] == c, "count"].values[0]
        company_data_selection_orig = df_company_data[df_company_data["Service technician ads"] > 0]
        # Remove companies that are already our customers:
        intersection_current_customers = list(set(company_data_selection_orig["Company"].tolist()).intersection(set(current_customers["Company"].unique().tolist())))
        if len(intersection_current_customers) > 0:
            for c in intersection_current_customers:
                company_data_selection = company_data_selection_orig.drop(company_data_selection_orig[company_data_selection_orig["Company"] == c].index)
        else:
            company_data_selection = company_data_selection_orig.copy()
        # Compute number of job ads per 100 employees:
        df_company_data["Ads per 100 employees"] = df_company_data["Service technician ads"] / df_company_data["Employees"] * 100
        company_data_selection["Ads per 100 employees"] = company_data_selection["Service technician ads"] / company_data_selection["Employees"] * 100
        company_data_selection = company_data_selection.sort_values(by="Ads per 100 employees", ascending=False).reset_index(drop=True)
        st.write(f"Number of companies with service technician ads: {len(company_data_selection)} \n\n You can view these companies in the 'View company data' tab.")
        df_rest = df_xing_orig[~df_xing_orig["lowercase_company"].isin(intersection)]

with tab2:
    if st.session_state["continue"]:
        cols = st.columns(3)
        with cols[0]:
            st.markdown("""In the Venn diagram on the right you can see
    - the number of companies in the excel list (red)
    - the number of companies found on Xing with service technician ads (green)
    - the intersection of both (brown)""")
        with cols[1]:
            venn_fig = plt.figure(figsize=(4,4))
            venn = venn2(
                subsets=(len(df_company_data), len(df_xing), len(company_data_selection_orig)),
                set_labels=('Excel list of companies', 'Xing search'))
            st.pyplot(venn_fig)
        with cols[2]:
            st.write("The table below shows companies in the intersection, where our current customers are already excluded.")
        st.subheader("Selection from list of companies  (🔜 📞)")
        st.write("These are the companies out of the excel list that have job advertisements for service technicians or similar positions on Xing.")
        st.dataframe(company_data_selection[["Company", "Annual Revenue (USD)", "Employees", "Industry", "Service technician ads", "Ads per 100 employees"]])
        if st.button("Show additional companies"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Additional companies from scraped data")
                st.write("These are the companies that have job advertisements for service technicians or similar positions on Xing but are not included in the excel file of companies.")
                st.dataframe(df_rest[["Company", "count"]].sort_values(by="count", ascending=False).reset_index(drop=True))
    else:
        st.warning("Some data is still missing.")

with tab3:
    if st.session_state["continue"]:
        st.subheader("Clustering of companies based on Annual Revenue and Employees")
        cols = st.columns(4)
        with cols[0]:
            n_clusters = st.selectbox("Select number of clusters", options=[2, 3, 4, 5, 6], index=3)
        X = df_company_data[["Annual Revenue (USD)", "Employees"]]
        df_clustered, kmeans, scaler = kmeans_clustering(X, n_clusters=n_clusters)
        df_company_data["Cluster labels"] = df_clustered["Cluster labels"]
        if st.button("Show silhouette score"):
            from sklearn.metrics import silhouette_score
            silhouette_avg = silhouette_score(X, df_clustered["Cluster labels"])
            st.metric("Silhouette Score", f"{silhouette_avg:.2f}")
            st.write(f"A higher silhouette score indicates better-defined clusters, where the "
                    " maximum value is 1 and worst value is -1.")
        # Plot companies with clusters and show current customers as dark crosses
        fig = plot_clusters_2d(df_clustered, kmeans, scaler, current_customers)
        st.plotly_chart(fig, use_container_width=True)

        # Prediction of clusters for current customers
        y_pred = kmeans.predict(scaler.transform(current_customers[["Annual Revenue (USD)", "Employees"]]))
        current_customers["Cluster"] = y_pred
        cluster_counts = current_customers["Cluster"].value_counts().reset_index()
        index = current_customers["Cluster"].value_counts().argmax()
        st.write(f"Most of our customers are in cluster {cluster_counts.loc[index, 'Cluster']}, which contains {cluster_counts.loc[index, 'count']} of our current customers.")
        fig = violin_plots(df_clustered)
        st.plotly_chart(fig, use_container_width=True)
        st.write("The violin plots above show that most of our customers have a relatively low annual revenue and small number of employees.")
        # Top ten companies in chosen cluster:
        st.write("Please choose a cluster number to display the top ten companies out of this cluster with the highest number of job advertisements.")
        cluster_number = st.selectbox("Select cluster number", options=list(range(n_clusters)))
        top_companies = df_company_data[df_company_data["Cluster labels"] == cluster_number].sort_values(by="Ads per 100 employees", ascending=False)
        # Remove companies that are already our customers:
        intersection_current_customers = list(set(top_companies["Company"].tolist()).intersection(set(current_customers["Company"].unique().tolist())))
        if len(intersection_current_customers) > 0:
            for c in intersection_current_customers:
                top_companies = top_companies.drop(top_companies[top_companies["Company"] == c].index)
        st.write(f"Top 10 companies in cluster {cluster_number}:")
        st.dataframe(top_companies[["Company", "Annual Revenue (USD)", "Employees", "Industry", "Service technician ads", "Ads per 100 employees"]].head(10))
    else:
        st.warning("Some data is still missing.")

with tab4:
    if st.session_state["continue"]:
        st.write("Visualisation of the data for our customers and companies which have job advertisements for service technicians or similar positions.")
        df_joined = pd.concat([
            company_data_selection[["Company", "Annual Revenue (USD)", "Employees", "Industry"]],
            current_customers[["Company", "Annual Revenue (USD)", "Employees", "Industry"]]
            ], ignore_index=True)
        df_joined["Current customer"] = ["No"] * len(company_data_selection) + ["Yes"] * len(current_customers)

        fig = px.histogram(df_joined, x="Industry", color="Current customer", title="Industry Distribution").update_xaxes(categoryorder="total descending")
        st.plotly_chart(fig, use_container_width=True)
        st.write("The information on the industry is not included in the clustering as there are too many different industries compared to the number "
                + " of companies. However, it is still interesting to see the distribution of industries among our current customers and the potential customers.")
        fig = px.bar(x=company_data_selection.sort_values(by="Service technician ads", ascending=False)["Company"].head(10),
                     y=company_data_selection.sort_values(by="Service technician ads", ascending=False)["Service technician ads"].head(10),
                     title="Top 10 companies with most service technician ads")
        fig.update_layout(xaxis_title="Company", yaxis_title="Number of service technician ads")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Some data is still missing.")