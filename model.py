"""
model.py — Arrhenius collagen breakdown model.

Collagen conversion follows first-order kinetics:
    dC/dt = -k(T) * C
where k(T) = A * exp(-Ea / (R * T)) is the Arrhenius rate constant.
"""

import numpy as np

# Universal gas constant (J/mol·K)
R: float = 8.314

# Default kinetic parameters — calibrated for INTERNAL meat temperatures
# Ea fitted from empirical rate data; A calibrated so that
# pull_early_195 (12hr cook) + 18hr hold at 150°F = exactly 80% actual collagen conversion
DEFAULT_Ea: float = 1.1278e+05  # J/mol — fitted from empirical rate data
DEFAULT_A:  float = 2.0258e+12  # 1/s   — calibrated to end-to-end cook scenario


def arrhenius_k(T: float, Ea: float = DEFAULT_Ea, A: float = DEFAULT_A) -> float:
    """
    Return the Arrhenius rate constant k [1/s] at temperature T [K].
    """
    return A * np.exp(-Ea / (R * T))


def simulate(
    temperature_profile,          # callable: t (seconds) -> T (Kelvin)
    total_hours: float = 12.0,
    dt: float = 10.0,             # time step, seconds
    Ea: float = DEFAULT_Ea,
    A:  float = DEFAULT_A,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simulate collagen breakdown over time.

    Parameters
    ----------
    temperature_profile : callable
        Function mapping time t [s] to temperature T [K].
    total_hours : float
        Total simulation duration in hours.
    dt : float
        Integration time step in seconds.
    Ea : float
        Activation energy in J/mol.
    A : float
        Pre-exponential factor in 1/s.

    Returns
    -------
    t : np.ndarray
        Time array in seconds.
    collagen : np.ndarray
        Normalized intact collagen fraction (1 = raw, 0 = fully broken down).
    """
    steps = int(total_hours * 3600 / dt)
    t = np.linspace(0, total_hours * 3600, steps)

    collagen = np.zeros(steps)
    collagen[0] = 1.0  # fully intact at start

    for i in range(1, steps):
        T = temperature_profile(t[i])
        rate = arrhenius_k(T, Ea=Ea, A=A)
        dC = -rate * collagen[i - 1] * dt
        collagen[i] = max(collagen[i - 1] + dC, 0.0)

    return t, collagen


def _to_celsius(temps: np.ndarray, unit: str) -> np.ndarray:
    """Convert temperature array to °C based on input unit."""
    unit = unit.lower()
    if unit in ("f", "fahrenheit"):
        return (temps - 32) * 5 / 9
    elif unit in ("c", "celsius"):
        return temps
    else:
        raise ValueError(f"Unknown temperature unit '{unit}'. Use 'C' or 'F'.")


def from_probe_data(
    times: list[float] | np.ndarray,   # seconds
    temps: list[float] | np.ndarray,   # internal probe readings (°C or °F)
    unit: str = "C",                    # "C" or "F"
    dt: float = 10.0,
    Ea: float = DEFAULT_Ea,
    A:  float = DEFAULT_A,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simulate collagen breakdown from real probe data.

    Interpolates between probe readings to get a continuous temperature
    profile, then runs the Arrhenius simulation on it.

    Parameters
    ----------
    times : array-like
        Probe timestamps in seconds.
    temps : array-like
        Internal meat temperatures in °C at each timestamp.
    dt : float
        Integration time step in seconds.
    Ea, A : float
        Arrhenius kinetic parameters.

    Returns
    -------
    t : np.ndarray
        Time array in seconds (from 0 to max probe time).
    collagen : np.ndarray
        Normalized intact collagen fraction over time.
    """
    times = np.asarray(times, dtype=float)
    temps = np.asarray(temps, dtype=float)
    temps_c = _to_celsius(temps, unit)

    # Build interpolating temperature profile from probe data
    def probe_profile(t: float) -> float:
        temp_c = float(np.interp(t, times, temps_c))
        return temp_c + 273.15  # convert to Kelvin

    total_hours = times[-1] / 3600
    return simulate(probe_profile, total_hours=total_hours, dt=dt, Ea=Ea, A=A)


TENDERNESS_TARGET: float = 0.80  # actual collagen conversion that = 100% on tenderness scale


def tenderness(collagen: np.ndarray) -> np.ndarray:
    """
    Convert collagen array to normalized tenderness scale.
    0% = raw, 100% = perfectly done (80% actual collagen conversion).
    Can exceed 100% if cooked/held beyond the target.
    """
    return (1.0 - collagen) / TENDERNESS_TARGET


def doneness_milestones(
    t: np.ndarray,
    collagen: np.ndarray,
    targets: list[float] = [0.5, 0.75, 1.0, 1.1],
) -> dict[float, float | None]:
    """
    Return the time (hours) at which each tenderness target is first reached.

    Parameters
    ----------
    targets : list of float
        Tenderness fractions, e.g. 0.8 means 80% collagen converted.

    Returns
    -------
    dict mapping target -> hours (or None if never reached).
    """
    conv = tenderness(collagen)
    milestones = {}
    for target in targets:
        idx = np.where(conv >= target)[0]
        milestones[target] = float(t[idx[0]] / 3600) if len(idx) > 0 else None
    return milestones