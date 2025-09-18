import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

    return data, kmeans, scaler


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

def plot_clusters_2d(df, kmeans, scaler, current_customers):
    """
    Plot the clusters in a 2D scatter plot.

    Parameters:
    data (DataFrame): The input data with cluster labels.
    """
    df = df.copy()  # Avoid SettingWithCopyWarning
    df["Cluster labels"] = df["Cluster labels"].astype("category")
    n = kmeans.n_clusters

    x_min, x_max = df["Annual Revenue (USD)"].min(), df["Annual Revenue (USD)"].max()
    y_min, y_max = df["Employees"].min(), df["Employees"].max()

    # Grid for Decision Boundaries:
    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, 300),
        np.linspace(y_min, y_max, 300)
    )
    mesh_data = np.c_[xx.ravel(), yy.ravel()]
    mesh_data_scaled = scaler.transform(mesh_data)
    Z = kmeans.predict(mesh_data_scaled).reshape(xx.shape)

    # Cluster colors in rgb format:
    cluster_colors = [
        "rgb(0, 114, 178)",
        "rgb(213, 94, 0)",
        "rgb(0, 158, 115)",
        "rgb(204, 121, 167)",
        "rgb(240, 228, 66)",
        "rgb(127, 127, 127)"
    ]
    colorscale = [[i, col] for i, col in zip(np.linspace(0, 1, n), cluster_colors[:n])]
    # [
    #     [0, "rgb(0, 114, 178)"],      # Cluster 0
    #     [0.25, "rgb(213, 94, 0)"],    # Cluster 1
    #     [0.5, "rgb(0, 158, 115)"],    # Cluster 2
    #     [0.75, "rgb(204, 121, 167)"], # Cluster 3
    #     [1, "rgb(240, 228, 66)"]      # Cluster 4
    # ]
   

    fig = go.Figure()

    # Show the decision boundaries as background:
    fig.add_trace(go.Contour(
        x=np.linspace(x_min, x_max, 300),
        y=np.linspace(y_min, y_max, 300),
        z=Z,
        showscale=False,
        colorscale=colorscale[:n],
        opacity=0.2,
        contours=dict(showlines=False)
    ))

    # Clusterpunkte:
    fig.add_trace(go.Scatter(
        x=df["Annual Revenue (USD)"],
        y=df["Employees"],
        mode='markers',
        marker=dict(
            color=df["Cluster labels"],
            colorscale=colorscale,
            size=5,
            opacity=0.7
        ),
        showlegend=False
    ))
    # Plot legend for clusters
    for i in range(n):
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=5, color=colorscale[i][1]),
            name=f"Cluster {i}"
        ))

    # Current customers as black crosses
    fig.add_trace(go.Scatter(
        x=current_customers["Annual Revenue (USD)"],
        y=current_customers["Employees"],
        mode='markers',
        marker=dict(color="#6C6B6B", size=10, symbol='x'),
        name='Current customers'
    ))

    fig.update_layout(
        title="2D Scatter Plot with Cluster Boundaries",
        xaxis_title="Annual Revenue (USD)",
        yaxis_title="Employees"
    )
    return fig
    