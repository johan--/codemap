"""Tests for the file watcher module."""

import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Skip all tests if watchdog is not available
try:
    from codemap.core.watcher import (
        CodeMapWatcher,
        CodemapEventHandler,
        watch_directory,
        WATCHDOG_AVAILABLE,
    )
except ImportError:
    WATCHDOG_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not WATCHDOG_AVAILABLE,
    reason="watchdog not installed"
)


class TestCodemapEventHandler:
    """Tests for CodemapEventHandler class."""

    @pytest.fixture
    def sample_project(self, tmp_path: Path):
        """Create a sample project with codemap."""
        from codemap.core.indexer import Indexer

        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        indexer = Indexer(root=tmp_path)
        indexer.index_all()
        return tmp_path

    @pytest.fixture
    def handler(self, sample_project):
        """Create a handler for testing."""
        from codemap.utils.config import load_config

        config = load_config(sample_project)
        changes = []

        def on_change(filepath, event_type):
            changes.append((filepath, event_type))

        handler = CodemapEventHandler(
            root=sample_project,
            config=config,
            on_change=on_change,
            debounce_seconds=0.1,
        )
        handler._changes = changes
        return handler

    def test_should_process_python_file(self, handler, sample_project):
        assert handler._should_process(str(sample_project / "test.py"))

    def test_should_not_process_text_file(self, handler, sample_project):
        assert not handler._should_process(str(sample_project / "readme.txt"))

    def test_should_not_process_excluded_path(self, handler, sample_project):
        assert not handler._should_process(str(sample_project / "node_modules" / "lib.py"))
        assert not handler._should_process(str(sample_project / "__pycache__" / "cache.py"))

    def test_should_not_process_directory(self, handler, sample_project):
        (sample_project / "subdir").mkdir()
        assert not handler._should_process(str(sample_project / "subdir"))

    def test_should_not_process_codemap_directory(self, handler, sample_project):
        """Should not process files in .codemap directory."""
        assert not handler._should_process(str(sample_project / ".codemap" / ".codemap.json"))
        assert not handler._should_process(str(sample_project / ".codemap" / "src" / ".codemap.json"))

    def test_debounce_multiple_changes(self, handler, sample_project):
        """Multiple rapid changes should be debounced into one."""
        # Trigger multiple changes rapidly
        filepath = sample_project / "test.py"
        for _ in range(5):
            handler._schedule_change(filepath, "modified")

        # Wait for debounce
        time.sleep(0.2)

        # Should only have one change recorded
        assert len(handler._changes) == 1
        assert handler._changes[0][1] == "modified"


class TestCodeMapWatcher:
    """Tests for CodeMapWatcher class."""

    @pytest.fixture
    def sample_project(self, tmp_path: Path):
        """Create a sample project with codemap."""
        from codemap.core.indexer import Indexer

        (tmp_path / "main.py").write_text("def main(): pass")

        indexer = Indexer(root=tmp_path)
        indexer.index_all()
        return tmp_path

    def test_init_requires_existing_codemap(self, tmp_path):
        """Should raise error if no codemap exists."""
        with pytest.raises(FileNotFoundError):
            CodeMapWatcher(root=tmp_path)

    def test_start_stop(self, sample_project):
        """Should start and stop cleanly."""
        watcher = CodeMapWatcher(root=sample_project)

        assert not watcher.is_running
        watcher.start()
        assert watcher.is_running
        watcher.stop()
        assert not watcher.is_running

    def test_context_manager(self, sample_project):
        """Should work as context manager."""
        with CodeMapWatcher(root=sample_project) as watcher:
            assert watcher.is_running
        assert not watcher.is_running

    def test_detects_file_modification(self, sample_project):
        """Should detect and process file modifications."""
        updates = []

        def on_update(filepath, symbols_changed):
            updates.append((filepath, symbols_changed))

        watcher = CodeMapWatcher(
            root=sample_project,
            on_update=on_update,
            debounce_seconds=0.1,
        )

        watcher.start()
        try:
            # Modify a file
            (sample_project / "main.py").write_text("def main(): pass\ndef new_func(): pass")

            # Wait for detection and processing
            time.sleep(0.5)

            # Should have detected the change
            assert len(updates) >= 1
            assert updates[-1][0] == "main.py"

        finally:
            watcher.stop()

    def test_detects_file_creation(self, sample_project):
        """Should detect new file creation."""
        updates = []

        def on_update(filepath, symbols_changed):
            updates.append((filepath, symbols_changed))

        watcher = CodeMapWatcher(
            root=sample_project,
            on_update=on_update,
            debounce_seconds=0.1,
        )

        watcher.start()
        try:
            # Create a new file
            (sample_project / "new_module.py").write_text("class NewClass: pass")

            # Wait for detection
            time.sleep(0.5)

            assert len(updates) >= 1
            assert any("new_module.py" in u[0] for u in updates)

        finally:
            watcher.stop()

    def test_detects_file_deletion(self, sample_project):
        """Should detect file deletion."""
        updates = []

        def on_update(filepath, symbols_changed):
            updates.append((filepath, symbols_changed))

        watcher = CodeMapWatcher(
            root=sample_project,
            on_update=on_update,
            debounce_seconds=0.1,
        )

        watcher.start()
        try:
            # Delete a file
            (sample_project / "main.py").unlink()

            # Wait for detection
            time.sleep(0.5)

            assert len(updates) >= 1

        finally:
            watcher.stop()

    def test_ignores_non_code_files(self, sample_project):
        """Should ignore non-code files."""
        updates = []

        def on_update(filepath, symbols_changed):
            updates.append((filepath, symbols_changed))

        watcher = CodeMapWatcher(
            root=sample_project,
            on_update=on_update,
            debounce_seconds=0.1,
        )

        watcher.start()
        try:
            # Wait for watcher to stabilize
            time.sleep(0.2)
            updates.clear()  # Clear any startup events

            # Create non-code files
            (sample_project / "readme.txt").write_text("Hello")
            (sample_project / "data.json").write_text("{}")

            # Wait
            time.sleep(0.3)

            # Should not have any updates for non-code files
            non_code_updates = [u for u in updates if u[0].endswith((".txt", ".json"))]
            assert len(non_code_updates) == 0

        finally:
            watcher.stop()

    def test_ignores_codemap_directory(self, sample_project):
        """Should ignore changes in .codemap directory."""
        updates = []

        def on_update(filepath, symbols_changed):
            updates.append((filepath, symbols_changed))

        watcher = CodeMapWatcher(
            root=sample_project,
            on_update=on_update,
            debounce_seconds=0.1,
        )

        watcher.start()
        try:
            # Wait for watcher to stabilize
            time.sleep(0.2)
            updates.clear()

            # Modify a codemap file directly (simulating external change)
            codemap_file = sample_project / ".codemap" / ".codemap.json"
            if codemap_file.exists():
                content = codemap_file.read_text()
                codemap_file.write_text(content + "\n")

            # Wait
            time.sleep(0.3)

            # Should not have any updates for codemap files
            codemap_updates = [u for u in updates if ".codemap" in u[0]]
            assert len(codemap_updates) == 0

        finally:
            watcher.stop()

    def test_error_callback(self, sample_project):
        """Should call error callback on processing errors."""
        errors = []

        def on_error(filepath, error):
            errors.append((filepath, error))

        # Mock the indexer to raise an error
        watcher = CodeMapWatcher(
            root=sample_project,
            on_error=on_error,
            debounce_seconds=0.1,
        )

        # Force an error by making update_file fail
        original_update = watcher.indexer.update_file

        def failing_update(filepath):
            raise RuntimeError("Test error")

        watcher.indexer.update_file = failing_update

        watcher.start()
        try:
            (sample_project / "main.py").write_text("def modified(): pass")
            time.sleep(0.5)

            # Should have recorded an error
            assert len(errors) >= 1

        finally:
            watcher.stop()
            watcher.indexer.update_file = original_update


class TestWatchDirectory:
    """Tests for watch_directory convenience function."""

    @pytest.fixture
    def sample_project(self, tmp_path: Path):
        """Create a sample project with codemap."""
        from codemap.core.indexer import Indexer

        (tmp_path / "main.py").write_text("def main(): pass")

        indexer = Indexer(root=tmp_path)
        indexer.index_all()
        return tmp_path

    def test_creates_running_watcher(self, sample_project):
        """Should create and start a watcher."""
        watcher = watch_directory(sample_project)
        try:
            assert watcher.is_running
        finally:
            watcher.stop()
