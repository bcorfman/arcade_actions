"""
Actions for continuous movement and physics-based movement.
"""

import math
from typing import Tuple, Optional, List
import arcade
from .base import Action
from enum import Enum, auto


class Boundary(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class _Move(Action):
    """Base class for continuous movement actions.

    This action updates sprite position based on velocity and acceleration.
    It can work with both regular sprites and physics-enabled sprites.
    """

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        if hasattr(self.target, "pymunk"):
            # Physics sprite - let Pymunk handle movement
            pass
        else:
            # Regular sprite - update position based on velocity
            x, y = self.target.position
            dx, dy = self.target.change_x, self.target.change_y

            # Apply acceleration if present
            if hasattr(self.target, "acceleration"):
                ax, ay = self.target.acceleration
                dx += ax * delta_time
                dy += ay * delta_time

            # Apply gravity if present
            if hasattr(self.target, "gravity"):
                dy += self.target.gravity * delta_time

            # Update velocity
            self.target.change_x = dx
            self.target.change_y = dy

            # Update position
            self.target.position = (x + dx * delta_time, y + dy * delta_time)

            # Update rotation if needed
            if hasattr(self.target, "change_angle"):
                self.target.angle += self.target.change_angle * delta_time


class WrappedMove(_Move):
    """Move sprites with wrapping at screen bounds."""

    def __init__(
        self, width: float, height: float, on_boundary_hit=None, *cb_args, **cb_kwargs
    ):
        super().__init__()
        self.width = width
        self.height = height
        self._on_boundary_hit = on_boundary_hit
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs

    def update(self, delta_time: float):
        """Update sprite positions with wrapping."""
        super().update(delta_time)
        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list()
        else:
            self._update_single_sprite()

    def _update_sprite_list(self):
        for sprite in self.target:
            self._wrap_sprite(sprite)

    def _update_single_sprite(self):
        self._wrap_sprite(self.target)

    def _wrap_sprite(self, sprite):
        boundaries_crossed = []
        # Handle x wrapping
        if sprite.right < 0:
            sprite.left = self.width
            boundaries_crossed.append(Boundary.LEFT)
        elif sprite.left > self.width:
            sprite.right = 0
            boundaries_crossed.append(Boundary.RIGHT)
        # Handle y wrapping
        if sprite.top < 0:
            sprite.bottom = self.height
            boundaries_crossed.append(Boundary.BOTTOM)
        elif sprite.bottom > self.height:
            sprite.top = 0
            boundaries_crossed.append(Boundary.TOP)
        # Update physics body if present
        if hasattr(sprite, "pymunk") and sprite.pymunk:
            sprite.pymunk.position = (sprite.center_x, sprite.center_y)
        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(
                sprite, boundaries_crossed, *self._cb_args, **self._cb_kwargs
            )

    def __repr__(self) -> str:
        return f"WrappedMove(width={self.width}, height={self.height})"


class BoundedMove(_Move):
    """Move the sprite but limit position to screen bounds.

    This action can work with both individual sprites and sprite lists.
    When used with a sprite list, it will reverse the direction of all
    sprites when any sprite hits the boundary.
    """

    def __init__(
        self, width: float, height: float, on_boundary_hit=None, *cb_args, **cb_kwargs
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.direction = 1  # 1 for right, -1 for left
        self._on_boundary_hit = on_boundary_hit
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs

    def update(self, delta_time: float) -> None:
        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        hit_boundary = False
        hit_sprite = None
        hit_boundaries = []
        for sprite in self.target:
            x, y = sprite.position
            w, h = sprite.width, sprite.height
            boundaries = []
            if self.direction > 0 and x > self.width - w / 2:
                boundaries.append(Boundary.RIGHT)
            elif self.direction < 0 and x < w / 2:
                boundaries.append(Boundary.LEFT)
            if boundaries:
                hit_boundary = True
                hit_sprite = sprite
                hit_boundaries = boundaries
                break
        if hit_boundary:
            self.direction *= -1
            for sprite in self.target:
                if hasattr(sprite, "pymunk"):
                    sprite.pymunk.velocity = (
                        -sprite.pymunk.velocity.x,
                        sprite.pymunk.velocity.y,
                    )
                else:
                    sprite.change_x *= -1
            if self._on_boundary_hit:
                self._on_boundary_hit(
                    hit_sprite, hit_boundaries, *self._cb_args, **self._cb_kwargs
                )
        for sprite in self.target:
            if hasattr(sprite, "pymunk"):
                pass
            else:
                x, y = sprite.position
                dx, dy = sprite.change_x, sprite.change_y
                if hasattr(sprite, "acceleration"):
                    ax, ay = sprite.acceleration
                    dx += ax * delta_time
                    dy += ay * delta_time
                if hasattr(sprite, "gravity"):
                    dy += sprite.gravity * delta_time
                sprite.change_x = dx
                sprite.change_y = dy
                sprite.position = (x + dx * delta_time, y + dy * delta_time)
                if hasattr(sprite, "change_angle"):
                    sprite.angle += sprite.change_angle * delta_time

    def _update_single_sprite(self, delta_time: float) -> None:
        super().update(delta_time)
        boundaries_crossed = []
        if hasattr(self.target, "pymunk"):
            x, y = self.target.pymunk.position
            w, h = self.target.width, self.target.height
            if x > self.width - w / 2:
                x = self.width - w / 2
                self.target.pymunk.velocity = (
                    -self.target.pymunk.velocity.x,
                    self.target.pymunk.velocity.y,
                )
                boundaries_crossed.append(Boundary.RIGHT)
            elif x < w / 2:
                x = w / 2
                self.target.pymunk.velocity = (
                    -self.target.pymunk.velocity.x,
                    self.target.pymunk.velocity.y,
                )
                boundaries_crossed.append(Boundary.LEFT)
            if y > self.height - h / 2:
                y = self.height - h / 2
                self.target.pymunk.velocity = (
                    self.target.pymunk.velocity.x,
                    -self.target.pymunk.velocity.y,
                )
                boundaries_crossed.append(Boundary.TOP)
            elif y < h / 2:
                y = h / 2
                self.target.pymunk.velocity = (
                    self.target.pymunk.velocity.x,
                    -self.target.pymunk.velocity.y,
                )
                boundaries_crossed.append(Boundary.BOTTOM)
            self.target.pymunk.position = (x, y)
        else:
            x, y = self.target.position
            w, h = self.target.width, self.target.height
            if x > self.width - w / 2:
                x = self.width - w / 2
                self.target.change_x *= -1
                boundaries_crossed.append(Boundary.RIGHT)
            elif x < w / 2:
                x = w / 2
                self.target.change_x *= -1
                boundaries_crossed.append(Boundary.LEFT)
            if y > self.height - h / 2:
                y = self.height - h / 2
                self.target.change_y *= -1
                boundaries_crossed.append(Boundary.TOP)
            elif y < h / 2:
                y = h / 2
                self.target.change_y *= -1
                boundaries_crossed.append(Boundary.BOTTOM)
            self.target.position = (x, y)
        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(
                self.target, boundaries_crossed, *self._cb_args, **self._cb_kwargs
            )

    def __repr__(self) -> str:
        return f"BoundedMove(width={self.width}, height={self.height})"


class Driver(Action):
    """Drive sprites like cars, moving in the direction they're facing.

    This action can work with both individual sprites and sprite lists.
    Each sprite will move independently based on its own speed, acceleration,
    and facing direction.
    """

    def update(self, delta_time: float) -> None:
        if self._paused:
            return

        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        """Update all sprites in a sprite list."""
        for sprite in self.target:
            self._drive_sprite(sprite, delta_time)

    def _update_single_sprite(self, delta_time: float) -> None:
        """Update a single sprite."""
        self._drive_sprite(self.target, delta_time)

    def _drive_sprite(self, sprite, delta_time: float) -> None:
        """Drive a single sprite based on its speed and direction."""
        # Get current speed and acceleration
        speed = getattr(sprite, "speed", 0)
        acceleration = getattr(sprite, "acceleration", 0)

        # Apply acceleration
        if acceleration:
            speed += acceleration * delta_time

            # Apply speed limits if present
            max_forward = getattr(sprite, "max_forward_speed", None)
            max_reverse = getattr(sprite, "max_reverse_speed", None)

            if max_forward is not None:
                speed = min(speed, max_forward)
            if max_reverse is not None:
                speed = max(speed, max_reverse)

        # Convert angle to radians
        angle_rad = math.radians(sprite.angle)

        # Calculate velocity components
        dx = math.sin(angle_rad) * speed * delta_time
        dy = math.cos(angle_rad) * speed * delta_time

        # Update position
        x, y = sprite.position
        sprite.position = (x + dx, y + dy)

        # Store current speed
        sprite.speed = speed

    def __repr__(self) -> str:
        return "Driver()"
