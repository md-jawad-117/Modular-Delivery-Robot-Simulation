# 🚚 Modular Food Delivery Robot Simulation

A professional, modular simulation framework for **multi-robot food delivery dispatching** on a grid map with obstacles.

This project models a realistic fulfillment loop:
- customer orders arrive over time,
- a dispatcher assigns idle robots,
- robots navigate to delivery points and return to the shop,
- operations are logged for analysis.

It supports multiple dispatch strategies (**MILP / Nearest-Neighbor / Greedy fallback**) and provides both visualization and experiment logs.

https://github.com/user-attachments/assets/5b7dc59c-6c4b-4978-b575-e3caa308c351

---

## 🌍 Why this project matters

Autonomous delivery systems are increasingly relevant in:
- smart campuses,
- warehouses,
- hospitals,
- last-mile urban logistics.

This simulator helps study key operational questions:
- How should orders be assigned under limited fleet capacity?
- How does fairness (SLA-based prioritization) affect outcomes?
- What trade-offs exist between optimization quality and runtime?
- How do baseline heuristics compare against optimization-based dispatch?

The modular design makes this repository suitable for:
- academic experimentation,
- algorithm comparison,
- rapid prototyping for dispatch policies.

---

## 🧩 Project structure

```text
delivery_modular/
  __init__.py
  __main__.py
  sim_config.py            # central configuration
  timing.py                # monotonic simulation time helper
  models.py                # domain models and log record schemas
  grid.py                  # obstacle map and shop placement
  pathfinding.py           # A* pathfinding and path cache
  arrivals.py              # order generation and Poisson arrivals
  logger.py                # CSV/config logging
  ui.py                    # pygame rendering/dashboard
  simulation.py            # orchestration engine
  dispatcher/
    __init__.py
    nn.py                  # nearest-neighbor baseline
    greedy.py              # greedy fallback
    milp.py                # MILP assignment (PuLP-backed)

run_modular_sim.py         # single entrypoint script
make_icons.py              # one-off script to regenerate icon PNGs
```

---

## ✅ What has been implemented

### 1) 🏗️ Professional modularization
The original single-file script was refactored into cohesive modules with clear responsibilities:
- **configuration layer** (`sim_config.py`),
- **domain models** (`models.py`),
- **routing/pathfinding layer** (`pathfinding.py`),
- **dispatch policy layer** (`dispatcher/*`),
- **simulation orchestration** (`simulation.py`),
- **presentation layer** (`ui.py`),
- **data logging layer** (`logger.py`).

### 2) 🤖 Multiple dispatch policies
- **MILP policy** (with optional PuLP)
- **Nearest-Neighbor baseline**
- **Greedy fallback** when MILP is unavailable/infeasible

### 3) 📈 Operational realism features
- obstacle-aware A* routing,
- Poisson order arrivals,
- optional order windows,
- SLA-aware prioritization,
- performance-oriented path caching,
- run logs (`dispatch.csv`, `orders.csv`, `config.json`).

### 4) ▶️ Single-command execution design
Run one script and the whole system executes end-to-end:
- `run_modular_sim.py`

---

## 📦 Requirements

Dependencies are listed in [`requirements.txt`](requirements.txt).

- `numpy`
- `pygame`
- `PuLP` (recommended for MILP mode; otherwise system falls back to greedy logic)

---

## ⚙️ Setup (Windows CMD)

### 1) Create virtual environment

```cmd
python -m venv .venv
```

### 2) Activate environment

```cmd
.venv\Scripts\activate
```

### 3) Upgrade pip (recommended)

```cmd
python -m pip install --upgrade pip
```

### 4) Install dependencies

```cmd
pip install -r requirements.txt
```

---

## ▶️ Run the simulation

From the project root:

```cmd
python run_modular_sim.py
```

Alternative package mode:

```cmd
python -m delivery_modular
```

---

## 🗂️ Output artifacts

Each run writes timestamped logs under `runs/<timestamp>/`:
- `dispatch.csv` → epoch-level dispatch decisions/solver stats
- `orders.csv` → per-order timing and SLA outcomes
- `config.json` → exact run configuration

These outputs are suitable for downstream analysis, plotting, and policy comparison.

---

## 🛠️ Configuration guide

Adjust runtime behavior in `delivery_modular/sim_config.py`:
- `policy = "milp" | "nn"`
- `force_greedy`
- `rate_arrival`
- `sla_sec`, `k_oldest`, `lambda_tie`
- `headless`
- `auto_quit_after_orders`
- `target_fps`, map/display settings

---

## 📝 Notes

- If PuLP is missing, MILP mode is skipped and fallback logic handles assignments.
- Icon files (`car.png`, `del.png`, `shop.png`) are included. To regenerate them, run `python make_icons.py`.
- For long experiments, prefer `headless=True` in config for improved performance.

---

## 🚀 Suggested next improvements

- unit tests for dispatcher and pathfinding modules,
- CLI arguments for policy/rate overrides,
- richer metrics export (percentiles, ECDF, per-robot utilization),
- benchmark scripts for policy comparison at scale.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
