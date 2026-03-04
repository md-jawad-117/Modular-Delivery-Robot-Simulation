import numpy as np

from ..timing import now_sec


def assign_nn(sim, idle_idxs, candidate_orders, T_ki):
    """Nearest-neighbor baseline assignment."""
    pairs_nn = []
    for k in idle_idxs:
        best = None
        for j in candidate_orders:
            tgo = T_ki.get((k, j), np.inf)
            if np.isfinite(tgo):
                if (best is None) or (tgo < best[2]):
                    best = (k, j, tgo)
        if best is not None:
            pairs_nn.append(best)

    pairs_nn.sort(key=lambda x: x[2])
    used_k, used_j = set(), set()
    assigned = 0

    for k, j, _ in pairs_nn:
        if k in used_k or j in used_j:
            continue
        sim.mark_assignment(k, j, now_sec())
        used_k.add(k)
        used_j.add(j)
        assigned += 1

    return assigned
