from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
from scipy.spatial.distance import squareform


OUTPUT = Path(__file__).resolve().parent / "analysis_output"
CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]


def main():
    df = pd.read_csv(OUTPUT / "fx_daily_log_returns_2010_2025.csv")
    values = df[CURRENCIES]
    if not np.isfinite(values.to_numpy()).all() or (values.std() == 0).any():
        raise ValueError("Returns must be finite and nonconstant.")
    correlation = values.corr()
    # Positive correlation gives a small distance; negative correlation does not.
    distance = np.sqrt(np.clip(2 * (1 - correlation.to_numpy()), 0, 4))
    np.fill_diagonal(distance, 0)
    tree = linkage(squareform(distance, checks=True), method="average")
    pd.DataFrame(distance, index=CURRENCIES, columns=CURRENCIES).to_csv(
        OUTPUT / "currency_correlation_distances.csv", index_label="currency",
        float_format="%.9f"
    )
    pd.DataFrame(tree, columns=["left_node", "right_node", "distance", "size"]).to_csv(
        OUTPUT / "currency_cluster_linkage.csv", index=False, float_format="%.9f"
    )
    # Multiple cuts illustrate sensitivity; no optimal cluster count is claimed.
    assignments = pd.DataFrame({"currency": CURRENCIES})
    for k in [2, 3, 4]:
        assignments[f"cluster_k{k}"] = cut_tree(tree, n_clusters=k).ravel() + 1
    assignments.to_csv(OUTPUT / "currency_cluster_assignments.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    dendrogram(tree, labels=CURRENCIES, color_threshold=0, above_threshold_color="steelblue", ax=ax)
    ax.set_title("Currency Clustering from Daily Log Changes, 2010–2025\nAverage linkage; all exchange rates quoted per EUR")
    ax.set_ylabel("Merge distance (average pairwise correlation distance)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT / "figures" / "currency_clustering_dendrogram.png", dpi=300)
    plt.close(fig)
    print(assignments.to_string(index=False))
    print("\nExploratory partitions only; cluster labels do not indicate rank.")


if __name__ == "__main__":
    main()
