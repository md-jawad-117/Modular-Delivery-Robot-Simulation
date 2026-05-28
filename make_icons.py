"""One-time script to generate car.png, del.png, and shop.png icon files."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # no window needed
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

def save(surf, path):
    pygame.image.save(surf, path)
    print(f"Saved {path}")


SIZE = 70


def make_car():
    """Top-down car silhouette (robot/vehicle)."""
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    # Body
    pygame.draw.rect(s, (30, 30, 200), (12, 18, 46, 34), border_radius=8)
    # Windscreen
    pygame.draw.rect(s, (180, 220, 255), (18, 22, 34, 14), border_radius=4)
    # Wheels
    wheel_color = (40, 40, 40)
    pygame.draw.rect(s, wheel_color, (8,  20, 8, 10), border_radius=2)
    pygame.draw.rect(s, wheel_color, (54, 20, 8, 10), border_radius=2)
    pygame.draw.rect(s, wheel_color, (8,  38, 8, 10), border_radius=2)
    pygame.draw.rect(s, wheel_color, (54, 38, 8, 10), border_radius=2)
    # Headlights
    pygame.draw.circle(s, (255, 240, 100), (20, 18), 4)
    pygame.draw.circle(s, (255, 240, 100), (50, 18), 4)
    return s


def make_delivery():
    """Package / delivery box icon."""
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    # Box body
    pygame.draw.rect(s, (210, 140, 50), (10, 22, 50, 38), border_radius=4)
    # Box lid
    pygame.draw.rect(s, (240, 170, 70), (10, 14, 50, 14), border_radius=4)
    # Tape stripe horizontal
    pygame.draw.rect(s, (255, 255, 255), (10, 33, 50, 6))
    # Tape stripe vertical
    pygame.draw.rect(s, (255, 255, 255), (32, 22, 6, 38))
    # Lid crease
    pygame.draw.line(s, (180, 110, 30), (10, 28), (60, 28), 2)
    return s


def make_shop():
    """Small shop / restaurant building icon."""
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    # Building
    pygame.draw.rect(s, (100, 180, 100), (10, 28, 50, 34), border_radius=3)
    # Roof / awning
    pygame.draw.polygon(s, (200, 60, 60), [(5, 30), (35, 8), (65, 30)])
    # Door
    pygame.draw.rect(s, (160, 100, 50), (28, 44, 14, 18), border_radius=2)
    # Window left
    pygame.draw.rect(s, (180, 230, 255), (13, 33, 12, 10), border_radius=2)
    # Window right
    pygame.draw.rect(s, (180, 230, 255), (45, 33, 12, 10), border_radius=2)
    # Sign
    pygame.draw.rect(s, (255, 220, 50), (18, 18, 34, 10), border_radius=2)
    return s


save(make_car(),      "car.png")
save(make_delivery(), "del.png")
save(make_shop(),     "shop.png")

pygame.quit()
print("Done.")
