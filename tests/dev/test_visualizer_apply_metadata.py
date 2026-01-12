"""Tests for DevVisualizer apply_metadata_actions method.

Tests the apply_metadata_actions method which converts action metadata
(_action_configs) to actual running actions. This tests current behavior
including hasattr/getattr patterns.
"""

from __future__ import annotations

import pytest
import arcade

from actions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase


class TestApplyMetadataActionsEarlyReturn(ActionTestBase):
    """Test suite for early return behavior in apply_metadata_actions."""

    def test_apply_metadata_early_return_if_no_configs(self, window, test_sprite, mocker):
        """Test that apply_metadata_actions returns early if sprite has no _action_configs."""
        # Document current behavior: hasattr check causes early return
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        assert not hasattr(test_sprite, '_action_configs')
        
        mock_registry = mocker.patch('actions.dev.get_preset_registry')
        
        # Should return early without calling registry
        dev_viz.apply_metadata_actions(test_sprite)
        mock_registry.assert_not_called()


class TestApplyMetadataActionsPresetBased(ActionTestBase):
    """Test suite for preset-based action application."""

    def test_apply_preset_action(self, window, test_sprite, mocker):
        """Test applying a preset-based action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        # Mock preset registry
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        # Set up sprite with _action_configs
        test_sprite._action_configs = [{'preset': 'test_preset', 'params': {'speed': 5}}]
        
        # Call apply_metadata_actions
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Verify action was created and applied
        mock_registry.create.assert_called_once_with('test_preset', dev_viz.ctx, speed=5)
        mock_preset_action.apply.assert_called_once_with(test_sprite)

    def test_apply_preset_with_empty_params(self, window, test_sprite, mocker):
        """Test applying a preset with empty params dict."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{'preset': 'test_preset', 'params': {}}]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_registry.create.assert_called_once_with('test_preset', dev_viz.ctx)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_none_params(self, window, test_sprite, mocker):
        """Test applying a preset with None params (should be treated as empty dict)."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{'preset': 'test_preset', 'params': None}]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # None params should be converted to empty dict
        mock_registry.create.assert_called_once_with('test_preset', dev_viz.ctx)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_condition_override(self, window, test_sprite, mocker):
        """Test applying a preset with condition override."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_preset_action.condition = None  # Initially no condition
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Verify condition was set (should be a callable from resolve_condition)
        assert callable(mock_preset_action.condition)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_condition_override_fails_gracefully(self, window, test_sprite, mocker):
        """Test that condition override failure is handled gracefully."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        # Create a custom class that raises when condition is set
        class ActionWithFailingCondition:
            def __init__(self):
                self._condition = None
                self.apply = mocker.MagicMock()
            
            @property
            def condition(self):
                return self._condition
            
            @condition.setter
            def condition(self, value):
                raise AttributeError("Cannot set condition")
        
        mock_preset_action = ActionWithFailingCondition()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'condition': 'after_frames:60'
        }]
        
        # Should not raise, should continue
        dev_viz.apply_metadata_actions(test_sprite)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_on_stop_callback(self, window, test_sprite, mocker):
        """Test applying a preset with on_stop callback."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        
        def resolver(callback_name):
            return lambda: None  # Return a dummy callback
        
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'on_stop': 'my_callback'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite, resolver=resolver)
        
        # Verify callback was set
        assert callable(mock_preset_action.on_stop)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_on_stop_callback_no_resolver(self, window, test_sprite, mocker):
        """Test that on_stop callback is skipped if no resolver provided."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        # Create a custom class to track if on_stop was set
        class ActionTrackingOnStop:
            def __init__(self):
                self._on_stop = None
                self._on_stop_was_set = False
                self.apply = mocker.MagicMock()
            
            @property
            def on_stop(self):
                return self._on_stop
            
            @on_stop.setter
            def on_stop(self, value):
                self._on_stop = value
                self._on_stop_was_set = True
        
        mock_preset_action = ActionTrackingOnStop()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'on_stop': 'my_callback'  # String without resolver
        }]
        
        dev_viz.apply_metadata_actions(test_sprite, resolver=None)
        
        # on_stop should not be set (resolver is None, so string callback is skipped)
        assert not mock_preset_action._on_stop_was_set, "on_stop should not have been set when resolver is None"
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_tag(self, window, test_sprite, mocker):
        """Test applying a preset with tag."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'tag': 'movement'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.tag == 'movement'
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_velocity_override(self, window, test_sprite, mocker):
        """Test applying a preset with velocity override."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        # Add target_velocity attribute to make hasattr check pass
        mock_preset_action.target_velocity = (0, 0)
        mock_preset_action.current_velocity = (0, 0)
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'velocity': (5, 10)
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.target_velocity == (5, 10)
        assert mock_preset_action.current_velocity == (5, 10)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_velocity_override_no_attribute(self, window, test_sprite, mocker):
        """Test that velocity override is skipped if action has no target_velocity attribute."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        # Don't add target_velocity attribute
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'velocity': (5, 10)
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Should not raise, should continue without setting velocity
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_bounds_override(self, window, test_sprite, mocker):
        """Test applying a preset with bounds override."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_preset_action.bounds = None
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'bounds': (0, 0, 800, 600)
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.bounds == (0, 0, 800, 600)
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_boundary_behavior_override(self, window, test_sprite, mocker):
        """Test applying a preset with boundary_behavior override."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_preset_action.boundary_behavior = None
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'boundary_behavior': 'wrap'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.boundary_behavior == 'wrap'
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_velocity_provider_override(self, window, test_sprite, mocker):
        """Test applying a preset with velocity_provider override."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_preset_action.velocity_provider = None
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        def velocity_provider():
            return (1, 1)
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'velocity_provider': velocity_provider
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.velocity_provider is velocity_provider
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_with_boundary_callbacks(self, window, test_sprite, mocker):
        """Test applying a preset with boundary callbacks."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_preset_action.on_boundary_enter = None
        mock_preset_action.on_boundary_exit = None
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        def enter_cb():
            pass
        def exit_cb():
            pass
        
        test_sprite._action_configs = [{
            'preset': 'test_preset',
            'params': {},
            'on_boundary_enter': enter_cb,
            'on_boundary_exit': exit_cb
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_preset_action.on_boundary_enter is enter_cb
        assert mock_preset_action.on_boundary_exit is exit_cb
        mock_preset_action.apply.assert_called_once()

    def test_apply_preset_invalid_preset_skipped(self, window, test_sprite, mocker):
        """Test that invalid presets are skipped silently."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_registry.create.side_effect = KeyError("Preset 'invalid' not found")
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [{'preset': 'invalid', 'params': {}}]
        
        # Should not raise, should continue to next config
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_registry.create.assert_called_once()

    def test_apply_multiple_preset_configs(self, window, test_sprite, mocker):
        """Test applying multiple preset configs."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_registry = mocker.MagicMock()
        mock_action1 = mocker.MagicMock()
        mock_action2 = mocker.MagicMock()
        mock_registry.create.side_effect = [mock_action1, mock_action2]
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        test_sprite._action_configs = [
            {'preset': 'preset1', 'params': {}},
            {'preset': 'preset2', 'params': {}}
        ]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        assert mock_registry.create.call_count == 2
        mock_action1.apply.assert_called_once()
        mock_action2.apply.assert_called_once()


class TestApplyMetadataActionsDirectActionTypes(ActionTestBase):
    """Test suite for direct action_type application (non-preset)."""

    def test_apply_move_until(self, window, test_sprite, mocker):
        """Test applying MoveUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Verify move_until was called with correct parameters
        mock_move_until.assert_called_once()
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['velocity'] == (5, 0)
        assert callable(call_kwargs['condition'])
        assert call_kwargs['bounds'] is None
        assert call_kwargs['boundary_behavior'] is None
        assert call_kwargs['tag'] is None

    def test_apply_move_until_with_all_params(self, window, test_sprite, mocker):
        """Test applying MoveUntil with all optional parameters."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        def velocity_provider():
            return (1, 1)
        
        def on_boundary_enter():
            pass
        
        def on_boundary_exit():
            pass
        
        def on_stop():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'condition': 'after_frames:60',
            'bounds': (0, 0, 800, 600),
            'boundary_behavior': 'wrap',
            'tag': 'movement',
            'velocity_provider': velocity_provider,
            'on_boundary_enter': on_boundary_enter,
            'on_boundary_exit': on_boundary_exit,
            'on_stop': on_stop
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['velocity'] == (5, 0)
        assert call_kwargs['bounds'] == (0, 0, 800, 600)
        assert call_kwargs['boundary_behavior'] == 'wrap'
        assert call_kwargs['tag'] == 'movement'
        assert call_kwargs['velocity_provider'] is velocity_provider
        assert call_kwargs['on_boundary_enter'] is on_boundary_enter
        assert call_kwargs['on_boundary_exit'] is on_boundary_exit
        assert call_kwargs['on_stop'] is on_stop

    def test_apply_follow_path_until(self, window, test_sprite, mocker):
        """Test applying FollowPathUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_follow_path = mocker.patch('actions.follow_path_until')
        
        control_points = [(0, 0), (100, 100), (200, 0)]
        test_sprite._action_configs = [{
            'action_type': 'FollowPathUntil',
            'control_points': control_points,
            'velocity': 50.0,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_follow_path.assert_called_once()
        call_kwargs = mock_follow_path.call_args[1]
        assert call_kwargs['control_points'] == control_points
        assert call_kwargs['velocity'] == 50.0
        assert callable(call_kwargs['condition'])

    def test_apply_follow_path_until_with_all_params(self, window, test_sprite, mocker):
        """Test applying FollowPathUntil with all optional parameters."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_follow_path = mocker.patch('actions.follow_path_until')
        
        control_points = [(0, 0), (100, 100)]
        def on_stop():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'FollowPathUntil',
            'control_points': control_points,
            'velocity': 50.0,
            'condition': 'after_frames:60',
            'rotate_with_path': True,
            'rotation_offset': 90.0,
            'use_physics': True,
            'steering_gain': 10.0,
            'on_stop': on_stop
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_follow_path.call_args[1]
        assert call_kwargs['rotate_with_path'] is True
        assert call_kwargs['rotation_offset'] == 90.0
        assert call_kwargs['use_physics'] is True
        assert call_kwargs['steering_gain'] == 10.0
        assert call_kwargs['on_stop'] is on_stop

    def test_apply_follow_path_until_skipped_if_no_control_points(self, window, test_sprite, mocker):
        """Test that FollowPathUntil is skipped if control_points is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_follow_path = mocker.patch('actions.follow_path_until')
        
        test_sprite._action_configs = [{
            'action_type': 'FollowPathUntil',
            'velocity': 50.0,
            'condition': 'after_frames:60'
            # Missing control_points
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Should not be called if control_points is missing
        mock_follow_path.assert_not_called()

    def test_apply_cycle_textures_until(self, window, test_sprite, mocker):
        """Test applying CycleTexturesUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_cycle = mocker.patch('actions.cycle_textures_until')
        
        textures = [arcade.load_texture(":resources:images/tiles/grassCenter.png")]
        test_sprite._action_configs = [{
            'action_type': 'CycleTexturesUntil',
            'textures': textures,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_cycle.assert_called_once()
        call_kwargs = mock_cycle.call_args[1]
        assert call_kwargs['textures'] == textures
        assert call_kwargs['frames_per_texture'] == 1  # Default
        assert call_kwargs['direction'] == 1  # Default

    def test_apply_cycle_textures_until_with_params(self, window, test_sprite, mocker):
        """Test applying CycleTexturesUntil with custom parameters."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_cycle = mocker.patch('actions.cycle_textures_until')
        
        textures = [arcade.load_texture(":resources:images/tiles/grassCenter.png")]
        def on_stop():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'CycleTexturesUntil',
            'textures': textures,
            'frames_per_texture': 5,
            'direction': -1,
            'tag': 'animation',
            'on_stop': on_stop,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_cycle.call_args[1]
        assert call_kwargs['frames_per_texture'] == 5
        assert call_kwargs['direction'] == -1
        assert call_kwargs['tag'] == 'animation'
        assert call_kwargs['on_stop'] is on_stop

    def test_apply_cycle_textures_until_skipped_if_no_textures(self, window, test_sprite, mocker):
        """Test that CycleTexturesUntil is skipped if textures is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_cycle = mocker.patch('actions.cycle_textures_until')
        
        test_sprite._action_configs = [{
            'action_type': 'CycleTexturesUntil',
            'condition': 'after_frames:60'
            # Missing textures
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_cycle.assert_not_called()

    def test_apply_fade_until(self, window, test_sprite, mocker):
        """Test applying FadeUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_fade = mocker.patch('actions.fade_until')
        
        test_sprite._action_configs = [{
            'action_type': 'FadeUntil',
            'fade_velocity': -5,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_fade.assert_called_once()
        call_kwargs = mock_fade.call_args[1]
        assert call_kwargs['velocity'] == -5
        assert callable(call_kwargs['condition'])

    def test_apply_fade_until_skipped_if_no_fade_velocity(self, window, test_sprite, mocker):
        """Test that FadeUntil is skipped if fade_velocity is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_fade = mocker.patch('actions.fade_until')
        
        test_sprite._action_configs = [{
            'action_type': 'FadeUntil',
            'condition': 'after_frames:60'
            # Missing fade_velocity
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_fade.assert_not_called()

    def test_apply_blink_until(self, window, test_sprite, mocker):
        """Test applying BlinkUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_blink = mocker.patch('actions.blink_until')
        
        def on_blink_enter():
            pass
        def on_blink_exit():
            pass
        def on_stop():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'BlinkUntil',
            'frames_until_change': 10,
            'condition': 'after_frames:60',
            'on_blink_enter': on_blink_enter,
            'on_blink_exit': on_blink_exit,
            'on_stop': on_stop,
            'tag': 'blink'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_blink.assert_called_once()
        call_kwargs = mock_blink.call_args[1]
        assert call_kwargs['frames_until_change'] == 10
        assert call_kwargs['on_blink_enter'] is on_blink_enter
        assert call_kwargs['on_blink_exit'] is on_blink_exit
        assert call_kwargs['on_stop'] is on_stop
        assert call_kwargs['tag'] == 'blink'

    def test_apply_blink_until_skipped_if_no_frames(self, window, test_sprite, mocker):
        """Test that BlinkUntil is skipped if frames_until_change is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_blink = mocker.patch('actions.blink_until')
        
        test_sprite._action_configs = [{
            'action_type': 'BlinkUntil',
            'condition': 'after_frames:60'
            # Missing frames_until_change
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_blink.assert_not_called()

    def test_apply_rotate_until(self, window, test_sprite, mocker):
        """Test applying RotateUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_rotate = mocker.patch('actions.rotate_until')
        
        test_sprite._action_configs = [{
            'action_type': 'RotateUntil',
            'angular_velocity': 90.0,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_rotate.assert_called_once()
        call_kwargs = mock_rotate.call_args[1]
        assert call_kwargs['angular_velocity'] == 90.0
        assert callable(call_kwargs['condition'])

    def test_apply_rotate_until_skipped_if_no_angular_velocity(self, window, test_sprite, mocker):
        """Test that RotateUntil is skipped if angular_velocity is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_rotate = mocker.patch('actions.rotate_until')
        
        test_sprite._action_configs = [{
            'action_type': 'RotateUntil',
            'condition': 'after_frames:60'
            # Missing angular_velocity
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_rotate.assert_not_called()

    def test_apply_tween_until(self, window, test_sprite, mocker):
        """Test applying TweenUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_tween = mocker.patch('actions.tween_until')
        
        test_sprite._action_configs = [{
            'action_type': 'TweenUntil',
            'start_value': 0.0,
            'end_value': 1.0,
            'property_name': 'alpha',
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_tween.assert_called_once()
        call_kwargs = mock_tween.call_args[1]
        assert call_kwargs['start_value'] == 0.0
        assert call_kwargs['end_value'] == 1.0
        assert call_kwargs['property_name'] == 'alpha'

    def test_apply_tween_until_skipped_if_missing_params(self, window, test_sprite, mocker):
        """Test that TweenUntil is skipped if required params are missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_tween = mocker.patch('actions.tween_until')
        
        # Missing end_value
        test_sprite._action_configs = [{
            'action_type': 'TweenUntil',
            'start_value': 0.0,
            'property_name': 'alpha',
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_tween.assert_not_called()

    def test_apply_scale_until(self, window, test_sprite, mocker):
        """Test applying ScaleUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_scale = mocker.patch('actions.scale_until')
        
        test_sprite._action_configs = [{
            'action_type': 'ScaleUntil',
            'velocity': 0.1,
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_scale.assert_called_once()
        call_kwargs = mock_scale.call_args[1]
        assert call_kwargs['velocity'] == 0.1

    def test_apply_scale_until_skipped_if_no_velocity(self, window, test_sprite, mocker):
        """Test that ScaleUntil is skipped if velocity is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_scale = mocker.patch('actions.scale_until')
        
        test_sprite._action_configs = [{
            'action_type': 'ScaleUntil',
            'condition': 'after_frames:60'
            # Missing velocity
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_scale.assert_not_called()

    def test_apply_callback_until(self, window, test_sprite, mocker):
        """Test applying CallbackUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_callback = mocker.patch('actions.callback_until')
        
        def my_callback():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'CallbackUntil',
            'callback': my_callback,
            'condition': 'after_frames:60',
            'seconds_between_calls': 0.5
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_callback.assert_called_once()
        call_kwargs = mock_callback.call_args[1]
        assert call_kwargs['callback'] is my_callback
        assert call_kwargs['seconds_between_calls'] == 0.5

    def test_apply_callback_until_skipped_if_no_callback(self, window, test_sprite, mocker):
        """Test that CallbackUntil is skipped if callback is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_callback = mocker.patch('actions.callback_until')
        
        test_sprite._action_configs = [{
            'action_type': 'CallbackUntil',
            'condition': 'after_frames:60'
            # Missing callback
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_callback.assert_not_called()

    def test_apply_delay_until(self, window, test_sprite, mocker):
        """Test applying DelayUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_delay = mocker.patch('actions.delay_until')
        
        def on_stop():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'DelayUntil',
            'condition': 'after_frames:60',
            'tag': 'delay',
            'on_stop': on_stop
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_delay.assert_called_once()
        call_kwargs = mock_delay.call_args[1]
        assert callable(call_kwargs['condition'])
        assert call_kwargs['tag'] == 'delay'
        assert call_kwargs['on_stop'] is on_stop

    def test_apply_emit_particles_until(self, window, test_sprite, mocker):
        """Test applying EmitParticlesUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_emit = mocker.patch('actions.emit_particles_until')
        
        def emitter_factory():
            return None  # Mock emitter
        
        test_sprite._action_configs = [{
            'action_type': 'EmitParticlesUntil',
            'emitter_factory': emitter_factory,
            'condition': 'after_frames:60',
            'anchor': 'bottom',
            'follow_rotation': True,
            'start_paused': False,
            'destroy_on_stop': False
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_emit.assert_called_once()
        call_kwargs = mock_emit.call_args[1]
        assert call_kwargs['emitter_factory'] is emitter_factory
        assert call_kwargs['anchor'] == 'bottom'
        assert call_kwargs['follow_rotation'] is True
        assert call_kwargs['start_paused'] is False
        assert call_kwargs['destroy_on_stop'] is False

    def test_apply_emit_particles_until_skipped_if_no_factory(self, window, test_sprite, mocker):
        """Test that EmitParticlesUntil is skipped if emitter_factory is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_emit = mocker.patch('actions.emit_particles_until')
        
        test_sprite._action_configs = [{
            'action_type': 'EmitParticlesUntil',
            'condition': 'after_frames:60'
            # Missing emitter_factory
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_emit.assert_not_called()

    def test_apply_glow_until(self, window, test_sprite, mocker):
        """Test applying GlowUntil action."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_glow = mocker.patch('actions.glow_until')
        
        def shadertoy_factory():
            return None  # Mock shadertoy
        
        def uniforms_provider():
            return {}
        
        def get_camera_bottom_left():
            return (0, 0)
        
        test_sprite._action_configs = [{
            'action_type': 'GlowUntil',
            'shadertoy_factory': shadertoy_factory,
            'condition': 'after_frames:60',
            'uniforms_provider': uniforms_provider,
            'get_camera_bottom_left': get_camera_bottom_left,
            'auto_resize': False
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_glow.assert_called_once()
        call_kwargs = mock_glow.call_args[1]
        assert call_kwargs['shadertoy_factory'] is shadertoy_factory
        assert call_kwargs['uniforms_provider'] is uniforms_provider
        assert call_kwargs['get_camera_bottom_left'] is get_camera_bottom_left
        assert call_kwargs['auto_resize'] is False

    def test_apply_glow_until_skipped_if_no_factory(self, window, test_sprite, mocker):
        """Test that GlowUntil is skipped if shadertoy_factory is missing."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_glow = mocker.patch('actions.glow_until')
        
        test_sprite._action_configs = [{
            'action_type': 'GlowUntil',
            'condition': 'after_frames:60'
            # Missing shadertoy_factory
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        mock_glow.assert_not_called()

    def test_apply_unknown_action_type_skipped(self, window, test_sprite, mocker):
        """Test that unknown action types are skipped silently."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        # No preset, no known action_type
        test_sprite._action_configs = [{
            'action_type': 'UnknownActionType',
            'condition': 'after_frames:60'
        }]
        
        # Should not raise, should continue
        dev_viz.apply_metadata_actions(test_sprite)


class TestApplyMetadataActionsConditionResolution(ActionTestBase):
    """Test suite for condition resolution in apply_metadata_actions."""

    def test_condition_defaults_to_infinite(self, window, test_sprite, mocker):
        """Test that condition defaults to infinite if not specified."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0)
            # No condition specified
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        # Should default to "infinite" which resolves to a callable
        assert callable(call_kwargs['condition'])
        # Infinite condition should return False
        assert call_kwargs['condition']() is False

    def test_condition_string_after_frames(self, window, test_sprite, mocker):
        """Test condition resolution with after_frames string."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'condition': 'after_frames:60'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        assert callable(call_kwargs['condition'])

    def test_condition_callable(self, window, test_sprite, mocker):
        """Test condition resolution with callable."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        def my_condition():
            return True
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'condition': my_condition
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['condition'] is my_condition


class TestApplyMetadataActionsCallbackResolution(ActionTestBase):
    """Test suite for callback resolution in apply_metadata_actions."""

    def test_callback_callable_passed_through(self, window, test_sprite, mocker):
        """Test that callable callbacks are passed through unchanged."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        def my_callback():
            pass
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'on_stop': my_callback
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['on_stop'] is my_callback

    def test_callback_string_with_resolver(self, window, test_sprite, mocker):
        """Test that string callbacks are resolved using resolver."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        def resolved_callback():
            pass
        
        def resolver(callback_name):
            assert callback_name == 'my_callback'
            return resolved_callback
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'on_stop': 'my_callback'
        }]
        
        dev_viz.apply_metadata_actions(test_sprite, resolver=resolver)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['on_stop'] is resolved_callback

    def test_callback_string_without_resolver(self, window, test_sprite, mocker):
        """Test that string callbacks are None if no resolver provided."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'on_stop': 'my_callback'  # String without resolver
        }]
        
        dev_viz.apply_metadata_actions(test_sprite, resolver=None)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['on_stop'] is None

    def test_callback_none_passed_through(self, window, test_sprite, mocker):
        """Test that None callbacks are passed through."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [{
            'action_type': 'MoveUntil',
            'velocity': (5, 0),
            'on_stop': None
        }]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        call_kwargs = mock_move_until.call_args[1]
        assert call_kwargs['on_stop'] is None


class TestApplyMetadataActionsMixedConfigs(ActionTestBase):
    """Test suite for mixed preset and direct action configs."""

    def test_apply_mixed_preset_and_direct_actions(self, window, test_sprite, mocker):
        """Test applying both preset and direct action configs."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        # Mock preset registry
        mock_registry = mocker.MagicMock()
        mock_preset_action = mocker.MagicMock()
        mock_registry.create.return_value = mock_preset_action
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        # Mock direct action
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [
            {'preset': 'preset1', 'params': {}},
            {'action_type': 'MoveUntil', 'velocity': (5, 0), 'condition': 'after_frames:60'}
        ]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Both should be applied
        mock_registry.create.assert_called_once()
        mock_preset_action.apply.assert_called_once()
        mock_move_until.assert_called_once()

    def test_apply_multiple_configs_continues_after_error(self, window, test_sprite, mocker):
        """Test that processing continues after an error in one config."""
        dev_viz = DevVisualizer()
        dev_viz.ctx = mocker.MagicMock()
        
        # First config will fail (invalid preset)
        mock_registry = mocker.MagicMock()
        mock_registry.create.side_effect = KeyError("Preset 'invalid' not found")
        mocker.patch('actions.dev.get_preset_registry', return_value=mock_registry)
        
        # Second config should still be processed
        mock_move_until = mocker.patch('actions.move_until')
        
        test_sprite._action_configs = [
            {'preset': 'invalid', 'params': {}},
            {'action_type': 'MoveUntil', 'velocity': (5, 0), 'condition': 'after_frames:60'}
        ]
        
        dev_viz.apply_metadata_actions(test_sprite)
        
        # Second action should still be applied
        mock_move_until.assert_called_once()
