"""
cli.py — Command-line entry point for bbq-iq simulations.

Usage:
    uv run python cli.py                             # classic smoke profile
    uv run python cli.py --profile hot_and_fast
    uv run python cli.py --compare                   # overlay all ambient profiles
    uv run python cli.py --probe classic_12hr
    uv run python cli.py --probe-compare             # overlay all probe profiles
    uv run python cli.py --plan classic_no_hold
    uv run python cli.py --plan-compare              # overlay all cook plans
    uv run python cli.py --save output.png
"""

import argparse

from model import simulate, doneness_milestones, from_probe_data
from profiles import PROFILES
from plan import build_temp_curve, phase_boundaries
from plot import plot_single, plot_comparison, plot_plan, plot_plan_comparison
from test_data import PROBE_PROFILES, PLAN_PROFILES


def print_milestones(t, collagen, label: str) -> None:
    print(f"\n── {label} ──")
    milestones = doneness_milestones(t, collagen)
    for target, time_h in milestones.items():
        if time_h is not None:
            print(f"  {int(target*100):>4}% tender at ~{time_h:.2f} hours")
        else:
            print(f"  {int(target*100):>4}% tender: not reached in simulation window")


def main() -> None:
    parser = argparse.ArgumentParser(description="BBQ-IQ Brisket Simulation")
    parser.add_argument(
        "--profile",
        default="classic_smoke",
        choices=list(PROFILES.keys()),
        help="Ambient temperature profile to simulate (default: classic_smoke)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Overlay all ambient profiles in one comparison chart",
    )
    parser.add_argument(
        "--probe",
        default=None,
        choices=list(PROBE_PROFILES.keys()),
        help="Simulate from a synthetic probe data profile",
    )
    parser.add_argument(
        "--probe-compare",
        action="store_true",
        help="Overlay all probe profiles in one comparison chart",
    )
    parser.add_argument(
        "--plan",
        default=None,
        choices=list(PLAN_PROFILES.keys()),
        help="Simulate a full CookPlan (cook + hold + decline)",
    )
    parser.add_argument(
        "--plan-compare",
        action="store_true",
        help="Overlay all CookPlan profiles in one comparison chart",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save plot to this file path instead of displaying",
    )
    args = parser.parse_args()

    if args.plan_compare:
        results = {}
        for name, fn in PLAN_PROFILES.items():
            cook_plan = fn()
            times, temps, unit = build_temp_curve(cook_plan)
            t, collagen = from_probe_data(times, temps, unit=unit)
            results[cook_plan.label] = (t, collagen)
            print_milestones(t, collagen, cook_plan.label)
        plot_plan_comparison(results, save_path=args.save)

    elif args.plan:
        cook_plan = PLAN_PROFILES[args.plan]()
        times, temps, unit = build_temp_curve(cook_plan)
        t, collagen = from_probe_data(times, temps, unit=unit)
        bounds = phase_boundaries(cook_plan)
        print_milestones(t, collagen, cook_plan.label)
        plot_plan(t, collagen, bounds, label=cook_plan.label, save_path=args.save)

    elif args.probe_compare:
        results = {}
        for name, fn in PROBE_PROFILES.items():
            times, temps = fn()
            t, collagen = from_probe_data(times, temps, unit="F")
            results[name] = (t, collagen)
            print_milestones(t, collagen, name)
        plot_comparison(results, save_path=args.save)

    elif args.probe:
        times, temps = PROBE_PROFILES[args.probe]()
        t, collagen = from_probe_data(times, temps, unit="F")
        print_milestones(t, collagen, args.probe)
        plot_single(t, collagen, label=args.probe.replace("_", " ").title(), save_path=args.save)

    elif args.compare:
        results = {}
        for name, profile_fn in PROFILES.items():
            t, collagen = simulate(profile_fn, total_hours=12.0)
            results[name] = (t, collagen)
            print_milestones(t, collagen, name)
        plot_comparison(results, save_path=args.save)

    else:
        profile_fn = PROFILES[args.profile]
        t, collagen = simulate(profile_fn, total_hours=12.0)
        print_milestones(t, collagen, args.profile)
        plot_single(t, collagen, label=args.profile.replace("_", " ").title(), save_path=args.save)


if __name__ == "__main__":
    main()