import types

import pytest

from actions import Action
from actions.conditional import duration


class FakeShadertoy:
    """Minimal stand-in for arcade.experimental.Shadertoy.

    Exposes a dict-like `program` for uniforms, resize() and render().
    """

    def __init__(self, size=(800, 600)):
        self.size = size
        self.program = {}
        self.resize_calls = []
        self.render_calls = 0

    def resize(self, size):
        self.size = size
        self.resize_calls.append(size)

    def render(self):
        self.render_calls += 1


def make_shadertoy_factory(fake: "FakeShadertoy"):
    def factory(initial_size):
        # size is provided by the action; we ignore and reuse the fake
        return fake

    return factory


class TestGlowUntil:
    def teardown_method(self):
        Action.stop_all()

    def test_glow_renders_and_sets_uniforms_with_camera_correction(self):
        from actions.conditional import GlowUntil

        # Arrange fakes
        fake = FakeShadertoy()

        # Uniforms provider returns world-space lightPosition that should be camera-corrected to screen-space
        def uniforms_provider(_shadertoy, _target):
            return {"lightPosition": (100.0, 50.0), "lightSize": 300.0}

        # Camera reports bottom-left offset in world space
        def get_camera_bottom_left():
            return (10.0, 5.0)

        action = GlowUntil(
            shadertoy_factory=make_shadertoy_factory(fake),
            condition=duration(0.05),
            uniforms_provider=uniforms_provider,
            get_camera_bottom_left=get_camera_bottom_left,
        )

        # Act: apply and run a couple of frames
        dummy_target = types.SimpleNamespace()
        action.apply(dummy_target)
        Action.update_all(0.016)
        Action.update_all(0.016)

        # Assert: render called, uniforms set with camera correction
        assert fake.render_calls >= 1
        assert fake.program["lightPosition"] == (90.0, 45.0)
        assert fake.program["lightSize"] == 300.0

        # After duration passes, action completes and stops rendering
        Action.update_all(0.05)
        render_calls_after = fake.render_calls
        Action.update_all(0.016)
        assert fake.render_calls == render_calls_after  # No new renders
        assert action.done

    def test_glow_resize(self):
        from actions.conditional import GlowUntil

        fake = FakeShadertoy()
        action = GlowUntil(
            shadertoy_factory=make_shadertoy_factory(fake),
            condition=duration(0.1),
            auto_resize=True,
        )

        action.apply(types.SimpleNamespace())
        # Simulate window resize
        action.on_resize(123, 456)
        assert fake.resize_calls and fake.resize_calls[-1] == (123, 456)
