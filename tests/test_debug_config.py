"""Tests for configurable debug logging system."""

import pytest

from actions import (
    Action,
    CallbackUntil,
    MoveUntil,
    RotateUntil,
    clear_observed_actions,
    duration,
    get_debug_actions,
    get_debug_options,
    infinite,
    observe_actions,
    set_debug_actions,
    set_debug_options,
)


class TestDebugConfiguration:
    """Test suite for debug configuration API."""

    def setup_method(self):
        """Reset debug config before each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def teardown_method(self):
        """Clean up after each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def test_set_debug_options_level(self):
        """Test setting debug level."""
        set_debug_options(level=2)
        options = get_debug_options()
        assert options["level"] == 2
        assert Action.debug_level == 2

    def test_set_debug_options_include_all(self):
        """Test setting include_all flag."""
        set_debug_options(level=1, include_all=True)
        options = get_debug_options()
        assert options["include_all"] is True
        assert Action.debug_all is True

    def test_set_debug_options_include_classes(self):
        """Test setting include filter with class types."""
        set_debug_options(level=2, include=[MoveUntil, CallbackUntil])
        options = get_debug_options()
        assert "MoveUntil" in options["include"]
        assert "CallbackUntil" in options["include"]
        assert "MoveUntil" in Action.debug_include_classes
        assert "CallbackUntil" in Action.debug_include_classes

    def test_set_debug_options_include_strings(self):
        """Test setting include filter with string names."""
        set_debug_options(level=2, include=["MoveUntil", "RotateUntil"])
        options = get_debug_options()
        assert "MoveUntil" in options["include"]
        assert "RotateUntil" in options["include"]

    def test_observe_actions_adds_to_filter(self):
        """Test observe_actions adds classes to filter."""
        observe_actions(MoveUntil, "CallbackUntil")
        assert "MoveUntil" in Action.debug_include_classes
        assert "CallbackUntil" in Action.debug_include_classes

    def test_observe_actions_accumulates(self):
        """Test observe_actions accumulates classes."""
        observe_actions(MoveUntil)
        observe_actions(CallbackUntil)
        assert "MoveUntil" in Action.debug_include_classes
        assert "CallbackUntil" in Action.debug_include_classes

    def test_clear_observed_actions(self):
        """Test clearing observed actions."""
        observe_actions(MoveUntil, CallbackUntil)
        assert Action.debug_include_classes is not None
        clear_observed_actions()
        assert Action.debug_include_classes is None

    def test_back_compat_set_debug_actions_true(self):
        """Test back-compat: set_debug_actions(True) sets level 1."""
        set_debug_actions(True)
        assert Action.debug_level == 1
        assert get_debug_actions() is True

    def test_back_compat_set_debug_actions_false(self):
        """Test back-compat: set_debug_actions(False) sets level 0."""
        set_debug_actions(False)
        assert Action.debug_level == 0
        assert get_debug_actions() is False

    def test_get_debug_options_returns_dict(self):
        """Test get_debug_options returns correct structure."""
        set_debug_options(level=3, include_all=True, include=["MoveUntil"])
        options = get_debug_options()
        assert isinstance(options, dict)
        assert "level" in options
        assert "include_all" in options
        assert "include" in options
        assert options["level"] == 3
        assert options["include_all"] is True
        assert "MoveUntil" in options["include"]


class TestDebugLogging:
    """Test suite for debug logging behavior."""

    def setup_method(self):
        """Reset debug config before each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def teardown_method(self):
        """Clean up after each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def test_level_0_no_output(self, capsys, test_sprite):
        """Test level 0 produces no output."""
        set_debug_options(level=0, include_all=True)

        action = MoveUntil((5, 0), duration(1.0))
        action.apply(test_sprite, tag="test")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_level_1_summary_on_change(self, capsys, test_sprite):
        """Test level 1 shows summary only when counts change."""
        set_debug_options(level=1, include_all=True)

        # First action - should log
        action1 = MoveUntil((5, 0), infinite)
        action1.apply(test_sprite, tag="test1")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        assert "[AA L1 summary]" in captured.out
        assert "Total=1" in captured.out
        assert "MoveUntil=1" in captured.out

        # Same action - no new log
        Action.update_all(0.016)
        captured = capsys.readouterr()
        assert captured.out == ""

        # Add second action - should log
        action2 = RotateUntil(180, infinite)
        action2.apply(test_sprite, tag="test2")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        assert "[AA L1 summary]" in captured.out
        assert "Total=2" in captured.out

    def test_level_2_creation_filtered(self, capsys, test_sprite):
        """Test level 2 shows creation only for observed actions."""
        set_debug_options(level=2, include=["MoveUntil"])

        # MoveUntil - should log creation at L2
        action1 = MoveUntil((5, 0), infinite)
        action1.apply(test_sprite, tag="movement")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        assert "[AA L2 MoveUntil]" in captured.out
        assert "created" in captured.out

        # RotateUntil - L1 summary shows it, but no L2 creation log
        capsys.readouterr()  # Clear
        action2 = RotateUntil(180, infinite)
        action2.apply(test_sprite, tag="rotation")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        # L1 summary includes all actions (not filtered)
        assert "RotateUntil=1" in captured.out
        # But no L2 creation log for RotateUntil (it's filtered out)
        assert "[AA L2 RotateUntil]" not in captured.out

    def test_level_2_all_actions(self, capsys, test_sprite):
        """Test level 2 with include_all shows all actions."""
        set_debug_options(level=2, include_all=True)

        action1 = MoveUntil((5, 0), infinite)
        action1.apply(test_sprite, tag="test1")
        action2 = RotateUntil(180, infinite)
        action2.apply(test_sprite, tag="test2")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        assert "[AA L2 MoveUntil]" in captured.out
        assert "[AA L2 RotateUntil]" in captured.out
        assert "created" in captured.out

    def test_lifecycle_logging_level_2(self, capsys, test_sprite):
        """Test lifecycle events log at level 2."""
        set_debug_options(level=2, include=["MoveUntil"])

        condition_met = False

        def condition():
            return condition_met

        action = MoveUntil((5, 0), condition)
        action.apply(test_sprite, tag="test")

        captured = capsys.readouterr()
        assert "[AA L2 MoveUntil] start()" in captured.out

        # Trigger condition to stop action
        capsys.readouterr()  # Clear
        condition_met = True
        Action.update_all(0.016)
        # Action completes in update, removal detected on next update
        Action.update_all(0.016)

        captured = capsys.readouterr()
        # Action completes and is removed - check for removal log
        assert "[AA L2 MoveUntil] removed" in captured.out

    def test_filter_excludes_unobserved(self, capsys, test_sprite):
        """Test that unobserved actions produce no level 2+ output."""
        set_debug_options(level=3, include=["MoveUntil"])

        # CallbackUntil not in filter - should not log at L2 or L3
        def callback():
            pass

        action = CallbackUntil(callback, duration(1.0))
        action.apply(test_sprite, tag="test")
        Action.update_all(0.016)

        captured = capsys.readouterr()
        # L1 summary shows all actions (not filtered)
        assert "CallbackUntil=1" in captured.out
        # But no L2/L3 logs for CallbackUntil (it's filtered out)
        assert "[AA L2 CallbackUntil]" not in captured.out
        assert "[AA L3 CallbackUntil]" not in captured.out


class TestDebugEnvironmentConfig:
    """Test environment variable configuration."""

    def setup_method(self):
        """Reset debug config before each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def teardown_method(self):
        """Clean up after each test."""
        set_debug_options(level=0, include_all=False, include=None)
        Action.stop_all()

    def test_env_debug_numeric_level(self, monkeypatch):
        """Test ARCADEACTIONS_DEBUG with numeric level."""
        from actions.config import apply_environment_configuration

        monkeypatch.setenv("ARCADEACTIONS_DEBUG", "2")
        apply_environment_configuration()

        assert Action.debug_level == 2

    def test_env_debug_boolean_true(self, monkeypatch):
        """Test ARCADEACTIONS_DEBUG with boolean values."""
        from actions.config import apply_environment_configuration

        monkeypatch.setenv("ARCADEACTIONS_DEBUG", "true")
        apply_environment_configuration()

        assert Action.debug_level == 1

    def test_env_debug_all_flag(self, monkeypatch):
        """Test ARCADEACTIONS_DEBUG_ALL environment variable."""
        from actions.config import apply_environment_configuration

        monkeypatch.setenv("ARCADEACTIONS_DEBUG", "2")
        monkeypatch.setenv("ARCADEACTIONS_DEBUG_ALL", "1")
        apply_environment_configuration()

        assert Action.debug_level == 2
        assert Action.debug_all is True

    def test_env_debug_include_classes(self, monkeypatch):
        """Test ARCADEACTIONS_DEBUG_INCLUDE environment variable."""
        from actions.config import apply_environment_configuration

        monkeypatch.setenv("ARCADEACTIONS_DEBUG", "2")
        monkeypatch.setenv("ARCADEACTIONS_DEBUG_INCLUDE", "MoveUntil,CallbackUntil")
        apply_environment_configuration()

        assert Action.debug_level == 2
        assert "MoveUntil" in Action.debug_include_classes
        assert "CallbackUntil" in Action.debug_include_classes


@pytest.fixture
def test_sprite():
    """Create a test sprite."""
    import arcade

    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite
