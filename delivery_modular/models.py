from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class DispatchLog:
    epoch: int
    n_idle: int
    n_cand: int
    solver: str
    status: str
    obj: float
    z_star: float
    solve_time: float


@dataclass
class OrderLog:
    order_id: int
    created_at: float
    assigned_at: float
    picked_at: float
    completed_at: float
    wait_assign: float
    wait_pick: float
    total_flow: float
    sla_hit: int


class Order:
    _ctr = 0

    def __init__(self, grid_xy: Tuple[int, int], created_at: float):
        Order._ctr += 1
        self.id: int = Order._ctr
        self.grid: Tuple[int, int] = grid_xy
        self.assigned_to: Optional[int] = None
        self.completed: bool = False
        self.created_at: float = created_at
        self.picked: bool = False
        self.assigned_at: Optional[float] = None
        self.picked_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.a: float = 0.0
        self.b: Optional[float] = None
