import pandas as pd


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
    df["Last Modified Date"] = pd.to_datetime(df["Last Modified Date"])

    # For all account names that are duplicated, keep only the latest entry based on "Last Modified Date"
    account_names = df['Account Name'].value_counts()
    account_names_duplicated = account_names.loc[account_names > 1].index
    account_names_duplicated.to_list()  
    df = keep_latest_entries(df, account_names_duplicated)

    return df