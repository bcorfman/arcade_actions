Scope: unit/integration tests for arcadeactions.

Testing:
- Follow `docs/testing_guide.md` for fixtures and patterns.
- Use arcade.Sprite/arcade.SpriteList fixtures with `action.apply()` and `Action.update_all()`.
- Include boundary behavior coverage where relevant.
- Keep unit tests fast; mark long-running tests as integration (window/OpenGL) or `slow` (non-window) so they only run on request or in GitHub Actions CI for Linux Python 3.11.
