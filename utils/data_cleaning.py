import pandas as pd
import Levenshtein as lev


def keep_latest_entries(df, account_names):
    for account_name in account_names:
        filtered_df = df[df['Account Name'] == account_name]
        indices_to_drop = filtered_df[filtered_df["Last Modified Date"] < filtered_df["Last Modified Date"].max()].index
        df = df.drop(index=indices_to_drop)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the input DataFrame by handling missing values and removing duplicates.

    Parameters:
    df (pd.DataFrame): The input DataFrame to be cleaned.

    Returns:
    pd.DataFrame: The cleaned DataFrame.
    """
    # Drop duplicate rows
    df = df.drop_duplicates()

    # Fill missing values with the mean of the column
    for column in df.select_dtypes(include=['number']).columns:
        df.fillna({column: df[column].mean()}, inplace=True)

    # Change data type of "Last Modified Date" to datetime
    df.loc[:, "Last Modified Date"] = pd.to_datetime(df["Last Modified Date"])

    # For all account names that are duplicated, keep only the latest entry based on "Last Modified Date"
    account_names = df['Account Name'].value_counts()
    account_names_duplicated = account_names.loc[account_names > 1].index
    account_names_duplicated.to_list()  
    df = keep_latest_entries(df, account_names_duplicated)

    return df

def clean_company_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the company names in the DataFrame.
    The new column 'lowercase_company' is created, which contains the cleaned and lowercased company names without suffixes.
    """
    df.drop_duplicates(inplace=True)
    df["Company"] = df["Company"].str.strip()
    df["Company"] = df["Company"].str.replace('Jetzt bewerben Drucken', '')
    df.sort_values(by='Company', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["lowercase_company"] = df["Company"].str.lower()
    df["lowercase_company"] = df["lowercase_company"].str.replace(
        r'\s(g?mbh|gmbh \&?\+? co kg|gmbh \&?\+? co. kg|se \&?\+? co. kg|ag|kg|ug|e.k.|e.v.|ohg|gbr|partg|partg mbb|kgaa|se|sce|ggmbh|gug|gag|gkg|eg|kgaa|gbr|llc|ltd.|ltd|inc.|inc|corp.|corp|plc|co. ltd.|co. kg|co kg|co.)*$', '', regex=True)
    df["lowercase_company"] = df["lowercase_company"].str.replace(r'\&|\+\s?$', '', regex=True)
    df["lowercase_company"] = df["lowercase_company"].str.replace("˚", "grad")

    return df

def join_entries_for_same_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Joins entries for the same companies based on the 'lowercase_company' column.
    If two consecutive entries have a Levenshtein distance of less than 2, they are considered the same company.
    The values of numerical columns are summed for these entries.
    """
    # Sort by lowercase company name
    df.sort_values(by='lowercase_company', inplace=True)
    df.reset_index(drop=True, inplace=True)
    # Measure distance between company names:
    df["lowercase_company_shifted"] = df["lowercase_company"].shift(-1)
    df["company_name_distance"] = df.apply(
        lambda x: lev.distance(x["lowercase_company"], x["lowercase_company_shifted"]) if x["lowercase_company_shifted"] is not None else None,
        axis=1)
    # Find indices where distance is less than 2 and replace following company name with representative:
    prev_same = False
    for i in df.index:
        if df["company_name_distance"].iloc[i] < 2:
            if prev_same == False:
                group_name = df["lowercase_company"].iloc[i]
                df.loc[i+1, "lowercase_company"] = group_name
            else:
                df.loc[i+1, "lowercase_company"] = group_name
            prev_same = True
        else:
            prev_same = False
    df.drop(columns=["lowercase_company_shifted", "company_name_distance"], inplace=True)
    df = df.groupby("lowercase_company")["count"].sum().reset_index()

    return df

def remove_outliers(df: pd.DataFrame, current_customers: pd.DataFrame) -> pd.DataFrame:
    """
    Removes outliers from the DataFrame based on current customers.

    Parameters:
    df (pd.DataFrame): The input DataFrame.

    Returns:
    pd.DataFrame: The DataFrame with outliers removed.
    """
    R_Q1 = current_customers["Annual Revenue (USD)"].quantile(0.25)
    R_Q3 = current_customers["Annual Revenue (USD)"].quantile(0.75)
    R_min = current_customers["Annual Revenue (USD)"].min()
    R_max = current_customers["Annual Revenue (USD)"].max()
    R_IQR = R_Q3 - R_Q1
    # Use minimum and maximum for lower/upper bounds as the number of current customers is small
    R_lower_bound = R_min - 1.5 * R_IQR
    R_upper_bound = R_max + 1.5 * R_IQR
    filter_rev = (df["Annual Revenue (USD)"] >= R_lower_bound) & (df["Annual Revenue (USD)"] <= R_upper_bound)
    E_Q1 = current_customers["Employees"].quantile(0.25)
    E_Q3 = current_customers["Employees"].quantile(0.75)  # Compute bounds based on current customers
    E_max = current_customers["Employees"].max()
    E_IQR = E_Q3 - E_Q1
    # Lower bound for Employees is set to 10 to exclude very small companies
    E_lower_bound = 10
    E_upper_bound = E_max + 1.5 * E_IQR
    filter_emp = (df["Employees"] >= E_lower_bound) & (df["Employees"] <= E_upper_bound)
    df_non_outliers = df[filter_rev & filter_emp]
    return df_non_outliers

def preprocess_scraped_data(df: pd.DataFrame, current_customers: pd.DataFrame) -> pd.DataFrame:

    df = clean_company_names(df)
    df = join_entries_for_same_companies(df)
    return df

def preprocess_company_list(df: pd.DataFrame, current_customers: pd.DataFrame) -> pd.DataFrame:

    df = clean_data(df)
    df.rename(columns={"Account Name": "Company"}, inplace=True)
    df = clean_company_names(df)
    df["Annual Revenue (USD)"] = df["Annual Revenue"].copy()
    df["Annual Revenue (USD)"] = df.apply(_to_usd, axis=1)
    df = remove_outliers(df, current_customers)
    return df

def _to_usd(row):
    if row["Annual Revenue Currency"] == "EUR":
        return int(row["Annual Revenue"] * 1.18)  # Approx. conversion rate
    else:
        return row["Annual Revenue"]