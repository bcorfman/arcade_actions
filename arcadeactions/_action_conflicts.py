from __future__ import annotations

from typing import Any

from ._action_targets import adapt_target


def check_action_conflicts(new_action: Any, target: Any) -> None:
    """Check for conflicts between the new action and existing actions on the target."""
    import os
    import warnings

    if not os.getenv("ACTIONS_WARN_CONFLICTS"):
        return

    new_conflicts = new_action.__class__._conflicts_with
    if not new_conflicts:
        return

    new_conflict_set = set(new_conflicts)
    from ._action_core import Action

    existing_actions = Action.get_actions_for_target(target)
    conflicting_actions = []

    for existing_action in existing_actions:
        if existing_action is new_action:
            continue
        existing_conflicts = existing_action.__class__._conflicts_with
        existing_conflict_set = set(existing_conflicts)
        if new_conflict_set & existing_conflict_set:
            conflicting_actions.append(existing_action)

    adapter = adapt_target(target)
    for sprite in adapter.iter_sprites():
        sprite_actions = Action.get_actions_for_target(sprite)
        for sprite_action in sprite_actions:
            sprite_conflicts = sprite_action.__class__._conflicts_with
            sprite_conflict_set = set(sprite_conflicts)
            if new_conflict_set & sprite_conflict_set:
                conflicting_actions.append(sprite_action)

    for sprite_list in adapter.iter_sprite_lists():
        list_actions = Action.get_actions_for_target(sprite_list)
        for list_action in list_actions:
            list_conflicts = list_action.__class__._conflicts_with
            list_conflict_set = set(list_conflicts)
            if new_conflict_set & list_conflict_set:
                conflicting_actions.append(list_action)

    if conflicting_actions:
        conflict_names = ", ".join(set(new_conflicts))
        existing_class_names = ", ".join(set(type(a).__name__ for a in conflicting_actions))
        new_class_name = type(new_action).__name__

        warnings.warn(
            f"Detected overlapping action conflicts ({conflict_names}): "
            f"{new_class_name}(tag={new_action.tag!r}) conflicts with {existing_class_names} "
            f"on the same target. Consider using replace=True or stopping existing actions first.",
            RuntimeWarning,
            stacklevel=3,
        )
