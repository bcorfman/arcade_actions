### 🔄 Project Awareness & Context
- **Always read `docs/api_usage_guide.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `docs/prd.md`.
- **Use `uv run`** whenever executing Python commands, including `uv run pytest` for unit/integration tests.
- This project uses uv for dependency management and virtual environment handling

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_env()** for environment variables.

### 🧪 Testing & Reliability
- **Consult `docs/testing_guide.md`** before writing tests to understand the project's testing style and methods.
- **Always create Pytest tests for new features** (functions, classes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `tests` folder** mirroring the main app structure.
- **Test coverage should be maintained at 80% or greater**

### 📎 Style & Conventions
- **Use Python 3.11** as the primary language.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```
- Never use Dataclasses unless you ask first.
- AVOID state flags (booleans like self.respawning, self.is_active); use action states and completion callbacks instead.

### 📚 Documentation & Explainability
- **Update `README.md` and `docs/api_usage_guide.md`** when new regular features are added, dependencies change, or setup steps are modified.
- **Update `docs/VISUALIZER_GUIDE.md` and `docs/devvisualizer`** when the DevVisualizer has its features added or modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- For any additions/changes to boundary interactions using MoveUntil, **consult `docs/boundary.md'**
- For any additions/changes to the debug logging system, **consult `docs/debug_logging.md'**
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to.
- Follow the workflow: PRD → API Guide → Testing Documentation → Implementation

The actions/ directory:
* Contains the main ArcadeActions system implementation
* Interfaces with Arcade 3.x functionality referenced in references/arcade/
* Works directly with arcade.Sprite and arcade.SpriteList - no custom sprite classes needed


