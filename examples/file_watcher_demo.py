"""
Demonstration of the FileWatcher service for hot-reload functionality.

This example shows how to use FileWatcher to monitor Python files and
trigger actions when they change, enabling hot-reload workflows.

Usage:
    uv run python examples/file_watcher_demo.py

Then edit any Python file in the current directory to see the watcher
detect the change.
"""

from pathlib import Path

from actions.dev import FileWatcher


def on_files_changed(changed_files: list[Path]) -> None:
    """Called when files change."""
    print("\n" + "=" * 60)
    print("📝 Files changed:")
    for file_path in changed_files:
        print(f"  - {file_path.name} ({file_path.parent})")
    print("=" * 60 + "\n")
    print("💡 In a real application, this would trigger:")
    print("   - Module reload (importlib.reload)")
    print("   - Game state preservation")
    print("   - Scene/sprite reconstruction")
    print("   - Resuming from saved state")
    print()


def main():
    """Run the file watcher demo."""
    # Watch the current directory for Python file changes
    current_dir = Path(__file__).parent

    print("🔍 FileWatcher Demo")
    print("=" * 60)
    print(f"Watching directory: {current_dir}")
    print("File patterns: *.py")
    print("Debounce time: 0.3 seconds")
    print()
    print("Try editing a Python file in this directory!")
    print("Press Ctrl+C to stop watching.")
    print("=" * 60 + "\n")

    # Create and start the watcher
    with FileWatcher(
        paths=[current_dir],
        callback=on_files_changed,
        patterns=["*.py"],
        debounce_seconds=0.3,
    ):
        # Keep running until user interrupts
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopping file watcher...")


if __name__ == "__main__":
    main()
