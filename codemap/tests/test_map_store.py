"""Tests for the map store module."""

import json
import pytest
from pathlib import Path

from codemap.core.map_store import MapStore, RootManifest, DirectoryMap, FileEntry
from codemap.parsers.base import Symbol


class TestMapStore:
    """Tests for MapStore class."""

    def test_save_and_load(self, tmp_path: Path):
        store = MapStore(tmp_path)

        # Add some data
        store.set_metadata(str(tmp_path), {"languages": ["python"]})
        store.update_file(
            rel_path="test.py",
            hash="abc123def456",
            language="python",
            lines=10,
            symbols=[
                Symbol(name="func", type="function", lines=(1, 5))
            ],
        )
        store.update_stats()
        store.save()

        # Load and verify
        loaded = MapStore.load(tmp_path)
        assert loaded.manifest.root == str(tmp_path)
        entry = loaded.get_file("test.py")
        assert entry is not None
        assert entry.hash == "abc123def456"

    def test_update_file(self, tmp_path: Path):
        store = MapStore(tmp_path)

        symbols = [
            Symbol(name="MyClass", type="class", lines=(1, 20), children=[
                Symbol(name="method", type="method", lines=(5, 10))
            ])
        ]

        store.update_file(
            rel_path="module.py",
            hash="hash123",
            language="python",
            lines=20,
            symbols=symbols,
        )

        entry = store.get_file("module.py")
        assert entry is not None
        assert entry.hash == "hash123"
        assert len(entry.symbols) == 1
        assert entry.symbols[0].name == "MyClass"

    def test_update_file_in_subdirectory(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file(
            rel_path="src/components/Button.py",
            hash="hash456",
            language="python",
            lines=50,
            symbols=[Symbol(name="Button", type="class", lines=(1, 50))],
        )
        store.save()

        # Verify directory structure is created
        codemap_dir = tmp_path / ".codemap"
        assert codemap_dir.exists()
        assert (codemap_dir / "src" / "components" / ".codemap.json").exists()

        # Verify we can load the file
        loaded = MapStore.load(tmp_path)
        entry = loaded.get_file("src/components/Button.py")
        assert entry is not None
        assert entry.hash == "hash456"

    def test_remove_file(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file("test.py", "hash", "python", 10, [])

        assert store.remove_file("test.py")
        assert store.get_file("test.py") is None
        assert not store.remove_file("nonexistent.py")

    def test_remove_file_from_subdirectory(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file("src/test.py", "hash", "python", 10, [])
        store.save()

        # Verify directory is tracked
        assert "src" in store.manifest.directories

        # Remove the file
        assert store.remove_file("src/test.py")
        store.save()

        # Directory should be removed from tracking since it's empty
        assert "src" not in store.manifest.directories

    def test_find_symbol_by_name(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file(
            "module.py",
            "hash",
            "python",
            50,
            [
                Symbol(name="UserService", type="class", lines=(1, 30), children=[
                    Symbol(name="get_user", type="method", lines=(5, 15)),
                    Symbol(name="create_user", type="method", lines=(17, 25)),
                ])
            ],
        )
        store.save()

        # Find class
        results = store.find_symbol("UserService")
        assert len(results) == 1
        assert results[0]["name"] == "UserService"
        assert results[0]["type"] == "class"

        # Find method (case insensitive)
        results = store.find_symbol("user")
        assert len(results) == 3  # UserService, get_user, create_user

    def test_find_symbol_across_directories(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file(
            "src/service.py",
            "hash1",
            "python",
            30,
            [Symbol(name="ServiceA", type="class", lines=(1, 30))],
        )
        store.update_file(
            "lib/utils.py",
            "hash2",
            "python",
            20,
            [Symbol(name="ServiceB", type="class", lines=(1, 20))],
        )
        store.save()

        results = store.find_symbol("Service")
        assert len(results) == 2
        files = {r["file"] for r in results}
        assert "src/service.py" in files
        assert "lib/utils.py" in files

    def test_find_symbol_by_type(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file(
            "module.py",
            "hash",
            "python",
            50,
            [
                Symbol(name="Service", type="class", lines=(1, 30)),
                Symbol(name="helper_func", type="function", lines=(32, 40)),
            ],
        )
        store.save()

        results = store.find_symbol("", symbol_type="class")
        assert all(r["type"] == "class" for r in results)

        results = store.find_symbol("", symbol_type="function")
        assert all(r["type"] == "function" for r in results)

    def test_get_file_structure(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file(
            "test.py",
            "hash123",
            "python",
            25,
            [Symbol(name="func", type="function", lines=(1, 10))],
        )

        structure = store.get_file_structure("test.py")
        assert structure is not None
        assert structure["hash"] == "hash123"
        assert structure["language"] == "python"
        assert structure["lines"] == 25
        assert len(structure["symbols"]) == 1

    def test_get_file_structure_not_found(self, tmp_path: Path):
        store = MapStore(tmp_path)
        assert store.get_file_structure("nonexistent.py") is None

    def test_update_stats(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file("file1.py", "h1", "python", 10, [
            Symbol(name="f1", type="function", lines=(1, 5))
        ])
        store.update_file("src/file2.py", "h2", "python", 20, [
            Symbol(name="C1", type="class", lines=(1, 15), children=[
                Symbol(name="m1", type="method", lines=(3, 10))
            ])
        ])

        store.update_stats()

        assert store.manifest.stats["total_files"] == 2
        assert store.manifest.stats["total_symbols"] == 3  # f1 + C1 + m1

    def test_load_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            MapStore.load(tmp_path)

    def test_load_corrupted_file(self, tmp_path: Path):
        # Create corrupted manifest
        codemap_dir = tmp_path / ".codemap"
        codemap_dir.mkdir()
        (codemap_dir / ".codemap.json").write_text("{ invalid json")

        store = MapStore(tmp_path)
        # Should return empty manifest instead of crashing
        assert store.manifest.directories == []

    def test_get_all_files(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file("root.py", "h1", "python", 10, [])
        store.update_file("src/module.py", "h2", "python", 20, [])
        store.update_file("src/utils/helper.py", "h3", "python", 30, [])
        store.save()

        files = list(store.get_all_files())
        paths = {f[0] for f in files}

        assert "root.py" in paths
        assert "src/module.py" in paths
        assert "src/utils/helper.py" in paths

    def test_clear(self, tmp_path: Path):
        store = MapStore(tmp_path)

        store.update_file("test.py", "hash", "python", 10, [])
        store.save()

        assert (tmp_path / ".codemap").exists()

        store.clear()

        assert not (tmp_path / ".codemap").exists()
        assert store.manifest.directories == []

    def test_directory_structure_mirrors_project(self, tmp_path: Path):
        """Test that .codemap mirrors the project structure."""
        store = MapStore(tmp_path)

        # Add files in various directories
        store.update_file("main.py", "h1", "python", 10, [])
        store.update_file("src/app.py", "h2", "python", 20, [])
        store.update_file("src/components/Button.py", "h3", "python", 30, [])
        store.update_file("tests/test_app.py", "h4", "python", 40, [])
        store.save()

        codemap_dir = tmp_path / ".codemap"

        # Verify structure
        assert (codemap_dir / ".codemap.json").exists()  # Root manifest
        assert (codemap_dir / "src" / ".codemap.json").exists()
        assert (codemap_dir / "src" / "components" / ".codemap.json").exists()
        assert (codemap_dir / "tests" / ".codemap.json").exists()


class TestRootManifest:
    """Tests for RootManifest class."""

    def test_serialization(self):
        manifest = RootManifest(
            version="1.0",
            root="/test",
            config={"languages": ["python"]},
            directories=["src", "lib"],
        )

        data = manifest.to_dict()
        restored = RootManifest.from_dict(data)

        assert restored.version == "1.0"
        assert restored.root == "/test"
        assert "src" in restored.directories
        assert "lib" in restored.directories


class TestDirectoryMap:
    """Tests for DirectoryMap class."""

    def test_serialization(self):
        dir_map = DirectoryMap(
            version="1.0",
            directory="src/components",
        )
        dir_map.files["Button.py"] = FileEntry(
            hash="abc123",
            indexed_at="2025-01-01T00:00:00Z",
            language="python",
            lines=50,
            symbols=[Symbol(name="Button", type="class", lines=(1, 50))],
        )

        data = dir_map.to_dict()
        restored = DirectoryMap.from_dict(data)

        assert restored.directory == "src/components"
        assert "Button.py" in restored.files
        assert restored.files["Button.py"].hash == "abc123"


class TestSymbol:
    """Tests for Symbol class."""

    def test_symbol_to_dict_basic(self):
        sym = Symbol(name="func", type="function", lines=(1, 10))
        result = sym.to_dict()

        assert result["name"] == "func"
        assert result["type"] == "function"
        assert result["lines"] == [1, 10]
        assert "signature" not in result
        assert "docstring" not in result
        assert "children" not in result

    def test_symbol_to_dict_full(self):
        sym = Symbol(
            name="MyClass",
            type="class",
            lines=(1, 50),
            docstring="A class that does things.",
            children=[
                Symbol(name="method", type="method", lines=(10, 20), signature="(self, x: int)")
            ],
        )
        result = sym.to_dict()

        assert result["docstring"] == "A class that does things."
        assert len(result["children"]) == 1
        assert result["children"][0]["signature"] == "(self, x: int)"

    def test_symbol_from_dict(self):
        data = {
            "name": "test",
            "type": "function",
            "lines": [5, 15],
            "signature": "(x: int) -> str",
            "children": [
                {"name": "nested", "type": "class", "lines": [7, 12]}
            ],
        }
        sym = Symbol.from_dict(data)

        assert sym.name == "test"
        assert sym.lines == (5, 15)
        assert len(sym.children) == 1
        assert sym.children[0].name == "nested"
