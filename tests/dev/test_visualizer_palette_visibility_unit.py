"""Unit tests for DevVisualizer palette visibility helpers.

These tests target small, deterministic branches used by CI-only palette window
coordination paths (show/hide, focus restore, and post-show reassert).
"""

from __future__ import annotations

import arcade

from arcadeactions import Action
from arcadeactions.dev.visualizer import DevVisualizer


def test_activate_main_window_schedules_and_activates(mocker):
    """_activate_main_window schedules two attempts and activates when not closed."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    window = mocker.MagicMock()
    window.closed = False
    dev_viz.window = window

    scheduled: list[callable] = []
    delays: list[float] = []

    def schedule_once(fn, delay: float):
        scheduled.append(fn)
        delays.append(float(delay))

    mocker.patch("arcade.schedule_once", side_effect=schedule_once)

    dev_viz._activate_main_window()

    assert delays == [0.0, 0.05]
    assert len(scheduled) == 2

    # Execute the scheduled callbacks to cover the guarded activate call.
    for fn in scheduled:
        fn(0.0)

    assert window.activate.call_count >= 1

    # When activation raises, it should be swallowed.
    window.activate.side_effect = RuntimeError("boom")
    scheduled[0](0.0)


def test_activate_main_window_returns_early_without_window(mocker):
    """_activate_main_window returns early when no window is set."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    mock_schedule = mocker.patch("arcade.schedule_once")

    dev_viz._activate_main_window()

    mock_schedule.assert_not_called()


def test_restore_palette_location_after_show_reasserts(mocker):
    """_restore_palette_location_after_show reasserts on the next tick when visible."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    dev_viz._palette_desired_visible = True
    dev_viz._palette_desired_location = (10, 20)

    palette = mocker.MagicMock()
    palette.visible = True
    dev_viz.palette_window = palette

    scheduled: list[callable] = []

    def schedule_once(fn, _delay: float):
        scheduled.append(fn)

    mocker.patch("arcade.schedule_once", side_effect=schedule_once)
    mock_track = mocker.patch.object(dev_viz._position_tracker, "track_known_position")

    dev_viz._restore_palette_location_after_show()

    # One immediate set + one scheduled reassert.
    assert palette.set_location.call_count == 1
    assert mock_track.call_count == 1
    assert len(scheduled) == 1

    scheduled[0](0.0)

    assert palette.set_location.call_count == 2
    assert mock_track.call_count == 2


def test_apply_palette_visibility_hides_when_not_desired(mocker):
    """_apply_palette_visibility hides palette when visible and not desired."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = True
    dev_viz._palette_desired_visible = False
    dev_viz._palette_show_pending = True

    palette = mocker.MagicMock()
    dev_viz.palette_window = palette

    mock_cache = mocker.patch.object(dev_viz, "_cache_palette_desired_location")
    mock_activate = mocker.patch.object(dev_viz, "_activate_main_window")
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    assert dev_viz._palette_show_pending is False
    mock_cache.assert_called_once()
    palette.hide_window.assert_called_once()
    mock_activate.assert_called_once()
    mock_log.assert_called_once()


def test_apply_palette_visibility_logs_when_create_fails(mocker):
    """_apply_palette_visibility logs and returns when palette creation fails."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = True
    dev_viz._palette_desired_visible = True
    dev_viz.palette_window = None

    mocker.patch.object(dev_viz, "_create_palette_window", return_value=None)
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    mock_log.assert_called_once()


def test_apply_palette_visibility_reuses_cached_location(mocker):
    """_apply_palette_visibility reuses cached absolute palette location when anchored."""
    window = mocker.MagicMock()
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=window)
    dev_viz.visible = True
    dev_viz._palette_desired_visible = True
    dev_viz._palette_desired_location = (10, 20)

    palette = mocker.MagicMock()
    dev_viz.palette_window = palette

    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
    mocker.patch.object(dev_viz, "update_main_window_position", return_value=True)
    mocker.patch.object(dev_viz, "_palette_needs_reposition", return_value=False)
    mock_set = mocker.patch.object(dev_viz, "_set_palette_location")
    mocker.patch.object(dev_viz, "_restore_palette_location_after_show")
    mocker.patch.object(dev_viz, "_activate_main_window")
    mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    mock_set.assert_called_once_with((10, 20))


def test_apply_palette_visibility_when_devviz_hidden_show_failed_create(mocker):
    """When devviz is hidden, showing palette logs a failed-create event."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = False
    dev_viz._palette_desired_visible = True
    dev_viz.palette_window = None

    mocker.patch.object(dev_viz, "_create_palette_window", return_value=None)
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    mock_log.assert_called_once()


def test_update_main_window_position_repositions_palette_when_needed(mocker):
    """update_main_window_position forces palette reposition when anchor changes."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    palette = mocker.MagicMock()
    palette.visible = True
    dev_viz.palette_window = palette
    dev_viz._palette_show_pending = False

    mocker.patch.object(dev_viz, "track_window_position", return_value=True)
    mocker.patch.object(dev_viz, "_palette_needs_reposition", return_value=True)
    mock_position = mocker.patch.object(dev_viz, "_position_palette_window", return_value=True)

    assert dev_viz.update_main_window_position() is True
    mock_position.assert_called_once_with(force=True)


def test_reset_scene_updates_palette_window_dev_context(mocker):
    """reset_scene updates palette_window.dev_context when palette exists."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    palette = mocker.MagicMock()
    dev_viz.palette_window = palette

    new_scene = arcade.SpriteList()
    dev_viz.reset_scene(new_scene)

    assert dev_viz.scene_sprites is new_scene
    assert palette.dev_context == dev_viz.ctx


def test_show_and_hide_set_palette_desired_visible(mocker):
    """show() sets palette desired-visible; hide() clears it."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    mocker.patch.object(dev_viz, "_apply_palette_visibility")
    mock_pause = mocker.patch.object(Action, "pause_all")
    mock_resume = mocker.patch.object(Action, "resume_all")

    dev_viz.show()
    assert dev_viz._palette_desired_visible is True
    mock_pause.assert_called()

    dev_viz.hide()
    assert dev_viz._palette_desired_visible is False
    mock_resume.assert_called()


def test_apply_palette_visibility_hidden_devviz_hides_existing_palette(mocker):
    """When devviz is hidden and palette not desired, existing palette is hidden."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = False
    dev_viz._palette_desired_visible = False
    palette = mocker.MagicMock()
    dev_viz.palette_window = palette
    mock_cache = mocker.patch.object(dev_viz, "_cache_palette_desired_location")
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    mock_cache.assert_called_once()
    palette.hide_window.assert_called_once()
    mock_log.assert_called_once()


def test_apply_palette_visibility_hidden_devviz_delegates_show_path(mocker):
    """When devviz is hidden but palette desired, hidden-mode show helper is used."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = False
    dev_viz._palette_desired_visible = True
    mock_hidden_show = mocker.patch.object(dev_viz, "_apply_palette_visibility_when_devviz_hidden")

    dev_viz._apply_palette_visibility()

    mock_hidden_show.assert_called_once()


def test_apply_palette_visibility_schedules_poll_once_when_location_invalid(mocker):
    """Show path should schedule poll when main window location is unavailable."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = True
    dev_viz._palette_desired_visible = True
    dev_viz._palette_show_pending = False
    dev_viz.palette_window = mocker.MagicMock()
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=False)
    mock_schedule = mocker.patch("arcade.schedule_once")
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    assert dev_viz._palette_show_pending is True
    mock_schedule.assert_called_once()
    mock_log.assert_called_once()


def test_apply_palette_visibility_does_not_reschedule_when_poll_already_pending(mocker):
    """Show path should avoid duplicate schedule when poll is already pending."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = True
    dev_viz._palette_desired_visible = True
    dev_viz._palette_show_pending = True
    dev_viz.palette_window = mocker.MagicMock()
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=False)
    mock_schedule = mocker.patch("arcade.schedule_once")
    mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility()

    mock_schedule.assert_not_called()


def test_apply_palette_visibility_hidden_devviz_schedules_poll_when_location_invalid(mocker):
    """Hidden-devviz show path should schedule poll on invalid location."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = False
    dev_viz._palette_desired_visible = True
    dev_viz._palette_show_pending = False
    dev_viz.palette_window = mocker.MagicMock()
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=False)
    mock_schedule = mocker.patch("arcade.schedule_once")
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility_when_devviz_hidden()

    assert dev_viz._palette_show_pending is True
    mock_schedule.assert_called_once()
    mock_log.assert_called_once()


def test_apply_palette_visibility_hidden_devviz_reuses_cached_location(mocker):
    """Hidden-devviz show path should reuse cached location when anchor is unchanged."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.visible = False
    dev_viz._palette_desired_visible = True
    dev_viz._palette_desired_location = (30, 40)
    palette = mocker.MagicMock()
    dev_viz.palette_window = palette
    mocker.patch.object(dev_viz, "_main_window_has_valid_location", return_value=True)
    mocker.patch.object(dev_viz, "update_main_window_position")
    mocker.patch.object(dev_viz, "_palette_needs_reposition", return_value=False)
    mock_set = mocker.patch.object(dev_viz, "_set_palette_location")
    mock_restore = mocker.patch.object(dev_viz, "_restore_palette_location_after_show")
    mock_activate = mocker.patch.object(dev_viz, "_activate_main_window")
    mock_log = mocker.patch.object(dev_viz, "_log_palette_positions")

    dev_viz._apply_palette_visibility_when_devviz_hidden()

    mock_set.assert_called_once_with((30, 40))
    palette.show_window.assert_called_once()
    mock_restore.assert_called_once()
    mock_activate.assert_called_once()
    mock_log.assert_called_once()


def test_main_window_has_valid_location_guards_invalid_values(mocker):
    """Location helper should reject origin, minimized sentinels, and exceptions."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.window.get_location.return_value = (0, 0)
    assert dev_viz._main_window_has_valid_location() is False

    dev_viz.window.get_location.return_value = (-32001, 100)
    assert dev_viz._main_window_has_valid_location() is False

    dev_viz.window.get_location.side_effect = RuntimeError("boom")
    assert dev_viz._main_window_has_valid_location() is False


def test_palette_needs_reposition_false_when_anchor_matches(mocker):
    """Reposition helper should return False when anchor matches main location."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.palette_window = mocker.MagicMock()
    dev_viz._palette_position_anchor = (100, 200)
    mocker.patch.object(dev_viz, "_get_window_location", return_value=(100, 200))

    assert dev_viz._palette_needs_reposition() is False


def test_cache_palette_desired_location_sets_anchor_even_without_tracked_pos(mocker):
    """Caching should still refresh anchor when tracked palette position is missing."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=mocker.MagicMock())
    dev_viz.palette_window = mocker.MagicMock()
    dev_viz._palette_desired_location = (1, 2)
    mocker.patch.object(dev_viz._position_tracker, "get_tracked_position", return_value=None)
    mocker.patch.object(dev_viz, "_get_window_location", return_value=(300, 400))

    dev_viz._cache_palette_desired_location()

    assert dev_viz._palette_desired_location == (1, 2)
    assert dev_viz._palette_position_anchor == (300, 400)


def test_restore_palette_location_after_show_reassert_bails_when_not_visible(mocker):
    """Scheduled reassert should bail out when palette is no longer visible."""
    dev_viz = DevVisualizer(scene_sprites=arcade.SpriteList(), window=None)
    dev_viz._palette_desired_visible = True
    dev_viz._palette_desired_location = (10, 20)

    palette = mocker.MagicMock()
    palette.visible = False
    dev_viz.palette_window = palette

    scheduled: list[callable] = []

    def schedule_once(fn, _delay: float):
        scheduled.append(fn)

    mocker.patch("arcade.schedule_once", side_effect=schedule_once)
    mock_track = mocker.patch.object(dev_viz._position_tracker, "track_known_position")

    dev_viz._restore_palette_location_after_show()

    assert len(scheduled) == 1
    scheduled[0](0.0)
    # Only initial location track should happen, no reassert track.
    assert mock_track.call_count == 1
