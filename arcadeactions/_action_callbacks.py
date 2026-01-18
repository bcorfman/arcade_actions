from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ActionCallbacksMixin:
    """Callback helpers for Action."""

    def _safe_call(self, fn: Callable, *args) -> None:
        """Safely call a callback function with exception handling."""
        if not self._callbacks_active:
            return
        type(self)._execute_callback_impl(fn, *args)

    @staticmethod
    def _execute_callback_impl(fn: Callable, *args) -> None:
        """Execute callback with exception handling - for internal use and testing."""
        from ._action_core import Action

        def _warn_signature_mismatch(exc: TypeError) -> None:
            if fn not in Action._warned_bad_callbacks and Action.debug_level >= 1:
                import warnings

                Action._warned_bad_callbacks.add(fn)
                warnings.warn(
                    f"Callback '{fn.__name__}' failed with TypeError - signature mismatch: {exc}",
                    RuntimeWarning,
                    stacklevel=4,
                )

        try:
            has_meaningful_args = args and not (len(args) == 1 and args[0] is None)

            def _call_with_args(call_args: tuple[Any, ...] | None) -> tuple[bool, TypeError | None]:
                try:
                    if call_args is None:
                        fn()
                    else:
                        fn(*call_args)
                    return True, None
                except TypeError as error:
                    return False, error

            initial_args = args if has_meaningful_args else None
            succeeded, error = _call_with_args(initial_args)
            if succeeded:
                return

            initial_error = error
            fallback_error = error
            fallback_called = False

            fallback_variants: list[tuple[Any, ...]] = []
            if has_meaningful_args:
                for size in range(len(args) - 1, -1, -1):
                    fallback_variants.append(args[:size])
            else:
                if args:
                    fallback_variants.append(args)
                fallback_variants.append(tuple())

            for variant in fallback_variants:
                if has_meaningful_args and variant == args:
                    continue
                call_args = variant if variant else None
                succeeded, error = _call_with_args(call_args)
                if succeeded:
                    fallback_called = True
                    break
                fallback_error = error

            if fallback_called:
                _warn_signature_mismatch(initial_error)
                return

            if fallback_error is not None:
                _warn_signature_mismatch(fallback_error)
        except Exception as exc:
            if Action.debug_level >= 2:
                print(f"[AA] Callback '{fn.__name__}' raised {type(exc).__name__}: {exc}")
