"""Tests for visualizer helper functions.

Tests the pure functions extracted from visualizer.py for better testability.
"""

from __future__ import annotations

from actions.dev.visualizer_helpers import resolve_callback, resolve_condition
from actions.frame_timing import after_frames, infinite, within_frames


class TestResolveCondition:
    """Test suite for resolve_condition function."""

    def test_resolve_condition_none(self):
        """Test resolving None returns infinite condition."""
        cond = resolve_condition(None)
        # Should return a callable (the result of infinite())
        assert callable(cond)
        # Should return False (never completes)
        assert cond() is False

    def test_resolve_condition_callable(self):
        """Test resolving a callable returns it unchanged."""

        def my_condition():
            return True

        result = resolve_condition(my_condition)
        assert result is my_condition
        assert result() is True

    def test_resolve_condition_infinite_string(self):
        """Test resolving 'infinite' string returns infinite condition."""
        cond = resolve_condition("infinite")
        assert callable(cond)
        assert cond() is False  # Never completes

    def test_resolve_condition_infinite_string_with_whitespace(self):
        """Test resolving 'infinite' string with whitespace."""
        cond = resolve_condition("  infinite  ")
        assert callable(cond)
        assert cond() is False

    def test_resolve_condition_after_frames(self):
        """Test resolving 'after_frames:N' string."""
        cond = resolve_condition("after_frames:60")
        assert callable(cond)
        # Should be equivalent to after_frames(60)
        expected = after_frames(60)
        # Both should be callables
        assert callable(cond)
        assert callable(expected)

    def test_resolve_condition_after_frames_invalid(self):
        """Test resolving invalid 'after_frames:' string falls back to infinite."""
        cond = resolve_condition("after_frames:")
        # Should fall back to infinite function (preserving original behavior)

        # Note: Original code returns 'infinite' function object in error cases
        assert cond is infinite

    def test_resolve_condition_after_frames_non_numeric(self):
        """Test resolving 'after_frames:abc' falls back to infinite."""
        cond = resolve_condition("after_frames:abc")

        assert cond is infinite

    def test_resolve_condition_after_seconds(self):
        """Test resolving 'after_seconds:N' string."""
        cond = resolve_condition("after_seconds:1.0")
        assert callable(cond)
        # Should convert seconds to frames

    def test_resolve_condition_seconds_alias(self):
        """Test resolving 'seconds:N' string (alias for after_seconds)."""
        cond = resolve_condition("seconds:0.5")
        assert callable(cond)

    def test_resolve_condition_after_seconds_invalid(self):
        """Test resolving invalid 'after_seconds:' string falls back to infinite."""
        cond = resolve_condition("after_seconds:")

        assert cond is infinite

    def test_resolve_condition_after_seconds_non_numeric(self):
        """Test resolving 'after_seconds:abc' falls back to infinite."""
        cond = resolve_condition("after_seconds:abc")

        assert cond is infinite

    def test_resolve_condition_within_frames(self):
        """Test resolving 'within_frames:S:E' string."""
        cond = resolve_condition("within_frames:10:20")
        assert callable(cond)
        # Should be equivalent to within_frames(10, 20)
        expected = within_frames(10, 20)
        assert callable(cond)
        assert callable(expected)

    def test_resolve_condition_within_frames_invalid(self):
        """Test resolving invalid 'within_frames:' string falls back to infinite."""
        cond = resolve_condition("within_frames:")

        assert cond is infinite

    def test_resolve_condition_within_frames_malformed(self):
        """Test resolving malformed 'within_frames:S:E' string falls back to infinite."""
        cond = resolve_condition("within_frames:10")

        assert cond is infinite

    def test_resolve_condition_unknown_string(self):
        """Test resolving unknown string falls back to infinite."""
        cond = resolve_condition("unknown_format")

        assert cond is infinite

    def test_resolve_condition_empty_string(self):
        """Test resolving empty string falls back to infinite."""
        cond = resolve_condition("")

        assert cond is infinite

    def test_resolve_condition_non_string_non_callable(self):
        """Test resolving non-string, non-callable falls back to infinite."""
        cond = resolve_condition(123)

        assert cond is infinite


class TestResolveCallback:
    """Test suite for resolve_callback function."""

    def test_resolve_callback_none(self):
        """Test resolving None returns None."""
        result = resolve_callback(None)
        assert result is None

    def test_resolve_callback_callable(self):
        """Test resolving a callable returns it unchanged."""

        def my_callback():
            return "result"

        result = resolve_callback(my_callback)
        assert result is my_callback
        assert result() == "result"

    def test_resolve_callback_string_with_resolver(self):
        """Test resolving string with resolver function."""

        def resolver(name: str):
            callbacks = {
                "callback1": lambda: "result1",
                "callback2": lambda: "result2",
            }
            return callbacks.get(name)

        result = resolve_callback("callback1", resolver)
        assert callable(result)
        assert result() == "result1"

    def test_resolve_callback_string_without_resolver(self):
        """Test resolving string without resolver returns None."""
        result = resolve_callback("some_string", None)
        assert result is None

    def test_resolve_callback_string_with_none_resolver(self):
        """Test resolving string with None resolver returns None."""
        result = resolve_callback("some_string", resolver=None)
        assert result is None

    def test_resolve_callback_string_resolver_returns_none(self):
        """Test resolving string when resolver returns None."""

        def resolver(name: str):
            return None

        result = resolve_callback("unknown", resolver)
        assert result is None

    def test_resolve_callback_string_resolver_exception(self):
        """Test resolving string when resolver raises exception returns None."""

        def resolver(name: str):
            raise ValueError("Resolver error")

        result = resolve_callback("callback", resolver)
        assert result is None

    def test_resolve_callback_non_string_non_callable(self):
        """Test resolving non-string, non-callable without resolver returns None."""
        result = resolve_callback(123)
        assert result is None

    def test_resolve_callback_string_resolver_returns_callable(self):
        """Test resolving string when resolver returns a callable."""

        def my_callback():
            return "success"

        def resolver(name: str):
            return my_callback

        result = resolve_callback("test", resolver)
        assert result is my_callback
        assert result() == "success"
