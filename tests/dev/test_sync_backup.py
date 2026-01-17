"""Tests for backup handling in sync.py."""

import textwrap

from actions.dev import code_parser, sync


class TestBackupHandling:
    """Test backup file handling in sync functions."""

    def test_update_position_assignment_creates_backup(self, tmp_path):
        """Test update_position_assignment creates backup file."""
        p = tmp_path / "scene.py"
        p.write_text("sprite.center_x = 100\n")

        res = sync.update_position_assignment(p, "sprite", "center_x", "200")

        assert res.changed
        assert res.backup is not None
        assert res.backup.exists()
        assert res.backup.name == "scene.py.bak"

    def test_update_position_assignment_preserves_existing_backup(self, tmp_path):
        """Test update_position_assignment doesn't overwrite existing backup."""
        p = tmp_path / "scene.py"
        p.write_text("sprite.center_x = 100\n")

        # Create existing backup
        backup = tmp_path / "scene.py.bak"
        backup.write_text("original content\n")

        res = sync.update_position_assignment(p, "sprite", "center_x", "200")

        assert res.changed
        assert res.backup is not None
        # Backup should still contain original content (not overwritten)
        assert backup.read_text() == "original content\n"

    def test_update_arrange_call_creates_backup(self, tmp_path):
        """Test update_arrange_call creates backup file."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, start_x=100)
        """)
        )

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.update_arrange_call(p, call.lineno, "start_x", "200")

        assert res.changed
        assert res.backup is not None
        assert res.backup.exists()

    def test_update_arrange_call_preserves_existing_backup(self, tmp_path):
        """Test update_arrange_call doesn't overwrite existing backup."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, start_x=100)
        """)
        )

        backup = tmp_path / "scene.py.bak"
        backup.write_text("original backup\n")

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.update_arrange_call(p, call.lineno, "start_x", "200")

        assert res.changed
        assert backup.read_text() == "original backup\n"

    def test_update_arrange_cell_creates_backup(self, tmp_path):
        """Test update_arrange_cell creates backup file."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2)
        """)
        )

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.update_arrange_cell(p, call.lineno, 0, 1, 150, 200)

        assert res.changed
        assert res.backup is not None
        assert res.backup.exists()

    def test_update_arrange_cell_preserves_existing_backup(self, tmp_path):
        """Test update_arrange_cell doesn't overwrite existing backup."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2)
        """)
        )

        backup = tmp_path / "scene.py.bak"
        backup.write_text("original backup\n")

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.update_arrange_cell(p, call.lineno, 0, 1, 150, 200)

        assert res.changed
        assert backup.read_text() == "original backup\n"

    def test_delete_arrange_override_creates_backup(self, tmp_path):
        """Test delete_arrange_override creates backup file."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 0, 'x': 50, 'y': 50}])
        """)
        )

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.delete_arrange_override(p, call.lineno, 0, 0)

        assert res.changed
        assert res.backup is not None
        assert res.backup.exists()

    def test_delete_arrange_override_preserves_existing_backup(self, tmp_path):
        """Test delete_arrange_override doesn't overwrite existing backup."""
        p = tmp_path / "scene.py"
        p.write_text(
            textwrap.dedent("""
        from mylib import arrange_grid

        sprites = [s1, s2, s3]
        arrange_grid(sprites, rows=2, cols=2, overrides=[{'row': 0, 'col': 0, 'x': 50, 'y': 50}])
        """)
        )

        backup = tmp_path / "scene.py.bak"
        backup.write_text("original backup\n")

        assigns, arr = code_parser.parse_file(str(p))
        call = arr[0]

        res = sync.delete_arrange_override(p, call.lineno, 0, 0)

        assert res.changed
        assert backup.read_text() == "original backup\n"
