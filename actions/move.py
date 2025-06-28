"""
Actions for continuous movement and boundary behaviors.
"""

from collections.abc import Callable

import arcade

from actions.base import Action


class WrappedMove(Action):
    """Wraps a movement action to provide screen wrapping behavior.

    When sprites move offscreen, they wrap to the opposite side while
    the contained movement action continues uninterrupted.

    Designed for velocity-based actions like MoveUntil/MoveWhile.
    """

    def __init__(
        self,
        get_bounds: Callable[[], tuple[float, float]],
        movement_action: Action,
        *,
        wrap_horizontal: bool = True,
        wrap_vertical: bool = True,
        on_wrap: Callable[[arcade.Sprite, str], None] | None = None,
    ):
        """Initialize the wrapped move action.

        Args:
            get_bounds: Function returning (width, height) screen bounds
            movement_action: The movement action to wrap (typically MoveUntil/MoveWhile)
            wrap_horizontal: Whether to wrap on horizontal boundaries
            wrap_vertical: Whether to wrap on vertical boundaries
            on_wrap: Optional callback when wrapping occurs
        """
        super().__init__()
        self.get_bounds = get_bounds
        self.movement_action = movement_action
        self.wrap_horizontal = wrap_horizontal
        self.wrap_vertical = wrap_vertical
        self.on_wrap = on_wrap

    def start(self) -> None:
        """Start the wrapped movement action."""
        super().start()
        self.movement_action.target = self.target
        self.movement_action.start()

    def update(self, delta_time: float) -> None:
        """Update movement and handle wrapping."""
        if self._paused:
            return

        # Update the contained movement action first
        if not self.movement_action.done:
            self.movement_action.update(delta_time)

        # Check for wrapping on each sprite
        for sprite in self._iter_target():
            self._check_wrap(sprite)

        # Done when movement action is done
        if self.movement_action.done:
            self.done = True

    def _check_wrap(self, sprite: arcade.Sprite) -> None:
        """Check if sprite needs wrapping and apply it."""
        bounds = self.get_bounds()
        width, height = bounds

        wrapped = False
        wrap_axis = None

        # Check horizontal wrapping
        if self.wrap_horizontal:
            if sprite.center_x < -sprite.width / 2:
                sprite.center_x = width + sprite.width / 2
                wrapped = True
                wrap_axis = "x"
            elif sprite.center_x > width + sprite.width / 2:
                sprite.center_x = -sprite.width / 2
                wrapped = True
                wrap_axis = "x"

        # Check vertical wrapping
        if self.wrap_vertical:
            if sprite.center_y < -sprite.height / 2:
                sprite.center_y = height + sprite.height / 2
                wrapped = True
                wrap_axis = "y"
            elif sprite.center_y > height + sprite.height / 2:
                sprite.center_y = -sprite.height / 2
                wrapped = True
                wrap_axis = "y"

        # Trigger callback if wrapping occurred
        if wrapped and self.on_wrap:
            self.on_wrap(sprite, wrap_axis)

    def stop(self) -> None:
        """Stop the wrapped movement action."""
        if self.movement_action:
            self.movement_action.stop()
        super().stop()

    def pause(self) -> None:
        """Pause the wrapped movement action."""
        if self.movement_action:
            self.movement_action.pause()
        super().pause()

    def resume(self) -> None:
        """Resume the wrapped movement action."""
        if self.movement_action:
            self.movement_action.resume()
        super().resume()

    def clone(self) -> "WrappedMove":
        """Create a copy of this WrappedMove action."""
        return WrappedMove(
            self.get_bounds,
            self.movement_action.clone(),
            wrap_horizontal=self.wrap_horizontal,
            wrap_vertical=self.wrap_vertical,
            on_wrap=self.on_wrap,
        )

    def _iter_target(self):
        """Iterate over target sprites."""
        try:
            return iter(self.target)  # type: ignore[not-an-iterable]
        except TypeError:
            return [self.target]


class BoundedMove(Action):
    """Wraps a movement action to provide boundary bouncing behavior.

    When sprites hit boundaries, their velocity is reversed while
    the contained movement action continues uninterrupted.

    Designed for velocity-based actions like MoveUntil/MoveWhile.
    """

    def __init__(
        self,
        get_bounds: Callable[[], tuple[float, float, float, float]],
        movement_action: Action,
        *,
        bounce_horizontal: bool = True,
        bounce_vertical: bool = True,
        on_bounce: Callable[[arcade.Sprite, str], None] | None = None,
    ):
        """Initialize the bounded move action.

        Args:
            get_bounds: Function returning (left, bottom, right, top) bounds
            movement_action: The movement action to bound (typically MoveUntil/MoveWhile)
            bounce_horizontal: Whether to bounce on horizontal boundaries
            bounce_vertical: Whether to bounce on vertical boundaries
            on_bounce: Optional callback when bouncing occurs
        """
        super().__init__()
        self.get_bounds = get_bounds
        self.movement_action = movement_action
        self.bounce_horizontal = bounce_horizontal
        self.bounce_vertical = bounce_vertical
        self.on_bounce = on_bounce

    def start(self) -> None:
        """Start the bounded movement action."""
        super().start()
        self.movement_action.target = self.target
        self.movement_action.start()

    def update(self, delta_time: float) -> None:
        """Update movement and handle bouncing."""
        if self._paused:
            return

        # Update the contained movement action first
        if not self.movement_action.done:
            self.movement_action.update(delta_time)

        # Check for bouncing on each sprite
        for sprite in self._iter_target():
            self._check_bounce(sprite)

        # Done when movement action is done
        if self.movement_action.done:
            self.done = True

    def _check_bounce(self, sprite: arcade.Sprite) -> None:
        """Check if sprite needs bouncing and apply it."""
        bounds = self.get_bounds()
        left, bottom, right, top = bounds

        bounced = False
        bounce_axis = None

        # Check horizontal boundaries
        if self.bounce_horizontal and sprite.change_x != 0:
            hit_box = sprite.hit_box
            sprite_left, sprite_right = hit_box.left, hit_box.right

            if (sprite.change_x > 0 and sprite_right >= right) or (sprite.change_x < 0 and sprite_left <= left):
                # Reverse horizontal velocity
                sprite.change_x = -sprite.change_x

                # Also reverse velocity in the movement action if supported
                if hasattr(self.movement_action, "set_current_velocity"):
                    dx, dy = self.movement_action.current_velocity
                    self.movement_action.set_current_velocity((-dx, dy))

                # Position correction to prevent sticking
                if sprite_right >= right:
                    sprite.center_x = right - sprite.width / 2
                elif sprite_left <= left:
                    sprite.center_x = left + sprite.width / 2

                bounced = True
                bounce_axis = "x"

        # Check vertical boundaries
        if self.bounce_vertical and sprite.change_y != 0:
            hit_box = sprite.hit_box
            sprite_bottom, sprite_top = hit_box.bottom, hit_box.top

            if (sprite.change_y > 0 and sprite_top >= top) or (sprite.change_y < 0 and sprite_bottom <= bottom):
                # Reverse vertical velocity
                sprite.change_y = -sprite.change_y

                # Also reverse velocity in the movement action if supported
                if hasattr(self.movement_action, "set_current_velocity"):
                    dx, dy = self.movement_action.current_velocity
                    self.movement_action.set_current_velocity((dx, -dy))

                # Position correction to prevent sticking
                if sprite_top >= top:
                    sprite.center_y = top - sprite.height / 2
                elif sprite_bottom <= bottom:
                    sprite.center_y = bottom + sprite.height / 2

                bounced = True
                bounce_axis = "y"

        # Trigger callback if bouncing occurred
        if bounced and self.on_bounce:
            self.on_bounce(sprite, bounce_axis)

    def stop(self) -> None:
        """Stop the bounded movement action."""
        if self.movement_action:
            self.movement_action.stop()
        super().stop()

    def pause(self) -> None:
        """Pause the bounded movement action."""
        if self.movement_action:
            self.movement_action.pause()
        super().pause()

    def resume(self) -> None:
        """Resume the bounded movement action."""
        if self.movement_action:
            self.movement_action.resume()
        super().resume()

    def clone(self) -> "BoundedMove":
        """Create a copy of this BoundedMove action."""
        return BoundedMove(
            self.get_bounds,
            self.movement_action.clone(),
            bounce_horizontal=self.bounce_horizontal,
            bounce_vertical=self.bounce_vertical,
            on_bounce=self.on_bounce,
        )

    def _iter_target(self):
        """Iterate over target sprites."""
        try:
            return iter(self.target)  # type: ignore[not-an-iterable]
        except TypeError:
            return [self.target]
