import types

import pytest

from actions import Action
from actions.conditional import duration


class FakeEmitter:
    def __init__(self):
        self.center_x = 0.0
        self.center_y = 0.0
        self.angle = 0.0
        self.update_calls = 0
        self.destroy_calls = 0

    def update(self):
        self.update_calls += 1

    def destroy(self):
        self.destroy_calls += 1


def make_emitter_factory():
    def factory(_sprite):
        return FakeEmitter()

    return factory


class TestEmitParticlesUntil:
    def teardown_method(self):
        Action.stop_all()

    def test_emitter_per_sprite_center_anchor_and_rotation(self, test_sprite_list):
        from actions.conditional import EmitParticlesUntil

        # Assign distinct angles for follow_rotation verification
        for i, s in enumerate(test_sprite_list):
            s.angle = 10 * (i + 1)

        # Apply action with follow_rotation
        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.05),
            anchor="center",
            follow_rotation=True,
        )
        action.apply(test_sprite_list)

        # Drive updates
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Validate emitters exist for each sprite and follow position/angle
        assert hasattr(action, "_emitters") and len(action._emitters) == len(test_sprite_list)

        for sprite in test_sprite_list:
            emitter = action._emitters[id(sprite)]
            assert pytest.approx(emitter.center_x) == sprite.center_x
            assert pytest.approx(emitter.center_y) == sprite.center_y
            assert pytest.approx(emitter.angle) == sprite.angle
            assert emitter.update_calls >= 1

        # After completion, emitters should be destroyed
        Action.update_all(0.06)
        for sprite in test_sprite_list:
            emitter = action._emitters_snapshot[id(sprite)]
            assert emitter.destroy_calls == 1
        assert action.done

    def test_custom_anchor_offset_tuple(self, test_sprite):
        from actions.conditional import EmitParticlesUntil

        test_sprite.center_x = 200
        test_sprite.center_y = 300

        offset = (5.0, -3.0)
        action = EmitParticlesUntil(
            emitter_factory=make_emitter_factory(),
            condition=duration(0.02),
            anchor=offset,
            follow_rotation=False,
        )
        action.apply(test_sprite)

        Action.update_all(0.016)

        emitter = next(iter(action._emitters.values()))
        assert pytest.approx(emitter.center_x) == test_sprite.center_x + offset[0]
        assert pytest.approx(emitter.center_y) == test_sprite.center_y + offset[1]
