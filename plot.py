"""
plot.py — Visualization helpers for simulation results.
"""

import matplotlib.pyplot as plt
import numpy as np

from model import tenderness, doneness_milestones


def plot_single(
    t: np.ndarray,
    collagen: np.ndarray,
    label: str = "Simulation",
    save_path: str | None = None,
) -> None:
    """Plot a single collagen conversion curve."""
    conv = tenderness(collagen)
    hours = t / 3600

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(hours, conv, linewidth=2, label=label)

    # Mark doneness milestones
    milestones = doneness_milestones(t, collagen)
    colors = ["#f0a500", "#e07000", "#c04000", "#800000"]
    for (target, time_h), color in zip(milestones.items(), colors):
        if time_h is not None:
            ax.axhline(target, color=color, linestyle="--", linewidth=0.8, alpha=0.7)
            ax.axvline(time_h, color=color, linestyle="--", linewidth=0.8, alpha=0.7)
            ax.annotate(
                f"{int(target*100)}% @ {time_h:.1f}h",
                xy=(time_h, target),
                xytext=(time_h + 0.15, target - 0.04),
                fontsize=8,
                color=color,
            )

    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Tenderness (100% = perfectly done)", fontsize=12)
    ax.set_title("Brisket Collagen Breakdown Model", fontsize=14)
    ax.set_ylim(0, 1.25)
    ax.set_xlim(0, hours[-1])
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Plot saved → {save_path}")
    else:
        plt.show()


def plot_plan(
    t: np.ndarray,
    collagen: np.ndarray,
    boundaries: dict,
    label: str = "Cook Plan",
    save_path: str | None = None,
) -> None:
    """Plot a CookPlan simulation with phase boundary annotations."""
    conv = tenderness(collagen)
    hours = t / 3600

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hours, conv, linewidth=2, color="#c04000", label=label)

    # Phase boundary lines
    phase_colors = {"pull": "#2196F3", "hold_start": "#4CAF50", "decline_start": "#9C27B0"}
    phase_labels = {"pull": "Pull", "hold_start": "Hold Start", "decline_start": "Decline"}

    for key, color in phase_colors.items():
        t_phase = boundaries.get(key)
        if t_phase is not None:
            ax.axvline(t_phase, color=color, linestyle="--", linewidth=1.2, alpha=0.8)
            ax.text(t_phase + 0.05, 0.95, phase_labels[key], color=color,
                    fontsize=8, va="top", transform=ax.get_xaxis_transform())

    # Tenderness milestones
    milestones = doneness_milestones(t, collagen)
    for target, time_h in milestones.items():
        if time_h is not None:
            ax.axhline(target, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
            ax.annotate(f"{int(target*100)}%", xy=(hours[-1], target),
                        xytext=(hours[-1] - 0.3, target + 0.02), fontsize=8, color="gray")

    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Tenderness (100% = perfectly done)", fontsize=12)
    ax.set_title(f"Brisket Cook Plan: {label}", fontsize=14)
    ax.set_ylim(0, 1.25)
    ax.set_xlim(0, hours[-1])
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Plot saved → {save_path}")
    else:
        plt.show()


def plot_plan_comparison(
    results: dict[str, tuple[np.ndarray, np.ndarray]],
    save_path: str | None = None,
) -> None:
    """Overlay multiple CookPlan simulations."""
    fig, ax = plt.subplots(figsize=(11, 6))

    for name, (t, collagen) in results.items():
        ax.plot(t / 3600, tenderness(collagen), linewidth=2,
                label=name.replace("_", " ").title())

    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1, label="100% done")
    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Tenderness (100% = perfectly done)", fontsize=12)
    ax.set_title("Brisket Cook Plan Comparison", fontsize=14)
    ax.set_ylim(0, 1.25)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Plot saved → {save_path}")
    else:
        plt.show()


def plot_comparison(
    results: dict[str, tuple[np.ndarray, np.ndarray]],
    save_path: str | None = None,
) -> None:
    """
    Overlay multiple temperature profiles on one chart.

    Parameters
    ----------
    results : dict
        Mapping of profile name -> (t, collagen) arrays.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, (t, collagen) in results.items():
        ax.plot(t / 3600, tenderness(collagen), linewidth=2, label=name.replace("_", " ").title())

    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1, label="100% done")
    ax.set_xlabel("Time (hours)", fontsize=12)
    ax.set_ylabel("Tenderness (100% = perfectly done)", fontsize=12)
    ax.set_title("Brisket Cook Comparison — Temperature Profiles", fontsize=14)
    ax.set_ylim(0, 1.25)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Plot saved → {save_path}")
    else:
        plt.show()