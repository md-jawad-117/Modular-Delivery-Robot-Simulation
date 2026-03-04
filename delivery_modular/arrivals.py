from typing import List

import numpy as np

from .models import Order
from .pathfinding import PathFinder
from .timing import now_sec


def random_reachable_cell(rng: np.random.Generator, pathfinder: PathFinder):
    cols, rows = pathfinder.grid.cols, pathfinder.grid.rows
    obstacles = pathfinder.grid.obstacles
    while True:
        x = int(rng.integers(0, cols))
        y = int(rng.integers(0, rows))
        if (x, y) not in obstacles and pathfinder.reachable_from_shop((x, y)):
            return (x, y)


def create_orders(
    pending_orders: List[Order],
    n: int,
    with_windows: bool,
    rng: np.random.Generator,
    pathfinder: PathFinder,
):
    for _ in range(n):
        o = Order(random_reachable_cell(rng, pathfinder), created_at=now_sec())
        if with_windows:
            o.a = 0.0
            o.b = float(rng.uniform(60, 180))
        pending_orders.append(o)


def schedule_next_arrival(now: float, rate_arrival: float, rng: np.random.Generator):
    if rate_arrival > 0:
        inter = float(rng.exponential(1.0 / rate_arrival))
        return now + inter
    return None
