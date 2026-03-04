from typing import List, Optional

import numpy as np
import pygame

from .arrivals import create_orders, schedule_next_arrival
from .dispatcher.greedy import assign_greedy
from .dispatcher.milp import PULP_OK, assign_milp
from .dispatcher.nn import assign_nn
from .grid import GridWorld
from .logger import CSVLogger
from .models import DispatchLog, Order, OrderLog
from .pathfinding import PathFinder
from .sim_config import SimulationConfig
from .timing import now_sec
from .ui import UI


class DeliverySimulation:
    def __init__(self, cfg: Optional[SimulationConfig] = None):
        self.cfg = cfg or SimulationConfig()
        self.rng = np.random.default_rng(self.cfg.seed)

        self.grid = GridWorld(self.cfg)
        self.pathfinder = PathFinder(self.cfg, self.grid)
        self.ui = UI(self.cfg, self.pathfinder)
        self.logger = CSVLogger(out_dir=self.cfg.log_out_dir)

        self.pending_orders: List[Order] = []
        self.completed_count = 0

        self.robots_pos = np.array(
            [self.pathfinder.to_pixel(self.grid.shop_location) for _ in range(self.cfg.num_robots)],
            dtype=np.float32,
        )
        self.total_distance = [0.0] * self.cfg.num_robots
        self.tasks_done = [0] * self.cfg.num_robots
        self.paths = [[] for _ in range(self.cfg.num_robots)]
        self.targets = [None] * self.cfg.num_robots
        self.returning = [False] * self.cfg.num_robots
        self.robot_idle = [True] * self.cfg.num_robots
        self.robot_last_grid = [self.grid.shop_location for _ in range(self.cfg.num_robots)]
        self.active_order_idx = [None] * self.cfg.num_robots
        self.order_ret_len = {}

        self.epoch_counter = 0
        self.t_start = now_sec()
        self.next_arrival_time = schedule_next_arrival(now_sec(), self.cfg.rate_arrival, self.rng)

        self._bootstrap_orders()
        self._save_config()

    def _bootstrap_orders(self):
        create_orders(self.pending_orders, n=8, with_windows=False, rng=self.rng, pathfinder=self.pathfinder)

    def _save_config(self):
        self.logger.save_config(self.cfg.to_dict())

    def order_age_sec(self, order: Order) -> float:
        return max(0.0, now_sec() - order.created_at)

    def get_return_time_sec(self, order_grid):
        if order_grid not in self.order_ret_len:
            self.order_ret_len[order_grid] = self.pathfinder.shortest_path_px(order_grid, self.grid.shop_location)
        px = self.order_ret_len[order_grid]
        return np.inf if not np.isfinite(px) else (px / self.cfg.speed_px_per_s)

    def log_order_if_ready(self, o: Order):
        if o.completed_at and o.assigned_at and o.picked_at:
            if (o.completed_at - self.t_start) < self.cfg.warmup_sec:
                return
            wait_assign = o.assigned_at - o.created_at
            wait_pick = o.picked_at - o.created_at
            total_flow = o.completed_at - o.created_at
            self.logger.log_order(
                OrderLog(
                    order_id=o.id,
                    created_at=o.created_at,
                    assigned_at=o.assigned_at,
                    picked_at=o.picked_at,
                    completed_at=o.completed_at,
                    wait_assign=wait_assign,
                    wait_pick=wait_pick,
                    total_flow=total_flow,
                    sla_hit=1 if wait_pick <= self.cfg.sla_sec else 0,
                )
            )

    def maybe_compact_completed_orders(self, min_size: int = 300):
        if len(self.pending_orders) < min_size:
            return
        if any(idx is not None for idx in self.active_order_idx):
            return
        self.pending_orders = [o for o in self.pending_orders if not o.completed]

    def mark_assignment(self, robot_idx: int, order_idx: int, assigned_at: float):
        o = self.pending_orders[order_idx]
        o.assigned_at = assigned_at
        o.assigned_to = robot_idx
        self.active_order_idx[robot_idx] = order_idx
        self.robot_idle[robot_idx] = False
        self.returning[robot_idx] = False
        self.targets[robot_idx] = self.pathfinder.to_pixel(o.grid)
        pth = self.pathfinder.get_path_nodes(self.robot_last_grid[robot_idx], o.grid)
        self.paths[robot_idx] = self.pathfinder.to_pixel_path(pth) if pth else []

    def dispatcher(self):
        idle_idxs = [i for i in range(self.cfg.num_robots) if self.robot_idle[i]]
        unassigned_idxs = [
            j for j, o in enumerate(self.pending_orders) if (not o.completed and o.assigned_to is None)
        ]
        if not idle_idxs or not unassigned_idxs:
            return

        sla_set = [j for j in unassigned_idxs if self.order_age_sec(self.pending_orders[j]) >= self.cfg.sla_sec]
        if sla_set:
            candidate_orders = sla_set
        else:
            unassigned_idxs.sort(key=lambda j: self.pending_orders[j].created_at)
            candidate_orders = unassigned_idxs[: self.cfg.k_oldest]

        if not candidate_orders:
            return

        now = now_sec()
        r = {j: max(0.0, now - self.pending_orders[j].created_at) for j in candidate_orders}

        T_ki = {}
        cost_pair = {}
        finite_pairs = []
        for k in idle_idxs:
            start_node = self.robot_last_grid[k]
            for j in candidate_orders:
                px = self.pathfinder.shortest_path_px(start_node, self.pending_orders[j].grid)
                if not np.isfinite(px):
                    T_ki[(k, j)] = np.inf
                    continue

                t_go = px / self.cfg.speed_px_per_s
                bj = getattr(self.pending_orders[j], "b", None)
                if bj is not None and t_go > (r[j] + bj):
                    T_ki[(k, j)] = np.inf
                    continue

                T_ki[(k, j)] = t_go
                t_ret = self.get_return_time_sec(self.pending_orders[j].grid)
                if not np.isfinite(t_ret):
                    continue

                cost_pair[(k, j)] = t_go + t_ret
                finite_pairs.append((k, j))

        if not finite_pairs:
            return

        if self.cfg.policy.lower() == "nn":
            assign_nn(self, idle_idxs, candidate_orders, T_ki)
            self.logger.log_dispatch(
                DispatchLog(
                    epoch=self.epoch_counter,
                    n_idle=len(idle_idxs),
                    n_cand=len(candidate_orders),
                    solver="NN",
                    status="N/A",
                    obj=-1.0,
                    z_star=-1.0,
                    solve_time=0.0,
                )
            )
            self.epoch_counter += 1
            return

        used_milp = False
        status_str = "N/A"
        obj_val = None
        solve_time = 0.0
        z_val = -1.0

        if PULP_OK and self.cfg.policy.lower() == "milp" and not self.cfg.force_greedy:
            used_milp, status_str, obj_val, solve_time, z_val, _ = assign_milp(
                self,
                idle_idxs,
                candidate_orders,
                T_ki,
                cost_pair,
                finite_pairs,
                r,
            )

        if used_milp:
            self.logger.log_dispatch(
                DispatchLog(
                    epoch=self.epoch_counter,
                    n_idle=len(idle_idxs),
                    n_cand=len(candidate_orders),
                    solver="MILP",
                    status=status_str,
                    obj=float(obj_val) if obj_val is not None else -1.0,
                    z_star=z_val,
                    solve_time=solve_time,
                )
            )
            self.epoch_counter += 1
            return

        assign_greedy(self, finite_pairs, cost_pair)
        self.logger.log_dispatch(
            DispatchLog(
                epoch=self.epoch_counter,
                n_idle=len(idle_idxs),
                n_cand=len(candidate_orders),
                solver="GREEDY",
                status=status_str if status_str != "N/A" else "N/A",
                obj=-1.0,
                z_star=-1.0,
                solve_time=0.0,
            )
        )
        self.epoch_counter += 1

    def _handle_events(self, running: bool) -> bool:
        if self.cfg.headless:
            return running

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                mods = pygame.key.get_mods()
                with_windows = bool(mods & pygame.KMOD_SHIFT)
                create_orders(
                    self.pending_orders,
                    n=3,
                    with_windows=with_windows,
                    rng=self.rng,
                    pathfinder=self.pathfinder,
                )
        return running

    def _update_arrivals(self):
        now = now_sec()
        if self.next_arrival_time is not None and now >= self.next_arrival_time:
            create_orders(
                self.pending_orders,
                n=1,
                with_windows=self.cfg.with_windows_default,
                rng=self.rng,
                pathfinder=self.pathfinder,
            )
            self.next_arrival_time = schedule_next_arrival(now, self.cfg.rate_arrival, self.rng)

    def _move_robots(self):
        for i in range(self.cfg.num_robots):
            if self.paths[i]:
                next_pos = self.paths[i][0]
                vec = next_pos - self.robots_pos[i]
                dist = float(np.linalg.norm(vec))
                if dist > 1e-6:
                    direction = vec / dist
                    move = min(self.cfg.step_size, dist)
                    self.robots_pos[i] += direction * move
                    self.total_distance[i] += move
                if dist <= self.cfg.step_size:
                    self.robots_pos[i] = next_pos
                    self.paths[i].pop(0)
                    self.robot_last_grid[i] = self.pathfinder.to_grid(next_pos)

    def _update_robot_task_status(self):
        for i in range(self.cfg.num_robots):
            if not self.paths[i] and self.targets[i] is not None and not self.returning[i]:
                j = self.active_order_idx[i]
                if j is not None and 0 <= j < len(self.pending_orders):
                    self.pending_orders[j].picked = True
                    if self.pending_orders[j].picked_at is None:
                        self.pending_orders[j].picked_at = now_sec()

                self.returning[i] = True
                p_back = self.pathfinder.get_path_nodes(self.robot_last_grid[i], self.grid.shop_location)
                self.paths[i] = self.pathfinder.to_pixel_path(p_back) if p_back else []

            elif not self.paths[i] and self.returning[i]:
                j = self.active_order_idx[i]
                if j is not None and 0 <= j < len(self.pending_orders):
                    o = self.pending_orders[j]
                    if o.assigned_to == i and not o.completed:
                        o.completed = True
                        if o.completed_at is None:
                            o.completed_at = now_sec()
                        self.tasks_done[i] += 1
                        self.completed_count += 1
                        self.log_order_if_ready(o)

                self.active_order_idx[i] = None
                self.targets[i] = None
                self.returning[i] = False
                self.robot_idle[i] = True
                self.robot_last_grid[i] = self.grid.shop_location

    def run(self):
        print("[INFO] Logging to:", self.logger.dir)
        running = True
        self.dispatcher()

        while running:
            self.ui.begin_frame()
            running = self._handle_events(running)

            self._update_arrivals()
            self.ui.draw_map_and_shop(self.grid.obstacles, self.grid.shop_location)
            self.ui.draw_orders(self.pending_orders)

            self._move_robots()
            self.ui.draw_robots(self.robots_pos, self.robot_idle, self.returning)

            self._update_robot_task_status()
            self.maybe_compact_completed_orders()

            need_dispatch = any(self.robot_idle) and any(
                (not o.completed and o.assigned_to is None) for o in self.pending_orders
            )
            if need_dispatch:
                self.dispatcher()

            self.ui.draw_dashboard(self)
            self.ui.end_frame()

            if (
                self.cfg.auto_quit_after_orders is not None
                and self.completed_count >= self.cfg.auto_quit_after_orders
            ):
                running = False

        self.close()

    def close(self):
        self.logger.close()
        self.ui.close()
        print("Simulation finished. Logs saved under:", self.logger.dir)
