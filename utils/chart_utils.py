import io
import base64

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=90, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


def chart_pie(series, title, top_n=8):
    counts = series.dropna().value_counts()
    if len(counts) == 0:
        return ""
    if len(counts) > top_n:
        other = counts.iloc[top_n:].sum()
        counts = counts.iloc[:top_n]
        if other > 0:
            counts["Other"] = other
    fig, ax = plt.subplots(figsize=(5, 3.5))
    colors = ["#00897b", "#4db6ac", "#80cbc4", "#26a69a", "#00695c",
              "#b2dfdb", "#00796b", "#48a999", "#e0f2f1"]
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct="%1.1f%%",
        colors=colors[:len(counts)], startangle=90,
        textprops={"fontsize": 7},
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_fontweight("bold")
    ax.set_title(title, fontsize=9, fontweight="bold")
    return fig_to_b64(fig)


def chart_line(x_series, y_series, title):
    try:
        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.plot(range(len(y_series)), y_series.values,
                color="#00897b", linewidth=2, marker="o", markersize=4)
        ax.set_xticks(range(len(y_series)))
        ax.set_xticklabels([str(p) for p in x_series], rotation=45,
                           ha="right", fontsize=7)
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        ax.fill_between(range(len(y_series)), y_series.values,
                        alpha=0.15, color="#00897b")
        return fig_to_b64(fig)
    except Exception:
        return ""


def chart_scatter(x_series, y_series, title, corr=None):
    try:
        x = x_series.dropna()
        y = y_series.dropna()
        common = x.index.intersection(y.index)
        if len(common) < 2:
            return ""
        x = x.loc[common].astype(float)
        y = y.loc[common].astype(float)
        fig, ax = plt.subplots(figsize=(5, 3.5))
        ax.scatter(x, y, alpha=0.5, color="#00897b", edgecolors="white", s=20)
        if corr is not None:
            ax.text(0.95, 0.95, f"r = {corr:.2f}", transform=ax.transAxes,
                    ha="right", va="top", fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="#f0f0f0", alpha=0.8))
        ax.set_title(title, fontsize=9, fontweight="bold")
        ax.tick_params(labelsize=7)
        return fig_to_b64(fig)
    except Exception:
        return ""


def chart_radar(labels, values_dict, title):
    try:
        n = len(labels)
        if n < 3:
            return ""
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        angles += angles[:1]
        fig, ax = plt.subplots(figsize=(5, 4), subplot_kw={"projection": "polar"})
        colors = ["#00897b", "#e74c3c", "#f39c12", "#17a2b8", "#8e44ad", "#27ae60"]
        for i, (name, vals) in enumerate(values_dict.items()):
            val_list = vals + vals[:1]
            ax.fill(angles, val_list, alpha=0.1, color=colors[i % len(colors)])
            ax.plot(angles, val_list, "o-", linewidth=2, label=name,
                    color=colors[i % len(colors)], markersize=4)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=7)
        ax.set_title(title, fontsize=9, fontweight="bold", pad=16)
        ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=7)
        return fig_to_b64(fig)
    except Exception:
        return ""
