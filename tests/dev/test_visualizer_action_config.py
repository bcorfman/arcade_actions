"""Tests for DevVisualizer action config management.

Tests attach_preset_to_selected, update_action_config, and update_selected_action_config.
These tests document current behavior including hasattr/getattr patterns.
"""

from __future__ import annotations

import pytest
import arcade

from actions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase


class TestAttachPresetToSelected(ActionTestBase):
    """Test suite for attach_preset_to_selected method."""

    def test_attach_preset_creates_configs_if_missing(self, window, test_sprite):
        """Test that attach_preset_to_selected creates _action_configs if missing."""
        # Document current behavior: hasattr check creates attribute
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        assert not hasattr(test_sprite, '_action_configs')
        
        dev_viz.attach_preset_to_selected('preset1')
        
        # Verify attribute was created
        assert hasattr(test_sprite, '_action_configs')
        # Tag is only included when tag is not None
        assert test_sprite._action_configs == [{'preset': 'preset1', 'params': {}}]

    def test_attach_preset_with_existing_configs(self, window, test_sprite):
        """Test that attach_preset_to_selected appends to existing configs."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        # Set up existing configs
        test_sprite._action_configs = [{'preset': 'existing_preset', 'params': {'x': 1}}]
        
        dev_viz.attach_preset_to_selected('new_preset', params={'speed': 5})
        
        assert len(test_sprite._action_configs) == 2
        assert test_sprite._action_configs[0] == {'preset': 'existing_preset', 'params': {'x': 1}}
        # Tag is only included when tag is not None
        assert test_sprite._action_configs[1] == {'preset': 'new_preset', 'params': {'speed': 5}}

    def test_attach_preset_with_params(self, window, test_sprite):
        """Test that attach_preset_to_selected includes params."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        params = {'velocity': (5, 0), 'duration': 60}
        dev_viz.attach_preset_to_selected('preset1', params=params)
        
        assert test_sprite._action_configs[0]['preset'] == 'preset1'
        assert test_sprite._action_configs[0]['params'] == params
        # Verify params dict is copied (not shared reference)
        params['new_key'] = 'value'
        assert 'new_key' not in test_sprite._action_configs[0]['params']

    def test_attach_preset_with_tag(self, window, test_sprite):
        """Test that attach_preset_to_selected includes tag when provided."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        dev_viz.attach_preset_to_selected('preset1', tag='movement')
        
        assert test_sprite._action_configs[0]['tag'] == 'movement'

    def test_attach_preset_without_tag(self, window, test_sprite):
        """Test that attach_preset_to_selected does not include tag when not provided."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        dev_viz.attach_preset_to_selected('preset1')
        
        # Tag is only included when tag is not None
        assert 'tag' not in test_sprite._action_configs[0]

    def test_attach_preset_to_multiple_selected(self, window, test_sprite_list):
        """Test that attach_preset_to_selected applies to all selected sprites."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)
        
        # Select all sprites
        for sprite in test_sprite_list:
            dev_viz.selection_manager._selected.add(sprite)
        
        dev_viz.attach_preset_to_selected('preset1', params={'x': 10})
        
        # Verify all sprites got the config
        for sprite in test_sprite_list:
            assert hasattr(sprite, '_action_configs')
            # Tag is only included when tag is not None
            assert sprite._action_configs == [{'preset': 'preset1', 'params': {'x': 10}}]

    def test_attach_preset_with_empty_params(self, window, test_sprite):
        """Test that attach_preset_to_selected handles empty params dict."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        dev_viz.attach_preset_to_selected('preset1', params={})
        
        assert test_sprite._action_configs[0]['params'] == {}

    def test_attach_preset_with_none_params(self, window, test_sprite):
        """Test that attach_preset_to_selected handles None params (defaults to empty dict)."""
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        dev_viz.attach_preset_to_selected('preset1', params=None)
        
        assert test_sprite._action_configs[0]['params'] == {}


class TestUpdateActionConfig(ActionTestBase):
    """Test suite for update_action_config method."""

    def test_update_action_config_updates_dict(self, window, test_sprite):
        """Test that update_action_config updates the config dict."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [{'preset': 'preset1', 'params': {'x': 1}}]
        
        dev_viz.update_action_config(test_sprite, 0, velocity=(5, 0))
        
        assert test_sprite._action_configs[0]['velocity'] == (5, 0)
        assert test_sprite._action_configs[0]['preset'] == 'preset1'  # Unchanged

    def test_update_action_config_multiple_fields(self, window, test_sprite):
        """Test that update_action_config can update multiple fields."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [{'preset': 'preset1', 'params': {}}]
        
        dev_viz.update_action_config(test_sprite, 0, velocity=(5, 0), condition='after_frames:60', tag='movement')
        
        assert test_sprite._action_configs[0]['velocity'] == (5, 0)
        assert test_sprite._action_configs[0]['condition'] == 'after_frames:60'
        assert test_sprite._action_configs[0]['tag'] == 'movement'

    def test_update_action_config_raises_value_error_if_no_configs(self, window, test_sprite):
        """Test that update_action_config raises ValueError if sprite has no _action_configs."""
        # Document current behavior: hasattr check raises ValueError
        dev_viz = DevVisualizer()
        
        assert not hasattr(test_sprite, '_action_configs')
        
        with pytest.raises(ValueError, match="Sprite has no _action_configs"):
            dev_viz.update_action_config(test_sprite, 0, velocity=(5, 0))

    def test_update_action_config_raises_index_error_if_invalid_index(self, window, test_sprite):
        """Test that update_action_config raises IndexError for invalid config_index."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [{'preset': 'preset1'}]
        
        with pytest.raises(IndexError, match="config_index out of range"):
            dev_viz.update_action_config(test_sprite, 1, velocity=(5, 0))

    def test_update_action_config_raises_index_error_if_negative_index(self, window, test_sprite):
        """Test that update_action_config raises IndexError for negative config_index."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [{'preset': 'preset1'}]
        
        with pytest.raises(IndexError, match="config_index out of range"):
            dev_viz.update_action_config(test_sprite, -1, velocity=(5, 0))

    def test_update_action_config_overwrites_existing_fields(self, window, test_sprite):
        """Test that update_action_config overwrites existing fields."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [{'preset': 'preset1', 'velocity': (1, 0)}]
        
        dev_viz.update_action_config(test_sprite, 0, velocity=(5, 0))
        
        assert test_sprite._action_configs[0]['velocity'] == (5, 0)

    def test_update_action_config_with_multiple_configs(self, window, test_sprite):
        """Test that update_action_config only updates the specified config_index."""
        dev_viz = DevVisualizer()
        test_sprite._action_configs = [
            {'preset': 'preset1', 'params': {}},
            {'preset': 'preset2', 'params': {}}
        ]
        
        dev_viz.update_action_config(test_sprite, 1, tag='second')
        
        assert test_sprite._action_configs[0]['preset'] == 'preset1'
        assert 'tag' not in test_sprite._action_configs[0]
        assert test_sprite._action_configs[1]['tag'] == 'second'


class TestUpdateSelectedActionConfig(ActionTestBase):
    """Test suite for update_selected_action_config method."""

    def test_update_selected_action_config_updates_all_selected(self, window, test_sprite_list):
        """Test that update_selected_action_config updates all selected sprites."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)
        
        # Set up configs for all sprites
        for sprite in test_sprite_list:
            sprite._action_configs = [{'preset': 'preset1'}]
            dev_viz.selection_manager._selected.add(sprite)
        
        dev_viz.update_selected_action_config(0, velocity=(5, 0))
        
        # Verify all sprites were updated
        for sprite in test_sprite_list:
            assert sprite._action_configs[0]['velocity'] == (5, 0)

    def test_update_selected_action_config_handles_missing_configs(self, window, test_sprite):
        """Test that update_selected_action_config silently ignores sprites without configs."""
        # Document current behavior: Exception is caught and ignored per-sprite
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        assert not hasattr(test_sprite, '_action_configs')
        
        # Should not raise error, just silently ignore
        dev_viz.update_selected_action_config(0, velocity=(5, 0))
        
        # Sprite should still not have _action_configs
        assert not hasattr(test_sprite, '_action_configs')

    def test_update_selected_action_config_handles_invalid_index(self, window, test_sprite):
        """Test that update_selected_action_config silently ignores invalid config_index."""
        # Document current behavior: IndexError is caught and ignored per-sprite
        dev_viz = DevVisualizer()
        dev_viz.scene_sprites.append(test_sprite)
        dev_viz.selection_manager._selected.add(test_sprite)
        
        test_sprite._action_configs = [{'preset': 'preset1'}]  # Only index 0 exists
        
        # Should not raise error, just silently ignore
        dev_viz.update_selected_action_config(1, velocity=(5, 0))
        
        # Config should be unchanged
        assert 'velocity' not in test_sprite._action_configs[0]

    def test_update_selected_action_config_partial_success(self, window, test_sprite_list):
        """Test that update_selected_action_config updates valid sprites even if others fail."""
        dev_viz = DevVisualizer(scene_sprites=test_sprite_list)
        
        # Set up: first sprite has configs, second doesn't
        test_sprite_list[0]._action_configs = [{'preset': 'preset1'}]
        # test_sprite_list[1] has no _action_configs
        
        # Select both
        for sprite in test_sprite_list:
            dev_viz.selection_manager._selected.add(sprite)
        
        dev_viz.update_selected_action_config(0, velocity=(5, 0))
        
        # First sprite should be updated
        assert test_sprite_list[0]._action_configs[0]['velocity'] == (5, 0)
        # Second sprite should be unchanged (no error raised)
        assert not hasattr(test_sprite_list[1], '_action_configs')

    def test_update_selected_action_config_with_empty_selection(self, window):
        """Test that update_selected_action_config does nothing with empty selection."""
        dev_viz = DevVisualizer()
        
        # No sprites selected
        assert len(dev_viz.selection_manager.get_selected()) == 0
        
        # Should not raise error
        dev_viz.update_selected_action_config(0, velocity=(5, 0))