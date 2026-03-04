import os
from typing import Optional

import pygame

from .models import Order
from .sim_config import SimulationConfig


class UI:
    def __init__(self, cfg: SimulationConfig, pathfinder):
        self.cfg = cfg
        self.pathfinder = pathfinder
        self.screen = None
        self.clock = None
        self.font = None

        self.robot_img = None
        self.delivery_img = None
        self.shop_img = None

        pygame.init()
        if not cfg.headless:
            self.screen = pygame.display.set_mode((cfg.width, cfg.height))
            pygame.display.set_caption("Food Delivery Robot Simulation (Modular)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20) if not cfg.headless else None

        self._load_icons()

    def _safe_load(self, path: str, size):
        try:
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            img = pygame.image.load(path)
            return pygame.transform.scale(img, size)
        except Exception:
            return None

    def _load_icons(self):
        if self.cfg.headless:
            return
        self.robot_img = self._safe_load(self.cfg.icon_robot_path, (30, 30))
        self.delivery_img = self._safe_load(self.cfg.icon_delivery_path, (30, 30))
        self.shop_img = self._safe_load(self.cfg.icon_shop_path, (70, 70))

    def begin_frame(self):
        if not self.cfg.headless:
            self.screen.fill(self.cfg.white)

    def draw_map_and_shop(self, obstacles, shop_location):
        if self.cfg.headless:
            return

        for (col, row) in obstacles:
            if 0 <= col < self.cfg.cols and 0 <= row < self.cfg.rows:
                pygame.draw.rect(
                    self.screen,
                    self.cfg.obstacle_color,
                    (col * self.cfg.grid_size, row * self.cfg.grid_size, self.cfg.grid_size, self.cfg.grid_size),
                )

        shop_pixel = self.pathfinder.to_pixel(shop_location)
        if self.shop_img is not None:
            self.screen.blit(self.shop_img, (shop_pixel[0] - 35, shop_pixel[1] - 35))
        else:
            pygame.draw.rect(self.screen, (160, 200, 255), (shop_pixel[0] - 35, shop_pixel[1] - 35, 70, 70))

    def draw_orders(self, pending_orders):
        if self.cfg.headless:
            return
        for o in pending_orders:
            if o.completed or o.picked:
                continue
            px = self.pathfinder.to_pixel(o.grid)
            if o.assigned_to is None:
                pygame.draw.circle(self.screen, self.cfg.pending_color, (int(px[0]), int(px[1])), 5)
            else:
                if self.delivery_img is not None:
                    self.screen.blit(self.delivery_img, (px[0] - 10, px[1] - 10))
                else:
                    pygame.draw.circle(self.screen, (0, 180, 0), (int(px[0]), int(px[1])), 7, 2)

    def draw_robots(self, robots_pos, robot_idle, returning):
        if self.cfg.headless:
            return
        for i, pos in enumerate(robots_pos):
            if self.robot_img is not None:
                self.screen.blit(self.robot_img, (pos[0] - 15, pos[1] - 15))
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), (int(pos[0]), int(pos[1])), 12, 2)
            label = f"R{i}"
            self.screen.blit(self.font.render(label, True, self.cfg.black), (int(pos[0] + 10), int(pos[1] - 20)))

    def draw_dashboard(self, sim):
        if self.cfg.headless:
            return

        dash_x = self.cfg.sim_width
        pygame.draw.rect(self.screen, (230, 230, 230), (dash_x, 0, self.cfg.dash_width, self.cfg.height))
        self.screen.blit(self.font.render("== Delivery Dashboard ==", True, self.cfg.text_color), (dash_x + 20, 10))

        if self.cfg.policy.lower() == "nn":
            self.screen.blit(
                self.font.render("Dispatcher: Nearest-Neighbor (baseline)", True, (0, 90, 140)),
                (dash_x + 20, 30),
            )
        else:
            self.screen.blit(
                self.font.render("Dispatcher: MILP + GREEDY fallback", True, (0, 120, 0)),
                (dash_x + 20, 30),
            )

        self.screen.blit(
            self.font.render(f"Objective: min max-wait + λ·dist  (λ={self.cfg.lambda_tie:g})", True, self.cfg.text_color),
            (dash_x + 20, 50),
        )
        self.screen.blit(
            self.font.render(
                f"SLA={int(self.cfg.sla_sec)}s, K_oldest={self.cfg.k_oldest}, speed={int(self.cfg.speed_px_per_s)}px/s",
                True,
                self.cfg.text_color,
            ),
            (dash_x + 20, 70),
        )
        self.screen.blit(
            self.font.render(
                f"Policy: {self.cfg.policy.upper()}  | Poisson rate: {self.cfg.rate_arrival:.3f} orders/s",
                True,
                self.cfg.text_color,
            ),
            (dash_x + 20, 90),
        )

        y0 = 120
        for i in range(self.cfg.num_robots):
            avg_dist = sim.total_distance[i] / sim.tasks_done[i] if sim.tasks_done[i] > 0 else 0.0
            status = "Idle" if sim.robot_idle[i] else ("Returning" if sim.returning[i] else "To Order")
            base_y = y0 + i * 90
            self.screen.blit(self.font.render(f"Robot R{i} [{status}]", True, self.cfg.text_color), (dash_x + 20, base_y))
            self.screen.blit(
                self.font.render(f"Avg Dist/Order: {avg_dist:.1f}px", True, self.cfg.text_color),
                (dash_x + 40, base_y + 20),
            )
            self.screen.blit(
                self.font.render(f"Orders Done: {sim.tasks_done[i]}", True, self.cfg.text_color),
                (dash_x + 40, base_y + 40),
            )

        total_pending = sum(1 for o in sim.pending_orders if not o.completed and o.assigned_to is None)
        total_inprog = sum(1 for o in sim.pending_orders if not o.completed and o.assigned_to is not None)
        total_done = sim.completed_count
        self.screen.blit(self.font.render(f"Pending: {total_pending}", True, self.cfg.text_color), (dash_x + 20, self.cfg.height - 110))
        self.screen.blit(
            self.font.render(f"In-Progress: {total_inprog}", True, self.cfg.text_color),
            (dash_x + 20, self.cfg.height - 90),
        )
        self.screen.blit(self.font.render(f"Completed: {total_done}", True, self.cfg.text_color), (dash_x + 20, self.cfg.height - 70))
        self.screen.blit(
            self.font.render("[N] add 3 orders (Shift+N -> with windows)", True, self.cfg.text_color),
            (dash_x + 20, self.cfg.height - 50),
        )

    def end_frame(self):
        if not self.cfg.headless:
            pygame.display.flip()
        self.clock.tick(self.cfg.target_fps)

    def close(self):
        pygame.quit()
