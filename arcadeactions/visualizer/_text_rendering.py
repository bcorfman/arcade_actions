"""Text rendering helpers for ACE visualizer."""

from __future__ import annotations

from typing import NamedTuple

import arcade


class _TextSpec(NamedTuple):
    """Description of a text element that will be rendered."""

    text: str
    x: float
    y: float
    color: arcade.Color
    font_size: int
    bold: bool = False


def _sync_text_objects(
    text_objects: list[arcade.Text],
    specs: list[_TextSpec],
    last_specs: list[_TextSpec],
) -> None:
    """
    Ensure text objects mirror the provided specifications.

    Rebuilds the cached text objects only when the specifications change to avoid
    interacting with arcade.Text properties before an OpenGL context is active.
    """

    if last_specs == specs:
        return

    text_objects.clear()
    if not specs:
        last_specs.clear()
        return

    for spec in specs:
        text_objects.append(
            arcade.Text(
                spec.text,
                spec.x,
                spec.y,
                spec.color,
                spec.font_size,
                bold=spec.bold,
            )
        )

    last_specs[:] = list(specs)
