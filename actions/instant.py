from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any, TypeVar

from arcade import Sprite

from .base import InstantAction

T = TypeVar("T", bound=Sprite)  # Type variable for sprite subclasses


class Place(InstantAction):
    """Place a sprite at specific coordinates.

    This action immediately sets the sprite's position to the specified coordinates.
    No interpolation or animation occurs - the change is instantaneous.

    Args:
        position: Target (x,y) coordinates for placement

    Raises:
        ValueError: If position is None or contains invalid coordinates
        AttributeError: If target sprite lacks required position attributes
    """

    def init(self, position: tuple[float, float]) -> None:
        """Initialize the placement action.

        Args:
            position: A tuple of (x, y) coordinates where the sprite will be placed

        Raises:
            ValueError: If position is None or contains invalid coordinates
        """
        if position is None:
            raise ValueError("Position cannot be None")
        if not isinstance(position, (tuple, list)) or len(position) != 2:
            raise ValueError("Position must be a tuple of (x, y) coordinates")
        if not all(isinstance(coord, (int, float)) for coord in position):
            raise ValueError("Position coordinates must be numeric")

        self.position: tuple[float, float] = position

    def start(self) -> None:
        """Execute the placement action.

        Places the target at the specified position immediately.

        Raises:
            AttributeError: If target lacks required position attributes
        """
        if self.target is None:
            raise AttributeError("Target cannot be None")

        # Check for required position-related attributes
        required_attrs = ["center", "center_x", "center_y"]
        missing_attrs = [attr for attr in required_attrs if not hasattr(self.target, attr)]
        if missing_attrs:
            raise AttributeError(f"Target must have these attributes: {', '.join(missing_attrs)}")

        self.target.center = self.position


class Hide(InstantAction):
    """Instantly hide a sprite by setting its visibility to False.

    This action makes a sprite invisible immediately upon execution.
    The sprite can be made visible again using the Show action.

    Raises:
        AttributeError: If target lacks visibility attribute
    """

    def start(self) -> None:
        """Execute the hide action.

        Sets the target's visibility to False immediately.

        Raises:
            AttributeError: If target lacks required visibility attribute
        """
        if self.target is None:
            raise AttributeError("Target cannot be None")

        if not hasattr(self.target, "visible"):
            raise AttributeError("Target must have 'visible' attribute")

        self.target.visible = False

    def __reversed__(self) -> Show:
        """Return the reverse of this action (Show).

        Returns:
            Show: A new Show action instance
        """
        return Show()


class Show(InstantAction):
    """Instantly show a sprite by setting its visibility to True.

    This action makes a sprite visible immediately upon execution.
    The sprite can be hidden using the Hide action.

    Raises:
        AttributeError: If target lacks visibility attribute
    """

    def start(self) -> None:
        """Execute the show action.

        Sets the target's visibility to True immediately.

        Raises:
            AttributeError: If target lacks required visibility attribute
        """
        if self.target is None:
            raise AttributeError("Target cannot be None")

        if not hasattr(self.target, "visible"):
            raise AttributeError("Target must have 'visible' attribute")

        self.target.visible = True

    def __reversed__(self) -> Hide:
        """Return the reverse of this action (Hide).

        Returns:
            Hide: A new Hide action instance
        """
        return Hide()


class ToggleVisibility(InstantAction):
    """Toggle a sprite's visibility between visible and invisible states.

    This action switches the sprite's visibility to its opposite state:
    visible becomes invisible, and invisible becomes visible.

    Raises:
        AttributeError: If target lacks visibility attribute
    """

    def start(self) -> None:
        """Execute the visibility toggle action.

        Inverts the target's current visibility state.

        Raises:
            AttributeError: If target lacks required visibility attribute
        """
        if self.target is None:
            raise AttributeError("Target cannot be None")

        if not hasattr(self.target, "visible"):
            raise AttributeError("Target must have 'visible' attribute")

        self.target.visible = not self.target.visible

    def __reversed__(self) -> ToggleVisibility:
        """Return the reverse of this action (self, as toggle is self-reversing).

        Returns:
            ToggleVisibility: This same action instance
        """
        return self


class CallFunc(InstantAction):
    """Execute a callable function as an action.

    This action calls a specified function with provided arguments when started.

    Args:
        func: The function to be called
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Raises:
        ValueError: If the provided function is not callable
    """

    def init(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Initialize the function call action.

        Args:
            func: The function to be called
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Raises:
            ValueError: If func is None or not callable
        """
        if func is None:
            raise ValueError("Function cannot be None")
        if not callable(func):
            raise ValueError("Function must be callable")

        self.func: Callable[..., Any] = func
        self.args: tuple = args
        self.kwargs: dict = kwargs

    def start(self) -> None:
        """Execute the function call action.

        Calls the stored function with its arguments.

        Raises:
            Exception: Any exception that the called function might raise
        """
        self.func(*self.args, **self.kwargs)

    def __deepcopy__(self, memo: dict | None = None) -> CallFunc:
        """Create a shallow copy instead of a deep copy.

        Args:
            memo: Memoization dictionary (unused)

        Returns:
            CallFunc: A shallow copy of this action
        """
        return copy.copy(self)

    def __reversed__(self) -> CallFunc:
        """Return the reverse of this action (self).

        Returns:
            CallFunc: This same action instance
        """
        return self


class CallFuncS(CallFunc):
    """Execute a callable function with the target as first argument.

    This action extends CallFunc by injecting the target as the first
    argument to the function call.

    Args:
        func: The function to be called (first arg will be target)
        *args: Additional positional arguments
        **kwargs: Keyword arguments

    Raises:
        ValueError: If the provided function is not callable
        AttributeError: If target is None when started
    """

    def start(self) -> None:
        """Execute the function call action with target as first argument.

        Calls the stored function with the target as first argument,
        followed by any stored arguments.

        Raises:
            AttributeError: If target is None
            Exception: Any exception that the called function might raise
        """
        if self.target is None:
            raise AttributeError("Target cannot be None")

        self.func(self.target, *self.args, **self.kwargs)
