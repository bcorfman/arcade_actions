"""Test suite for action overlap prevention and conflict detection.

Tests tag-based replacement and automatic conflict detection to prevent
overlapping actions that mutate the same sprite properties.
"""

import os
import warnings

import arcade

from actions import Action
from actions.conditional import CycleTexturesUntil, FadeUntil, MoveUntil, RotateUntil, infinite


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.SpriteSolidColor(width=32, height=32, color=arcade.color.WHITE)
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class MockActionWithConflicts(Action):
    """Mock action for testing conflict detection."""

    # Class-level conflict declaration
    _conflicts_with = ("position", "velocity")

    def __init__(self, condition=None, on_stop=None):
        if condition is None:
            condition = lambda: False
        super().__init__(condition=condition, on_stop=on_stop)

    def update_effect(self, delta_time: float) -> None:
        pass

    def clone(self) -> Action:
        return MockActionWithConflicts(condition=self.condition, on_stop=self.on_stop)


class TestTagBasedReplacement:
    """Test suite for tag-based single-occupancy replacement."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()

    def test_replace_true_stops_existing_action_with_same_tag(self):
        """Test that replace=True stops existing actions with same target+tag."""
        sprite = create_test_sprite()
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        # Apply first action with tag
        action1.apply(sprite, tag="movement")
        assert action1._is_active
        assert action1 in Action._active_actions

        # Apply second action with same tag and replace=True
        action2.apply(sprite, tag="movement", replace=True)

        # First action should be stopped
        assert not action1._is_active
        assert action1.done
        assert action1 not in Action._active_actions

        # Second action should be active
        assert action2._is_active
        assert action2 in Action._active_actions

    def test_replace_false_allows_overlapping_actions_same_tag(self):
        """Test that replace=False (default) allows overlapping actions with same tag."""
        sprite = create_test_sprite()
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        # Apply first action with tag
        action1.apply(sprite, tag="movement")
        assert action1._is_active

        # Apply second action with same tag and replace=False (default)
        action2.apply(sprite, tag="movement", replace=False)

        # Both actions should be active
        assert action1._is_active
        assert action2._is_active
        assert action1 in Action._active_actions
        assert action2 in Action._active_actions

    def test_replace_true_only_affects_same_tag(self):
        """Test that replacement only affects actions with the same tag."""
        sprite = create_test_sprite()
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)
        action3 = RotateUntil(5, infinite)

        # Apply actions with different tags
        action1.apply(sprite, tag="movement")
        action3.apply(sprite, tag="rotation")

        assert action1._is_active
        assert action3._is_active

        # Apply action with replace=True for "movement" tag
        action2.apply(sprite, tag="movement", replace=True)

        # action1 should be stopped (same tag)
        assert not action1._is_active
        # action3 should still be active (different tag)
        assert action3._is_active
        # action2 should be active
        assert action2._is_active

    def test_replace_true_requires_tag(self):
        """Test that replace=True only works when a tag is provided."""
        sprite = create_test_sprite()
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        # Apply first action without tag
        action1.apply(sprite)
        assert action1._is_active

        # Apply second action without tag and replace=True
        # Should not replace (no tag to match against)
        action2.apply(sprite, replace=True)

        # Both actions should be active (replace only works with tags)
        assert action1._is_active
        assert action2._is_active

    def test_replace_true_stops_multiple_actions_same_tag(self):
        """Test that replace=True stops all existing actions with same tag."""
        sprite = create_test_sprite()
        action1 = MoveUntil((5, 0), infinite)
        action2 = RotateUntil(5, infinite)
        action3 = MoveUntil((10, 0), infinite)

        # Apply multiple actions with same tag
        action1.apply(sprite, tag="movement")
        action2.apply(sprite, tag="movement")

        assert action1._is_active
        assert action2._is_active

        # Apply new action with replace=True
        action3.apply(sprite, tag="movement", replace=True)

        # Both previous actions should be stopped
        assert not action1._is_active
        assert not action2._is_active
        # New action should be active
        assert action3._is_active

    def test_replace_true_no_existing_actions(self):
        """Test that replace=True works even when no existing actions exist."""
        sprite = create_test_sprite()
        action = MoveUntil((5, 0), infinite)

        # Apply with replace=True when no actions exist yet
        action.apply(sprite, tag="movement", replace=True)

        # Should work normally (no error, action is active)
        assert action._is_active
        assert action in Action._active_actions


class TestConflictDetection:
    """Test suite for automatic conflict detection."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
        # Reset environment variable
        if "ACTIONS_WARN_CONFLICTS" in os.environ:
            del os.environ["ACTIONS_WARN_CONFLICTS"]

    def test_conflict_warning_logged_when_env_var_set(self, monkeypatch):
        """Test that warnings are logged when env var is set and conflicts detected."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite = create_test_sprite()

        # MoveUntil conflicts with position, velocity
        # Apply two MoveUntil actions - should conflict
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        action1.apply(sprite, tag="move1")

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite, tag="move2")

            # Should have at least one warning about conflict
            assert len(w) >= 1
            assert any("conflict" in str(warning.message).lower() for warning in w)
            assert any("MoveUntil" in str(warning.message) for warning in w)

    def test_no_warning_when_env_var_not_set(self, monkeypatch):
        """Test that no warnings are logged when env var is not set."""
        # Delete the env var (fixture sets it, so we need to remove it)
        monkeypatch.delenv("ACTIONS_WARN_CONFLICTS", raising=False)
        sprite = create_test_sprite()

        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        action1.apply(sprite, tag="move1")

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite, tag="move2")

            # Should have no conflict warnings
            conflict_warnings = [warning for warning in w if "conflict" in str(warning.message).lower()]
            assert len(conflict_warnings) == 0

    def test_no_warning_for_non_conflicting_actions(self, monkeypatch):
        """Test that no warnings are logged for actions that don't conflict."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite = create_test_sprite()

        # MoveUntil and RotateUntil don't conflict (different properties)
        action1 = MoveUntil((5, 0), infinite)
        action2 = RotateUntil(5, infinite)

        action1.apply(sprite, tag="move")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite, tag="rotate")

            # Should have no conflict warnings
            conflict_warnings = [warning for warning in w if "conflict" in str(warning.message).lower()]
            assert len(conflict_warnings) == 0

    def test_conflict_detection_sprite_list_vs_per_sprite(self, monkeypatch):
        """Test that SpriteList actions conflict with per-sprite actions."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite_list = arcade.SpriteList()
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()
        sprite_list.append(sprite1)
        sprite_list.append(sprite2)

        # Apply action to SpriteList
        list_action = MoveUntil((5, 0), infinite)
        list_action.apply(sprite_list, tag="list_move")

        # Apply conflicting action to individual sprite
        sprite_action = MoveUntil((10, 0), infinite)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            sprite_action.apply(sprite1, tag="sprite_move")

            # Should have warning about conflict between list and sprite actions
            assert len(w) >= 1
            assert any("conflict" in str(warning.message).lower() for warning in w)

    def test_conflict_detection_only_same_target(self, monkeypatch):
        """Test that conflicts are only detected for same target."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite1 = create_test_sprite()
        sprite2 = create_test_sprite()

        # Apply MoveUntil to sprite1
        action1 = MoveUntil((5, 0), infinite)
        action1.apply(sprite1, tag="move1")

        # Apply MoveUntil to sprite2 (different target)
        action2 = MoveUntil((5, 0), infinite)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite2, tag="move2")

            # Should have no conflict warnings (different targets)
            conflict_warnings = [warning for warning in w if "conflict" in str(warning.message).lower()]
            assert len(conflict_warnings) == 0

    def test_multiple_conflicts_detected(self, monkeypatch):
        """Test that multiple conflicting actions are all detected."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite = create_test_sprite()

        # Apply multiple MoveUntil actions
        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)
        action3 = MoveUntil((15, 0), infinite)

        action1.apply(sprite, tag="move1")
        # Suppress warning from action2.apply since we're testing action3's conflict detection
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            action2.apply(sprite, tag="move2")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action3.apply(sprite, tag="move3")

            # Should detect conflicts with both existing actions
            assert len(w) >= 1
            # Warning should mention multiple conflicts
            warning_messages = [str(warning.message) for warning in w]
            assert any("conflict" in msg.lower() for msg in warning_messages)


class TestConflictDeclaration:
    """Test suite for conflict declaration in action classes."""

    def test_move_until_declares_conflicts(self):
        """Test that MoveUntil declares position and velocity conflicts."""
        # MoveUntil should declare conflicts with position and velocity
        conflicts = MoveUntil._conflicts_with
        assert "position" in conflicts or "velocity" in conflicts

    def test_rotate_until_declares_conflicts(self):
        """Test that RotateUntil declares angle conflicts."""
        conflicts = RotateUntil._conflicts_with
        assert "angle" in conflicts or "rotation" in conflicts

    def test_fade_until_declares_conflicts(self):
        """Test that FadeUntil declares alpha conflicts."""
        conflicts = FadeUntil._conflicts_with
        assert "alpha" in conflicts

    def test_cycle_textures_until_declares_conflicts(self):
        """Test that CycleTexturesUntil declares texture conflicts."""
        conflicts = CycleTexturesUntil._conflicts_with
        assert "texture" in conflicts

    def test_conflict_declaration_is_tuple(self):
        """Test that _conflicts_with is a tuple or tuple-like."""
        conflicts = MoveUntil._conflicts_with
        assert isinstance(conflicts, (tuple, list, set))
        # Should be iterable
        assert hasattr(conflicts, "__iter__")


class TestStrictModeFixture:
    """Test suite for strict-mode pytest fixture."""

    def test_strict_mode_fixture_enables_warnings(self, enable_action_safety):
        """Test that strict-mode fixture enables conflict warnings."""
        sprite = create_test_sprite()

        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        action1.apply(sprite, tag="move1")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite, tag="move2")

            # Should have conflict warning (fixture enabled warnings)
            assert len(w) >= 1
            assert any("conflict" in str(warning.message).lower() for warning in w)


class TestCombinedFeatures:
    """Test suite for combined features (replacement + conflict detection)."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.stop_all()
        if "ACTIONS_WARN_CONFLICTS" in os.environ:
            del os.environ["ACTIONS_WARN_CONFLICTS"]

    def test_replace_prevents_conflict_warning(self, monkeypatch):
        """Test that using replace=True prevents conflict warnings."""
        monkeypatch.setenv("ACTIONS_WARN_CONFLICTS", "1")
        sprite = create_test_sprite()

        action1 = MoveUntil((5, 0), infinite)
        action2 = MoveUntil((10, 0), infinite)

        action1.apply(sprite, tag="movement")

        # Use replace=True - should not generate conflict warning
        # because old action is stopped before new one is applied
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            action2.apply(sprite, tag="movement", replace=True)

            # Should have no conflict warnings (replacement happened first)
            conflict_warnings = [warning for warning in w if "conflict" in str(warning.message).lower()]
            assert len(conflict_warnings) == 0

            # But action1 should be stopped
            assert not action1._is_active
