"""
Tests for ACE visualizer instrumentation layer.

Tests the debug data store and instrumentation hooks that capture
action lifecycle events and condition evaluations.
"""

from arcadeactions.visualizer.instrumentation import (
    DebugDataStore,
)


class TestDebugDataStore:
    """Test the debug data store for capturing action state."""

    def test_initialization(self):
        """Test that store initializes with correct defaults."""
        store = DebugDataStore(max_events=100, max_evaluations=50)

        assert store.max_events == 100
        assert store.max_evaluations == 50
        assert len(store.events) == 0
        assert len(store.evaluations) == 0
        assert store.current_frame == 0
        assert store.current_time == 0.0
        assert len(store.active_snapshots) == 0

    def test_update_frame(self):
        """Test updating frame and timestamp."""
        store = DebugDataStore()
        store.update_frame(42, 1.5)

        assert store.current_frame == 42
        assert store.current_time == 1.5

    def test_record_event_created(self):
        """Test recording an action creation event."""
        store = DebugDataStore()
        store.update_frame(10, 0.5)

        store.record_event(
            event_type="created",
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
        )

        assert len(store.events) == 1
        event = store.events[0]
        assert event.frame == 10
        assert event.timestamp == 0.5
        assert event.event_type == "created"
        assert event.action_id == 1
        assert event.action_type == "MoveUntil"
        assert event.target_id == 100
        assert event.target_type == "Sprite"
        assert event.tag == "movement"
        assert store.total_actions_created == 1

    def test_record_event_builds_indices(self):
        """Test that event recording builds lookup indices."""
        store = DebugDataStore()

        store.record_event(
            event_type="created",
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
        )

        assert 100 in store.actions_by_target
        assert 1 in store.actions_by_target[100]
        assert "movement" in store.actions_by_tag
        assert 1 in store.actions_by_tag["movement"]

    def test_record_event_removed_cleans_indices(self):
        """Test that removal events clean up indices."""
        store = DebugDataStore()

        # Create action
        store.record_event(
            event_type="created",
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
        )

        # Add snapshot
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        # Remove action
        store.record_event(
            event_type="removed",
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
        )

        assert 1 not in store.actions_by_target.get(100, [])
        assert 1 not in store.actions_by_tag.get("movement", [])
        assert 1 not in store.active_snapshots

    def test_record_condition_evaluation(self):
        """Test recording condition evaluation results."""
        store = DebugDataStore()
        store.update_frame(20, 1.0)

        store.record_condition_evaluation(
            action_id=1, action_type="MoveUntil", result=False, condition_str="sprite.center_x > 700", center_x=650
        )

        assert len(store.evaluations) == 1
        eval_result = store.evaluations[0]
        assert eval_result.frame == 20
        assert eval_result.timestamp == 1.0
        assert eval_result.action_id == 1
        assert eval_result.result is False
        assert eval_result.condition_str == "sprite.center_x > 700"
        assert eval_result.variables["center_x"] == 650
        assert store.total_conditions_evaluated == 1

    def test_update_snapshot_creates_new(self):
        """Test that update_snapshot creates new snapshot if needed."""
        store = DebugDataStore()

        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.25,
        )

        assert 1 in store.active_snapshots
        snapshot = store.active_snapshots[1]
        assert snapshot.action_id == 1
        assert snapshot.action_type == "MoveUntil"
        assert snapshot.progress == 0.25

    def test_update_snapshot_metadata_merge(self):
        """Test that metadata updates merge rather than overwrite."""
        store = DebugDataStore()

        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
            metadata={"path_points": [(0, 0), (1, 1)]},
        )

        store.update_snapshot(action_id=1, metadata={"path_points": [(2, 2)], "extra": 5})

        snapshot = store.active_snapshots[1]
        assert snapshot.metadata["extra"] == 5
        assert (2, 2) in snapshot.metadata["path_points"]

    def test_update_snapshot_updates_existing(self):
        """Test that update_snapshot modifies existing snapshot."""
        store = DebugDataStore()

        # Create initial snapshot
        store.update_snapshot(
            action_id=1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="test",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.5,
            progress=0.25,
        )

        # Update progress
        store.update_snapshot(action_id=1, progress=0.75)

        snapshot = store.active_snapshots[1]
        assert snapshot.progress == 0.75
        assert snapshot.action_type == "MoveUntil"  # Unchanged

    def test_get_events_for_action(self):
        """Test retrieving events for a specific action."""
        store = DebugDataStore()

        store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        store.record_event("started", 1, "MoveUntil", 100, "Sprite")
        store.record_event("created", 2, "RotateUntil", 100, "Sprite")
        store.record_event("stopped", 1, "MoveUntil", 100, "Sprite")

        events = store.get_events_for_action(1)
        assert len(events) == 3
        assert all(e.action_id == 1 for e in events)

    def test_get_evaluations_for_action(self):
        """Test retrieving evaluations for a specific action."""
        store = DebugDataStore()

        store.record_condition_evaluation(1, "MoveUntil", False)
        store.record_condition_evaluation(2, "RotateUntil", False)
        store.record_condition_evaluation(1, "MoveUntil", True)

        evals = store.get_evaluations_for_action(1)
        assert len(evals) == 2
        assert all(e.action_id == 1 for e in evals)

    def test_get_actions_for_target(self):
        """Test retrieving all actions for a target."""
        store = DebugDataStore()

        # Create actions for target 100
        store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        store.record_event("created", 2, "RotateUntil", 100, "Sprite")
        store.update_snapshot(
            1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            2,
            action_type="RotateUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        # Create action for different target
        store.record_event("created", 3, "FadeTo", 200, "Sprite")
        store.update_snapshot(
            3,
            action_type="FadeTo",
            target_id=200,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        snapshots = store.get_actions_for_target(100)
        assert len(snapshots) == 2
        assert all(s.target_id == 100 for s in snapshots)

    def test_get_actions_by_tag(self):
        """Test retrieving all actions with a specific tag."""
        store = DebugDataStore()

        store.record_event("created", 1, "MoveUntil", 100, "Sprite", tag="movement")
        store.record_event("created", 2, "RotateUntil", 100, "Sprite", tag="movement")
        store.record_event("created", 3, "FadeTo", 100, "Sprite", tag="visual")

        store.update_snapshot(
            1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            2,
            action_type="RotateUntil",
            target_id=100,
            target_type="Sprite",
            tag="movement",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )
        store.update_snapshot(
            3,
            action_type="FadeTo",
            target_id=100,
            target_type="Sprite",
            tag="visual",
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        movement_snapshots = store.get_actions_by_tag("movement")
        assert len(movement_snapshots) == 2
        assert all(s.tag == "movement" for s in movement_snapshots)

    def test_ring_buffer_limits_events(self):
        """Test that events ring buffer respects max size."""
        store = DebugDataStore(max_events=5, max_evaluations=10)

        # Add more events than the limit
        for i in range(10):
            store.record_event("created", i, "MoveUntil", 100, "Sprite")

        assert len(store.events) == 5  # Limited to max_events
        # Oldest events should be dropped
        assert store.events[0].action_id == 5

    def test_ring_buffer_limits_evaluations(self):
        """Test that evaluations ring buffer respects max size."""
        store = DebugDataStore(max_events=10, max_evaluations=3)

        # Add more evaluations than the limit
        for i in range(10):
            store.record_condition_evaluation(i, "MoveUntil", False)

        assert len(store.evaluations) == 3  # Limited to max_evaluations

    def test_clear(self):
        """Test clearing all store data."""
        store = DebugDataStore()
        store.update_frame(100, 5.0)
        store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        store.record_condition_evaluation(1, "MoveUntil", False)
        store.update_snapshot(
            1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        store.clear()

        assert len(store.events) == 0
        assert len(store.evaluations) == 0
        assert len(store.active_snapshots) == 0
        assert store.current_frame == 0
        assert store.current_time == 0.0
        assert store.total_actions_created == 0

    def test_get_statistics(self):
        """Test retrieving store statistics."""
        store = DebugDataStore()
        store.update_frame(50, 2.5)
        store.record_event("created", 1, "MoveUntil", 100, "Sprite")
        store.record_condition_evaluation(1, "MoveUntil", False)
        store.update_snapshot(
            1,
            action_type="MoveUntil",
            target_id=100,
            target_type="Sprite",
            tag=None,
            is_active=True,
            is_paused=False,
            factor=1.0,
            elapsed=0.0,
            progress=None,
        )

        stats = store.get_statistics()
        stats = store.get_statistics()
        assert stats["current_frame"] == 50
        assert stats["current_time"] == 2.5
        assert stats["active_actions"] == 1
        assert stats["total_created"] == 1
        assert stats["total_evaluations"] == 1
        assert stats["events_buffered"] == 1
        assert stats["evaluations_buffered"] == 1


class TestFrameCounterIntegration:
    """Test that instrumentation correctly uses Action.current_frame()."""

    def test_debug_store_receives_frame_numbers(self):
        """Test that DebugDataStore receives frame numbers from Action frame counter."""
        import arcade

        from arcadeactions import Action
        from arcadeactions.conditional import MoveUntil
        from arcadeactions.frame_timing import after_frames

        store = DebugDataStore()
        Action.set_debug_store(store)
        Action._enable_visualizer = True
        Action._frame_counter = 0

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Create and apply action
        action = MoveUntil((5, 0), condition=after_frames(10))
        action.apply(sprite, tag="test_frame")

        # Update a few frames
        for i in range(5):
            Action.update_all(0.016)

        # Store should have received frame updates
        assert store.current_frame == 5
        assert store.current_frame == Action.current_frame()

        # Events should have correct frame numbers
        events = store.get_events_for_action(id(action))
        assert len(events) > 0
        # Created event should be at frame 0 or 1
        created_events = [e for e in events if e.event_type == "created"]
        assert len(created_events) > 0
        assert created_events[0].frame >= 0
        assert created_events[0].frame <= Action.current_frame()

        # Clean up
        Action._enable_visualizer = False
        Action.set_debug_store(None)
        Action.stop_all()

    def test_pause_snapshots_reflect_pause_state(self):
        """Test that snapshots reflect pause state when actions are paused."""
        import arcade

        from arcadeactions import Action
        from arcadeactions.conditional import MoveUntil
        from arcadeactions.frame_timing import after_frames

        store = DebugDataStore()
        Action.set_debug_store(store)
        Action._enable_visualizer = True
        Action._frame_counter = 0

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        action = MoveUntil((5, 0), condition=after_frames(10))
        action.apply(sprite, tag="test_pause")

        # Update a few frames
        for _ in range(3):
            Action.update_all(0.016)

        # Snapshot should show not paused
        snapshot = store.active_snapshots.get(id(action))
        assert snapshot is not None
        assert snapshot.is_paused is False

        # Pause actions
        Action.pause_all()

        # Update snapshot
        action._update_snapshot()

        # Snapshot should now show paused
        snapshot = store.active_snapshots.get(id(action))
        assert snapshot is not None
        assert snapshot.is_paused is True

        # Frame counter should not increment when paused
        frame_before = Action.current_frame()
        Action.update_all(0.016)
        assert Action.current_frame() == frame_before

        # Clean up
        Action._enable_visualizer = False
        Action.set_debug_store(None)
        Action.stop_all()


class TestTimelinePruning:
    """Test that timeline entries are properly pruned when actions complete."""

    def test_timeline_shows_only_active_entries(self):
        """Test that timeline shows only active actions to match the overlay."""
        import arcade

        from arcadeactions import Action
        from arcadeactions.conditional import MoveUntil
        from arcadeactions.frame_timing import after_frames
        from arcadeactions.visualizer.timeline import TimelineStrip

        store = DebugDataStore()
        Action.set_debug_store(store)
        Action._enable_visualizer = True
        Action._frame_counter = 0

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        timeline = TimelineStrip(store)

        # Create 30 short-lived actions that will complete quickly
        for i in range(30):
            action = MoveUntil((5, 0), condition=after_frames(2))
            action.apply(sprite, tag=f"bullet_{i}")
            # Run the action until completion
            for _ in range(5):
                Action.update_all(0.016)

        # Now create 2 active actions that won't complete
        active1 = MoveUntil((1, 0), condition=after_frames(1000))
        active1.apply(sprite, tag="active1")
        active2 = MoveUntil((1, 0), condition=after_frames(1000))
        active2.apply(sprite, tag="active2")

        Action.update_all(0.016)
        timeline.update()

        # Timeline should show ONLY active actions to match overlay
        assert len(timeline.entries) == 2

        # All entries should be active
        active_entries = [e for e in timeline.entries if e.is_active]
        assert len(active_entries) == 2

        # Should have NO inactive entries
        inactive_entries = [e for e in timeline.entries if not e.is_active]
        assert len(inactive_entries) == 0

        # Cache should only contain active actions
        assert len(timeline._entry_cache) == 2

        # Clean up
        Action._enable_visualizer = False
        Action.set_debug_store(None)
        Action.stop_all()

    def test_timeline_removes_inactive_entries_immediately(self):
        """Test that inactive entries are removed from cache immediately."""
        import arcade

        from arcadeactions import Action
        from arcadeactions.conditional import MoveUntil
        from arcadeactions.frame_timing import after_frames
        from arcadeactions.visualizer.timeline import TimelineStrip

        store = DebugDataStore()
        Action.set_debug_store(store)
        Action._enable_visualizer = True
        Action._frame_counter = 0

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        timeline = TimelineStrip(store)

        # Create an action and let it complete
        action1 = MoveUntil((5, 0), condition=after_frames(2))
        action_id = id(action1)
        action1.apply(sprite, tag="bullet_1")

        # Run until completion
        for _ in range(5):
            Action.update_all(0.016)

        timeline.update()

        # Since we only show active actions, completed action should be removed from cache
        assert action_id not in timeline._entry_cache

        # Timeline should be empty (no active actions)
        assert len(timeline.entries) == 0

        # Clean up
        Action._enable_visualizer = False
        Action.set_debug_store(None)
        Action.stop_all()
