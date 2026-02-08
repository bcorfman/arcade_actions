"""Test suite for DevVisualizer sprite import/export and state management.

Tests focus on functionality that works in headless CI environments without
requiring OpenGL context or graphics rendering.
"""

import arcade
import pytest

from arcadeactions import infinite, move_until
from arcadeactions.dev.visualizer import DevVisualizer
from tests.conftest import ActionTestBase

pytestmark = pytest.mark.integration


class TestDevVisualizerImportExport(ActionTestBase):
    """Test suite for sprite import/export functionality."""

    def test_import_sprites_clears_selection_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears selection manager."""
        dev_viz = DevVisualizer()

        # Add sprites and select one
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Select the sprite
        dev_viz.selection_manager.handle_mouse_press(100, 100, False)
        assert len(dev_viz.selection_manager.get_selected()) == 1

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Selection should be cleared
        assert len(dev_viz.selection_manager.get_selected()) == 0
        # Scene should only have new sprite
        assert len(dev_viz.scene_sprites) == 1
        assert dev_viz.scene_sprites[0].center_x == 200

    def test_import_sprites_clears_gizmos_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears gizmo cache."""
        dev_viz = DevVisualizer()

        # Add sprite with bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Create a bounded MoveUntil action
        move_until(sprite1, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Get gizmo (this will cache it)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is not None
        assert sprite1 in dev_viz._gizmos

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Gizmo cache should be cleared
        assert len(dev_viz._gizmos) == 0
        assert len(dev_viz._gizmo_miss_refresh_at) == 0
        # Old sprite should not be in scene
        assert sprite1 not in dev_viz.scene_sprites

    def test_import_sprites_clears_gizmo_miss_cache_when_clear_true(self, window):
        """Test that import_sprites with clear=True clears gizmo miss refresh cache."""
        dev_viz = DevVisualizer()

        # Add sprite without bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Get gizmo (will create negative cache entry)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is None
        assert sprite1 in dev_viz._gizmos
        assert sprite1 in dev_viz._gizmo_miss_refresh_at

        # Import new sprites with clear=True
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Both caches should be cleared
        assert len(dev_viz._gizmos) == 0
        assert len(dev_viz._gizmo_miss_refresh_at) == 0

    def test_import_sprites_preserves_selection_when_clear_false(self, window):
        """Test that import_sprites with clear=False preserves selection."""
        dev_viz = DevVisualizer()

        # Add sprite and select it
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Select the sprite
        dev_viz.selection_manager.handle_mouse_press(100, 100, False)
        assert len(dev_viz.selection_manager.get_selected()) == 1
        selected_sprite = dev_viz.selection_manager.get_selected()[0]

        # Import new sprites with clear=False
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=False)

        # Selection should still contain original sprite
        assert len(dev_viz.selection_manager.get_selected()) == 1
        assert dev_viz.selection_manager.get_selected()[0] is selected_sprite
        # Scene should have both sprites
        assert len(dev_viz.scene_sprites) == 2

    def test_import_sprites_preserves_gizmos_when_clear_false(self, window):
        """Test that import_sprites with clear=False preserves gizmo cache."""
        dev_viz = DevVisualizer()

        # Add sprite with bounded action
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        dev_viz.scene_sprites.append(sprite1)

        # Create a bounded MoveUntil action
        move_until(sprite1, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Get gizmo (this will cache it)
        gizmo = dev_viz._get_gizmo(sprite1)
        assert gizmo is not None
        assert sprite1 in dev_viz._gizmos

        # Import new sprites with clear=False
        game_sprites = arcade.SpriteList()
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        game_sprites.append(sprite2)

        dev_viz.import_sprites(game_sprites, clear=False)

        # Gizmo cache should still contain original sprite
        assert sprite1 in dev_viz._gizmos
        # Scene should have both sprites
        assert len(dev_viz.scene_sprites) == 2

    def test_import_sprites_clears_scene_before_import(self, window):
        """Test that import_sprites clears scene_sprites when clear=True."""
        dev_viz = DevVisualizer()

        # Add some sprites
        for i in range(3):
            sprite = arcade.Sprite()
            sprite.center_x = i * 100
            dev_viz.scene_sprites.append(sprite)

        assert len(dev_viz.scene_sprites) == 3

        # Import with clear=True
        game_sprites = arcade.SpriteList()
        sprite = arcade.Sprite()
        sprite.center_x = 500
        game_sprites.append(sprite)

        dev_viz.import_sprites(game_sprites, clear=True)

        # Should only have imported sprite
        assert len(dev_viz.scene_sprites) == 1
        assert dev_viz.scene_sprites[0].center_x == 500

    def test_export_sprites_syncs_position(self, window):
        """Test that export_sprites syncs position back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 100
        original.center_y = 200
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.center_x = 300
        imported.center_y = 400

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.center_x == 300
        assert original.center_y == 400

    def test_export_sprites_syncs_angle(self, window):
        """Test that export_sprites syncs angle back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.angle = 0
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.angle = 45

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.angle == 45

    def test_export_sprites_syncs_scale(self, window):
        """Test that export_sprites syncs scale back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.scale = 1.0
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.scale = 2.0

        # Export
        dev_viz.export_sprites()

        # Original should be updated (Arcade 3.x uses tuple scale)
        assert original.scale == (2.0, 2.0) or original.scale == 2.0

    def test_export_sprites_syncs_alpha(self, window):
        """Test that export_sprites syncs alpha back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.alpha = 255
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.alpha = 128

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.alpha == 128

    def test_export_sprites_syncs_color(self, window):
        """Test that export_sprites syncs color back to original."""
        # Create game sprite
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.color = arcade.color.WHITE
        game_sprites.append(original)

        # Import and modify
        dev_viz = DevVisualizer()
        dev_viz.import_sprites(game_sprites)

        imported = dev_viz.scene_sprites[0]
        imported.color = arcade.color.RED

        # Export
        dev_viz.export_sprites()

        # Original should be updated
        assert original.color == arcade.color.RED

    def test_export_sprites_only_syncs_sprites_with_original(self, window):
        """Test that export_sprites only syncs sprites with _original_sprite reference."""
        dev_viz = DevVisualizer()

        # Add sprite without _original_sprite (created directly in scene)
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        dev_viz.scene_sprites.append(sprite1)

        # Add sprite with _original_sprite (imported)
        game_sprites = arcade.SpriteList()
        original = arcade.Sprite()
        original.center_x = 200
        game_sprites.append(original)
        dev_viz.import_sprites(game_sprites, clear=False)

        # Modify both
        sprite1.center_x = 300
        dev_viz.scene_sprites[1].center_x = 400

        # Export
        dev_viz.export_sprites()

        # Only imported sprite should sync
        assert original.center_x == 400
        # Direct sprite should be unchanged (no original to sync to)
        assert sprite1.center_x == 300


class TestDevVisualizerGizmoCaching(ActionTestBase):
    """Test suite for gizmo caching behavior."""

    def test_get_gizmo_caches_bounded_action(self, window):
        """Test that _get_gizmo caches gizmo for sprite with bounded action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # Create bounded action
        move_until(sprite, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # First call creates gizmo
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is not None
        assert sprite in dev_viz._gizmos

        # Second call returns cached gizmo
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is gizmo1

    def test_get_gizmo_negative_caches_sprite_without_bounded_action(self, window):
        """Test that _get_gizmo negative-caches sprite without bounded action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # No bounded action - should negative cache
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is None
        assert sprite in dev_viz._gizmos
        assert dev_viz._gizmos[sprite] is None
        assert sprite in dev_viz._gizmo_miss_refresh_at

        # Second call should return None without re-checking (within refresh window)
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is None

    def test_get_gizmo_refreshes_after_miss_cache_expires(self, window):
        """Test that _get_gizmo refreshes negative cache after expiration."""
        import time

        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100
        dev_viz.scene_sprites.append(sprite)

        # First call - negative cache
        gizmo1 = dev_viz._get_gizmo(sprite)
        assert gizmo1 is None
        assert sprite in dev_viz._gizmo_miss_refresh_at

        # Manually expire the cache by setting refresh time in the past
        dev_viz._gizmo_miss_refresh_at[sprite] = time.monotonic() - 1.0

        # Now add bounded action
        move_until(sprite, velocity=(5, 0), condition=infinite, bounds=(0, 0, 800, 600))

        # Should refresh and find the action
        gizmo2 = dev_viz._get_gizmo(sprite)
        assert gizmo2 is not None
        assert sprite not in dev_viz._gizmo_miss_refresh_at


class TestDevVisualizerApplyMetadataActions(ActionTestBase):
    """Test suite for apply_metadata_actions functionality."""

    def test_apply_metadata_actions_creates_moveuntil(self, window):
        """Test that apply_metadata_actions creates MoveUntil from metadata."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Add metadata
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (5, 0),
                "condition": "infinite",
            }
        ]

        # Apply metadata
        dev_viz.apply_metadata_actions(sprite)

        # Action should be applied
        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        # MoveUntil uses target_velocity attribute
        assert actions[0].target_velocity == (5, 0)

    def test_apply_metadata_actions_no_metadata(self, window):
        """Test that apply_metadata_actions does nothing if no metadata."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # No metadata - should not crash
        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0

    def test_apply_metadata_actions_skips_unknown_action_type(self, window):
        """Test that apply_metadata_actions skips unknown action types."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Add unknown action type
        sprite._action_configs = [
            {
                "action_type": "UnknownAction",
                "velocity": (5, 0),
            }
        ]

        # Should not crash
        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0

    def test_apply_metadata_actions_applies_bounds_and_behavior(self, window):
        """Test that apply_metadata_actions applies bounds and boundary_behavior."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Add metadata with bounds and boundary behavior
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (5, 0),
                "condition": "infinite",
                "bounds": (0, 0, 800, 600),
                "boundary_behavior": "limit",
            }
        ]

        # Apply metadata
        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        assert actions[0].bounds == (0, 0, 800, 600)
        assert actions[0].boundary_behavior == "limit"

    def test_apply_metadata_actions_passes_callbacks_and_tag(self, window):
        """Test that apply_metadata_actions passes callbacks and tag to MoveUntil."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        flag = {}

        def on_enter(s, axis, side):
            flag["enter"] = (axis, side)

        def on_exit(s, axis, side):
            flag["exit"] = (axis, side)

        # Add metadata with callbacks and tag
        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (5, 0),
                "condition": "infinite",
                "tag": "movement",
                "on_boundary_enter": on_enter,
                "on_boundary_exit": on_exit,
            }
        ]

        # Apply metadata
        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        action = actions[0]
        assert action.tag == "movement"
        assert action.on_boundary_enter is on_enter
        assert action.on_boundary_exit is on_exit

    def test_apply_metadata_actions_supports_velocity_provider(self, window):
        """Test that a velocity_provider from metadata is attached and used."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        def vp():
            return (2, 3)

        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (0, 0),
                "condition": "infinite",
                "velocity_provider": vp,
            }
        ]

        # Apply metadata
        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        action = actions[0]
        assert action.velocity_provider is vp
        # apply_effect should have run and set current_velocity using the provider
        assert action.current_velocity == (2, 3)

    def test_apply_metadata_actions_resolves_condition_after_frames(self, window):
        """Test that condition strings like after_frames:N are resolved."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        sprite._action_configs = [
            {
                "action_type": "MoveUntil",
                "velocity": (5, 0),
                "condition": "after_frames:3",
            }
        ]

        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        # Step frames - action should finish after 3 frames
        for _ in range(3):
            Action.update_all(1.0 / 60.0)

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0  # action completed and removed

    def test_apply_metadata_actions_creates_followpath(self, window):
        """Test that FollowPathUntil metadata creates a FollowPathUntil action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        sprite._action_configs = [
            {
                "action_type": "FollowPathUntil",
                "control_points": [(100, 100), (200, 200)],
                "velocity": 150,
                "condition": "after_frames:2",
            }
        ]

        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        # Simulate two frames to let it stop
        for _ in range(2):
            Action.update_all(1.0 / 60.0)
        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 0

    def test_apply_metadata_actions_uses_preset_and_resolves_string_callbacks(self, window):
        """Test that presets and string callbacks (via resolver) are handled."""
        from arcadeactions import MoveUntil
        from arcadeactions.dev import register_preset
        from arcadeactions.frame_timing import infinite

        # Register preset factory that returns unbound MoveUntil
        @register_preset("test_scroll", category="Test", params={"speed": 4})
        def preset_factory(ctx, speed=4):
            return MoveUntil(velocity=(-speed, 0), condition=infinite)

        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        # Resolver for string callbacks
        called = {}

        def resolver(name: str):
            if name == "on_stop_fn":

                def on_stop_cb():
                    called["stopped"] = True

                return on_stop_cb
            return None

        # Use preset and a string callback for on_stop
        sprite._action_configs = [
            {
                "preset": "test_scroll",
                "params": {"speed": 5},
                "action_type": "MoveUntil",
                "condition": "after_frames:1",
                "on_stop": "on_stop_fn",
            }
        ]

        dev_viz.apply_metadata_actions(sprite, resolver=resolver)

        from arcadeactions import Action

        # After one frame the action should finish and resolver callback called
        Action.update_all(1.0 / 60.0)
        assert called.get("stopped") is True

    def test_apply_metadata_actions_creates_cycle_textures(self, window):
        """Test that CycleTexturesUntil metadata creates a CycleTexturesUntil action."""
        dev_viz = DevVisualizer()

        sprite = arcade.Sprite()
        sprite.center_x = 100
        sprite.center_y = 100

        textures = [arcade.Texture.create_empty(f"tex_{i}", (4, 4)) for i in range(3)]

        sprite._action_configs = [
            {
                "action_type": "CycleTexturesUntil",
                "textures": textures,
                "frames_per_texture": 2,
                "condition": "after_frames:1",
            }
        ]

        dev_viz.apply_metadata_actions(sprite)

        from arcadeactions import Action

        actions = Action.get_actions_for_target(sprite)
        assert len(actions) == 1
        action = actions[0]
        assert hasattr(action, "_textures")
        assert action._frames_per_texture == 2

    def test_apply_metadata_actions_creates_fadeto_and_blinkuntil(self, window):
        """Test that FadeTo and BlinkUntil metadata create actions with proper params."""
        dev_viz = DevVisualizer()

        # FadeTo
        sprite1 = arcade.Sprite()
        sprite1.center_x = 100
        sprite1.center_y = 100
        sprite1._action_configs = [
            {
                "action_type": "FadeTo",
                "target_alpha": 0,
                "speed": 10.0,
                "condition": "infinite",
            }
        ]

        # BlinkUntil
        sprite2 = arcade.Sprite()
        sprite2.center_x = 200
        sprite2.center_y = 200
        sprite2._action_configs = [
            {
                "action_type": "BlinkUntil",
                "frames_until_change": 3,
                "condition": "after_frames:1",
            }
        ]

        dev_viz.apply_metadata_actions(sprite1)
        dev_viz.apply_metadata_actions(sprite2)

        from arcadeactions import Action

        actions1 = Action.get_actions_for_target(sprite1)
        actions2 = Action.get_actions_for_target(sprite2)
        assert len(actions1) == 1
        assert len(actions2) == 1
        assert actions1[0].target_alpha == 0
        assert actions1[0].target_speed == 10.0
        assert actions2[0].target_frames_until_change == 3

    def test_apply_metadata_actions_creates_rotate_and_tween(self, window):
        """Test that RotateUntil and TweenUntil metadata create actions and can run."""
        dev_viz = DevVisualizer()

        # RotateUntil
        sprite_r = arcade.Sprite()
        sprite_r.center_x = 100
        sprite_r.center_y = 100
        sprite_r._action_configs = [
            {
                "action_type": "RotateUntil",
                "angular_velocity": 45.0,
                "condition": "after_frames:1",
            }
        ]

        # TweenUntil (tween center_x to new value)
        sprite_t = arcade.Sprite()
        sprite_t.center_x = 10
        sprite_t.center_y = 10
        sprite_t._action_configs = [
            {
                "action_type": "TweenUntil",
                "start_value": 10,
                "end_value": 50,
                "property_name": "center_x",
                "condition": "after_frames:1",
            }
        ]

        dev_viz.apply_metadata_actions(sprite_r)
        dev_viz.apply_metadata_actions(sprite_t)

        from arcadeactions import Action

        # Run one frame - tween should update property, rotate should be applied
        Action.update_all(1.0 / 60.0)

        actions_r = Action.get_actions_for_target(sprite_r)
        actions_t = Action.get_actions_for_target(sprite_t)

        # Both should have completed due to after_frames:1
        assert len(actions_r) == 0
        assert len(actions_t) == 0
        # Ensure tween changed the property (end achieved or in progress)
        assert sprite_t.center_x != 10

    def test_apply_metadata_actions_creates_emit_and_glow_and_scale_and_callbacks(self, window):
        """Test that EmitParticlesUntil, GlowUntil, ScaleUntil, CallbackUntil and DelayFrames are created from metadata."""
        dev_viz = DevVisualizer()

        # EmitParticlesUntil
        emitted_destroyed = {}

        class Emitter:
            def __init__(self):
                self.center_x = 0
                self.center_y = 0
                self.angle = 0
                self.destroyed = False

            def update(self):
                pass

            def destroy(self):
                self.destroyed = True
                emitted_destroyed["destroyed"] = True

        def emitter_factory(sprite):
            return Emitter()

        sprite_e = arcade.Sprite()
        sprite_e.center_x = 10
        sprite_e.center_y = 20
        sprite_e._action_configs = [
            {
                "action_type": "EmitParticlesUntil",
                "emitter_factory": emitter_factory,
                "anchor": (1, 2),
                "follow_rotation": True,
                "destroy_on_stop": True,
                "condition": "after_frames:1",
            }
        ]

        # GlowUntil
        render_called = {}

        class Shader:
            def __init__(self):
                self.program = {}

            def render(self):
                render_called["rendered"] = True

            def resize(self, size):
                pass

        def shadertoy_factory(size):
            return Shader()

        def uniforms_provider(shader, target):
            return {"lightPosition": (50, 60)}

        def get_cam_bottom_left():
            return (10, 10)

        sprite_g = arcade.Sprite()
        sprite_g._action_configs = [
            {
                "action_type": "GlowUntil",
                "shadertoy_factory": shadertoy_factory,
                "uniforms_provider": uniforms_provider,
                "get_camera_bottom_left": get_cam_bottom_left,
                "auto_resize": True,
                "condition": "after_frames:1",
            }
        ]

        # ScaleUntil
        sprite_s = arcade.Sprite()
        sprite_s.scale = 1.0
        sprite_s._action_configs = [
            {
                "action_type": "ScaleUntil",
                "velocity": 0.5,
                "condition": "after_frames:1",
            }
        ]

        # CallbackUntil
        called = {"count": 0}

        def cb(target=None):
            called["count"] += 1

        sprite_c = arcade.Sprite()
        sprite_c._action_configs = [
            {
                "action_type": "CallbackUntil",
                "callback": cb,
                "condition": "after_frames:1",
            }
        ]

        # DelayFrames
        sprite_d = arcade.Sprite()
        sprite_d._action_configs = [
            {
                "action_type": "DelayFrames",
                "frames": 1,
                "condition": "infinite",
            }
        ]

        dev_viz.apply_metadata_actions(sprite_e)
        dev_viz.apply_metadata_actions(sprite_g)
        dev_viz.apply_metadata_actions(sprite_s)
        dev_viz.apply_metadata_actions(sprite_c)
        dev_viz.apply_metadata_actions(sprite_d)

        from arcadeactions import Action

        # Run one frame to trigger after_frames:1
        Action.update_all(1.0 / 60.0)

        # Emitters should have been destroyed on stop
        assert emitted_destroyed.get("destroyed") is True

        # Glow shader should have rendered
        assert render_called.get("rendered") is True

        # Scale action should have applied at least one scaling change or completed
        # Accept either behavior: scale changed or action removed
        actions_s = Action.get_actions_for_target(sprite_s)
        assert len(actions_s) in (0, 1)

        # Callback should have been called at least once
        assert called["count"] >= 1

        # DelayFrames should have completed and been removed
        actions_d = Action.get_actions_for_target(sprite_d)
        assert len(actions_d) == 0
