from dataclasses import dataclass, asdict
from typing import Optional, Tuple


@dataclass
class SimulationConfig:
    # Policy
    policy: str = "milp"            # "milp" | "nn"
    force_greedy: bool = False       # if True, skip MILP and use GREEDY/NN

    # Arrivals
    rate_arrival: float = 0.0005     # orders/sec (Poisson)
    with_windows_default: bool = False

    # Fairness / horizon
    sla_sec: float = 90.0
    k_oldest: int = 12
    lambda_tie: float = 1e-3

    # MILP controls
    solver_time_limit: Optional[float] = 2.0
    solver_rel_gap: Optional[float] = None
    good_statuses: Tuple[str, ...] = ("Optimal", "Feasible")

    # Runtime
    headless: bool = False
    auto_quit_after_orders: Optional[int] = 100
    warmup_sec: float = 0.0
    target_fps: int = 60
    seed: int = 42

    # Map / display
    grid_size: int = 20
    dash_width: int = 290
    sim_width: int = 1300
    sim_height: int = 900
    step_size: int = 5
    num_robots: int = 5

    # Logging
    log_out_dir: str = "runs"

    # Optional icon paths (relative/absolute)
    icon_robot_path: str = "car.png"
    icon_delivery_path: str = "del.png"
    icon_shop_path: str = "shop.png"

    # Colors
    white: Tuple[int, int, int] = (255, 255, 255)
    black: Tuple[int, int, int] = (0, 0, 0)
    obstacle_color: Tuple[int, int, int] = (70, 70, 70)
    text_color: Tuple[int, int, int] = (20, 20, 20)
    pending_color: Tuple[int, int, int] = (200, 0, 0)

    @property
    def width(self) -> int:
        return self.sim_width + self.dash_width

    @property
    def height(self) -> int:
        return self.sim_height

    @property
    def cols(self) -> int:
        return self.sim_width // self.grid_size

    @property
    def rows(self) -> int:
        return self.sim_height // self.grid_size

    @property
    def speed_px_per_s(self) -> float:
        return float(self.target_fps * self.step_size)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["cols"] = self.cols
        data["rows"] = self.rows
        data["speed_px_per_s"] = self.speed_px_per_s
        return data
