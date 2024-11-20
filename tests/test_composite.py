from actions.base import ActionSprite, Spawn
from actions.interval import FadeIn, MoveTo, RotateBy


def test_repeat_action():
    # Define an action to repeat
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0
    move_action = MoveTo(x=100, y=100, duration=1)
    repeat_action = move_action * 3  # Equivalent to Repeat(move_action, times=3)

    # Test the repeated action
    repeat_action.start(sprite)
    repeat_action.step(1)  # First repeat

    assert sprite.center_x == 100 and sprite.center_y == 100


def test_sequence_action():
    # Create an ActionSprite instance
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0

    # Create a sequence of actions
    move_action = MoveTo(x=100, y=100, duration=1)
    rotate_action = RotateBy(delta_angle=90, duration=1)
    fade_in_action = FadeIn(duration=1)

    # Sequence actions using the plus operator
    sequence_action = move_action + rotate_action + fade_in_action

    # Run through the sequence in steps
    sequence_action.start(sprite)
    sequence_action.step(1)  # Completes MoveTo
    assert sprite.center_x == 100
    assert sprite.center_y == 100

    sequence_action.step(1)  # Completes RotateBy
    assert sprite.angle == 90

    sequence_action.step(1)  # Completes FadeIn
    assert sprite.alpha == 255


def test_spawn_action():
    # Define multiple actions to run in parallel
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0
    move_action = MoveTo(x=100, y=100, duration=1)
    rotate_action = RotateBy(delta_angle=90, duration=1)
    spawn_action = Spawn(move_action, rotate_action)

    spawn_action.start(sprite)
    spawn_action.step(1)  # Both actions should complete

    assert sprite.center_x == 100
    assert sprite.center_y == 100
    assert sprite.angle == 90


def test_combined_sequence_and_repeat():
    # Combined Sequence and Repeat action
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0
    move_action = MoveTo(x=100, y=100, duration=1)
    rotate_action = RotateBy(delta_angle=90, duration=1)

    # Sequence and Repeat together
    combined_action = (move_action + rotate_action) * 2  # Repeat the sequence twice

    combined_action.start(sprite)
    combined_action.step(1)  # First MoveTo

    assert sprite.center_x == 100 and sprite.center_y == 100


def test_complex_pipe_operator():
    # Create a complex action using the pipe (parallel) operator
    sprite = ActionSprite()
    sprite.center_x, sprite.center_y = 0, 0
    move_action = MoveTo(x=100, y=100, duration=1)
    rotate_action = RotateBy(delta_angle=90, duration=1)
    fade_in_action = FadeIn(duration=1)

    # Run actions in parallel
    parallel_action = move_action | rotate_action | fade_in_action

    # Run the parallel action
    parallel_action.start(sprite)
    parallel_action.step(1)  # All actions should complete in parallel

    assert sprite.center_x == 100
    assert sprite.center_y == 100
    assert sprite.angle == 90
    assert sprite.alpha == 255
