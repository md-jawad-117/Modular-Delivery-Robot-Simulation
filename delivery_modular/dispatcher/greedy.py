from ..timing import now_sec


def assign_greedy(sim, finite_pairs, cost_pair):
    """Greedy fallback assignment by min (go+return)."""
    pairs = sorted(((k, j, cost_pair[(k, j)]) for (k, j) in finite_pairs), key=lambda t3: t3[2])
    used_k, used_j = set(), set()
    assigned = 0

    for k, j, _ in pairs:
        if k in used_k or j in used_j:
            continue
        sim.mark_assignment(k, j, now_sec())
        used_k.add(k)
        used_j.add(j)
        assigned += 1

    return assigned
