"""
utils.py — CSV export and matplotlib chart helpers.
"""

import csv
from datetime import datetime
from collections import defaultdict

from matplotlib.figure import Figure


def _get_plt():
    if getattr(_get_plt, "plt", None) is None:
        import matplotlib
        matplotlib.use("TkAgg", force=True)
        import matplotlib.pyplot as plt
        _get_plt.plt = plt
    return _get_plt.plt


def _get_patches():
    if getattr(_get_patches, "mpatches", None) is None:
        import matplotlib.patches as mpatches
        _get_patches.mpatches = mpatches
    return _get_patches.mpatches


# ── Colour palette ──────────────────────────────────────────────────────────
PALETTE = {
    "bg":       "#0F1117",
    "surface":  "#1A1D27",
    "accent":   "#6C63FF",
    "income":   "#2ECC71",
    "expense":  "#E74C3C",
    "text":     "#E8E8F0",
    "subtext":  "#8888AA",
    "border":   "#2A2D3E",
}


def _apply_dark_style(fig: Figure, ax) -> None:
    """Apply consistent dark theme to a matplotlib figure."""
    fig.patch.set_facecolor(PALETTE["surface"])
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["subtext"], labelsize=9)
    ax.xaxis.label.set_color(PALETTE["subtext"])
    ax.yaxis.label.set_color(PALETTE["subtext"])
    ax.title.set_color(PALETTE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["border"])


# ── Charts ───────────────────────────────────────────────────────────────────

def chart_monthly_bar(trend_data: list[dict]) -> Figure:
    """Grouped bar chart: income vs expense by month."""
    months_map: dict[str, dict] = defaultdict(lambda: {"income": 0, "expense": 0})
    for row in trend_data:
        months_map[row["month"]][row["type"]] = row["total"]

    sorted_months = sorted(months_map)[-12:]
    labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in sorted_months]
    incomes  = [months_map[m]["income"]  for m in sorted_months]
    expenses = [months_map[m]["expense"] for m in sorted_months]

    x = range(len(labels))
    width = 0.38

    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([i - width/2 for i in x], incomes,  width, color=PALETTE["income"],
           label="Income",  alpha=0.9, zorder=3)
    ax.bar([i + width/2 for i in x], expenses, width, color=PALETTE["expense"],
           label="Expense", alpha=0.9, zorder=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_title("Monthly Income vs Expense", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Amount (PKR)", fontsize=9)
    ax.yaxis.grid(True, color=PALETTE["border"], linewidth=0.6, zorder=0)
    mpatches = _get_patches()
    ax.legend(
        handles=[
            mpatches.Patch(color=PALETTE["income"],  label="Income"),
            mpatches.Patch(color=PALETTE["expense"], label="Expense"),
        ],
        facecolor=PALETTE["bg"], edgecolor=PALETTE["border"],
        labelcolor=PALETTE["text"], fontsize=9,
    )
    _apply_dark_style(fig, ax)
    fig.tight_layout()
    return fig


def chart_category_donut(by_category: list[dict], type_: str) -> Figure:
    """Donut chart for category breakdown of income or expense."""
    items = [r for r in by_category if r["type"] == type_]
    plt = _get_plt()
    if not items:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                color=PALETTE["subtext"], fontsize=12)
        ax.axis("off")
        _apply_dark_style(fig, ax)
        return fig

    labels = [r["name"] or "Uncategorised" for r in items]
    values = [r["total"] for r in items]
    colors = [r["color"] or PALETTE["accent"] for r in items]

    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        autopct="%1.1f%%",
        pctdistance=0.82,
        startangle=90,
        wedgeprops=dict(width=0.52, edgecolor=PALETTE["surface"], linewidth=2),
    )
    for at in autotexts:
        at.set_color(PALETTE["text"])
        at.set_fontsize(8)

    ax.legend(
        wedges, labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        facecolor=PALETTE["bg"],
        edgecolor=PALETTE["border"],
        labelcolor=PALETTE["text"],
        fontsize=8,
    )
    title = "Expense" if type_ == "expense" else "Income"
    ax.set_title(f"{title} by Category", fontsize=12, fontweight="bold",
                 color=PALETTE["text"], pad=10)
    _apply_dark_style(fig, ax)
    fig.patch.set_facecolor(PALETTE["surface"])
    fig.tight_layout()
    return fig


def chart_net_line(trend_data: list[dict]) -> Figure:
    """Line chart of monthly net savings."""
    months_map: dict[str, dict] = defaultdict(lambda: {"income": 0, "expense": 0})
    for row in trend_data:
        months_map[row["month"]][row["type"]] = row["total"]

    sorted_months = sorted(months_map)[-12:]
    labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in sorted_months]
    nets   = [months_map[m]["income"] - months_map[m]["expense"] for m in sorted_months]

    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    colors_net = [PALETTE["income"] if n >= 0 else PALETTE["expense"] for n in nets]
    ax.axhline(0, color=PALETTE["border"], linewidth=1)
    ax.fill_between(range(len(nets)), nets, 0,
                    where=[n >= 0 for n in nets], alpha=0.15,
                    color=PALETTE["income"], interpolate=True)
    ax.fill_between(range(len(nets)), nets, 0,
                    where=[n < 0  for n in nets], alpha=0.15,
                    color=PALETTE["expense"], interpolate=True)
    ax.plot(nets, color=PALETTE["accent"], linewidth=2, marker="o",
            markersize=5, markerfacecolor=PALETTE["text"])
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_title("Monthly Net Savings", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Net (PKR)", fontsize=9)
    ax.yaxis.grid(True, color=PALETTE["border"], linewidth=0.6, zorder=0)
    _apply_dark_style(fig, ax)
    fig.tight_layout()
    return fig


# ── CSV export ────────────────────────────────────────────────────────────────

def export_transactions_csv(transactions: list[dict], filepath: str) -> None:
    """Write transaction list to a CSV file."""
    fieldnames = ["id", "date", "type", "category", "amount", "description"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for tx in transactions:
            writer.writerow({k: tx.get(k, "") for k in fieldnames})


def export_summary_csv(summary: dict, year: int, month: int, filepath: str) -> None:
    """Write a monthly summary to CSV."""
    month_label = datetime(year, month, 1).strftime("%B %Y")
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Personal Finance Summary —", month_label])
        writer.writerow([])
        writer.writerow(["Total Income",  f"{summary['income']:.2f}"])
        writer.writerow(["Total Expense", f"{summary['expense']:.2f}"])
        writer.writerow(["Net Savings",   f"{summary['net']:.2f}"])
        writer.writerow([])
        writer.writerow(["Category", "Type", "Amount"])
        for row in summary["by_category"]:
            writer.writerow([row["name"], row["type"], f"{row['total']:.2f}"])