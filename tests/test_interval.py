"""Test suite for interval.py - Interval action implementations."""

import arcade
import pytest
from arcade.texture import Texture

from actions.base import ActionSprite
from actions.interval import (
    Blink,
    Easing,
    FadeIn,
    FadeOut,
    FadeTo,
    MoveBy,
    MoveTo,
    RotateBy,
    RotateTo,
    ScaleBy,
    ScaleTo,
)


def create_test_sprite(texture_size=(1, 1)) -> arcade.Sprite:
    """Create a sprite with a transparent texture for testing."""
    texture = Texture.create_empty("test", texture_size)
    sprite = ActionSprite(filename=":resources:images/items/star.png")  # Using a default image from arcade
    sprite.texture = texture
    sprite.position = (0, 0)
    sprite.angle = 0
    sprite.scale = 1.0
    sprite.alpha = 255
    sprite.visible = True
    return sprite


class TestMoveTo:
    """Test suite for MoveTo action."""

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position."""
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        return sprite

    def test_move_to_initialization(self):
        """Test MoveTo action initialization."""
        position = (100, 200)
        duration = 1.0
        action = MoveTo(position, duration)
        assert action.end_position == position
        assert action.duration == duration
        assert not action.use_physics

    def test_move_to_requires_position(self):
        """Test MoveTo requires position parameter."""
        with pytest.raises(ValueError):
            MoveTo(duration=1.0)

    def test_move_to_requires_duration(self):
        """Test MoveTo requires duration parameter."""
        with pytest.raises(ValueError):
            MoveTo(position=(100, 200))

    def test_move_to_execution(self, sprite):
        """Test MoveTo action execution.

        The MoveTo action should:
        1. Store the initial position and calculate total change
        2. Update position directly based on progress ratio
        3. Ensure final position matches target
        """
        position = (100, 200)
        duration = 1.0
        action = MoveTo(position, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert not action.done
        # At t=0.5, position should be halfway between start and end
        assert abs(sprite.position[0] - 50) < 0.001  # 0 + (100 * 0.5)
        assert abs(sprite.position[1] - 100) < 0.001  # 0 + (200 * 0.5)

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert abs(sprite.position[0] - 100) < 0.001  # Final x position
        assert abs(sprite.position[1] - 200) < 0.001  # Final y position


class TestMoveBy:
    """Test suite for MoveBy action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        return sprite

    def test_move_by_initialization(self):
        """Test MoveBy action initialization."""
        delta = (100, 200)
        duration = 1.0
        action = MoveBy(delta, duration)
        assert action.delta == delta
        assert action.duration == duration
        assert not action.use_physics

    def test_move_by_requires_delta(self):
        """Test MoveBy requires delta parameter."""
        with pytest.raises(ValueError):
            MoveBy(duration=1.0)

    def test_move_by_requires_duration(self):
        """Test MoveBy requires duration parameter."""
        with pytest.raises(ValueError):
            MoveBy(delta=(100, 200))

    def test_move_by_execution(self, sprite):
        """Test MoveBy action execution.

        The MoveBy action should:
        1. Calculate target position as current position plus delta
        2. Update position directly based on progress ratio
        3. Ensure final position matches target
        """
        delta = (100, 200)
        duration = 1.0
        action = MoveBy(delta, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert not action.done
        # At t=0.5, position should be halfway between start and end
        assert abs(sprite.position[0] - 50) < 0.001  # 0 + (100 * 0.5)
        assert abs(sprite.position[1] - 100) < 0.001  # 0 + (200 * 0.5)

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert abs(sprite.position[0] - 100) < 0.001  # Final x position
        assert abs(sprite.position[1] - 200) < 0.001  # Final y position

    def test_move_by_reverse(self):
        """Test MoveBy reversal."""
        delta = (100, 200)
        duration = 1.0
        action = MoveBy(delta, duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, MoveBy)
        assert reversed_action.delta == (-100, -200)
        assert reversed_action.duration == duration


class TestRotateTo:
    """Test suite for RotateTo action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.angle = 0
        return sprite

    def test_rotate_to_initialization(self):
        """Test RotateTo action initialization."""
        angle = 90
        duration = 1.0
        action = RotateTo(angle, duration)
        assert action.end_angle == 90
        assert action.duration == duration
        assert not action.use_physics

    def test_rotate_to_requires_angle(self):
        """Test RotateTo requires angle parameter."""
        with pytest.raises(ValueError):
            RotateTo(duration=1.0)

    def test_rotate_to_requires_duration(self):
        """Test RotateTo requires duration parameter."""
        with pytest.raises(ValueError):
            RotateTo(angle=90)

    def test_rotate_to_execution(self, sprite):
        """Test RotateTo action execution.

        The RotateTo action should:
        1. Store the initial angle and calculate total change
        2. Update the angle directly based on progress
        3. End exactly at the target angle
        """
        angle = 90
        duration = 1.0
        action = RotateTo(angle, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert not action.done
        # Angle should be updated based on progress
        assert abs(sprite.angle - 45) < 0.001  # 0 + 90 * 0.5

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert abs(sprite.angle - angle) < 0.001  # Should end at target angle


class TestRotateBy:
    """Test suite for RotateBy action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.angle = 0
        return sprite

    def test_rotate_by_initialization(self):
        """Test RotateBy action initialization."""
        angle = 90
        duration = 1.0
        action = RotateBy(angle, duration)
        assert action.angle == 90
        assert action.duration == duration
        assert not action.use_physics

    def test_rotate_by_requires_angle(self):
        """Test RotateBy requires angle parameter."""
        with pytest.raises(ValueError):
            RotateBy(duration=1.0)

    def test_rotate_by_requires_duration(self):
        """Test RotateBy requires duration parameter."""
        with pytest.raises(ValueError):
            RotateBy(angle=90)

    def test_rotate_by_execution(self, sprite):
        """Test RotateBy action execution.

        The RotateBy action should:
        1. Store the initial angle and calculate total change
        2. Update the angle directly based on progress
        3. End exactly at the target angle
        """
        angle = 90
        duration = 1.0
        action = RotateBy(angle, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert not action.done
        # Angle should be updated based on progress
        assert sprite.angle == 45  # 0 + 90 * 0.5

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.angle == angle  # Should end at target angle

    def test_rotate_by_reverse(self):
        """Test RotateBy reversal."""
        angle = 90
        duration = 1.0
        action = RotateBy(angle, duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, RotateBy)
        assert reversed_action.angle == -90
        assert reversed_action.duration == duration


class TestScaleTo:
    """Test suite for ScaleTo action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite((100, 100))
        sprite.scale = 1.0
        return sprite

    def test_scale_to_initialization(self):
        """Test ScaleTo action initialization."""
        scale = 2.0
        duration = 1.0
        action = ScaleTo(scale, duration)
        assert action.end_scale == 2.0
        assert action.duration == duration

    def test_scale_to_requires_scale(self):
        """Test ScaleTo requires scale parameter."""
        with pytest.raises(ValueError):
            ScaleTo(duration=1.0)

    def test_scale_to_requires_duration(self):
        """Test ScaleTo requires duration parameter."""
        with pytest.raises(ValueError):
            ScaleTo(scale=2.0)

    def test_scale_to_execution(self, sprite):
        """Test ScaleTo action execution."""
        scale = 2.0
        duration = 1.0
        action = ScaleTo(scale, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        # Scale is applied directly, not through velocity
        assert sprite.scale.x == 1.5  # 1.0 + (2.0 - 1.0) * 0.5
        assert sprite.scale.y == 1.5
        assert sprite.width == 150  # 100 * 1.5
        assert sprite.height == 150  # 100 * 1.5
        assert not action.done

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.scale.x == 2.0
        assert sprite.scale.y == 2.0
        assert sprite.width == 200  # 100 * 2.0
        assert sprite.height == 200  # 100 * 2.0


class TestScaleBy:
    """Test suite for ScaleBy action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite((100, 100))
        sprite.scale = 1.0
        return sprite

    def test_scale_by_initialization(self):
        """Test ScaleBy action initialization."""
        scale = 2.0
        duration = 1.0
        action = ScaleBy(scale, duration)
        assert action.scale == 2.0
        assert action.duration == duration

    def test_scale_by_requires_scale(self):
        """Test ScaleBy requires scale parameter."""
        with pytest.raises(ValueError):
            ScaleBy(duration=1.0)

    def test_scale_by_requires_duration(self):
        """Test ScaleBy requires duration parameter."""
        with pytest.raises(ValueError):
            ScaleBy(scale=2.0)

    def test_scale_by_execution(self, sprite):
        """Test ScaleBy action execution."""
        scale = 2.0
        duration = 1.0
        action = ScaleBy(scale, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        # Scale is applied directly, not through velocity
        assert sprite.scale.x == 1.5  # 1.0 * (1.0 + (2.0 - 1.0) * 0.5)
        assert sprite.scale.y == 1.5
        assert sprite.width == 150  # 100 * 1.5
        assert sprite.height == 150  # 100 * 1.5
        assert not action.done

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.scale.x == 2.0
        assert sprite.scale.y == 2.0
        assert sprite.width == 200  # 100 * 2.0
        assert sprite.height == 200  # 100 * 2.0

    def test_scale_by_reverse(self):
        """Test ScaleBy reversal."""
        scale = 2.0
        duration = 1.0
        action = ScaleBy(scale, duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, ScaleBy)
        assert reversed_action.scale == 0.5  # 1.0 / 2.0
        assert reversed_action.duration == duration


class TestFadeOut:
    """Test suite for FadeOut action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.alpha = 255
        return sprite

    def test_fade_out_initialization(self):
        """Test FadeOut action initialization."""
        duration = 1.0
        action = FadeOut(duration)
        assert action.duration == duration

    def test_fade_out_requires_duration(self):
        """Test FadeOut requires duration parameter."""
        with pytest.raises(ValueError):
            FadeOut()

    def test_fade_out_execution(self, sprite):
        """Test FadeOut action execution."""
        duration = 1.0
        action = FadeOut(duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert sprite.alpha == 127  # 255 * (1 - 0.5)
        assert not action.done

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.alpha == 0

    def test_fade_out_reverse(self):
        """Test FadeOut reversal."""
        duration = 1.0
        action = FadeOut(duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, FadeIn)
        assert reversed_action.duration == duration


class TestFadeIn:
    """Test suite for FadeIn action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.alpha = 0
        return sprite

    def test_fade_in_initialization(self):
        """Test FadeIn action initialization."""
        duration = 1.0
        action = FadeIn(duration)
        assert action.duration == duration

    def test_fade_in_requires_duration(self):
        """Test FadeIn requires duration parameter."""
        with pytest.raises(ValueError):
            FadeIn()

    def test_fade_in_execution(self, sprite):
        """Test FadeIn action execution."""
        duration = 1.0
        action = FadeIn(duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert sprite.alpha == 127  # 0 + (255 - 0) * 0.5
        assert not action.done

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.alpha == 255

    def test_fade_in_reverse(self):
        """Test FadeIn reversal."""
        duration = 1.0
        action = FadeIn(duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, FadeOut)
        assert reversed_action.duration == duration


class TestFadeTo:
    """Test suite for FadeTo action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.alpha = 255
        return sprite

    def test_fade_to_initialization(self):
        """Test FadeTo action initialization."""
        alpha = 128
        duration = 1.0
        action = FadeTo(alpha, duration)
        assert action.alpha == 128
        assert action.duration == duration

    def test_fade_to_requires_alpha(self):
        """Test FadeTo requires alpha parameter."""
        with pytest.raises(ValueError):
            FadeTo(duration=1.0)

    def test_fade_to_requires_duration(self):
        """Test FadeTo requires duration parameter."""
        with pytest.raises(ValueError):
            FadeTo(alpha=128)

    def test_fade_to_clamps_alpha(self):
        """Test FadeTo clamps alpha values."""
        action = FadeTo(300, 1.0)  # Should be clamped to 255
        assert action.alpha == 255

        action = FadeTo(-50, 1.0)  # Should be clamped to 0
        assert action.alpha == 0

    def test_fade_to_execution(self, sprite):
        """Test FadeTo action execution."""
        alpha = 128
        duration = 1.0
        action = FadeTo(alpha, duration)
        sprite.do(action)

        # Update halfway
        sprite.update(0.5)
        assert sprite.alpha == 191  # 255 + (128 - 255) * 0.5
        assert not action.done

        # Complete the action
        sprite.update(0.5)
        assert action.done
        assert sprite.alpha == 128


class TestBlink:
    """Test suite for Blink action."""

    @pytest.fixture
    def sprite(self):
        sprite = create_test_sprite()
        sprite.visible = True
        return sprite

    def test_blink_initialization(self):
        """Test Blink action initialization."""
        times = 3
        duration = 1.0
        action = Blink(times, duration)
        assert action.times == 3
        assert action.duration == duration

    def test_blink_requires_times(self):
        """Test Blink requires times parameter."""
        with pytest.raises(ValueError):
            Blink(duration=1.0)

    def test_blink_requires_duration(self):
        """Test Blink requires duration parameter."""
        with pytest.raises(ValueError):
            Blink(times=3)

    def test_blink_execution(self, sprite):
        """Test Blink action execution."""
        times = 3
        duration = 1.0
        action = Blink(times, duration)
        sprite.do(action)
        assert sprite.visible
        # First interval
        sprite.update(0.33)
        assert not sprite.visible
        assert not action.done

        # Second interval
        sprite.update(0.33)
        assert sprite.visible
        assert not action.done

        # Third interval
        sprite.update(0.34)
        assert action.done

        # Ensure sprite is restored to original state
        assert sprite.visible

    def test_blink_reverse(self):
        """Test Blink reversal."""
        times = 3
        duration = 1.0
        action = Blink(times, duration)
        reversed_action = action.__reversed__()
        assert isinstance(reversed_action, Blink)
        assert reversed_action.times == times
        assert reversed_action.duration == duration


class TestEasing:
    """Test suite for Easing action."""

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position."""
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        return sprite

    def test_easing_initialization(self):
        """Test Easing action initialization."""
        from arcade import easing

        move = MoveTo((100, 200), duration=2.0)
        action = Easing(move, ease_function=easing.ease_in_out)

        assert action.duration == 2.0
        assert isinstance(action.other, MoveTo)
        assert action.ease_function == easing.ease_in_out
        assert action.elapsed == 0.0
        assert action.prev_eased == 0.0

    def test_easing_execution(self, sprite):
        """Test Easing action execution with ease_in_out function."""
        from arcade import easing

        move = MoveTo((100, 0), duration=1.0)
        action = Easing(move, ease_function=easing.ease_in_out)
        sprite.do(action)

        # At t=0.25, ease_in_out(0.25) ≈ 0.125
        # This means the sprite should have moved 12.5% of the total distance
        sprite.update(0.25)
        assert not action.done
        # Position should be about 12.5% of the way (100 * 0.125)
        assert abs(sprite.position[0] - 12.5) < 0.1

        # At t=0.5, ease_in_out(0.5) = 0.5
        sprite.update(0.25)
        assert not action.done
        # Position should be 50% of the way
        assert abs(sprite.position[0] - 50.0) < 0.1

        # At t=0.75, ease_in_out(0.75) ≈ 0.875
        sprite.update(0.25)
        assert not action.done
        # Position should be about 87.5% of the way
        assert abs(sprite.position[0] - 87.5) < 0.1

        # Complete the action
        sprite.update(0.25)
        assert action.done
        assert abs(sprite.position[0] - 100.0) < 0.1

    def test_easing_with_different_functions(self, sprite):
        """Test Easing action with different easing functions."""
        from arcade import easing

        # Test with ease_in
        move = MoveTo((100, 0), duration=1.0)
        action = Easing(move, ease_function=easing.ease_in)
        sprite.do(action)

        # At t=0.5, ease_in(0.5) = 0.25
        sprite.update(0.5)
        assert not action.done
        # Position should be 25% of the way
        assert abs(sprite.position[0] - 25.0) < 0.1

        # Clean up first action
        sprite.clear_actions()
        sprite.position = (0, 0)  # Reset position

        # Test with ease_out
        move = MoveTo((100, 0), duration=1.0)
        action = Easing(move, ease_function=easing.ease_out)
        sprite.do(action)

        # At t=0.5, ease_out(0.5) = 0.75
        sprite.update(0.5)
        assert not action.done
        # Position should be 75% of the way
        assert abs(sprite.position[0] - 75.0) < 0.1

    def test_easing_reversal(self):
        """Test Easing action reversal."""
        from arcade import easing

        move = MoveTo((100, 200), duration=2.0)
        action = Easing(move, ease_function=easing.ease_in_out)
        reversed_action = action.__neg__()

        assert isinstance(reversed_action, Easing)
        assert reversed_action.duration == 2.0
        assert reversed_action.ease_function == easing.ease_in_out
        assert isinstance(reversed_action.other, MoveTo)
        assert reversed_action.other.end_position == (-100, -200)

    def test_easing_with_other_actions(self, sprite):
        """Test Easing action with different types of actions."""
        from arcade import easing

        # Test with RotateTo
        rotate = RotateTo(90, duration=1.0)
        action = Easing(rotate, ease_function=easing.ease_in_out)
        sprite.do(action)

        # At t=0.5, ease_in_out(0.5) = 0.5
        sprite.update(0.5)
        assert not action.done
        # Angle should be 45 degrees (90 * 0.5)
        assert abs(sprite.angle - 45.0) < 0.1

        # Test with ScaleTo
        sprite.scale = 1.0
        scale = ScaleTo(2.0, duration=1.0)
        action = Easing(scale, ease_function=easing.ease_in_out)
        sprite.do(action)

        # At t=0.5, ease_in_out(0.5) = 0.5
        sprite.update(0.5)
        assert not action.done
        # Scale should be 1.5 (1.0 + (2.0 - 1.0) * 0.5)
        assert abs(sprite.scale.x - 1.5) < 0.1
        assert abs(sprite.scale.y - 1.5) < 0.1

    def test_easing_repr(self):
        """Test Easing action string representation."""
        from arcade import easing

        move = MoveTo((100, 200), duration=2.0)
        action = Easing(move, ease_function=easing.ease_in_out)

        expected = f"<Easing(duration=2.0, ease_function=ease_in_out, wrapped={repr(move)})>"
        assert repr(action) == expected
