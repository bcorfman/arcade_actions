"""Test suite for composite.py - Composite actions."""

import arcade

from actions.base import Action
from actions.composite import Sequence, Spawn, sequence, spawn


def create_test_sprite() -> arcade.Sprite:
    """Create a sprite with texture for testing."""
    sprite = arcade.Sprite(":resources:images/items/star.png")
    sprite.center_x = 100
    sprite.center_y = 100
    return sprite


class MockAction(Action):
    """Mock action for testing composite actions."""

    def __init__(self, duration=0.1, name="mock"):
        super().__init__()
        self.duration = duration
        self.name = name
        self.time_elapsed = 0.0
        self.started = False
        self.stopped = False

    def start(self):
        super().start()
        self.started = True

    def update(self, delta_time: float):
        super().update(delta_time)
        if not self.done:
            self.time_elapsed += delta_time
            if self.time_elapsed >= self.duration:
                self.done = True

    def stop(self):
        super().stop()
        self.stopped = True

    def clone(self) -> "MockAction":
        return MockAction(self.duration, self.name)


class TestSequence:
    """Test suite for Sequence composite action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_sequence_empty_initialization(self):
        """Test empty Sequence initialization."""
        seq = Sequence()
        assert len(seq.actions) == 0
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_with_actions_initialization(self):
        """Test Sequence initialization with actions."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        seq = Sequence(action1, action2)

        assert len(seq.actions) == 2
        assert seq.actions[0] == action1
        assert seq.actions[1] == action2
        assert seq.current_action is None
        assert seq.current_index == 0

    def test_sequence_empty_completes_immediately(self):
        """Test that empty Sequence completes immediately."""
        sprite = create_test_sprite()
        seq = Sequence()
        seq.target = sprite
        seq.start()

        assert seq.done

    def test_sequence_starts_first_action(self):
        """Test that Sequence starts the first action."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        seq = Sequence(action1, action2)

        seq.target = sprite
        seq.start()

        assert seq.current_action == action1
        assert seq.current_index == 0
        assert action1.started
        assert not action2.started

    def test_sequence_advances_to_next_action(self):
        """Test that Sequence advances to next action when current completes."""
        sprite = create_test_sprite()
        action1 = MockAction(duration=0.05, name="action1")
        action2 = MockAction(duration=0.05, name="action2")
        seq = Sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until first action completes
        seq.update(0.06)

        assert action1.done
        assert seq.current_action == action2
        assert seq.current_index == 1
        assert action2.started

    def test_sequence_completes_when_all_actions_done(self):
        """Test that Sequence completes when all actions are done."""
        sprite = create_test_sprite()
        action1 = MockAction(duration=0.05, name="action1")
        action2 = MockAction(duration=0.05, name="action2")
        seq = Sequence(action1, action2)

        seq.target = sprite
        seq.start()

        # Update until both actions complete
        seq.update(0.06)  # Complete first action
        seq.update(0.06)  # Complete second action

        assert action1.done
        assert action2.done
        assert seq.done
        assert seq.current_action is None

    def test_sequence_stop_stops_current_action(self):
        """Test that stopping Sequence stops the current action."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        seq = Sequence(action1, action2)

        seq.target = sprite
        seq.start()
        seq.stop()

        assert action1.stopped

    def test_sequence_clone(self):
        """Test Sequence cloning."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        seq = Sequence(action1, action2)

        cloned = seq.clone()

        assert cloned is not seq
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2
        assert cloned.actions[0].name == "action1"
        assert cloned.actions[1].name == "action2"


class TestSpawn:
    """Test suite for Spawn composite action."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_spawn_empty_initialization(self):
        """Test empty Spawn initialization."""
        spawn_action = Spawn()
        assert len(spawn_action.actions) == 0

    def test_spawn_with_actions_initialization(self):
        """Test Spawn initialization with actions."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        spawn_action = Spawn(action1, action2)

        assert len(spawn_action.actions) == 2
        assert spawn_action.actions[0] == action1
        assert spawn_action.actions[1] == action2

    def test_spawn_empty_completes_immediately(self):
        """Test that empty Spawn completes immediately."""
        sprite = create_test_sprite()
        spawn_action = Spawn()
        spawn_action.target = sprite
        spawn_action.start()

        assert spawn_action.done

    def test_spawn_starts_all_actions(self):
        """Test that Spawn starts all actions simultaneously."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        spawn_action = Spawn(action1, action2)

        spawn_action.target = sprite
        spawn_action.start()

        assert action1.started
        assert action2.started

    def test_spawn_completes_when_all_actions_done(self):
        """Test that Spawn completes when all actions are done."""
        sprite = create_test_sprite()
        action1 = MockAction(duration=0.05, name="action1")
        action2 = MockAction(duration=0.03, name="action2")
        spawn_action = Spawn(action1, action2)

        spawn_action.target = sprite
        spawn_action.start()

        # Update until both actions complete
        spawn_action.update(0.06)

        assert action1.done
        assert action2.done
        assert spawn_action.done

    def test_spawn_stops_all_actions(self):
        """Test that stopping Spawn stops all actions."""
        sprite = create_test_sprite()
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        spawn_action = Spawn(action1, action2)

        spawn_action.target = sprite
        spawn_action.start()
        spawn_action.stop()

        assert action1.stopped
        assert action2.stopped

    def test_spawn_clone(self):
        """Test Spawn cloning."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")
        spawn_action = Spawn(action1, action2)

        cloned = spawn_action.clone()

        assert cloned is not spawn_action
        assert len(cloned.actions) == 2
        assert cloned.actions[0] is not action1
        assert cloned.actions[1] is not action2
        assert cloned.actions[0].name == "action1"
        assert cloned.actions[1].name == "action2"


class TestCompositeHelperFunctions:
    """Test suite for composite helper functions."""

    def test_sequence_helper_function(self):
        """Test sequence helper function."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")

        seq = sequence(action1, action2)

        assert isinstance(seq, Sequence)
        assert len(seq.actions) == 2
        # Actions should be cloned
        assert seq.actions[0] is not action1
        assert seq.actions[1] is not action2
        assert seq.actions[0].name == "action1"
        assert seq.actions[1].name == "action2"

    def test_spawn_helper_function(self):
        """Test spawn helper function."""
        action1 = MockAction(name="action1")
        action2 = MockAction(name="action2")

        spawn_action = spawn(action1, action2)

        assert isinstance(spawn_action, Spawn)
        assert len(spawn_action.actions) == 2
        # Actions should be cloned
        assert spawn_action.actions[0] is not action1
        assert spawn_action.actions[1] is not action2
        assert spawn_action.actions[0].name == "action1"
        assert spawn_action.actions[1].name == "action2"


class TestNestedComposites:
    """Test suite for nested composite actions."""

    def teardown_method(self):
        """Clean up after each test."""
        Action.clear_all()

    def test_sequence_of_spawns(self):
        """Test Sequence containing Spawn actions."""
        sprite = create_test_sprite()

        # Create two spawn actions
        spawn1 = Spawn(MockAction(0.02, "s1a1"), MockAction(0.02, "s1a2"))
        spawn2 = Spawn(MockAction(0.02, "s2a1"), MockAction(0.02, "s2a2"))

        seq = Sequence(spawn1, spawn2)
        seq.target = sprite
        seq.start()

        # First spawn should start
        assert seq.current_action == spawn1

        # Update to complete first spawn
        seq.update(0.03)

        # Second spawn should start
        assert seq.current_action == spawn2

        # Update to complete second spawn
        seq.update(0.03)

        assert seq.done

    def test_spawn_of_sequences(self):
        """Test Spawn containing Sequence actions."""
        sprite = create_test_sprite()

        # Create two sequence actions
        seq1 = Sequence(MockAction(0.02, "seq1a1"), MockAction(0.02, "seq1a2"))
        seq2 = Sequence(MockAction(0.02, "seq2a1"), MockAction(0.02, "seq2a2"))

        spawn_action = Spawn(seq1, seq2)
        spawn_action.target = sprite
        spawn_action.start()

        # Both sequences should start
        assert seq1.current_action is not None
        assert seq2.current_action is not None

        # Update multiple times to complete both sequences (more realistic)
        for _ in range(3):  # 3 updates of 0.02 each = 0.06 total, enough for both sequences
            spawn_action.update(0.02)

        assert spawn_action.done
