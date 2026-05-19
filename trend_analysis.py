import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import os

# ─────────────────────────────────────────────
# Load & Merge Data
# ─────────────────────────────────────────────
videos = pd.read_csv("videos.csv")
sentiment = pd.read_csv("sentiment_scores.csv")

videos["Publish Date"] = pd.to_datetime(videos["Publish Date"])
videos["View Count"] = pd.to_numeric(videos["View Count"], errors="coerce")
videos["Quarter"] = pd.PeriodIndex(pd.to_datetime(videos["Publish Date"]).dt.to_period("Q").astype(str), freq="Q")

# Average views per channel per quarter (top 5 sampled)
avg_views = (
    videos.sort_values("View Count", ascending=False)
    .groupby(["Channel Name", videos["Publish Date"].dt.to_period("Q").astype(str)])
    .head(5)
    .groupby(["Channel Name", videos["Publish Date"].dt.to_period("Q").astype(str)])["View Count"]
    .mean()
    .reset_index()
)
avg_views.columns = ["Channel Name", "Quarter", "avg_views"]

# Merge with sentiment
merged = pd.merge(avg_views, sentiment, on=["Channel Name", "Quarter"])
merged = merged.sort_values(["Channel Name", "Quarter"]).reset_index(drop=True)

merged.to_csv("merged_data.csv", index=False)
print(f"Merged dataset: {len(merged)} channel-quarter rows")

os.makedirs("outputs/charts", exist_ok=True)
sns.set_theme(style="darkgrid")
plt.rcParams["figure.dpi"] = 150

# ─────────────────────────────────────────────
# Chart 5 — Backlash Ratio vs Avg Views Over Time (Aggregated)
# ─────────────────────────────────────────────
agg = merged.groupby("Quarter").agg(
    avg_views=("avg_views", "mean"),
    backlash_ratio=("backlash_ratio", "mean")
).reset_index().sort_values("Quarter")

fig, ax1 = plt.subplots(figsize=(16, 6))

ax1.set_xlabel("Quarter")
ax1.set_ylabel("Average View Count", color="tomato")
ax1.plot(agg["Quarter"], agg["avg_views"], color="tomato", marker="o",
         linewidth=2, markersize=4, label="Avg Views")
ax1.tick_params(axis="y", labelcolor="tomato")

ax2 = ax1.twinx()
ax2.set_ylabel("Backlash Ratio", color="steelblue")
ax2.plot(agg["Quarter"], agg["backlash_ratio"], color="steelblue", marker="s",
         linewidth=2, markersize=4, linestyle="--", label="Backlash Ratio")
ax2.tick_params(axis="y", labelcolor="steelblue")

step = max(1, len(agg) // 20)
ax1.set_xticks(range(0, len(agg), step))
ax1.set_xticklabels(agg["Quarter"].iloc[::step], rotation=45, ha="right", fontsize=7)

plt.title("Avg View Count vs Backlash Ratio Over Time — All Channels Combined", fontsize=13)
fig.tight_layout()
plt.savefig("outputs/charts/05_views_vs_backlash.png")
plt.close()
print("Chart 5 saved.")

# ─────────────────────────────────────────────
# Chart 6 — Backlash Breakdown by Signal Type Over Time
# ─────────────────────────────────────────────
signal_agg = merged.groupby("Quarter").agg(
    fake_ratio=("fake_ratio", "mean"),
    fatigue_ratio=("fatigue_ratio", "mean"),
    callout_ratio=("callout_ratio", "mean"),
    out_of_touch_ratio=("out_of_touch_ratio", "mean")
).reset_index().sort_values("Quarter")

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(signal_agg["Quarter"], signal_agg["fake_ratio"],
        marker="o", label="Fake/Scripted", linewidth=2, markersize=3)
ax.plot(signal_agg["Quarter"], signal_agg["fatigue_ratio"],
        marker="s", label="Fatigue", linewidth=2, markersize=3)
ax.plot(signal_agg["Quarter"], signal_agg["callout_ratio"],
        marker="^", label="Creator Callout", linewidth=2, markersize=3)
ax.plot(signal_agg["Quarter"], signal_agg["out_of_touch_ratio"],
        marker="D", label="Out of Touch", linewidth=2, markersize=3)

step = max(1, len(signal_agg) // 20)
ax.set_xticks(range(0, len(signal_agg), step))
ax.set_xticklabels(signal_agg["Quarter"].iloc[::step], rotation=45, ha="right", fontsize=7)
ax.set_xlabel("Quarter")
ax.set_ylabel("Signal Ratio")
ax.set_title("Backlash Signal Breakdown Over Time — All Channels Combined", fontsize=13)
ax.legend()
plt.tight_layout()
plt.savefig("outputs/charts/06_backlash_breakdown.png")
plt.close()
print("Chart 6 saved.")

# ─────────────────────────────────────────────
# Chart 7 — Per Channel Backlash Ratio Heatmap
# ─────────────────────────────────────────────
pivot = merged.pivot_table(
    index="Channel Name",
    columns="Quarter",
    values="backlash_ratio"
)

# Keep only quarters from 2019 onwards for readability
pivot = pivot[[c for c in pivot.columns if c >= "2019Q1"]]

fig, ax = plt.subplots(figsize=(20, 8))
sns.heatmap(pivot, cmap="RdYlGn_r", ax=ax, linewidths=0.3,
            cbar_kws={"label": "Backlash Ratio"})
ax.set_title("Backlash Ratio Per Channel Per Quarter\n(Red = high backlash, Green = low)", fontsize=13)
ax.set_xlabel("Quarter")
ax.set_ylabel("Channel")
plt.xticks(rotation=45, ha="right", fontsize=7)
plt.tight_layout()
plt.savefig("outputs/charts/07_backlash_heatmap.png")
plt.close()
print("Chart 7 saved.")

# ─────────────────────────────────────────────
# Chart 8 — Lagged Correlation Analysis
# ─────────────────────────────────────────────
correlations = []

for channel in merged["Channel Name"].unique():
    ch = merged[merged["Channel Name"] == channel].sort_values("Quarter").reset_index(drop=True)

    if len(ch) < 6:
        continue

    for lag in [1, 2, 3]:
        backlash_lagged = ch["backlash_ratio"].iloc[:-lag].values
        views_future = ch["avg_views"].iloc[lag:].values

        if len(backlash_lagged) < 4:
            continue

        r, p = stats.pearsonr(backlash_lagged, views_future)
        correlations.append({
            "Channel": channel,
            "Lag (Quarters)": lag,
            "Pearson r": round(r, 3),
            "p-value": round(p, 3),
            "Significant": "Yes" if p < 0.05 else "No"
        })

corr_df = pd.DataFrame(correlations)
corr_df.to_csv("correlation_results.csv", index=False)

fig, ax = plt.subplots(figsize=(12, 6))
for lag in [1, 2, 3]:
    subset = corr_df[corr_df["Lag (Quarters)"] == lag]
    ax.scatter(subset["Channel"], subset["Pearson r"],
               label=f"Lag {lag}Q", s=80, alpha=0.8)

ax.axhline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Channel")
ax.set_ylabel("Pearson r (backlash → views)")
ax.set_title("Lagged Correlation: Does Backlash Predict Future View Decline?", fontsize=13)
ax.legend()
plt.xticks(rotation=45, ha="right", fontsize=8)
plt.tight_layout()
plt.savefig("outputs/charts/08_lagged_correlation.png")
plt.close()
print("Chart 8 saved.")

print("\nAll charts saved. Summary of correlations:")
print(corr_df.groupby("Lag (Quarters)")[["Pearson r"]].mean())