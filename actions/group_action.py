import arcade

from actions.base import Action


class GroupAction:
    """A high-level controller for running a shared Action over a group of sprites."""

    def __init__(self, group: arcade.SpriteList | list, action: Action):
        self.group = list(group)
        self.template = action
        self.active = None  # will hold the cloned group-wide action

    def start(self):
        self.active = self.template.clone()
        self.active.start(self.group)

    def step(self, delta_time: float):
        if self.active and not self.active.is_done():
            self.active.step(delta_time)

    def stop(self):
        if self.active:
            self.active.stop()
            self.active = None

    def reset(self):
        if self.active:
            self.active.stop()
        self.start()

    def is_done(self) -> bool:
        return self.active.is_done() if self.active else True

    def replace(self, new_action: Action):
        """Replace the current group action with a new one (auto-started)."""
        self.stop()
        self.template = new_action
        self.start()


class SpriteGroup:
    def __init__(self, sprites=None):
        self.sprites = sprites if sprites is not None else []

    def append(self, sprite):
        self.sprites.append(sprite)

    def extend(self, sprite_list):
        self.sprites.extend(sprite_list)

    def update(self, delta_time: float):
        for sprite in self.sprites:
            sprite.update(delta_time)

    def __iter__(self):
        return iter(self.sprites)

    def __getitem__(self, index):
        return self.sprites[index]

    def __len__(self):
        return len(self.sprites)

    def center(self):
        if not self.sprites:
            return (0, 0)
        avg_x = sum(sprite.center_x for sprite in self.sprites) / len(self.sprites)
        avg_y = sum(sprite.center_y for sprite in self.sprites) / len(self.sprites)
        return avg_x, avg_y

    def do(self, action):
        group_action = GroupAction(self.sprites, action)
        group_action.start()
        return group_action

    def clear_actions(self):
        for sprite in self.sprites:
            if hasattr(sprite, "clear_actions"):
                sprite.clear_actions()

    def breakaway(self, breakaway_sprites):
        """Remove given sprites and return a new SpriteGroup."""
        for sprite in breakaway_sprites:
            self.sprites.remove(sprite)
        return SpriteGroup(breakaway_sprites)
