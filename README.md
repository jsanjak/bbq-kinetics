# BBQ-IQ 🔥

A brisket collagen breakdown simulator using Arrhenius kinetics.

## Setup

```bash
cd bbq-iq
uv sync
```

## Run

```bash
# Fit SmokeTrailsBBQ Data to Arrhenius Equation
uv run python fit_kinetics.py brisket_data.csv

#Compare some cook plans
uv run python cli.py --plan-compare
