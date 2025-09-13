"""Test suite for config.py - Runtime configuration."""

import os
from unittest.mock import patch

from actions import Action
from actions.config import (
    _ENV_DEBUG_FLAG,
    apply_environment_configuration,
    get_debug_actions,
    set_debug_actions,
)


class TestSetDebugActions:
    """Test suite for set_debug_actions function."""

    def test_set_debug_actions_enable(self):
        """Test enabling debug actions."""
        # Reset to known state
        Action.debug_actions = False

        set_debug_actions(True)
        assert Action.debug_actions is True

    def test_set_debug_actions_disable(self):
        """Test disabling debug actions."""
        # Reset to known state
        Action.debug_actions = True

        set_debug_actions(False)
        assert Action.debug_actions is False

    def test_set_debug_actions_truthy_values(self):
        """Test that truthy values enable debug actions."""
        Action.debug_actions = False

        # Test various truthy values
        for value in [1, "yes", "true", [1, 2, 3], {"key": "value"}]:
            set_debug_actions(value)
            assert Action.debug_actions is True

    def test_set_debug_actions_falsy_values(self):
        """Test that falsy values disable debug actions."""
        Action.debug_actions = True

        # Test various falsy values
        for value in [0, "", None, [], {}]:
            set_debug_actions(value)
            assert Action.debug_actions is False

    def test_set_debug_actions_boolean_conversion(self):
        """Test that values are converted to boolean."""
        Action.debug_actions = False

        # Test that non-boolean values are converted
        set_debug_actions("false")  # Non-empty string is truthy
        assert Action.debug_actions is True

        set_debug_actions(0)  # Zero is falsy
        assert Action.debug_actions is False


class TestGetDebugActions:
    """Test suite for get_debug_actions function."""

    def test_get_debug_actions_returns_current_state(self):
        """Test that get_debug_actions returns current debug state."""
        Action.debug_actions = True
        assert get_debug_actions() is True

        Action.debug_actions = False
        assert get_debug_actions() is False

    def test_get_debug_actions_boolean_conversion(self):
        """Test that get_debug_actions converts to boolean."""
        # Test with non-boolean values
        Action.debug_actions = "true"
        assert get_debug_actions() is True

        Action.debug_actions = ""
        assert get_debug_actions() is False

        Action.debug_actions = 1
        assert get_debug_actions() is True

        Action.debug_actions = 0
        assert get_debug_actions() is False


class TestApplyEnvironmentConfiguration:
    """Test suite for apply_environment_configuration function."""

    def test_apply_environment_configuration_no_env_var(self):
        """Test when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset to known state
            Action.debug_actions = False

            apply_environment_configuration()
            assert Action.debug_actions is False

    def test_apply_environment_configuration_env_var_none(self):
        """Test when environment variable is explicitly None."""
        # Remove the environment variable instead of setting it to None
        with patch.dict(os.environ, {}, clear=True):
            # Ensure the variable is not set
            if _ENV_DEBUG_FLAG in os.environ:
                del os.environ[_ENV_DEBUG_FLAG]

            Action.debug_actions = False

            apply_environment_configuration()
            assert Action.debug_actions is False

    def test_apply_environment_configuration_enable_values(self):
        """Test enabling debug actions with various environment values."""
        enable_values = ["1", "true", "yes", "on", "TRUE", "YES", "ON", "True", "Yes", "On"]

        for value in enable_values:
            with patch.dict(os.environ, {_ENV_DEBUG_FLAG: value}, clear=True):
                Action.debug_actions = False
                apply_environment_configuration()
                assert Action.debug_actions is True, f"Failed for value: {value}"

    def test_apply_environment_configuration_disable_values(self):
        """Test disabling debug actions with various environment values."""
        disable_values = ["0", "false", "no", "off", "FALSE", "NO", "OFF", "False", "No", "Off", "anything_else"]

        for value in disable_values:
            with patch.dict(os.environ, {_ENV_DEBUG_FLAG: value}, clear=True):
                Action.debug_actions = True
                apply_environment_configuration()
                assert Action.debug_actions is False, f"Failed for value: {value}"

    def test_apply_environment_configuration_whitespace_handling(self):
        """Test that whitespace is stripped from environment values."""
        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "  true  "}, clear=True):
            Action.debug_actions = False
            apply_environment_configuration()
            assert Action.debug_actions is True

        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "  false  "}, clear=True):
            Action.debug_actions = True
            apply_environment_configuration()
            assert Action.debug_actions is False

    def test_apply_environment_configuration_empty_string(self):
        """Test that empty string disables debug actions."""
        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: ""}, clear=True):
            Action.debug_actions = True
            apply_environment_configuration()
            assert Action.debug_actions is False

    def test_apply_environment_configuration_whitespace_only(self):
        """Test that whitespace-only string disables debug actions."""
        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "   "}, clear=True):
            Action.debug_actions = True
            apply_environment_configuration()
            assert Action.debug_actions is False


class TestEnvironmentFlagConstant:
    """Test suite for _ENV_DEBUG_FLAG constant."""

    def test_env_debug_flag_constant(self):
        """Test that _ENV_DEBUG_FLAG has the expected value."""
        assert _ENV_DEBUG_FLAG == "ARCADEACTIONS_DEBUG"


class TestIntegration:
    """Integration tests for config module."""

    def test_set_get_debug_actions_integration(self):
        """Test integration between set_debug_actions and get_debug_actions."""
        # Test round-trip
        set_debug_actions(True)
        assert get_debug_actions() is True

        set_debug_actions(False)
        assert get_debug_actions() is False

    def test_environment_configuration_integration(self):
        """Test integration with environment configuration."""
        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "true"}, clear=True):
            apply_environment_configuration()
            assert get_debug_actions() is True

        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "false"}, clear=True):
            apply_environment_configuration()
            assert get_debug_actions() is False

    def test_multiple_calls_consistency(self):
        """Test that multiple calls maintain consistency."""
        # Set via function
        set_debug_actions(True)
        assert get_debug_actions() is True

        # Set via environment
        with patch.dict(os.environ, {_ENV_DEBUG_FLAG: "false"}, clear=True):
            apply_environment_configuration()
            assert get_debug_actions() is False

        # Set via function again
        set_debug_actions(True)
        assert get_debug_actions() is True

    def test_action_debug_actions_direct_access(self):
        """Test that functions work with direct Action.debug_actions access."""
        # Set via function
        set_debug_actions(True)
        assert Action.debug_actions is True

        # Modify directly
        Action.debug_actions = False
        assert get_debug_actions() is False

        # Set via function again
        set_debug_actions(True)
        assert Action.debug_actions is True
