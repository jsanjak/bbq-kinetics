"""
plan.py — CookPlan dataclass and temperature curve construction.

Stitches together three phases into one continuous temp series:
  1. Cook phase    — real or simulated probe data
  2. Hot hold      — optional flat hold at hold_temp for hold_duration hours
  3. Decline       — exponential cooldown to room temperature

The full curve is then passed to from_probe_data() for Arrhenius integration.
"""

from dataclasses import dataclass, field
import numpy as np

# Default cooling rate: wrapped brisket drops from pull temp to ~50°C in ~3-4 hrs
DEFAULT_COOLING_RATE: float = 0.00012
DEFAULT_ROOM_TEMP:    float = 70.0      # °F (≈21°C)
DEFAULT_DECLINE_HOURS: float = 4.0


@dataclass
class CookPlan:
    # --- Probe data (cook phase) ---
    probe_times: np.ndarray             # seconds
    probe_temps: np.ndarray             # °F or °C depending on unit

    # --- Unit ---
    unit: str = "F"                     # "F" or "C" — applies to all temps in this plan

    # --- Target ---
    target_tenderness: float = 0.80

    # --- Pull point (optional) ---
    pull_temp: float | None = None      # same unit as probe_temps. None = run to target tenderness

    # --- Hot hold (optional) ---
    hold_enabled: bool = False
    hold_temp: float | None = 165.0     # °F default (≈74°C)
    hold_duration: float | None = 2.0   # hours

    # --- Decline ---
    decline_enabled: bool = True
    room_temp: float = DEFAULT_ROOM_TEMP
    cooling_rate: float = DEFAULT_COOLING_RATE
    decline_hours: float = DEFAULT_DECLINE_HOURS

    # --- Metadata ---
    label: str = "Cook"


def build_temp_curve(
    plan: CookPlan,
    dt: float = 10.0,
) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Construct a continuous (times, temps) curve from a CookPlan.

    Returns
    -------
    times : np.ndarray   seconds
    temps : np.ndarray   temperature in plan.unit (°F or °C)
    unit  : str          "F" or "C" — pass to from_probe_data
    """
    times = list(plan.probe_times)
    temps = list(plan.probe_temps)

    # --- Find pull point ---
    # Either the first time internal temp reaches pull_temp,
    # or the end of probe data if pull_temp is None
    pull_idx = len(times) - 1
    if plan.pull_temp is not None:
        for i, T in enumerate(temps):
            if T >= plan.pull_temp:
                pull_idx = i
                break

    pull_time = times[pull_idx]
    pull_temp = temps[pull_idx]

    # Trim probe data to pull point
    times = times[:pull_idx + 1]
    temps = temps[:pull_idx + 1]

    # --- Hot hold phase ---
    if plan.hold_enabled and plan.hold_temp is not None and plan.hold_duration is not None:
        hold_seconds = plan.hold_duration * 3600
        t_hold = np.arange(dt, hold_seconds + dt, dt)
        times_hold = pull_time + t_hold
        temps_hold = np.full_like(t_hold, plan.hold_temp)
        times = np.concatenate([times, times_hold])
        temps = np.concatenate([temps, temps_hold])
        transition_temp = plan.hold_temp
        transition_time = times[-1]
    else:
        transition_temp = pull_temp
        transition_time = pull_time

    # --- Decline phase ---
    if plan.decline_enabled:
        decline_seconds = plan.decline_hours * 3600
        t_dec = np.arange(dt, decline_seconds + dt, dt)
        times_decline = transition_time + t_dec
        temps_decline = (
            plan.room_temp
            + (transition_temp - plan.room_temp) * np.exp(-plan.cooling_rate * t_dec)
        )
        times = np.concatenate([times, times_decline])
        temps = np.concatenate([temps, temps_decline])

    return np.asarray(times), np.asarray(temps), plan.unit


def phase_boundaries(plan: CookPlan) -> dict[str, float | None]:
    """
    Return the time (hours) at which each phase starts.
    Useful for annotating plots.
    """
    times = plan.probe_times
    temps = plan.probe_temps

    pull_time = times[-1]
    if plan.pull_temp is not None:
        for i, T in enumerate(temps):
            if T >= plan.pull_temp:
                pull_time = times[i]
                break

    hold_start = pull_time if plan.hold_enabled else None
    hold_end = (pull_time + plan.hold_duration * 3600) if plan.hold_enabled else None
    decline_start = hold_end if plan.hold_enabled else pull_time

    return {
        "pull":          pull_time / 3600,
        "hold_start":    hold_start / 3600 if hold_start else None,
        "hold_end":      hold_end / 3600 if hold_end else None,
        "decline_start": decline_start / 3600,
    }