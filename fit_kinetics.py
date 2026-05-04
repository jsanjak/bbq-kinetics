"""
fit_kinetics.py — Fit Arrhenius parameters (Ea, A) from empirical brisket data.

Input CSV columns:
  temperature_F         : internal meat temperature in °F
  conversion_rate_per_hour : % collagen conversion per hour, normalized so
                             "ideal done" = 100% total conversion

The observed rate k_obs [1/s] is derived from the empirical %/hr values and
then fit to the Arrhenius equation:
    k(T) = A * exp(-Ea / (R * T))

using nonlinear least squares (scipy.optimize.curve_fit).

Outputs:
  - Fitted Ea and A
  - Comparison of observed vs fitted rates across the temperature range
  - A plot of the Arrhenius fit (ln(k) vs 1/T)
  - Updated model.py constants (printed, not auto-applied)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr

# Universal gas constant
R = 8.314  # J/mol·K


def f_to_k(T_f: float) -> float:
    """Convert °F to Kelvin."""
    return (T_f - 32) * 5 / 9 + 273.15


def arrhenius(T_k: np.ndarray, ln_A: float, Ea: float) -> np.ndarray:
    """
    Arrhenius model in log space for numerical stability:
        ln(k) = ln(A) - Ea / (R * T)
    Fitting ln(A) instead of A avoids overflow with large pre-exponential factors.
    """
    return ln_A - Ea / (R * T_k)


def fit(csv_path: str = "brisket_data.csv", plot: bool = True) -> dict:
    # --- Load data ---
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} data points\n")
    print(df.to_string(index=False))
    print()

    # --- Convert units ---
    # Empirical rate is %/hr normalized to 100% total conversion
    # Empirical rate is %/hr normalized so 100% = "ideal done" = 80% actual collagen conversion.
    # Scale by 0.80 to convert to actual fractional collagen conversion rate per second.
    NORMALIZATION = 0.80
    T_k = df["temperature_F"].apply(f_to_k).values
    k_obs = df["conversion_rate_per_hour"].values / 100.0 * NORMALIZATION / 3600.0  # 1/s
    ln_k_obs = np.log(k_obs)

    # --- Fit in log space ---
    p0 = [40.0, 150e3]  # initial guesses: ln(A), Ea
    popt, pcov = curve_fit(arrhenius, T_k, ln_k_obs, p0=p0, maxfev=10000)
    ln_A_fit, Ea_fit = popt
    A_fit = np.exp(ln_A_fit)
    perr = np.sqrt(np.diag(pcov))

    # --- Goodness of fit ---
    ln_k_pred = arrhenius(T_k, *popt)
    k_pred = np.exp(ln_k_pred)
    r, _ = pearsonr(ln_k_obs, ln_k_pred)

    print("=" * 50)
    print("FITTED ARRHENIUS PARAMETERS")
    print("=" * 50)
    print(f"  Ea  = {Ea_fit/1000:.2f} kJ/mol  (±{perr[1]/1000:.2f})")
    print(f"  A   = {A_fit:.4e} 1/s")
    print(f"  R²  = {r**2:.6f}")
    print()

    print("OBSERVED vs FITTED RATES")
    print(f"{'Temp (°F)':<12} {'Temp (°C)':<12} {'Obs %/hr':<12} {'Fit %/hr':<12} {'Error %':<10}")
    print("-" * 58)
    for i in range(len(df)):
        obs_phr = df["conversion_rate_per_hour"].values[i]
        fit_phr = k_pred[i] / NORMALIZATION * 100 * 3600
        err_pct = (fit_phr - obs_phr) / obs_phr * 100
        T_c = (df["temperature_F"].values[i] - 32) * 5 / 9
        print(f"  {df['temperature_F'].values[i]:<10.0f} {T_c:<12.1f} {obs_phr:<12.1f} {fit_phr:<12.2f} {err_pct:+.1f}%")

    print()
    print("=" * 50)
    print("UPDATE model.py WITH THESE VALUES:")
    print("=" * 50)
    print(f"  DEFAULT_Ea: float = {Ea_fit:.4e}  # J/mol (fitted from empirical data)")
    print(f"  DEFAULT_A:  float = {A_fit:.4e}   # 1/s   (fitted from empirical data)")
    print()

    # --- Plot ---
    if plot:
        inv_T = 1 / T_k
        inv_T_fine = np.linspace(inv_T.min() * 0.995, inv_T.max() * 1.005, 200)
        ln_k_fine = arrhenius(1 / inv_T_fine, *popt)  # convert back to T_k for arrhenius()

        fig, axes = plt.subplots(1, 2, figsize=(13, 5))

        # Left: Arrhenius plot (ln k vs 1/T)
        ax = axes[0]
        inv_T_scaled = inv_T * 1000          # scale for display
        inv_T_fine_scaled = inv_T_fine * 1000

        ax.scatter(inv_T_scaled, ln_k_obs, color="#c04000", zorder=5,
                   s=60, label="Observed")
        ax.plot(inv_T_fine_scaled, ln_k_fine, color="#2196F3", linewidth=2,
                label=f"Fit (R²={r**2:.4f})")
        ax.set_xlabel("1/T × 10³  (K⁻¹)", fontsize=12)
        ax.set_ylabel("ln(k)", fontsize=12)
        ax.set_title("Arrhenius Plot", fontsize=13)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Right: observed vs fitted rate in intuitive units (%/hr vs °F)
        ax2 = axes[1]
        T_f_fine = np.linspace(df["temperature_F"].min() - 5,
                               df["temperature_F"].max() + 5, 200)
        T_k_fine = np.array([f_to_k(t) for t in T_f_fine])
        k_fine = np.exp(arrhenius(T_k_fine, *popt)) / NORMALIZATION * 100 * 3600

        ax2.scatter(df["temperature_F"], df["conversion_rate_per_hour"],
                    color="#c04000", zorder=5, s=60, label="Observed")
        ax2.plot(T_f_fine, k_fine, color="#2196F3", linewidth=2, label="Fitted")
        ax2.set_xlabel("Internal Temperature (°F)", fontsize=12)
        ax2.set_ylabel("Conversion rate (%/hr)", fontsize=12)
        ax2.set_title("Conversion Rate vs Temperature", fontsize=13)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        fig.suptitle(
            f"Arrhenius Fit — Ea={Ea_fit/1000:.1f} kJ/mol, A={A_fit:.2e} 1/s",
            fontsize=13
        )
        fig.tight_layout()
        plt.savefig("fit_results.png", dpi=150)
        print("Plot saved → fit_results.png")
        plt.show()

    return {"Ea": Ea_fit, "A": A_fit, "r_squared": r**2}


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "brisket_data.csv"
    fit(csv_path)