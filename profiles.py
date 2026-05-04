"""
profiles.py — Temperature profile functions.

Each profile takes time t [seconds] and returns temperature T [Kelvin].
Add your own by following the same signature.
"""

C_TO_K = 273.15


def classic_smoke(t: float) -> float:
    """
    Classic 3-phase Texas-style brisket smoke:
      0–3 hr   : 110 °C open smoker
      3–6 hr   : 95 °C (the stall — evaporative cooling)
      6–10 hr  : 120 °C wrapped (butcher paper / foil) finish
    """
    hours = t / 3600
    if hours < 3:
        return 110 + C_TO_K
    elif hours < 6:
        return 95 + C_TO_K
    else:
        return 120 + C_TO_K


def hot_and_fast(t: float) -> float:
    """
    Hot-and-fast method: 120°C (250°F) throughout.
    Targets ~80% tenderness in ~3 hours.
    """
    return 120 + C_TO_K


def low_and_slow(t: float) -> float:
    """
    Low-and-slow overnight: 105°C (221°F).
    Targets ~80% tenderness in ~18 hours.
    """
    return 105 + C_TO_K


def franklin_method(t: float) -> float:
    """
    Approximation of Aaron Franklin's approach:
      0–2 hr   : 115°C to build bark
      2–8 hr   : 110°C steady smoke
      8+ hr    : 118°C wrapped to finish
    """
    hours = t / 3600
    if hours < 2:
        return 115 + C_TO_K
    elif hours < 8:
        return 110 + C_TO_K
    else:
        return 118 + C_TO_K


# Registry for CLI / future use
PROFILES: dict[str, callable] = {
    "classic_smoke": classic_smoke,
    "hot_and_fast": hot_and_fast,
    "low_and_slow": low_and_slow,
    "franklin_method": franklin_method,
}