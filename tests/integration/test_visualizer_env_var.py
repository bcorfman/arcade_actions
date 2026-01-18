"""Integration test for visualizer environment variable auto-attach.

This test spawns a subprocess to verify environment variable handling,
which makes it slower than typical unit tests.
"""

import os
import subprocess
import sys
import textwrap


def test_visualizer_env_var_triggers_auto_attach():
    """Test that ARCADEACTIONS_VISUALIZER env var triggers visualizer auto-attach."""

    script = textwrap.dedent(
        """
        import os

        # The test harness injects this environment variable before import.
        assert os.environ.get("ARCADEACTIONS_VISUALIZER") == "1"

        # Import should succeed and auto-attach should run without raising.
        import arcadeactions  # noqa: F401
        from arcadeactions import visualizer  # noqa: F401
        """
    )

    env = os.environ.copy()
    env["ARCADEACTIONS_VISUALIZER"] = "1"

    completed = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"Auto-attach script failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )
