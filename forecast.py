import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
import os

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────
merged = pd.read_csv("merged_data.csv")
merged = merged.sort_values("Quarter").reset_index(drop=True)

os.makedirs("outputs/charts", exist_ok=True)
sns.set_theme(style="darkgrid")
plt.rcParams["figure.dpi"] = 150

# ─────────────────────────────────────────────
# Aggregate across all channels by quarter
# ─────────────────────────────────────────────
agg = merged.groupby("Quarter").agg(
    avg_views=("avg_views", "mean"),
    backlash_ratio=("backlash_ratio", "mean")
).reset_index().sort_values("Quarter").reset_index(drop=True)

# Filter to 2019 onwards for cleaner forecasting
agg = agg[agg["Quarter"] >= "2019Q1"].reset_index(drop=True)

# ─────────────────────────────────────────────
# Chart 9 — View Count Forecast (ARIMA)
# ─────────────────────────────────────────────
views_series = agg["avg_views"].values
quarters = agg["Quarter"].tolist()

# Fit ARIMA model
model = ARIMA(views_series, order=(2, 1, 2))
fit = model.fit()

# Forecast 6 quarters ahead (~18 months)
forecast_steps = 6
forecast = fit.get_forecast(steps=forecast_steps)
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int(alpha=0.2)

# Generate future quarter labels
last_quarter = pd.Period(quarters[-1], freq="Q")
future_quarters = [str(last_quarter + i) for i in range(1, forecast_steps + 1)]

fig, ax = plt.subplots(figsize=(16, 6))

# Historical
ax.plot(range(len(quarters)), views_series, color="tomato", marker="o",
        linewidth=2, markersize=4, label="Historical Avg Views")

# Forecast
forecast_x = range(len(quarters), len(quarters) + forecast_steps)
ax.plot(forecast_x, forecast_mean, color="darkred", marker="o",
        linewidth=2, markersize=4, linestyle="--", label="Forecast")
ax.fill_between(forecast_x, forecast_ci[:, 0], forecast_ci[:, 1],
                alpha=0.2, color="darkred", label="80% Confidence Interval")

# Labels
all_labels = quarters + future_quarters
step = max(1, len(all_labels) // 20)
ax.set_xticks(range(0, len(all_labels), step))
ax.set_xticklabels(all_labels[::step], rotation=45, ha="right", fontsize=7)
ax.axvline(len(quarters) - 1, color="gray", linestyle=":", linewidth=1.5, label="Forecast Start")
ax.set_xlabel("Quarter")
ax.set_ylabel("Average View Count")
ax.set_title("View Count Forecast — Next 6 Quarters (ARIMA)\nAll Channels Combined", fontsize=13)
ax.legend()
plt.tight_layout()
plt.savefig("outputs/charts/09_view_forecast.png")
plt.close()
print("Chart 9 saved.")

# ─────────────────────────────────────────────
# Chart 10 — Backlash Ratio Forecast
# ─────────────────────────────────────────────
backlash_series = agg["backlash_ratio"].values

model_b = ARIMA(backlash_series, order=(1, 1, 1))
fit_b = model_b.fit()

forecast_b = fit_b.get_forecast(steps=forecast_steps)
forecast_b_mean = forecast_b.predicted_mean
forecast_b_ci = forecast_b.conf_int(alpha=0.2)

fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(range(len(quarters)), backlash_series, color="steelblue", marker="o",
        linewidth=2, markersize=4, label="Historical Backlash Ratio")
ax.plot(forecast_x, forecast_b_mean, color="darkblue", marker="o",
        linewidth=2, markersize=4, linestyle="--", label="Forecast")
ax.fill_between(forecast_x, forecast_b_ci[:, 0], forecast_b_ci[:, 1],
                alpha=0.2, color="darkblue", label="80% Confidence Interval")

ax.set_xticks(range(0, len(all_labels), step))
ax.set_xticklabels(all_labels[::step], rotation=45, ha="right", fontsize=7)
ax.axvline(len(quarters) - 1, color="gray", linestyle=":", linewidth=1.5, label="Forecast Start")
ax.set_xlabel("Quarter")
ax.set_ylabel("Backlash Ratio")
ax.set_title("Backlash Ratio Forecast — Next 6 Quarters (ARIMA)\nAll Channels Combined", fontsize=13)
ax.legend()
plt.tight_layout()
plt.savefig("outputs/charts/10_backlash_forecast.png")
plt.close()
print("Chart 10 saved.")

# ─────────────────────────────────────────────
# Chart 11 — Per Channel View Trend with Forecast
# ─────────────────────────────────────────────
channels = merged["Channel Name"].unique()
fig, axes = plt.subplots(4, 4, figsize=(24, 16))
axes = axes.flatten()

for i, channel in enumerate(channels):
    ch = merged[merged["Channel Name"] == channel].sort_values("Quarter").reset_index(drop=True)
    ch = ch[ch["Quarter"] >= "2019Q1"]

    if len(ch) < 8:
        axes[i].set_visible(False)
        continue

    views = ch["avg_views"].values
    q_labels = ch["Quarter"].tolist()

    try:
        m = ARIMA(views, order=(1, 1, 1))
        f = m.fit()
        fc = f.get_forecast(steps=4)
        fc_mean = fc.predicted_mean
        fc_ci = fc.conf_int(alpha=0.2)
        future_q = [str(pd.Period(q_labels[-1], freq="Q") + j) for j in range(1, 5)]

        axes[i].plot(range(len(views)), views, color="tomato",
                     linewidth=1.5, markersize=2, marker="o")
        fc_x = range(len(views), len(views) + 4)
        axes[i].plot(fc_x, fc_mean, color="darkred",
                     linewidth=1.5, linestyle="--", marker="o", markersize=2)
        axes[i].fill_between(fc_x, fc_ci[:, 0], fc_ci[:, 1],
                             alpha=0.2, color="darkred")
        axes[i].axvline(len(views) - 1, color="gray", linestyle=":", linewidth=1)

        all_q = q_labels + future_q
        step_q = max(1, len(all_q) // 6)
        axes[i].set_xticks(range(0, len(all_q), step_q))
        axes[i].set_xticklabels(all_q[::step_q], rotation=45, ha="right", fontsize=6)
        axes[i].set_title(channel, fontsize=9)
        axes[i].set_ylabel("Avg Views", fontsize=7)

    except Exception as e:
        axes[i].set_title(f"{channel} (error)", fontsize=9)

# Hide unused subplots
for j in range(len(channels), len(axes)):
    axes[j].set_visible(False)

plt.suptitle("Per Channel View Count Forecast — Next 4 Quarters", fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig("outputs/charts/11_per_channel_forecast.png", bbox_inches="tight")
plt.close()
print("Chart 11 saved.")

# ─────────────────────────────────────────────
# Print forecast summary
# ─────────────────────────────────────────────
print("\n── View Count Forecast Summary ──")
print(f"Last known quarter: {quarters[-1]} — Avg Views: {int(views_series[-1]):,}")
print("\nForecasted avg views:")
for q, v in zip(future_quarters, forecast_mean):
    print(f"  {q}: {int(v):,}")

print("\n── Backlash Ratio Forecast Summary ──")
print(f"Last known quarter: {quarters[-1]} — Backlash Ratio: {backlash_series[-1]:.4f}")
print("\nForecasted backlash ratio:")
for q, v in zip(future_quarters, forecast_b_mean):
    print(f"  {q}: {v:.4f}")