"""The ten-level vault path."""

from __future__ import annotations

import random

import pygame

import config as c
from level import Obstacle, Orb, Portal


class Path:
    """Level-select screen and progress for the vault path."""

    def __init__(self, completed: set[int] | None = None, boss_unlocked: bool = False) -> None:
        self.completed = set(completed or set())
        self.boss_unlocked = boss_unlocked
        self._level_cache: dict[int, tuple[list[Obstacle], list[Portal], list[Orb], float]] = {}
        self.request_vault = False
        self.level_to_play: int | None = None
        self.master_room = False
        self._title = pygame.font.SysFont("Arial", 52, bold=True)
        self._body = pygame.font.SysFont("Arial", 22, bold=True)
        self._small = pygame.font.SysFont("Arial", 16)
        self.level_rects = [
            pygame.Rect(100 + (i % 5) * 155, 170 + (i // 5) * 110, 120, 76)
            for i in range(10)
        ]
        self.door_rect = pygame.Rect(c.SCREEN_W // 2 - 78, 410, 156, 82)
        self.master_rect = pygame.Rect(c.SCREEN_W // 2 - 150, 245, 300, 90)
        self.boss_rect = pygame.Rect(c.SCREEN_W // 2 - 150, 355, 300, 70)

    @property
    def door_open(self) -> bool:
        return len(self.completed) == 10

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_vault = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.door_open and not self.master_room and self.door_rect.collidepoint(event.pos):
                self.master_room = True
                return
            if self.master_room and self.master_rect.collidepoint(event.pos):
                self.level_to_play = 10
                return
            if self.boss_unlocked and self.master_room and self.boss_rect.collidepoint(event.pos):
                self.level_to_play = 11
                return
            for index, rect in enumerate(self.level_rects):
                if rect.collidepoint(event.pos) and index not in self.completed:
                    self.level_to_play = index
                    return

    def update(self, dt: float) -> None:
        pass

    def level_data(self, level_index: int) -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
        """Return one cached random layout so retries use the same course."""
        if level_index not in self._level_cache:
            seed = random.SystemRandom().randrange(0, 2**32)
            self._level_cache[level_index] = build_path_level(level_index, seed)
        return self._level_cache[level_index]

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill((10, 15, 34))
        if self.master_room:
            self._draw_master_room(surf)
            return
        title = self._title.render("THE PATH", True, c.GROUND_LINE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 70)))
        subtitle = self._small.render(
            f"WHITE ORBS: {len(self.completed)}/10  ·  Complete every level to open the door",
            True,
            c.UI_DIM,
        )
        surf.blit(subtitle, subtitle.get_rect(center=(c.SCREEN_W // 2, 112)))

        for index, rect in enumerate(self.level_rects):
            complete = index in self.completed
            color = c.PROGRESS_FILL if complete else c.MENU_BTN
            pygame.draw.rect(surf, color, rect, border_radius=8)
            pygame.draw.rect(surf, c.UI, rect, width=2, border_radius=8)
            label = "WHITE ORB" if complete else f"LEVEL {index + 1}"
            text = self._body.render(label, True, (12, 18, 32) if complete else c.UI)
            surf.blit(text, text.get_rect(center=rect.center))

        door_color = c.PROGRESS_FILL if self.door_open else c.UI_DIM
        door = self.door_rect
        pygame.draw.rect(surf, door_color, door, width=5, border_radius=8)
        pygame.draw.circle(surf, door_color, door.center, 9)
        status = "DOOR OPEN" if self.door_open else "DOOR LOCKED"
        status_text = self._body.render(status, True, door_color)
        surf.blit(status_text, status_text.get_rect(center=(c.SCREEN_W // 2, 512)))
        hint = self._small.render("Click a level or the open door  ·  Esc back to vault", True, c.UI_DIM)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 530)))

    def _draw_master_room(self, surf: pygame.Surface) -> None:
        """Render the room revealed behind the completed path door."""
        title = self._title.render("MASTER ROOM", True, c.SPIKE)
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2, 100)))
        subtitle = self._small.render(
            "One of the hardest jumps in JUMP awaits.", True, c.UI_DIM
        )
        surf.blit(subtitle, subtitle.get_rect(center=(c.SCREEN_W // 2, 155)))
        pygame.draw.rect(surf, c.SPIKE, self.master_rect, border_radius=10)
        pygame.draw.rect(surf, c.UI, self.master_rect, width=3, border_radius=10)
        text = self._title.render("MASTER", True, c.UI)
        surf.blit(text, text.get_rect(center=self.master_rect.center))
        if self.boss_unlocked:
            pygame.draw.rect(surf, c.PORTAL_SPEED, self.boss_rect, width=4, border_radius=10)
            boss_text = self._body.render("BOSS LEVEL", True, c.PORTAL_SPEED)
            surf.blit(boss_text, boss_text.get_rect(center=self.boss_rect.center))
        hint = self._small.render("Click MASTER to enter  ·  Esc back", True, c.UI_DIM)
        surf.blit(hint, hint.get_rect(center=(c.SCREEN_W // 2, 410)))


def build_path_level(
    level_index: int, seed: int | None = None
) -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Build one fair, increasingly difficult, randomly varied path level."""
    rng = random.Random(level_index if seed is None else seed)
    ground = c.GROUND_Y
    obstacles: list[Obstacle] = []
    difficulty = level_index + 1
    start = 520.0
    spacing = max(125.0, 190.0 - difficulty * 4.0 + rng.randint(-14, 18))
    hazard_count = max(3, 4 + difficulty + rng.randint(-2, 2))
    for i in range(hazard_count):
        x = start + i * spacing
        obstacles.append(Obstacle("spike", x, ground - 28.0, 28.0, 28.0))
        if difficulty >= 6 and i % 5 == 4 and rng.random() < 0.8:
            obstacles.append(Obstacle("spike", x + 38.0, ground - 28.0, 28.0, 28.0))
    if difficulty >= 6 and rng.random() < 0.8:
        block_index = min(5, hazard_count - 1)
        obstacles.append(Obstacle("block", start + block_index * spacing, ground - 72.0, 72.0, 36.0))
    portals: list[Portal] = []
    if difficulty >= 8 and rng.random() < 0.85:
        portals.append(Portal(start + 2 * spacing, "ship"))
        portals.append(Portal(start + 5 * spacing, "cube"))
    orbs = [Orb("white", start + 3 * spacing, ground - 120.0)]
    return obstacles, portals, orbs, start + (hazard_count + 3) * spacing


def build_boss_level() -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Build the boss level unlocked after defeating MASTER."""
    ground = c.GROUND_Y
    obstacles: list[Obstacle] = []
    # The boss arena is a long attack pattern with alternating safe lanes.
    for index, x in enumerate(range(520, 3000, 110)):
        if index % 3 != 1:
            obstacles.append(Obstacle("spike", float(x), ground - 28.0, 28.0, 28.0))
        if index % 4 == 2:
            obstacles.append(Obstacle("spike", float(x), c.CEILING_Y, 28.0, 28.0))
        if index % 6 == 5:
            obstacles.append(Obstacle("block", float(x + 42), ground - 72.0, 72.0, 36.0))
    portals = [Portal(900.0, "ship"), Portal(1800.0, "speed"), Portal(3100.0, "cube")]
    orbs = [Orb("black", 760.0, ground - 120.0), Orb("white", 2200.0, ground - 130.0)]
    return obstacles, portals, orbs, 3500.0


def build_master_level() -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Build the extreme but traversable MASTER challenge."""
    ground = c.GROUND_Y
    obstacles: list[Obstacle] = []
    for x in (500.0, 620.0, 740.0, 860.0):
        obstacles.extend(
            [
                Obstacle("spike", x, ground - 28.0, 28.0, 28.0),
                Obstacle("spike", x + 38.0, ground - 28.0, 28.0, 28.0),
            ]
        )
    for x in (1120.0, 1270.0, 1420.0, 1570.0, 1720.0):
        obstacles.append(Obstacle("spike", x, ground - 28.0, 28.0, 28.0))
    for index, x in enumerate(range(2050, 3250, 100)):
        obstacles.append(
            Obstacle(
                "spike",
                float(x),
                c.CEILING_Y if index % 2 else ground - 28.0,
                28.0,
                28.0,
            )
        )
    for x in (3500.0, 3610.0, 3720.0, 3830.0, 3940.0, 4050.0):
        obstacles.append(Obstacle("spike", x, ground - 28.0, 28.0, 28.0))
    portals = [Portal(1900.0, "speed"), Portal(2000.0, "ship"), Portal(3300.0, "speed"), Portal(3400.0, "cube")]
    orbs = [
        Orb("black", 1000.0, ground - 120.0),
        Orb("yellow", 2700.0, (c.CEILING_Y + ground) / 2),
        Orb("white", 4100.0, ground - 120.0),
    ]
    return obstacles, portals, orbs, 4400.0
