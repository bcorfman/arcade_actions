"""Test suite for interval.py - Interval action implementations."""

import arcade
import pytest
from arcade.texture import Texture

from actions.interval import (
    AccelDecel,
    Accelerate,
    Blink,
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
    """Create a sprite with a 1x1 transparent texture for testing."""
    texture = Texture.create_empty("test", texture_size)
    sprite = arcade.Sprite()
    sprite.texture = texture
    return sprite


class TestMoveTo:
    """Test suite for MoveTo action."""

    @pytest.fixture
    def sprite(self):
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
        """Test MoveTo action execution."""
        position = (100, 200)
        duration = 1.0
        action = MoveTo(position, duration)
        action.target = sprite
        action.start()

        # Check initial velocities
        assert sprite.change_x == 100  # (100 - 0) / 1.0
        assert sprite.change_y == 200  # (200 - 0) / 1.0

        # Update halfway
        action.update(0.5)
        assert not action.done
        # Let Arcade update the position based on velocity
        sprite.update(0.5)
        # Position should be updated by velocity * time
        assert sprite.position == (50, 100)  # (0 + 100 * 0.5, 0 + 200 * 0.5)

        # Complete the action
        action.update(0.5)
        assert action.done
        # Let Arcade update the position based on velocity
        sprite.update(0.5)
        assert sprite.position == position  # Should end at target position
        action.stop()
        assert sprite.change_x == 0
        assert sprite.change_y == 0


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
        """Test MoveBy action execution."""
        delta = (100, 200)
        duration = 1.0
        action = MoveBy(delta, duration)
        action.target = sprite
        action.start()

        # Check initial velocities
        assert sprite.change_x == 100  # 100 / 1.0
        assert sprite.change_y == 200  # 200 / 1.0

        # Update halfway
        action.update(0.5)
        assert not action.done
        # Let Arcade update the position based on velocity
        sprite.update(0.5)
        # Position should be updated by velocity * time
        assert sprite.position == (50, 100)  # (0 + 100 * 0.5, 0 + 200 * 0.5)

        # Complete the action
        action.update(0.5)
        assert action.done
        # Let Arcade update the position based on velocity
        sprite.update(0.5)
        assert sprite.position == delta  # Should end at delta position
        action.stop()
        assert sprite.change_x == 0
        assert sprite.change_y == 0

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
        """Test RotateTo action execution."""
        angle = 90
        duration = 1.0
        action = RotateTo(angle, duration)
        action.target = sprite
        action.start()

        # Check initial angular velocity
        assert sprite.change_angle == 90  # 90 / 1.0

        # Update halfway
        action.update(0.5)
        assert not action.done
        # Let Arcade update the angle based on angular velocity
        sprite.update(0.5)
        # Angle should be updated by angular velocity * time
        assert sprite.angle == 45  # 0 + 90 * 0.5

        # Complete the action
        action.update(0.5)
        assert action.done
        # Let Arcade update the angle based on angular velocity
        sprite.update(0.5)
        assert sprite.angle == angle  # Should end at target angle
        action.stop()
        assert sprite.change_angle == 0


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
        """Test RotateBy action execution."""
        angle = 90
        duration = 1.0
        action = RotateBy(angle, duration)
        action.target = sprite
        action.start()

        # Check initial angular velocity
        assert sprite.change_angle == 90  # 90 / 1.0

        # Update halfway
        action.update(0.5)
        assert not action.done
        # Let Arcade update the angle based on angular velocity
        sprite.update(0.5)
        # Angle should be updated by angular velocity * time
        assert sprite.angle == 45  # 0 + 90 * 0.5

        # Complete the action
        action.update(0.5)
        assert action.done
        # Let Arcade update the angle based on angular velocity
        sprite.update(0.5)
        assert sprite.angle == angle  # Should end at target angle
        action.stop()
        assert sprite.change_angle == 0

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
        action.target = sprite
        action.start()

        # Update halfway
        action.update(0.5)
        # Scale is applied directly, not through velocity
        assert sprite.scale.x == 1.5  # 1.0 + (2.0 - 1.0) * 0.5
        assert sprite.scale.y == 1.5
        assert sprite.width == 150  # 100 * 1.5
        assert sprite.height == 150  # 100 * 1.5
        assert not action.done

        # Complete the action
        action.update(0.5)
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
        action.target = sprite
        action.start()

        # Update halfway
        action.update(0.5)
        # Scale is applied directly, not through velocity
        assert sprite.scale.x == 1.5  # 1.0 * (1.0 + (2.0 - 1.0) * 0.5)
        assert sprite.scale.y == 1.5
        assert sprite.width == 150  # 100 * 1.5
        assert sprite.height == 150  # 100 * 1.5
        assert not action.done

        # Complete the action
        action.update(0.5)
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
        action.target = sprite
        action.start()

        # Update halfway
        action.update(0.5)
        assert sprite.alpha == 127  # 255 * (1 - 0.5)
        assert not action.done

        # Complete the action
        action.update(0.5)
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
        action.target = sprite
        action.start()

        # Update halfway
        action.update(0.5)
        assert sprite.alpha == 127  # 0 + (255 - 0) * 0.5
        assert not action.done

        # Complete the action
        action.update(0.5)
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
        action.target = sprite
        action.start()

        # Update halfway
        action.update(0.5)
        assert sprite.alpha == 191  # 255 + (128 - 255) * 0.5
        assert not action.done

        # Complete the action
        action.update(0.5)
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
        action.target = sprite
        action.start()
        assert sprite.visible
        # First interval
        action.update(0.33)
        assert not sprite.visible
        assert not action.done

        # Second interval
        action.update(0.33)
        assert sprite.visible
        assert not action.done

        # Third interval
        action.update(0.34)
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


class TestAccelerate:
    """Test suite for Accelerate action.

    Tests that the Accelerate action properly modifies the timing of other actions
    using a power function, making them start slow and accelerate over time.
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position."""
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        return sprite

    def test_accelerate_initialization(self):
        """Test Accelerate action initialization."""
        move_action = MoveBy((100, 0), 1.0)
        rate = 2.0
        action = Accelerate(move_action, rate)
        assert action.other == move_action
        assert action.rate == rate
        assert action.duration == move_action.duration

    def test_accelerate_requires_positive_rate(self):
        """Test Accelerate requires positive rate."""
        move_action = MoveBy((100, 0), 1.0)
        with pytest.raises(ValueError):
            Accelerate(move_action, rate=0)
        with pytest.raises(ValueError):
            Accelerate(move_action, rate=-1)

    def test_accelerate_execution(self, sprite):
        """Test Accelerate action execution.

        Verifies that the action starts slow and accelerates over time.
        With rate=2.0, at 50% duration we should be at 25% progress (0.5^2).
        """
        move_action = MoveBy((100, 0), 1.0)
        rate = 2.0
        action = Accelerate(move_action, rate)
        action.target = sprite
        action.start()

        # At 25% of duration, should be at 6.25% of distance (0.25^2)
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(6.25, abs=0.1)

        # At 50% of duration, should be at 25% of distance (0.5^2)
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(25.0, abs=0.1)

        # At 75% of duration, should be at 56.25% of distance (0.75^2)
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(56.25, abs=0.1)

        # Complete the action
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(100.0, abs=0.1)
        assert action.done

    def test_accelerate_with_different_actions(self, sprite):
        """Test Accelerate works with different types of actions."""
        # Test with rotation
        rotate_action = RotateBy(90, 1.0)
        action = Accelerate(rotate_action, rate=2.0)
        action.target = sprite
        action.start()

        # At 50% of duration, should be at 25% of rotation (0.5^2)
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.angle == pytest.approx(22.5, abs=0.1)

        # Complete the action
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.angle == pytest.approx(90.0, abs=0.1)
        assert action.done

        # Test with scaling
        sprite.scale = 1.0
        scale_action = ScaleTo(2.0, 1.0)
        action = Accelerate(scale_action, rate=2.0)
        action.target = sprite
        action.start()

        # At 50% of duration, should be at 25% of scale change (0.5^2)
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.scale.x == pytest.approx(1.25, abs=0.1)
        assert sprite.scale.y == pytest.approx(1.25, abs=0.1)

        # Complete the action
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.scale.x == pytest.approx(2.0, abs=0.1)
        assert sprite.scale.y == pytest.approx(2.0, abs=0.1)
        assert action.done


class TestAccelDecel:
    """Test suite for AccelDecel action.

    Tests that the AccelDecel action properly modifies the timing of other actions
    using a sigmoid function, making them start slow, accelerate in the middle,
    and slow down at the end.
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position."""
        sprite = create_test_sprite()
        sprite.position = (0, 0)
        return sprite

    def test_accel_decel_initialization(self):
        """Test AccelDecel action initialization."""
        move_action = MoveBy((100, 0), 1.0)
        action = AccelDecel(move_action)
        assert action.other == move_action
        assert action.duration == move_action.duration

    def test_accel_decel_execution(self, sprite):
        """Test AccelDecel action execution.

        Verifies that the action starts slow, accelerates in the middle,
        and slows down at the end.
        """
        move_action = MoveBy((100, 0), 1.0)
        action = AccelDecel(move_action)
        action.target = sprite
        action.start()

        # At 25% of duration, should be at 25% of distance with delta time
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(25.0, abs=1)

        # At 50% of duration, should be at 50% of distance
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(50.0, abs=1)

        # At 75% of duration, should be at 75% of distance
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(75.0, abs=1)

        # Complete the action
        action.update(0.25)
        sprite.update(0.25)
        assert sprite.position[0] == pytest.approx(100.0, abs=1)
        assert action.done

    def test_accel_decel_with_different_actions(self, sprite):
        """Test AccelDecel works with different types of actions."""
        # Test with rotation
        rotate_action = RotateBy(90, 1.0)
        action = AccelDecel(rotate_action)
        action.target = sprite
        action.start()

        # At 50% of duration, should be at 50% of rotation with delta time
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.angle == pytest.approx(45.0, abs=1)

        # Complete the action
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.angle == pytest.approx(90.0, abs=1)
        assert action.done

        # Test with scaling
        sprite.scale = 1.0
        scale_action = ScaleTo(2.0, 1.0)
        action = AccelDecel(scale_action)
        action.target = sprite
        action.start()

        # At 50% of duration, should be at 50% of scale change
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.scale.x == pytest.approx(1.5, abs=0.1)
        assert sprite.scale.y == pytest.approx(1.5, abs=0.1)

        # Complete the action
        action.update(0.5)
        sprite.update(0.5)
        assert sprite.scale.x == pytest.approx(2.0, abs=0.1)
        assert sprite.scale.y == pytest.approx(2.0, abs=0.1)
        assert action.done
