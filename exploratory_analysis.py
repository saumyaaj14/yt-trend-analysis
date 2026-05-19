import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
df = pd.read_csv("videos.csv")

# Convert types
df["Publish Date"] = pd.to_datetime(df["Publish Date"])
df["View Count"] = pd.to_numeric(df["View Count"], errors="coerce")
df["Quarter"] = df["Publish Date"].dt.to_period("Q")

# Filter to relevant date range only
df = df[df["Publish Date"].dt.year >= 2013]

# Create output folder
os.makedirs("outputs/charts", exist_ok=True)

# Style
sns.set_theme(style="darkgrid")
plt.rcParams["figure.dpi"] = 150

# ─────────────────────────────────────────────
# Plot 1 — Total Videos Per Channel
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
channel_counts = df["Channel Name"].value_counts().sort_values()
bars = ax.barh(channel_counts.index, channel_counts.values,
               color=sns.color_palette("muted", len(channel_counts)))
ax.set_xlabel("Total Videos")
ax.set_title("Total Videos Per Channel\n(Why we sample instead of using all 33K videos)", fontsize=13)
for bar, val in zip(bars, channel_counts.values):
    ax.text(bar.get_width() + 20, bar.get_y() + bar.get_height()/2,
            str(val), va="center", fontsize=9)
plt.tight_layout()
plt.savefig("outputs/charts/01_videos_per_channel.png")
plt.close()
print("Chart 1 saved.")

# ─────────────────────────────────────────────
# Plot 2 — Videos Per Quarter Per Channel
# ─────────────────────────────────────────────
quarterly = df.groupby(["Channel Name", "Quarter"]).size().reset_index(name="Video Count")
quarterly["Quarter"] = quarterly["Quarter"].astype(str)

# Sort quarters properly
all_quarters = sorted(quarterly["Quarter"].unique())

fig, ax = plt.subplots(figsize=(16, 7))
for channel in quarterly["Channel Name"].unique():
    ch_data = quarterly[quarterly["Channel Name"] == channel].copy()
    ch_data = ch_data.set_index("Quarter").reindex(all_quarters).reset_index()
    ax.plot(ch_data["Quarter"], ch_data["Video Count"],
            marker="o", label=channel, linewidth=1.5, markersize=3)

ax.set_xlabel("Quarter")
ax.set_ylabel("Number of Videos")
ax.set_title("Videos Uploaded Per Quarter Per Channel\n(Justifies quarterly sampling — upload frequency varies widely)", fontsize=13)
ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)
step = max(1, len(all_quarters) // 20)
ax.set_xticks(range(0, len(all_quarters), step))
ax.set_xticklabels(all_quarters[::step], rotation=45, ha="right", fontsize=7)
plt.tight_layout()
plt.savefig("outputs/charts/02_videos_per_quarter.png")
plt.close()
print("Chart 2 saved.")

# ─────────────────────────────────────────────
# Plot 3 — View Count Distribution
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
views_filtered = df["View Count"].dropna()
views_filtered = views_filtered[views_filtered > 0]
ax.hist(views_filtered, bins=100, color="steelblue", edgecolor="none", log=True)
ax.axvline(views_filtered.quantile(0.95), color="red", linestyle="--",
           label=f"95th percentile ({int(views_filtered.quantile(0.95)):,} views)")
ax.set_xlabel("View Count (log scale)")
ax.set_ylabel("Number of Videos")
ax.set_title("Distribution of View Counts Across All Videos\n(Most videos get low views — top 5 per quarter captures the real signal)", fontsize=13)
ax.legend()
plt.tight_layout()
plt.savefig("outputs/charts/03_view_count_distribution.png")
plt.close()
print("Chart 3 saved.")

# ─────────────────────────────────────────────
# Plot 4 — Average View Count Over Time (All Channels)
# ─────────────────────────────────────────────
quarterly_views = df.groupby("Quarter")["View Count"].mean().reset_index()
quarterly_views = quarterly_views.sort_values("Quarter")
quarterly_views["Quarter"] = quarterly_views["Quarter"].astype(str)

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(quarterly_views["Quarter"], quarterly_views["View Count"],
        color="tomato", marker="o", linewidth=2, markersize=4)
ax.fill_between(range(len(quarterly_views)), quarterly_views["View Count"],
                alpha=0.1, color="tomato")
step = max(1, len(quarterly_views) // 20)
ax.set_xticks(range(0, len(quarterly_views), step))
ax.set_xticklabels(quarterly_views["Quarter"].iloc[::step], rotation=45, ha="right", fontsize=7)
ax.set_xlabel("Quarter")
ax.set_ylabel("Average View Count")
ax.set_title("Average View Count Per Quarter — All Channels Combined\n(Early look at the trend we are testing)", fontsize=13)
plt.tight_layout()
plt.savefig("outputs/charts/04_avg_views_over_time.png")
plt.close()
print("Chart 4 saved.")

print("\nAll 4 charts saved to outputs/charts/")