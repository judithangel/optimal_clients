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
    df["company"] = df["company"].str.strip()
    df["company"] = df["company"].str.replace('Jetzt bewerben Drucken', '')
    df.sort_values(by='company', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["lowercase_company"] = df["company"].str.lower()
    df["lowercase_company"] = df["lowercase_company"].str.replace(
        r'\s(g?mbh|gmbh \& co kg|gmbh \&?\+? co. kg|se \&?\+? co. kg|ag|kg|ug|e.k.|e.v.|ohg|gbr|partg|partg mbb|kgaa|se|sce|ggmbh|gug|gag|gkg|eg|kgaa|gbr|llc|ltd.|ltd|inc.|inc|corp.|corp|plc|co. ltd.|co. kg|co kg|co.)*$', '', regex=True)
    df["lowercase_company"] = df["lowercase_company"].str.replace(r'\&|\+\s?$', '', regex=True)
    df["lowercase_company"] = df["lowercase_company"].str.replace("˚", "grad")

    return df

def join_entries_for_same_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Joins entries for the same companies based on the 'lowercase_company' column.
    If two consecutive entries have a Levenshtein distance of less than 2, they are considered the same company.
    The values of numerical columns are summed for these entries.
    """
    # Measure distance between company names:
    df["lowercase_company_shifted"] = df["lowercase_company"].shift(-1)
    df["company_name_distance"] = df.apply(
        lambda x: lev.distance(x["lowercase_company"], x["lowercase_company_shifted"]) if x["lowercase_company_shifted"] is not None else None,
        axis=1)
    # Find indices where distance is less than 2 and replace company name with the next one:
    filter = df["company_name_distance"] < 2
    indices = df.loc[filter, "company"].index
    df.loc[indices, "company"] = df.loc[indices + 1, "company"]
    df.loc[indices, "lowercase_company"] = df.loc[indices + 1, "lowercase_company"]
    df.drop(columns=["lowercase_company_shifted", "company_name_distance"], inplace=True)
    # Add corresponding number of job ads:
    df = df.groupby("company").sum().reset_index()

    return df