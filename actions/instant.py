from __future__ import annotations

from collections.abc import Callable

from .base import ActionSprite, InstantAction


class Place(InstantAction):
    """
    Sets the sprite's position to a specified (x, y) coordinate.

    Attributes:
        position (Tuple[float, float]): Target (x, y) coordinates for the sprite.
    """

    def __init__(self, position: tuple[float, float]) -> None:
        """Initialize with target position."""
        super().__init__()
        self.position: tuple[float, float] = position

    def update(self, t: float) -> None:
        """Set the sprite's center_x and center_y to the specified position."""
        if self.target:
            self.target.center_x, self.target.center_y = self.position


class Hide(InstantAction):
    """
    Makes the sprite invisible by setting its alpha to 0.
    """

    def update(self, t: float) -> None:
        """Set the sprite's alpha to 0 to hide it."""
        if self.target:
            self.target.alpha = 0


class Show(InstantAction):
    """
    Makes the sprite visible by setting its alpha to 255.
    """

    def update(self, t: float) -> None:
        """Set the sprite's alpha to 255 to show it."""
        if self.target:
            self.target.alpha = 255


class ToggleVisibility(InstantAction):
    """
    Toggles the sprite's visibility by changing its alpha between 0 and 255.
    """

    def update(self, t: float) -> None:
        """Toggle the sprite's alpha between 0 (hidden) and 255 (visible)."""
        if self.target:
            self.target.alpha = 0 if self.target.alpha > 0 else 255


class CallFunc(InstantAction):
    """
    Calls a specified function when executed.

    Attributes:
        func (Callable[[], None]): The function to be called.
    """

    def __init__(self, func: Callable[[], None]) -> None:
        """Initialize with the function to call."""
        super().__init__()
        self.func: Callable[[], None] = func

    def update(self, t: float) -> None:
        """Call the specified function."""
        self.func()


class CallFuncS(InstantAction):
    """
    Calls a specified function, passing the sprite as the first argument.

    Attributes:
        func (Callable[[ActionSprite], None]): The function to be called, with the sprite as argument.
    """

    def __init__(self, func: Callable[[ActionSprite], None]) -> None:
        """Initialize with the function to call."""
        super().__init__()
        self.func: Callable[[ActionSprite], None] = func

    def update(self, t: float) -> None:
        """Call the function, passing the sprite as an argument."""
        if self.target:
            self.func(self.target)
