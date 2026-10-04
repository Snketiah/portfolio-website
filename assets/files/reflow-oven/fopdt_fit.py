"""
FOPDT parameter extraction from step response CSV.

Fits: T(t) - T0 = K * du * (1 - exp(-(t - t_step - theta) / tau))  for t > t_step + theta
                = 0                                                 otherwise

Where:
    T0   = pre-step ambient temperature (mean of samples before step)
    du   = step size in duty (normalized 0-1, i.e. duty_cycle / 255)
    K    = process gain [degC per unit duty]
    tau  = time constant [s]
    theta = dead time [s]

Change FILE_PATH to point at any step-response CSV with columns:
    elapsed_s, temperature_c, duty_cycle
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ------------------------------------------------------------------
# CONFIG — change this to point at whichever step test you want to fit
# ------------------------------------------------------------------
FILE_PATH = "bump_test_data/bump_test_duty102.csv"

# How many pre-step samples to average for ambient baseline
PRE_STEP_AVG_N = 10

# Plot the fit against the data for visual sanity check
SHOW_PLOT = True


def load_step_response(path):
    """Load CSV, tolerating a duplicated header row from resumed logs."""
    df = pd.read_csv(path)
    # Drop any rows where numeric columns failed to parse (e.g. duplicated header)
    df["elapsed_s"] = pd.to_numeric(df["elapsed_s"], errors="coerce")
    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")
    df["duty_cycle"] = pd.to_numeric(df["duty_cycle"], errors="coerce")
    df = df.dropna(subset=["elapsed_s", "temperature_c", "duty_cycle"]).reset_index(drop=True)
    return df


def find_step_index(duty):
    """Index of first sample where duty transitions from 0 to nonzero."""
    nonzero = np.where(duty > 0)[0]
    if len(nonzero) == 0:
        raise ValueError("No nonzero duty cycle found — cannot locate step.")
    return int(nonzero[0])


def fopdt_model(t, K, tau, theta, t_step, du, T0):
    """FOPDT response anchored at t_step with step magnitude du (duty in 0-1)."""
    dT = np.zeros_like(t, dtype=float)
    active = t >= (t_step + theta)
    dT[active] = K * du * (1.0 - np.exp(-(t[active] - t_step - theta) / tau))
    return T0 + dT


def fit_fopdt(t, T, duty, pre_step_n=PRE_STEP_AVG_N):
    step_idx = find_step_index(duty)
    t_step = float(t[step_idx])

    # Ambient baseline from samples just before the step
    baseline_slice = slice(max(0, step_idx - pre_step_n), step_idx)
    T0 = float(np.mean(T[baseline_slice])) if step_idx > 0 else float(T[0])

    # Step size in normalized duty (0–1), matching firmware K convention
    du = float(duty[step_idx]) / 255.0

    # Initial guesses
    dT_final = float(np.mean(T[-max(pre_step_n, 3):])) - T0
    K0 = dT_final / du if du > 0 else 1.0
    tau0 = max((t[-1] - t_step) / 4.0, 1.0)
    theta0 = 5.0

    # Wrap model to expose only (K, tau, theta) to curve_fit
    def _model(t_, K, tau, theta):
        return fopdt_model(t_, K, tau, theta, t_step=t_step, du=du, T0=T0)

    popt, pcov = curve_fit(
        _model,
        t,
        T,
        p0=[K0, tau0, theta0],
        bounds=([0.0, 0.1, 0.0], [np.inf, np.inf, max(t[-1] - t_step, 1.0)]),
        maxfev=10000,
    )
    K, tau, theta = popt
    perr = np.sqrt(np.diag(pcov))

    # Fit quality
    T_pred = _model(t, *popt)
    ss_res = np.sum((T - T_pred) ** 2)
    ss_tot = np.sum((T - np.mean(T)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {
        "K": K,
        "tau": tau,
        "theta": theta,
        "K_err": perr[0],
        "tau_err": perr[1],
        "theta_err": perr[2],
        "T0": T0,
        "du": du,
        "t_step": t_step,
        "r_squared": r_squared,
        "T_pred": T_pred,
    }


def main():
    df = load_step_response(FILE_PATH)
    t = df["elapsed_s"].to_numpy()
    T = df["temperature_c"].to_numpy()
    duty = df["duty_cycle"].to_numpy()

    res = fit_fopdt(t, T, duty)

    print(f"\nFile: {FILE_PATH}")
    print(f"Step detected at t = {res['t_step']:.2f} s, du = {res['du']:.3f} (normalized)")
    print(f"Baseline T0 = {res['T0']:.2f} degC")
    print("\nFOPDT parameters:")
    print(f"  K     = {res['K']:.3f} degC / duty   (+/- {res['K_err']:.3f})")
    print(f"  tau   = {res['tau']:.2f} s             (+/- {res['tau_err']:.2f})")
    print(f"  theta = {res['theta']:.2f} s             (+/- {res['theta_err']:.2f})")
    print(f"  R^2   = {res['r_squared']:.4f}")

    if SHOW_PLOT:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t, T, "o", ms=3, label="Measured", color="#1f77b4")
        ax.plot(t, res["T_pred"], "-", lw=2, label="FOPDT fit", color="#d62728")
        ax.axvline(res["t_step"], ls="--", color="gray", alpha=0.6, label="Step")
        ax.axvline(res["t_step"] + res["theta"], ls=":", color="green", alpha=0.6,
                   label=f"Step + theta ({res['theta']:.1f}s)")
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Temperature [degC]")
        ax.set_title(
            f"FOPDT fit:  K={res['K']:.2f} degC/duty,  tau={res['tau']:.1f}s,  "
            f"theta={res['theta']:.1f}s,  R^2={res['r_squared']:.3f}"
        )
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
