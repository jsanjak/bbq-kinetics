"""
test_data.py — Synthetic internal probe temperature profiles for testing.

All temperatures are in °F, all times in seconds.

Based on real brisket cook characteristics:
- Cold meat starts at ~40°F (fridge temp)
- Rises steadily until the stall (~150–160°F)
- Stall can last 2–4 hours (evaporative cooling)
- Post-wrap temp climbs to finish at ~200–205°F
"""

import numpy as np


def _interpolate(waypoints: list[tuple[float, float]], n: int = 500) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a smooth time/temp curve from (hour, °F) waypoints.
    Returns (times_seconds, temps_fahrenheit).
    """
    hrs = np.array([w[0] for w in waypoints])
    tmp = np.array([w[1] for w in waypoints])
    t_fine = np.linspace(hrs[0], hrs[-1], n) * 3600
    T_fine = np.interp(t_fine, hrs * 3600, tmp)
    return t_fine, T_fine


def classic_12hr_smoke() -> tuple[np.ndarray, np.ndarray]:
    """Classic 13-hour low-and-slow, smoker ~225°F ambient."""
    waypoints = [
        (0.0,  40),
        (1.0,  95),
        (2.5,  130),
        (4.0,  150),   # entering stall
        (5.0,  151),
        (6.0,  153),
        (7.0,  155),   # wrap
        (8.5,  168),
        (10.0, 180),
        (11.0, 189),
        (12.0, 195),   # pull here
        (13.0, 203),   # pull here
    ]
    return _interpolate(waypoints)


def hot_and_fast_6hr() -> tuple[np.ndarray, np.ndarray]:
    """Hot-and-fast, smoker ~250°F ambient, done in ~6 hours."""
    waypoints = [
        (0.0, 40),
        (0.5, 104),
        (1.5, 144),
        (2.0, 154),    # entering stall
        (2.5, 156),
        (3.0, 158),
        (3.5, 162),    # wrap
        (4.5, 181),
        (5.5, 200),
        (6.0, 205),
    ]
    return _interpolate(waypoints)


def overnight_low_and_slow_16hr() -> tuple[np.ndarray, np.ndarray]:
    """Overnight low-and-slow, ~220°F ambient, long stall."""
    waypoints = [
        (0.0,  40),
        (2.0,  95),
        (4.0,  136),
        (6.0,  149),   # stall starts
        (7.0,  150),
        (8.0,  151),
        (9.0,  153),
        (10.0, 155),   # wrap
        (12.0, 172),
        (14.0, 189),
        (15.0, 196),
        (16.0, 201),
    ]
    return _interpolate(waypoints)


def pull_early_190() -> tuple[np.ndarray, np.ndarray]:
    """Classic 12hr smoke profile, reaches 190°F at hour 10."""
    waypoints = [
        (0.0,  40),
        (1.0,  95),
        (2.5,  130),
        (4.0,  150),   # entering stall
        (5.0,  151),
        (6.0,  153),
        (7.0,  155),   # wrap
        (8.5,  168),
        (10.0, 180),
        (11.0, 189),
        (12.0, 195),   # pull here
    ]
    return _interpolate(waypoints)


# Registry — raw probe profiles only
PROBE_PROFILES: dict[str, callable] = {
    "classic_12hr":    classic_12hr_smoke,
    "hot_and_fast_6hr": hot_and_fast_6hr,
    "overnight_16hr":  overnight_low_and_slow_16hr,
    "pull_early_190":  pull_early_190,
}


# ---------------------------------------------------------------------------
# CookPlan test profiles
# ---------------------------------------------------------------------------

from plan import CookPlan


def plan_classic_no_hold() -> CookPlan:
    """Classic 12-14hr cook, pull at 203°F, no hold."""
    times, temps = classic_12hr_smoke()
    return CookPlan(
        label="Classic — Pull 203°F No Hold",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=203.0,
        hold_enabled=False,
    )


def plan_overnight_no_hold() -> CookPlan:
    """Overnight low-and-slow, pull at 203°F, no hold."""
    times, temps = overnight_low_and_slow_16hr()
    return CookPlan(
        label="Overnight — Pull 203°F No Hold",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=203.0,
        hold_enabled=False,
    )


def plan_hot_and_fast_cooler_rest() -> CookPlan:
    """Hot & fast, pull at 205°F, 8hr gradual cooler rest."""
    times, temps = hot_and_fast_6hr()
    return CookPlan(
        label="Hot & Fast — Pull 203°F + 8hr Cooler Rest",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=203.0,
        hold_enabled=False,      # no active hold — passive cooler rest
        decline_enabled=True,
        decline_hours=8.0,
        room_temp=70.0,
        cooling_rate=0.00004,    # slower rate: well-insulated cooler
    )


def plan_pull_early_no_hold() -> CookPlan:
    """Pull early at 195°F, no hold."""
    times, temps = pull_early_190()
    return CookPlan(
        label="Pull Early 195°F — No Hold",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=195.0,
        hold_enabled=False,
    )


def plan_pull_early_hold_18hr_150() -> CookPlan:
    """Pull early at 195°F, hold 18hrs at 150°F."""
    times, temps = pull_early_190()
    return CookPlan(
        label="Pull Early 195°F + 18hr Hold @ 150°F",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=195.0,
        hold_enabled=True,
        hold_temp=150.0,
        hold_duration=18.0,
    )


def plan_pull_early_hold_6hr_175() -> CookPlan:
    """Pull early at 190°F, hold 6hrs at 175°F."""
    times, temps = pull_early_190()
    return CookPlan(
        label="Pull Early 190°F + 6hr Hold @ 175°F",
        probe_times=times,
        probe_temps=temps,
        unit="F",
        pull_temp=190.0,
        hold_enabled=True,
        hold_temp=175.0,
        hold_duration=6.0,
    )


PLAN_PROFILES: dict[str, callable] = {
    "classic_no_hold":           plan_classic_no_hold,
    #"overnight_no_hold":         plan_overnight_no_hold,
    "hot_and_fast_cooler_rest":  plan_hot_and_fast_cooler_rest,
    #"pull_early_no_hold":        plan_pull_early_no_hold,
    "pull_early_hold_18hr_150":  plan_pull_early_hold_18hr_150,
    "pull_early_hold_6hr_175":  plan_pull_early_hold_6hr_175,
}


if __name__ == "__main__":
    for name, fn in PROBE_PROFILES.items():
        times, temps = fn()
        print(f"{name}: {times[-1]/3600:.0f}h cook, "
              f"start={temps[0]:.0f}°F, finish={temps[-1]:.0f}°F")