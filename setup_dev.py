#!/usr/bin/env python3
"""
Development Setup Script for ArcadeActions

This script helps developers get started with the ArcadeActions library development.
It checks dependencies, runs tests, and provides helpful information.
"""

import os
import subprocess
import sys


def run_command(command, description=""):
    """Run a command and return True if successful."""
    print(f"\n{'='*50}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {command}")
    print("=" * 50)

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False, text=True)
        print(f"✅ Success: {description or command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description or command}")
        print(f"Error: {e}")
        return False


def check_uv_installation():
    """Check if uv is installed."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ uv is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not installed or not in PATH")
        print("Please install uv from: https://docs.astral.sh/uv/")
        return False


def main():
    """Main setup function."""
    print("🚀 ArcadeActions Development Setup")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found!")
        print("Please run this script from the arcade_actions root directory.")
        sys.exit(1)

    # Check uv installation
    if not check_uv_installation():
        sys.exit(1)

    # Setup development environment
    steps = [
        ("uv sync --dev", "Installing dependencies"),
        ("uv run pytest", "Running tests"),
        ("uv run python -c \"import actions; print('✅ Package imports successfully')\"", "Testing package import"),
    ]

    success_count = 0
    for command, description in steps:
        if run_command(command, description):
            success_count += 1
        else:
            print(f"\n❌ Setup step failed: {description}")
            break

    print(f"\n{'='*50}")
    print("📋 Setup Summary")
    print("=" * 50)
    print(f"Completed: {success_count}/{len(steps)} steps")

    if success_count == len(steps):
        print("🎉 Setup completed successfully!")
        print("\n📚 Next steps:")
        print("   • Run demo: uv run python demo.py")
        print("   • Run example: uv run python examples/basic_usage.py")
        print("   • Run tests: uv run pytest")
        print("   • Build package: uv run python -m build --no-isolation")
        print("   • View docs: Check the docs/ directory")
    else:
        print("⚠️  Setup incomplete. Please fix the errors above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
