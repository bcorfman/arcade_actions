import pytest

from actions.base import Action, InstantAction, IntervalAction, Loop_InstantAction, Loop_IntervalAction


class MockTarget:
    def __init__(self):
        self.value = 0


@pytest.fixture
def mock_target():
    return MockTarget()


@pytest.fixture
def basic_action():
    return Action()


@pytest.fixture
def test_interval():
    class TestInterval(IntervalAction):
        def __init__(self):
            super().__init__()
            self.duration = 1.0

        def update(self, t):
            self.target.value = t

    return TestInterval()


@pytest.fixture
def test_instant():
    class TestInstant(InstantAction):
        def start(self):
            self.target.value = 1

    return TestInstant()


class TestAction:
    def test_basic_initialization(self, basic_action):
        """Test basic action initialization"""
        assert basic_action.duration is None
        assert basic_action.target is None
        assert basic_action._elapsed == 0.0
        assert not basic_action._done

    def test_start_stop(self, basic_action, mock_target):
        """Test start and stop functionality"""
        basic_action.target = mock_target
        basic_action.start()
        assert basic_action.target == mock_target

        basic_action.stop()
        assert basic_action.target is None

    def test_step(self, basic_action):
        """Test basic step functionality"""
        dt = 0.1
        basic_action.step(dt)
        assert basic_action._elapsed == dt


class TestIntervalAction:
    def test_interval_step(self, test_interval, mock_target):
        """Test interval action stepping"""
        test_interval.target = mock_target
        test_interval.step(0.5)
        assert mock_target.value == 0.5

        test_interval.step(0.5)
        assert mock_target.value == 1.0
        assert test_interval.done()

    def test_interval_zero_duration(self, test_interval, mock_target):
        """Test interval action with zero duration"""
        test_interval.duration = 0
        test_interval.target = mock_target
        test_interval.step(0.1)
        assert mock_target.value == 1.0
        assert test_interval.done()


class TestInstantAction:
    def test_instant_execution(self, test_instant, mock_target):
        """Test instant action execution"""
        test_instant.target = mock_target
        test_instant.start()
        assert mock_target.value == 1
        assert test_instant.done()

    def test_instant_properties(self, test_instant):
        """Test instant action properties"""
        assert test_instant.duration == 0.0


class TestLoopActions:
    @pytest.fixture
    def counter_instant(self):
        counter = {"value": 0}

        class CounterInstant(InstantAction):
            def start(self):
                counter["value"] += 1

        return CounterInstant(), counter

    def test_loop_instant_action(self, counter_instant, mock_target):
        """Test loop instant action"""
        action, counter = counter_instant
        loop_action = Loop_InstantAction(action, 3)
        loop_action.target = mock_target
        loop_action.start()

        assert counter["value"] == 3
        assert loop_action.done()

    def test_loop_interval_action(self, test_interval, mock_target):
        """Test loop interval action"""
        loop_action = Loop_IntervalAction(test_interval, 2)
        loop_action.target = mock_target
        loop_action.start()

        loop_action.update(0.25)  # 25% through first iteration
        assert pytest.approx(mock_target.value, 0.01) == 0.5

        loop_action.update(0.75)  # 75% through second iteration
        assert pytest.approx(mock_target.value, 0.01) == 0.5

    @pytest.mark.parametrize("loop_count,expected_updates", [(1, 1), (2, 2), (3, 3)])
    def test_loop_iterations(self, counter_instant, mock_target, loop_count, expected_updates):
        """Test different loop counts"""
        action, counter = counter_instant
        loop_action = Loop_InstantAction(action, loop_count)
        loop_action.target = mock_target
        loop_action.start()

        assert counter["value"] == expected_updates
