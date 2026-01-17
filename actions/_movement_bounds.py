from __future__ import annotations

from ._shared_logging import _debug_log


class _MoveUntilBoundsMixin:
    def _apply_boundary_limits(self) -> None:
        """Apply boundary behavior and trigger events based on intended movement."""

        _debug_log(
            f"_apply_boundary_limits: id={id(self)}, target={self.target}, boundary_behavior={self.boundary_behavior}",
            action="MoveUntil",
        )

        # Track callbacks triggered in this frame to prevent duplicates
        self._frame_callback_tracker.clear()

        def apply_limits(sprite):
            if not self.bounds:
                return

            left, bottom, right, top = self.bounds
            sprite_id = id(sprite)

            # Initialize boundary state if needed
            if sprite_id not in self._boundary_state:
                self._boundary_state[sprite_id] = {"x": None, "y": None}

            current_state = self._boundary_state[sprite_id]

            # For limit behavior, check if sprite would cross boundaries and clamp using edge-based coordinates
            if self.boundary_behavior == "limit":
                # First, clamp sprites that are already outside bounds
                if sprite.left <= left:
                    # At or past left boundary - clamp and clear velocity
                    # But don't clear if sprite is moving away (manually set velocity)
                    sprite.left = left
                    # Only clear velocity if sprite is moving toward boundary or stationary
                    # (not if it's moving away with manually set velocity)
                    if sprite.change_x <= 0:
                        sprite.change_x = 0
                    # Only trigger callback if not already at this boundary and not already triggered this frame
                    callback_key = (sprite_id, "x", "left")
                    if current_state["x"] != "left" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "x", "left")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["x"] = "left"
                elif sprite.right >= right:
                    # At or past right boundary - clamp and clear velocity
                    # But don't clear if sprite is moving away (manually set velocity)
                    sprite.right = right
                    # Only clear velocity if sprite is moving toward boundary or stationary
                    # (not if it's moving away with manually set velocity)
                    if sprite.change_x >= 0:
                        sprite.change_x = 0
                    # Only trigger callback if not already at this boundary and not already triggered this frame
                    callback_key = (sprite_id, "x", "right")
                    if current_state["x"] != "right" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "x", "right")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["x"] = "right"

                if sprite.bottom <= bottom:
                    # At or past bottom boundary - clamp and clear velocity
                    # But don't clear if sprite is moving away (manually set velocity)
                    sprite.bottom = bottom
                    # Only clear velocity if sprite is moving toward boundary or stationary
                    # (not if it's moving away with manually set velocity)
                    if sprite.change_y <= 0:
                        sprite.change_y = 0
                    # Only trigger callback if not already at this boundary and not already triggered this frame
                    callback_key = (sprite_id, "y", "bottom")
                    if current_state["y"] != "bottom" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "y", "bottom")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["y"] = "bottom"
                elif sprite.top >= top:
                    # At or past top boundary - clamp and clear velocity
                    # But don't clear if sprite is moving away (manually set velocity)
                    sprite.top = top
                    # Only clear velocity if sprite is moving toward boundary or stationary
                    # (not if it's moving away with manually set velocity)
                    if sprite.change_y >= 0:
                        sprite.change_y = 0
                    # Only trigger callback if not already at this boundary and not already triggered this frame
                    callback_key = (sprite_id, "y", "top")
                    if current_state["y"] != "top" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "y", "top")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["y"] = "top"

                # Check horizontal movement using edge positions
                # Check if sprite would cross boundary (only if not already handled above)
                # Skip if sprite is already at or past boundary (handled by checks above)
                # Also skip if sprite is exactly at boundary (handled by checks above)
                if sprite.right < right and sprite.change_x > 0 and sprite.right + sprite.change_x > right:
                    # Would cross right boundary
                    callback_key = (sprite_id, "x", "right")
                    if current_state["x"] != "right" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "x", "right")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["x"] = "right"
                    sprite.right = right
                    sprite.change_x = 0
                elif sprite.left > left and sprite.change_x < 0 and sprite.left + sprite.change_x < left:
                    # Would cross left boundary
                    callback_key = (sprite_id, "x", "left")
                    if current_state["x"] != "left" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "x", "left")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["x"] = "left"
                    sprite.left = left
                    sprite.change_x = 0
                elif current_state["x"] is not None:
                    # Was at boundary, now moving away
                    # Only reset state if sprite is actually moving away from boundary
                    # (not just at boundary with zero velocity)
                    is_moving_away = False
                    if current_state["x"] == "right" and sprite.change_x < 0:
                        is_moving_away = True
                    elif current_state["x"] == "left" and sprite.change_x > 0:
                        is_moving_away = True

                    if is_moving_away:
                        old_side = current_state["x"]
                        if self.on_boundary_exit:
                            self._safe_call(self.on_boundary_exit, sprite, "x", old_side)
                        current_state["x"] = None

                # Check vertical movement using edge positions
                # Check if sprite would cross boundary OR is at boundary and moving toward it
                # But skip if sprite is already outside bounds (handled by first check above)
                if sprite.top < top and sprite.change_y > 0 and sprite.top + sprite.change_y > top:
                    # Would cross top boundary
                    callback_key = (sprite_id, "y", "top")
                    if current_state["y"] != "top" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "y", "top")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["y"] = "top"
                    sprite.top = top
                    sprite.change_y = 0
                elif sprite.bottom > bottom and sprite.change_y < 0 and sprite.bottom + sprite.change_y < bottom:
                    # Would cross bottom boundary
                    callback_key = (sprite_id, "y", "bottom")
                    if current_state["y"] != "bottom" and callback_key not in self._frame_callback_tracker:
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "y", "bottom")
                            self._frame_callback_tracker.add(callback_key)
                        current_state["y"] = "bottom"
                    sprite.bottom = bottom
                    sprite.change_y = 0
                elif sprite.bottom == bottom and sprite.change_y < 0:
                    # Already at bottom boundary and moving into it - clear velocity
                    if current_state["y"] != "bottom":
                        if self.on_boundary_enter:
                            self._safe_call(self.on_boundary_enter, sprite, "y", "bottom")
                        current_state["y"] = "bottom"
                    sprite.change_y = 0
                elif current_state["y"] is not None:
                    # Was at boundary, now moving away
                    # Only reset state if sprite is actually moving away from boundary
                    # (not just at boundary with zero velocity)
                    is_moving_away = False
                    if current_state["y"] == "top" and sprite.change_y < 0:
                        is_moving_away = True
                    elif current_state["y"] == "bottom" and sprite.change_y > 0:
                        is_moving_away = True

                    if is_moving_away:
                        old_side = current_state["y"]
                        if self.on_boundary_exit:
                            self._safe_call(self.on_boundary_exit, sprite, "y", old_side)
                        current_state["y"] = None
            else:
                # For other boundary behaviors, use the existing method
                self._check_boundaries(sprite)

        self.for_each_sprite(apply_limits)

    def _validate_bounds_for_sprite_dimensions(self) -> None:
        """Validate that edge-based bounds are large enough for sprite dimensions.

        With edge-based bounds, the patrol span must be larger than the sprite dimensions.
        For horizontal movement, span must exceed sprite width.
        For vertical movement, span must exceed sprite height.
        """
        if not self.bounds:
            return

        left, bottom, right, top = self.bounds
        x_span = right - left
        y_span = top - bottom

        # Check first sprite to get dimensions
        def check_sprite_dimensions(sprite):
            # Check horizontal span
            if x_span < 1e9 and x_span < sprite.width:  # 1e9 is the "infinite" bound marker
                raise ValueError(
                    f"Horizontal patrol span ({x_span:.1f}px) must be >= sprite width ({sprite.width:.1f}px) "
                    f"for edge-based bounds. Bounds: left={left}, right={right}"
                )
            # Check vertical span
            if y_span < 1e9 and y_span < sprite.height:
                raise ValueError(
                    f"Vertical patrol span ({y_span:.1f}px) must be >= sprite height ({sprite.height:.1f}px) "
                    f"for edge-based bounds. Bounds: bottom={bottom}, top={top}"
                )

        # Only need to check one sprite since all sprites in a list should have same dimensions
        try:
            target_iter = iter(self.target)
        except TypeError:
            check_sprite_dimensions(self.target)
            return

        try:
            first_sprite = next(target_iter)
        except StopIteration:
            return
        check_sprite_dimensions(first_sprite)

    def _check_boundaries(self, sprite) -> None:
        """Check and handle boundary interactions for a single sprite using edge-based coordinates."""
        if not self.bounds:
            return

        left, bottom, right, top = self.bounds
        sprite_id = id(sprite)

        # Initialize boundary state for this sprite if needed
        if sprite_id not in self._boundary_state:
            self._boundary_state[sprite_id] = {"x": None, "y": None}

        current_state = self._boundary_state.setdefault(sprite_id, {"x": None, "y": None})

        # Check each axis independently for enter/exit events using edge positions
        self._process_axis_boundary_events(sprite, sprite.left, sprite.right, left, right, "x", current_state)
        self._process_axis_boundary_events(sprite, sprite.bottom, sprite.top, bottom, top, "y", current_state)

    def _process_axis_boundary_events(self, sprite, low_edge, high_edge, low_bound, high_bound, axis, current_state):
        """Process boundary enter/exit events for a single axis using edge positions."""
        current_side = self._current_boundary_side(low_edge, high_edge, low_bound, high_bound, axis)

        previous_side = current_state[axis]

        # Get velocity for this axis
        velocity = sprite.change_x if axis == "x" else sprite.change_y

        # For bounce/wrap behaviors, check predicted movement to trigger boundary enter callback
        # For limit behavior, use current position
        predicted_side = None
        if self.boundary_behavior == "bounce" or self.boundary_behavior == "wrap":
            predicted_side = self._predict_boundary_side(
                low_edge,
                high_edge,
                low_bound,
                high_bound,
                velocity,
                axis,
            )

        # Detect enter/exit events
        # For bounce/wrap: use predicted_side if available, otherwise current_side
        # For limit: use current_side
        effective_side = self._effective_boundary_side(predicted_side, current_side)

        if effective_side != previous_side:
            # Exit event (was on a side, now not or on different side)
            if previous_side is not None:
                if self.on_boundary_exit:
                    self._safe_call(self.on_boundary_exit, sprite, axis, previous_side)

            # Enter event (now on a side, was not before or was on different side)
            if effective_side is not None:
                if self.on_boundary_enter:
                    self._safe_call(self.on_boundary_enter, sprite, axis, effective_side)

        # Update state - use effective_side for state tracking (predicted for bounce/wrap, current for limit)
        # This ensures exit callbacks trigger correctly for wrap/bounce behaviors
        current_state[axis] = effective_side

        # Apply boundary behavior based on predicted movement (would cross boundary)
        # instead of current position (is at boundary) for bounce/wrap behaviors
        # This allows frame-by-frame stepping to work correctly
        should_apply_behavior = self._should_apply_boundary_behavior(
            predicted_side,
            current_side,
        )

        if should_apply_behavior:
            self._apply_boundary_behavior(
                sprite,
                low_edge,
                high_edge,
                low_bound,
                high_bound,
                velocity,
                axis,
            )

    def _apply_boundary_behavior(self, sprite, low_edge, high_edge, low_bound, high_bound, velocity, axis):
        """Apply the specific boundary behavior for an axis using edge positions."""
        behavior_handlers = {
            "bounce": self._bounce_behavior,
            "wrap": self._wrap_behavior,
            "limit": self._limit_behavior,
        }

        handler = behavior_handlers.get(self.boundary_behavior)
        if handler:
            handler(sprite, low_edge, high_edge, low_bound, high_bound, velocity, axis)

    def _current_boundary_side(self, low_edge, high_edge, low_bound, high_bound, axis):
        """Return the current boundary side based on edge positions."""
        if low_edge <= low_bound:
            return "left" if axis == "x" else "bottom"
        if high_edge >= high_bound:
            return "right" if axis == "x" else "top"
        return None

    def _predict_boundary_side(self, low_edge, high_edge, low_bound, high_bound, velocity, axis):
        """Predict boundary side if velocity would cross a bound."""
        if velocity > 0:  # Moving toward high boundary
            predicted_high = high_edge + velocity
            if predicted_high > high_bound:
                return "right" if axis == "x" else "top"
        elif velocity < 0:  # Moving toward low boundary
            predicted_low = low_edge + velocity
            if predicted_low < low_bound:
                return "left" if axis == "x" else "bottom"
        return None

    def _effective_boundary_side(self, predicted_side, current_side):
        """Choose effective side for state tracking based on behavior."""
        if predicted_side is not None and (self.boundary_behavior == "bounce" or self.boundary_behavior == "wrap"):
            return predicted_side
        return current_side

    def _should_apply_boundary_behavior(self, predicted_side, current_side):
        """Return True if a boundary behavior should run this frame."""
        if self.boundary_behavior == "bounce" or self.boundary_behavior == "wrap":
            return predicted_side is not None
        return current_side is not None

    def _bounce_behavior(self, sprite, low_edge, high_edge, low_bound, high_bound, velocity, axis):
        """Handle bounce boundary behavior using edge-based coordinates.

        Only bounces when sprite would cross boundary (predicted movement),
        not when sprite is already at boundary. This allows frame-by-frame
        stepping to work correctly.
        """
        if axis == "x":
            # Check if would cross boundary based on predicted movement
            would_cross_low = velocity < 0 and low_edge + velocity < low_bound
            would_cross_high = velocity > 0 and high_edge + velocity > high_bound

            if would_cross_low or would_cross_high:
                # Reverse velocity
                sprite.change_x = -sprite.change_x
                self.current_velocity = (-self.current_velocity[0], self.current_velocity[1])
                self.target_velocity = (-self.target_velocity[0], self.target_velocity[1])

                # Clamp sprite to boundary if it would cross
                if would_cross_low:
                    sprite.left = low_bound
                elif would_cross_high:
                    sprite.right = high_bound
        else:  # axis == "y"
            # Check if would cross boundary based on predicted movement
            would_cross_low = velocity < 0 and low_edge + velocity < low_bound
            would_cross_high = velocity > 0 and high_edge + velocity > high_bound

            if would_cross_low or would_cross_high:
                # Reverse velocity
                sprite.change_y = -sprite.change_y
                self.current_velocity = (self.current_velocity[0], -self.current_velocity[1])
                self.target_velocity = (self.target_velocity[0], -self.target_velocity[1])

                # Clamp sprite to boundary if it would cross
                if would_cross_low:
                    sprite.bottom = low_bound
                elif would_cross_high:
                    sprite.top = high_bound

    def _wrap_behavior(self, sprite, low_edge, high_edge, low_bound, high_bound, velocity, axis):
        """Handle wrap boundary behavior using edge-based coordinates."""
        if axis == "x":
            # When left edge crosses left bound, wrap so right edge is at right bound
            if low_edge <= low_bound:
                sprite.right = high_bound
            # When right edge crosses right bound, wrap so left edge is at left bound
            elif high_edge >= high_bound:
                sprite.left = low_bound
        else:  # axis == "y"
            # When bottom edge crosses bottom bound, wrap so top edge is at top bound
            if low_edge <= low_bound:
                sprite.top = high_bound
            # When top edge crosses top bound, wrap so bottom edge is at bottom bound
            elif high_edge >= high_bound:
                sprite.bottom = low_bound

    def _limit_behavior(self, sprite, low_edge, high_edge, low_bound, high_bound, velocity, axis):
        """Handle limit boundary behavior using edge-based coordinates."""
        if axis == "x":
            if low_edge < low_bound:
                sprite.left = low_bound
                sprite.change_x = 0
                self.current_velocity = (0, self.current_velocity[1])
                self.target_velocity = (0, self.target_velocity[1])
            elif high_edge > high_bound:
                sprite.right = high_bound
                sprite.change_x = 0
                self.current_velocity = (0, self.current_velocity[1])
                self.target_velocity = (0, self.target_velocity[1])
        else:  # axis == "y"
            if low_edge < low_bound:
                sprite.bottom = low_bound
                sprite.change_y = 0
                self.current_velocity = (self.current_velocity[0], 0)
                self.target_velocity = (self.current_velocity[0], 0)
            elif high_edge > high_bound:
                sprite.top = high_bound
                sprite.change_y = 0
                self.current_velocity = (self.current_velocity[0], 0)
                self.target_velocity = (self.current_velocity[0], 0)
