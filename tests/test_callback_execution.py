"""Test suite for callback execution implementation (_execute_callback_impl)."""

import warnings

from actions.base import Action


class TestCallbackExecution:
    """Test suite for _execute_callback_impl with clear exception strategy."""

    def setup_method(self):
        """Reset warning tracking before each test."""
        Action._warned_bad_callbacks.clear()
        Action.debug_level = 1  # Enable warnings by default

    def teardown_method(self):
        """Clean up after each test."""
        Action._warned_bad_callbacks.clear()
        Action.debug_level = 0  # Disable debug by default

    # --- Basic Functionality Tests ---

    def test_no_parameter_callback_executes(self):
        """No-parameter callback should execute successfully."""
        executed = []

        def callback():
            executed.append(True)

        Action._execute_callback_impl(callback)

        assert len(executed) == 1

    def test_with_parameter_callback_executes(self):
        """With-parameter callback should execute successfully with args."""
        received = []

        def callback(data):
            received.append(data)

        test_data = {"result": "success"}
        Action._execute_callback_impl(callback, test_data)

        assert len(received) == 1
        assert received[0] == test_data

    def test_callback_with_multiple_parameters(self):
        """Callback with multiple parameters should receive all args."""
        received = []

        def callback(sprite, axis, side):
            received.append((sprite, axis, side))

        Action._execute_callback_impl(callback, "sprite_obj", "x", "right")

        assert len(received) == 1
        assert received[0] == ("sprite_obj", "x", "right")

    def test_callback_with_defaults_no_args(self):
        """Callback with default parameters works with no args."""
        executed = []

        def callback(data=None):
            executed.append(data)

        Action._execute_callback_impl(callback)

        assert len(executed) == 1
        assert executed[0] is None

    def test_callback_with_defaults_with_args(self):
        """Callback with default parameters works with args."""
        received = []

        def callback(data=None):
            received.append(data)

        test_data = "test_value"
        Action._execute_callback_impl(callback, test_data)

        assert len(received) == 1
        assert received[0] == test_data

    # --- Signature Mismatch and Fallback Tests ---

    def test_no_param_callback_with_args_warns_and_tries_fallback(self):
        """No-parameter callback called with args should warn and try without args."""
        executed = []

        def callback():
            executed.append(True)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Action._execute_callback_impl(callback, "unwanted_arg")

        # Should still execute (using fallback to no-args)
        assert len(executed) == 1

        # Should warn about mismatch
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) == 1
        assert "TypeError" in warning_msgs[0]

    def test_with_param_callback_without_args_warns_and_fails(self):
        """With-parameter callback called without args should warn but can't fallback."""
        executed = []

        def callback(data):
            executed.append(data)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Action._execute_callback_impl(callback)  # No args provided

        # Cannot execute without args (no fallback possible)
        assert len(executed) == 0

        # Should warn about mismatch
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) >= 1

    def test_warning_only_once_per_callback(self):
        """Same callback should only trigger warning once, even with multiple calls."""

        def callback():
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            # Call multiple times with wrong signature
            Action._execute_callback_impl(callback, "arg1")
            Action._execute_callback_impl(callback, "arg2")
            Action._execute_callback_impl(callback, "arg3")

        # Should only warn once
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) == 1

    def test_different_callbacks_each_get_warning(self):
        """Different callbacks should each get their own warning."""

        def callback1():
            pass

        def callback2():
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            # Call different callbacks with wrong signatures
            Action._execute_callback_impl(callback1, "arg")
            Action._execute_callback_impl(callback2, "arg")

        # Should warn for both callbacks
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) == 2

    # --- None Argument Handling Tests ---

    def test_none_argument_treated_as_no_args(self):
        """Single None argument should optimize for no-parameter callbacks."""
        executed = []

        def callback():
            executed.append("no_params")

        # None should be treated as "no meaningful args"
        Action._execute_callback_impl(callback, None)

        assert len(executed) == 1
        assert executed[0] == "no_params"

    def test_meaningful_data_prioritizes_with_params(self):
        """Meaningful (non-None) data should try with-params callback first."""
        call_order = []

        def callback(data=None):
            call_order.append("called")

        test_data = {"key": "value"}
        Action._execute_callback_impl(callback, test_data)

        # Should successfully call with data
        assert len(call_order) == 1

    # --- Exception Handling Tests ---

    def test_non_typeerror_exception_caught_silently(self):
        """Non-TypeError exceptions should be caught to prevent crashes."""
        executed = []

        def callback():
            executed.append("before_exception")
            raise RuntimeError("Something went wrong!")

        # Should not raise, should be caught silently
        Action._execute_callback_impl(callback)

        assert len(executed) == 1  # Callback did start

    def test_non_typeerror_logged_at_debug_level_2(self, capsys):
        """Non-TypeError exceptions should be logged when debug level >= 2."""
        Action.debug_level = 2  # Enable verbose logging

        def callback():
            raise ValueError("Test error")

        Action._execute_callback_impl(callback)

        captured = capsys.readouterr()
        # Should have logged the exception
        assert "ValueError" in captured.out or "Test error" in captured.out

    def test_non_typeerror_not_logged_at_debug_level_0(self, capsys):
        """Non-TypeError exceptions should not be logged at debug level 0."""
        Action.debug_level = 0  # Disable logging

        def callback():
            raise ValueError("Test error")

        Action._execute_callback_impl(callback)

        captured = capsys.readouterr()
        # Should not have logged anything
        assert "ValueError" not in captured.out

    def test_attribute_error_caught_silently(self):
        """AttributeError in callback should be caught."""

        def callback():
            # Try to access non-existent attribute
            obj = type("TestObj", (), {})()
            _ = obj.nonexistent_attribute

        # Should not raise
        Action._execute_callback_impl(callback)

    def test_name_error_caught_silently(self):
        """NameError in callback should be caught."""

        def callback():
            # Reference undefined variable
            return undefined_variable  # noqa: F821

        # Should not raise
        Action._execute_callback_impl(callback)

    # --- Debug Level Control Tests ---

    def test_warnings_disabled_at_debug_level_0(self):
        """Warnings should not appear when debug_level < 1."""
        Action.debug_level = 0

        def callback():
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Action._execute_callback_impl(callback, "unwanted_arg")

        # Should not warn at debug level 0
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) == 0

    def test_warnings_enabled_at_debug_level_1(self):
        """Warnings should appear when debug_level >= 1."""
        Action.debug_level = 1

        def callback():
            pass

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Action._execute_callback_impl(callback, "unwanted_arg")

        # Should warn at debug level 1
        warning_msgs = [str(w.message) for w in caught if issubclass(w.category, RuntimeWarning)]
        assert len(warning_msgs) == 1

    # --- Edge Cases ---

    def test_empty_args_tuple(self):
        """Empty args tuple should work like no args."""
        executed = []

        def callback():
            executed.append(True)

        Action._execute_callback_impl(callback, *())

        assert len(executed) == 1

    def test_lambda_callback(self):
        """Lambda callbacks should work."""
        result = []

        callback = lambda: result.append("lambda_executed")  # noqa: E731

        Action._execute_callback_impl(callback)

        assert len(result) == 1
        assert result[0] == "lambda_executed"

    def test_lambda_with_args(self):
        """Lambda callbacks with args should work."""
        result = []

        callback = lambda data: result.append(data)  # noqa: E731

        Action._execute_callback_impl(callback, "test_data")

        assert len(result) == 1
        assert result[0] == "test_data"

    def test_callback_with_varargs(self):
        """Callback with *args should handle variable arguments."""
        received = []

        def callback(*args):
            received.append(args)

        Action._execute_callback_impl(callback, "arg1", "arg2", "arg3")

        assert len(received) == 1
        assert received[0] == ("arg1", "arg2", "arg3")

    def test_callback_with_kwargs_works(self):
        """Callback with **kwargs receives args as positional."""
        received = []

        def callback(*args, **kwargs):
            received.append({"args": args, "kwargs": kwargs})

        # Kwargs callback receives positional args
        Action._execute_callback_impl(callback, "arg1", "arg2")

        assert len(received) == 1
        assert received[0]["args"] == ("arg1", "arg2")
        assert received[0]["kwargs"] == {}
