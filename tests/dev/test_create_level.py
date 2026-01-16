"""Tests for actions.dev.create_level module."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from actions.dev import create_level


class TestDeriveTitleFromFilename:
    """Test _derive_title_from_filename function."""

    def test_simple_filename(self):
        """Test simple filename conversion."""
        assert create_level._derive_title_from_filename("my_level.py") == "My Level"

    def test_underscores(self):
        """Test filename with underscores."""
        assert create_level._derive_title_from_filename("boss_fight.py") == "Boss Fight"

    def test_hyphens(self):
        """Test filename with hyphens."""
        assert create_level._derive_title_from_filename("level-1.py") == "Level 1"

    def test_mixed_separators(self):
        """Test filename with mixed separators."""
        assert create_level._derive_title_from_filename("my_level-1.py") == "My Level 1"

    def test_numbers(self):
        """Test filename with numbers."""
        assert create_level._derive_title_from_filename("level_1.py") == "Level 1"

    def test_single_word(self):
        """Test single word filename."""
        assert create_level._derive_title_from_filename("test.py") == "Test"

    def test_nested_path(self):
        """Test filename with path."""
        assert create_level._derive_title_from_filename("levels/my_level.py") == "My Level"


class TestDeriveExportNameFromFilename:
    """Test _derive_export_name_from_filename function."""

    def test_simple_filename(self):
        """Test simple filename."""
        assert create_level._derive_export_name_from_filename("my_level.py") == "my_level"

    def test_with_path(self):
        """Test filename with path."""
        assert create_level._derive_export_name_from_filename("levels/boss_fight.py") == "boss_fight"

    def test_with_numbers(self):
        """Test filename with numbers."""
        assert create_level._derive_export_name_from_filename("level_1.py") == "level_1"


class TestValidateFilename:
    """Test _validate_filename function."""

    def test_empty_filename(self):
        """Test empty filename."""
        is_valid, error_msg = create_level._validate_filename("")
        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_no_py_extension(self):
        """Test filename without .py extension."""
        is_valid, error_msg = create_level._validate_filename("my_level")
        assert is_valid is False
        assert ".py" in error_msg.lower()

    def test_valid_filename(self):
        """Test valid filename."""
        is_valid, error_msg = create_level._validate_filename("my_level.py")
        assert is_valid is True
        assert error_msg is None

    def test_invalid_characters(self):
        """Test filename with invalid characters."""
        is_valid, error_msg = create_level._validate_filename("my<level>.py")
        assert is_valid is False
        assert "invalid" in error_msg.lower()

    def test_path_separator_allowed(self):
        """Test that path separators are allowed for relative paths."""
        is_valid, error_msg = create_level._validate_filename("levels/my_level.py")
        assert is_valid is True
        assert error_msg is None

    def test_absolute_path(self):
        """Test absolute path."""
        is_valid, error_msg = create_level._validate_filename("/tmp/my_level.py")
        assert is_valid is True
        assert error_msg is None


class TestGenerateLevelFile:
    """Test generate_level_file function."""

    def test_generate_file_creates_file(self, tmp_path):
        """Test that generate_level_file creates the file."""
        filename = tmp_path / "test_level.py"
        result = create_level.generate_level_file(str(filename))

        assert Path(result).exists()
        assert Path(result) == filename.resolve()

    def test_generate_file_creates_directory(self, tmp_path):
        """Test that generate_level_file creates parent directories."""
        filename = tmp_path / "nested" / "dir" / "test_level.py"
        result = create_level.generate_level_file(str(filename))

        assert filename.parent.exists()
        assert Path(result).exists()

    def test_generate_file_content(self, tmp_path):
        """Test that generated file has correct content."""
        filename = tmp_path / "my_level.py"
        result = create_level.generate_level_file(str(filename))

        content = Path(result).read_text(encoding="utf-8")
        assert "My Level" in content
        assert "my_level" in content
        assert "SceneEditorView" in content
        assert "register_prototype" in content

    def test_generate_file_invalid_filename(self):
        """Test that generate_level_file raises ValueError for invalid filename."""
        with pytest.raises(ValueError, match=".py extension"):
            create_level.generate_level_file("invalid")

    def test_generate_file_overwrites_existing(self, tmp_path):
        """Test that generate_level_file overwrites existing file."""
        filename = tmp_path / "test_level.py"
        filename.write_text("old content")

        result = create_level.generate_level_file(str(filename))
        content = Path(result).read_text(encoding="utf-8")

        assert "SceneEditorView" in content
        assert "old content" not in content


class TestRunLevelFile:
    """Test run_level_file function."""

    def test_run_level_file_executes_subprocess(self, tmp_path, mocker):
        """Test that run_level_file calls subprocess.run correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")

        mock_run = mocker.patch("actions.dev.create_level.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0)

        create_level.run_level_file(str(test_file))

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["uv", "run", "python", str(test_file.resolve())]
        assert call_args[1]["check"] is True
        assert call_args[1]["env"]["ARCADEACTIONS_DEVVIZ"] == "1"

    def test_run_level_file_file_not_found(self, tmp_path):
        """Test that run_level_file raises FileNotFoundError for missing file."""
        missing_file = tmp_path / "missing.py"

        with pytest.raises(FileNotFoundError):
            create_level.run_level_file(str(missing_file))

    def test_run_level_file_subprocess_error(self, tmp_path, mocker):
        """Test that run_level_file raises CalledProcessError on subprocess failure."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")

        mock_run = mocker.patch("actions.dev.create_level.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "uv")

        with pytest.raises(subprocess.CalledProcessError):
            create_level.run_level_file(str(test_file))

    def test_run_level_file_uv_not_found(self, tmp_path, mocker):
        """Test that run_level_file raises FileNotFoundError when uv is not found."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")

        mock_run = mocker.patch("actions.dev.create_level.subprocess.run")
        mock_run.side_effect = FileNotFoundError("uv not found")

        with pytest.raises(FileNotFoundError):
            create_level.run_level_file(str(test_file))


class TestMain:
    """Test main() function."""

    def test_main_with_filename_argument(self, tmp_path, mocker, capsys):
        """Test main() with filename argument."""
        filename = tmp_path / "test_level.py"

        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.return_value = str(filename.resolve())

        mock_run = mocker.patch("actions.dev.create_level.run_level_file")

        with patch("sys.argv", ["create_level", str(filename)]):
            try:
                create_level.main()
            except SystemExit:
                pass

        mock_generate.assert_called_once_with(str(filename))
        mock_run.assert_called_once()

    def test_main_interactive_mode(self, tmp_path, mocker, capsys):
        """Test main() in interactive mode."""
        filename = tmp_path / "interactive_level.py"

        mock_input = mocker.patch("builtins.input", return_value=str(filename))
        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.return_value = str(filename.resolve())

        mock_run = mocker.patch("actions.dev.create_level.run_level_file")

        with patch("sys.argv", ["create_level"]):
            try:
                create_level.main()
            except SystemExit:
                pass

        mock_input.assert_called_once()
        mock_generate.assert_called_once()
        mock_run.assert_called_once()

    def test_main_interactive_mode_empty_input(self, mocker, capsys):
        """Test main() in interactive mode with empty input."""
        mock_input = mocker.patch("builtins.input", return_value="")

        with patch("sys.argv", ["create_level"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 1

    def test_main_invalid_filename(self, mocker, capsys):
        """Test main() with invalid filename."""
        mock_input = mocker.patch("builtins.input", return_value="invalid")

        with patch("sys.argv", ["create_level"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 1

    def test_main_file_exists_overwrite(self, tmp_path, mocker):
        """Test main() when file exists and user confirms overwrite."""
        filename = tmp_path / "existing.py"
        filename.write_text("existing content")

        mock_input = mocker.patch("builtins.input", side_effect=["y"])
        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.return_value = str(filename.resolve())

        mock_run = mocker.patch("actions.dev.create_level.run_level_file")

        with patch("sys.argv", ["create_level", str(filename)]):
            try:
                create_level.main()
            except SystemExit:
                pass

        mock_generate.assert_called_once()
        mock_run.assert_called_once()

    def test_main_file_exists_cancel(self, tmp_path, mocker):
        """Test main() when file exists and user cancels."""
        filename = tmp_path / "existing.py"
        filename.write_text("existing content")

        mock_input = mocker.patch("builtins.input", return_value="n")

        with patch("sys.argv", ["create_level", str(filename)]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 0

    def test_main_keyboard_interrupt(self, mocker):
        """Test main() handles KeyboardInterrupt."""
        mock_input = mocker.patch("builtins.input", side_effect=KeyboardInterrupt())

        with patch("sys.argv", ["create_level"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 130

    def test_main_value_error(self, mocker):
        """Test main() handles ValueError."""
        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.side_effect = ValueError("Invalid filename")

        with patch("sys.argv", ["create_level", "invalid"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 1

    def test_main_file_not_found_error(self, mocker):
        """Test main() handles FileNotFoundError."""
        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.return_value = "/fake/path.py"

        mock_run = mocker.patch("actions.dev.create_level.run_level_file")
        mock_run.side_effect = FileNotFoundError("File not found")

        with patch("sys.argv", ["create_level", "test.py"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 1

    def test_main_unexpected_error(self, mocker):
        """Test main() handles unexpected errors."""
        mock_generate = mocker.patch("actions.dev.create_level.generate_level_file")
        mock_generate.side_effect = RuntimeError("Unexpected error")

        with patch("sys.argv", ["create_level", "test.py"]):
            with pytest.raises(SystemExit) as exc_info:
                create_level.main()

        assert exc_info.value.code == 1
