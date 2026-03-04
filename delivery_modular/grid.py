from typing import List, Set, Tuple

from .sim_config import SimulationConfig


GridPos = Tuple[int, int]


def build_obstacles() -> Set[GridPos]:
    obstacles: Set[GridPos] = set()
    for col in range(5, 18): obstacles.add((col, 40))
    for col in range(20, 30): obstacles.add((col, 42))
    for col in range(38, 45): obstacles.add((col, 44))
    for row in range(38, 45): obstacles.add((18, row))
    for row in range(34, 50): obstacles.add((32, row))
    for row in range(30, 53): obstacles.add((38, row))
    for row in range(46, 56): obstacles.add((22, row))
    for col in range(23, 35): obstacles.add((col, 25))
    for col in range(40, 52): obstacles.add((col, 24))
    for row in range(30, 40): obstacles.add((12, row))
    for row in range(43, 50): obstacles.add((22, row))
    for row in range(38, 58): obstacles.add((48, row))
    for col in range(5, 15): obstacles.add((col, 10))
    for col in range(15, 30): obstacles.add((col, 5))
    for col in range(10, 25): obstacles.add((col, 22))
    for col in range(12, 21): obstacles.add((col, 15))
    for col in range(28, 47): obstacles.add((col, 8))
    for col in range(26, 42): obstacles.add((col, 14))
    for col in range(5, 18): obstacles.add((col, 27))
    for col in range(38, 45): obstacles.add((col, 24))
    for row in range(0, 13): obstacles.add((38, row))
    for row in range(17, 25): obstacles.add((37, row))
    for row in range(8, 14): obstacles.add((15, row))
    for row in range(2, 19): obstacles.add((8, row))
    for row in range(12, 20): obstacles.add((32, row))
    for row in range(20, 32): obstacles.add((18, row))
    for row in range(0, 15): obstacles.add((25, row))
    for col in range(43, 62): obstacles.add((col, 4))
    for col in range(45, 62): obstacles.add((col, 14))
    for col in range(48, 58): obstacles.add((col, 20))
    for col in range(42, 55): obstacles.add((col, 29))
    for col in range(18, 28): obstacles.add((col, 31))
    for col in range(18, 26): obstacles.add((col, 37))
    for row in range(20, 34): obstacles.add((55, row))
    for row in range(28, 44): obstacles.add((60, row))
    for col in range(40, 60): obstacles.add((col, 37))
    for row in range(25, 35): obstacles.add((30, row))
    for row in range(27, 37): obstacles.add((7, row))
    for row in range(10, 20): obstacles.add((44, row))
    for row in range(17, 26): obstacles.add((27, row))
    for row in range(5, 15): obstacles.add((20, row))
    for row in range(7, 15): obstacles.add((54, row))
    return obstacles


class GridWorld:
    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg
        self.obstacles: Set[GridPos] = build_obstacles()
        self.shop_location = self.place_shop_at_center(clear_radius=2)

    @property
    def cols(self) -> int:
        return self.cfg.cols

    @property
    def rows(self) -> int:
        return self.cfg.rows

    def place_shop_at_center(self, clear_radius: int = 2) -> GridPos:
        cx, cy = self.cols // 2, self.rows // 2
        to_clear: List[GridPos] = []
        for dx in range(-clear_radius, clear_radius + 1):
            for dy in range(-clear_radius, clear_radius + 1):
                if abs(dx) + abs(dy) <= clear_radius:
                    gx, gy = cx + dx, cy + dy
                    if 0 <= gx < self.cols and 0 <= gy < self.rows:
                        to_clear.append((gx, gy))
        for cell in to_clear:
            self.obstacles.discard(cell)
        return (cx, cy)
