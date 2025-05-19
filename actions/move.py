"""
Actions for continuous movement and physics-based movement.
"""

import math
from enum import Enum, auto

import arcade

from .base import Action


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
    """Move sprites with wrapping at screen bounds.

    This action moves sprites continuously across the screen, wrapping them to the opposite
    edge when they move completely off-screen. The wrapping behavior ensures that sprites
    must be fully off-screen before wrapping occurs, and when they wrap, they appear at
    the opposite edge with their appropriate edge aligned to the boundary.

    For example, if a sprite moves off the left edge (right < 0), it will wrap to the right
    edge with its left edge aligned to the right boundary. Similarly, if a sprite moves off
    the right edge (left > width), it will wrap to the left edge with its right edge aligned
    to the left boundary. The same behavior applies to vertical wrapping.

    This action can work with both individual sprites and sprite lists. When used with a
    sprite list, each sprite is wrapped independently.

    Note: This action only handles wrapping behavior. The sprite's position should be updated
    by other actions or directly before this action is updated.

    Attributes:
        width (float): The width of the screen/boundary.
        height (float): The height of the screen/boundary.
        _on_boundary_hit (callable, optional): Callback function to be called when a sprite
            crosses a boundary. The callback receives the sprite, a list of boundaries crossed,
            and any additional args/kwargs provided during initialization.
        _cb_args (tuple): Additional positional arguments for the boundary hit callback.
        _cb_kwargs (dict): Additional keyword arguments for the boundary hit callback.
    """

    def __init__(self, width: float, height: float, on_boundary_hit=None, *cb_args, **cb_kwargs):
        """Initialize the WrappedMove action.

        Args:
            width (float): The width of the screen/boundary.
            height (float): The height of the screen/boundary.
            on_boundary_hit (callable, optional): Callback function to be called when a sprite
                crosses a boundary. The callback receives:
                - sprite: The sprite that crossed the boundary
                - boundaries: List of Boundary enum values indicating which boundaries were crossed
                - *cb_args: Additional positional arguments
                - **cb_kwargs: Additional keyword arguments
            *cb_args: Additional positional arguments for the boundary hit callback.
            **cb_kwargs: Additional keyword arguments for the boundary hit callback.
        """
        super().__init__()
        self.width = width
        self.height = height
        self._on_boundary_hit = on_boundary_hit
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs

    def update(self, delta_time: float):
        """Update sprite positions with wrapping.

        Note: This method only handles wrapping behavior. The sprite's position should be
        updated by other actions or directly before this method is called.
        """
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
            # When wrapping from left to right, maintain the same offset from right edge
            sprite.left = self.width + sprite.right
            boundaries_crossed.append(Boundary.LEFT)
        elif sprite.left > self.width:
            # When wrapping from right to left, maintain the same offset from left edge
            sprite.right = sprite.left - self.width
            boundaries_crossed.append(Boundary.RIGHT)
        # Handle y wrapping
        if sprite.bottom < 0:
            # When wrapping from bottom to top, maintain the same offset from top edge
            sprite.top = self.height + sprite.bottom
            boundaries_crossed.append(Boundary.BOTTOM)
        elif sprite.top > self.height:
            # When wrapping from top to bottom, maintain the same offset from bottom edge
            sprite.bottom = sprite.top - self.height
            boundaries_crossed.append(Boundary.TOP)
        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(sprite, boundaries_crossed, *self._cb_args, **self._cb_kwargs)

    def __repr__(self) -> str:
        return f"WrappedMove(width={self.width}, height={self.height})"


class BoundedMove(_Move):
    """Move the sprite but limit position to screen bounds.

    This action moves sprites within screen boundaries, bouncing them off the edges
    when they collide. The bounce behavior is determined by the sprite's movement
    direction and its edges:

    - When moving right, the sprite bounces when its right edge hits the right boundary
    - When moving left, the sprite bounces when its left edge hits the left boundary
    - When moving up, the sprite bounces when its top edge hits the top boundary
    - When moving down, the sprite bounces when its bottom edge hits the bottom boundary

    This action can work with both individual sprites and sprite lists. When used with a
    sprite list, it will reverse the direction of all sprites when any sprite hits a boundary.

    Attributes:
        width (float): The width of the screen/boundary.
        height (float): The height of the screen/boundary.
        direction (int): The current horizontal movement direction (1 for right, -1 for left).
        _on_boundary_hit (callable, optional): Callback function to be called when a sprite
            hits a boundary. The callback receives:
            - sprite: The sprite that hit the boundary
            - boundaries: List of Boundary enum values indicating which boundaries were hit
            - *cb_args: Additional positional arguments
            - **cb_kwargs: Additional keyword arguments
        _cb_args (tuple): Additional positional arguments for the boundary hit callback.
        _cb_kwargs (dict): Additional keyword arguments for the boundary hit callback.
    """

    def __init__(self, width: float, height: float, on_boundary_hit=None, *cb_args, **cb_kwargs):
        """Initialize the BoundedMove action.

        Args:
            width (float): The width of the screen/boundary.
            height (float): The height of the screen/boundary.
            on_boundary_hit (callable, optional): Callback function to be called when a sprite
                hits a boundary. The callback receives:
                - sprite: The sprite that hit the boundary
                - boundaries: List of Boundary enum values indicating which boundaries were hit
                - *cb_args: Additional positional arguments
                - **cb_kwargs: Additional keyword arguments
            *cb_args: Additional positional arguments for the boundary hit callback.
            **cb_kwargs: Additional keyword arguments for the boundary hit callback.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.direction = 1  # 1 for right, -1 for left
        self._on_boundary_hit = on_boundary_hit
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs

    def update(self, delta_time: float) -> None:
        """Update sprite positions with boundary bouncing."""
        if isinstance(self.target, arcade.SpriteList):
            self._update_sprite_list(delta_time)
        else:
            self._update_single_sprite(delta_time)

    def _update_sprite_list(self, delta_time: float) -> None:
        hit_boundary = False
        hit_sprite = None
        hit_boundaries = []

        # First check for boundary hits
        for sprite in self.target:
            boundaries = []
            # Check horizontal boundaries based on movement direction
            if sprite.change_x > 0 and sprite.right >= self.width:
                boundaries.append(Boundary.RIGHT)
            elif sprite.change_x < 0 and sprite.left <= 0:
                boundaries.append(Boundary.LEFT)
            # Check vertical boundaries based on movement direction
            if sprite.change_y > 0 and sprite.top >= self.height:
                boundaries.append(Boundary.TOP)
            elif sprite.change_y < 0 and sprite.bottom <= 0:
                boundaries.append(Boundary.BOTTOM)

            if boundaries:
                hit_boundary = True
                hit_sprite = sprite
                hit_boundaries = boundaries
                break

        # If any sprite hit a boundary, reverse directions for all sprites
        if hit_boundary:
            for sprite in self.target:
                if Boundary.RIGHT in hit_boundaries or Boundary.LEFT in hit_boundaries:
                    sprite.change_x *= -1
                if Boundary.TOP in hit_boundaries or Boundary.BOTTOM in hit_boundaries:
                    sprite.change_y *= -1
            if self._on_boundary_hit:
                self._on_boundary_hit(hit_sprite, hit_boundaries, *self._cb_args, **self._cb_kwargs)

        # Update all sprite positions
        for sprite in self.target:
            self._update_sprite_position(sprite, delta_time)

    def _update_single_sprite(self, delta_time: float) -> None:
        """Update a single sprite's position with boundary bouncing."""
        boundaries_crossed = []

        # Update position based on velocity and acceleration
        super().update(delta_time)

        # Check and handle boundary collisions
        if self.target.change_x > 0 and self.target.right >= self.width:
            self.target.right = self.width
            self.target.change_x *= -1
            boundaries_crossed.append(Boundary.RIGHT)
        elif self.target.change_x < 0 and self.target.left <= 0:
            self.target.left = 0
            self.target.change_x *= -1
            boundaries_crossed.append(Boundary.LEFT)

        if self.target.change_y > 0 and self.target.top >= self.height:
            self.target.top = self.height
            self.target.change_y *= -1
            boundaries_crossed.append(Boundary.TOP)
        elif self.target.change_y < 0 and self.target.bottom <= 0:
            self.target.bottom = 0
            self.target.change_y *= -1
            boundaries_crossed.append(Boundary.BOTTOM)

        if self._on_boundary_hit and boundaries_crossed:
            self._on_boundary_hit(self.target, boundaries_crossed, *self._cb_args, **self._cb_kwargs)

    def _update_sprite_position(self, sprite, delta_time: float) -> None:
        """Update a sprite's position based on its velocity and acceleration."""
        x, y = sprite.position
        dx, dy = sprite.change_x, sprite.change_y

        # Apply acceleration if present
        if hasattr(sprite, "acceleration"):
            ax, ay = sprite.acceleration
            dx += ax * delta_time
            dy += ay * delta_time

        # Apply gravity if present
        if hasattr(sprite, "gravity"):
            dy += sprite.gravity * delta_time

        # Update velocity
        sprite.change_x = dx
        sprite.change_y = dy

        # Update position
        sprite.position = (x + dx * delta_time, y + dy * delta_time)

        # Update rotation if needed
        if hasattr(sprite, "change_angle"):
            sprite.angle += sprite.change_angle * delta_time

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
