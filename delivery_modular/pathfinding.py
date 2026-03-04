import heapq
from typing import Dict, Iterable, List, Tuple

import numpy as np

from .grid import GridWorld, GridPos
from .sim_config import SimulationConfig


class PathFinder:
    def __init__(self, cfg: SimulationConfig, grid: GridWorld):
        self.cfg = cfg
        self.grid = grid
        self._path_cache: Dict[Tuple[GridPos, GridPos], List[GridPos]] = {}

    def to_grid(self, pos_px) -> GridPos:
        return tuple(int(p // self.cfg.grid_size) for p in pos_px)

    def to_pixel(self, grid_pos: GridPos):
        return np.array([
            grid_pos[0] * self.cfg.grid_size + self.cfg.grid_size // 2,
            grid_pos[1] * self.cfg.grid_size + self.cfg.grid_size // 2,
        ], dtype=np.float32)

    def to_pixel_path(self, path_nodes: List[GridPos]):
        return [self.to_pixel(p) for p in path_nodes]

    @staticmethod
    def heuristic(a: GridPos, b: GridPos) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def neighbors(self, node: GridPos) -> Iterable[GridPos]:
        x, y = node
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid.cols and 0 <= ny < self.grid.rows and (nx, ny) not in self.grid.obstacles:
                yield (nx, ny)

    def astar(self, start: GridPos, goal: GridPos) -> List[GridPos]:
        if start == goal:
            return [start]

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for nb in self.neighbors(current):
                tentative = g_score[current] + 1
                if nb not in g_score or tentative < g_score[nb]:
                    came_from[nb] = current
                    g_score[nb] = tentative
                    f_score[nb] = tentative + self.heuristic(nb, goal)
                    heapq.heappush(open_set, (f_score[nb], nb))

        return []

    def get_path_nodes(self, start: GridPos, goal: GridPos) -> List[GridPos]:
        key = (start, goal)
        if key not in self._path_cache:
            self._path_cache[key] = self.astar(start, goal)
        return self._path_cache[key]

    def path_length_in_pixels(self, path_nodes: List[GridPos]) -> float:
        if path_nodes is None:
            return np.inf
        if len(path_nodes) == 0:
            return 0.0
        return len(path_nodes) * self.cfg.grid_size

    def shortest_path_px(self, start: GridPos, goal: GridPos) -> float:
        if start == goal:
            return 0.0
        p = self.get_path_nodes(start, goal)
        if not p:
            return np.inf
        return self.path_length_in_pixels(p)

    def reachable_from_shop(self, grid_xy: GridPos) -> bool:
        if grid_xy == self.grid.shop_location:
            return True
        return bool(self.get_path_nodes(self.grid.shop_location, grid_xy))
