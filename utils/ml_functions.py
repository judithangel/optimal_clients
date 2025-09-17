import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.express as px

def kmeans_clustering(data: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
    """
    Perform K-Means clustering on the given data.

    Parameters:
    data (DataFrame): The input data for clustering.
    n_clusters (int): The number of clusters to form.

    Returns:
    DataFrame: The input data with an additional column for cluster labels.
    """
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    data = data.copy()  # Avoid SettingWithCopyWarning
    data['Cluster labels'] = kmeans.fit_predict(data_scaled)

    return data

def plot_clusters_3d(df: pd.DataFrame):
    """
    Plot the clusters in a 3D scatter plot.

    Parameters:
    data (DataFrame): The input data with cluster labels.
    """
    df = df.copy()  # Avoid SettingWithCopyWarning
    df["Cluster labels"] = df["Cluster labels"].astype("category")

    # Farbzuordnung (funktioniert leider nicht)
    cluster_colors = {
        0: '#1f77b4',  # Blue
        1: '#ff7f0e',  # Orange
        2: "#024402",  # Green
        3: '#d62728',  # Red
        4: '#9467bd'   # Purple
    }

    fig = px.scatter_3d(
        df,
        x="Annual Revenue (USD)",
        y="Employees",
        z="Ads per 100 employees",
        color="Cluster labels",
        color_discrete_map={str(k): v for k, v in cluster_colors.items()},  # Map on category names
        opacity=0.8,
        title="3D Scatter Plot of Customer Data by Cluster"
    )

    fig.update_traces(marker=dict(size=3))

    # Axis titles + Camera perspective for better readability
    fig.update_layout(
        scene=dict(
            xaxis_title="Annual Revenue",
            yaxis_title="Employees",
            zaxis_title="Ads per 100 employees"
        ),
        scene_camera=dict(eye=dict(x=1.8, y=1.8, z=1.2)),
        legend_title_text="Cluster labels"
    )
    return fig

def plot_clusters_2d(df: pd.DataFrame):
    """
    Plot the clusters in a 2D scatter plot.

    Parameters:
    data (DataFrame): The input data with cluster labels.
    """
    df = df.copy()  # Avoid SettingWithCopyWarning
    df["Cluster labels"] = df["Cluster labels"].astype("category")

    # Farbzuordnung (funktioniert leider nicht)
    cluster_colors = {
        0: '#1f77b4',  # Blue
        1: '#ff7f0e',  # Orange
        2: "#024402",  # Green
        3: '#d62728',  # Red
        4: '#9467bd'   # Purple
    }

    fig = px.scatter(
        df,
        x="Annual Revenue (USD)",
        y="Employees",
        color="Cluster labels",
        color_discrete_map={str(k): v for k, v in cluster_colors.items()},  # Map on category names
        opacity=0.7,
        title="2D Scatter Plot of Customer Data by Cluster"
    )

    fig.update_traces(marker=dict(size=4))

    # Axis titles + Camera perspective for better readability
    fig.update_layout(
        scene=dict(
            xaxis_title="Annual Revenue",
            yaxis_title="Employees"
        ),
        legend_title_text="Cluster labels"
    )
    return fig
    