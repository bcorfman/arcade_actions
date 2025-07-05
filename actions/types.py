"""Type aliases for the Arcade Actions system."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import arcade

SpriteTarget = arcade.Sprite | arcade.SpriteList
ConditionFunc = Callable[[], Any]
ActionCallback = Callable[[Any], None] | Callable[[], None] | None
