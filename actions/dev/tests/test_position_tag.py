import types

from actions.dev.position_tag import positioned, tag_sprite, get_sprites_for, remove_sprite_from_registry


class DummySprite:
    def __init__(self, name="d"):
        self.name = name


def test_decorator_tags_sprite_and_registers():
    @positioned("forcefield")
    def create():
        return DummySprite("ff")

    s = create()
    assert getattr(s, "_position_id") == "forcefield"
    sprites = get_sprites_for("forcefield")
    assert s in sprites


def test_manual_tagging_and_removal():
    s = DummySprite("x")
    tag_sprite(s, "manual")
    assert getattr(s, "_position_id") == "manual"
    assert s in get_sprites_for("manual")

    remove_sprite_from_registry(s)
    assert s not in get_sprites_for("manual")


def test_decorator_preserves_factory_metadata():
    @positioned("p1")
    def f():
        """docstring"""
        return DummySprite("a")

    assert hasattr(f, "__wrapped__")
    assert getattr(f, "__doc__") == "docstring"
    assert getattr(f, "_positioned_id") == "p1"
