import numpy as np

from ..timing import now_sec

try:
    import pulp

    PULP_OK = True
except Exception:
    pulp = None
    PULP_OK = False


def assign_milp(sim, idle_idxs, candidate_orders, T_ki, cost_pair, finite_pairs, r):
    """MILP assignment. Returns (used_milp, status_str, obj_val, solve_time, z_val, assigned)."""
    if not PULP_OK:
        return (False, "PuLP missing", None, 0.0, -1.0, 0)

    try:
        cfg = sim.cfg
        prob = pulp.LpProblem("MinMaxWaitAssign", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("x", (idle_idxs, candidate_orders), 0, 1, cat="Binary")
        t = pulp.LpVariable.dicts("t", candidate_orders, lowBound=0)
        w = pulp.LpVariable.dicts("w", candidate_orders, lowBound=0)
        z = pulp.LpVariable("z", lowBound=0)
        y = pulp.LpVariable.dicts("y", candidate_orders, 0, 1, cat="Binary")
        M = 1e4

        # robust exact assignment count from feasible bipartite matching size
        pairs_for_A = sorted(((k, j, cost_pair[(k, j)]) for (k, j) in finite_pairs), key=lambda t3: t3[2])
        used_k_A, used_j_A = set(), set()
        A = 0
        for k, j, _ in pairs_for_A:
            if k in used_k_A or j in used_j_A:
                continue
            used_k_A.add(k)
            used_j_A.add(j)
            A += 1
        if A == 0:
            return (False, "No feasible pairs", None, 0.0, -1.0, 0)

        prob += pulp.lpSum(x[k][j] for k in idle_idxs for j in candidate_orders) == A

        for j in candidate_orders:
            prob += y[j] == pulp.lpSum(x[k][j] for k in idle_idxs)
            prob += t[j] >= r[j]
            prob += w[j] >= t[j] - r[j] - M * (1 - y[j])
            prob += w[j] <= z + M * (1 - y[j])

            for k in idle_idxs:
                if np.isfinite(T_ki.get((k, j), np.inf)):
                    prob += t[j] >= T_ki[(k, j)] - M * (1 - x[k][j])
                else:
                    prob += x[k][j] == 0

            bj = getattr(sim.pending_orders[j], "b", None)
            if bj is not None:
                prob += t[j] <= r[j] + bj + M * (1 - y[j])

        for k in idle_idxs:
            prob += pulp.lpSum(x[k][j] for j in candidate_orders) <= 1
        for j in candidate_orders:
            prob += pulp.lpSum(x[k][j] for k in idle_idxs) <= 1

        prob += z + cfg.lambda_tie * pulp.lpSum(cost_pair[(k, j)] * x[k][j] for (k, j) in finite_pairs)

        solver_kwargs = {"msg": False}
        if cfg.solver_time_limit is not None:
            solver_kwargs["timeLimit"] = cfg.solver_time_limit
        if cfg.solver_rel_gap is not None:
            try:
                solver_kwargs["gapRel"] = cfg.solver_rel_gap
            except Exception:
                pass

        solver = pulp.PULP_CBC_CMD(**solver_kwargs)
        t0 = now_sec()
        prob.solve(solver)
        solve_time = now_sec() - t0

        status_code = prob.status
        status_str = pulp.LpStatus.get(status_code, "Unknown")
        obj_val = pulp.value(prob.objective)
        try:
            z_val = float(pulp.value(z)) if pulp.value(z) is not None else -1.0
        except Exception:
            z_val = -1.0

        if status_str not in set(cfg.good_statuses) or obj_val is None:
            return (False, status_str, obj_val, solve_time, z_val, 0)

        assigned = 0
        for (k, j) in finite_pairs:
            val = pulp.value(x[k][j])
            if val is None:
                continue
            if val > 0.5:
                sim.mark_assignment(k, j, now_sec())
                assigned += 1

        if assigned == 0:
            return (False, "Feasible but no assignment", obj_val, solve_time, z_val, 0)

        return (True, status_str, obj_val, solve_time, z_val, assigned)

    except Exception as e:
        return (False, f"MILP exception: {e}", None, 0.0, -1.0, 0)
