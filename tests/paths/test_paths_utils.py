"""Tests for path utilities module."""

from pathlib import Path
import tempfile
import pytest

from saaaaaa.utils.paths import (
    PathTraversalError,
    PathNotFoundError,
    PathOutsideWorkspaceError,
    proj_root,
    src_dir,
    data_dir,
    tmp_dir,
    build_dir,
    cache_dir,
    reports_dir,
    is_within,
    safe_join,
    normalize_unicode,
    validate_read_path,
    validate_write_path,
    PROJECT_ROOT,
    SRC_DIR,
)


def system_tmp_path(name: str) -> Path:
    """Return a path in the system temporary directory (outside workspace)."""
    return Path(tempfile.gettempdir()) / name


class TestProjectRoots:
    """Test project root detection."""
    
    def test_proj_root_returns_path(self):
        """proj_root() should return a Path."""
        root = proj_root()
        assert isinstance(root, Path)
        assert root.exists()
        assert root.is_dir()
    
    def test_proj_root_has_pyproject_toml(self):
        """Project root should contain pyproject.toml."""
        root = proj_root()
        assert (root / "pyproject.toml").exists()
    
    def test_src_dir_exists(self):
        """src_dir() should return existing directory."""
        src = src_dir()
        assert isinstance(src, Path)
        assert src.exists()
        assert src.is_dir()
        assert (src / "saaaaaa").exists()
    
    def test_constants_match_functions(self):
        """Global constants should match function results."""
        assert PROJECT_ROOT == proj_root()
        assert SRC_DIR == src_dir()


class TestDirectoryCreation:
    """Test directory creation functions."""
    
    def test_data_dir_creates_if_missing(self):
        """data_dir() should create directory if it doesn't exist."""
        dd = data_dir()
        assert isinstance(dd, Path)
        assert dd.exists()
        assert dd.is_dir()
    
    def test_tmp_dir_creates_if_missing(self):
        """tmp_dir() should create directory if it doesn't exist."""
        td = tmp_dir()
        assert isinstance(td, Path)
        assert td.exists()
        assert td.is_dir()
        assert is_within(proj_root(), td)
    
    def test_build_dir_creates_if_missing(self):
        """build_dir() should create directory if it doesn't exist."""
        bd = build_dir()
        assert isinstance(bd, Path)
        assert bd.exists()
        assert bd.is_dir()
    
    def test_cache_dir_under_build(self):
        """cache_dir() should be under build/."""
        cd = cache_dir()
        assert isinstance(cd, Path)
        assert cd.exists()
        assert is_within(build_dir(), cd)
    
    def test_reports_dir_under_build(self):
        """reports_dir() should be under build/."""
        rd = reports_dir()
        assert isinstance(rd, Path)
        assert rd.exists()
        assert is_within(build_dir(), rd)


class TestIsWithin:
    """Test is_within path containment checks."""
    
    def test_direct_child(self):
        """Direct child should be within parent."""
        parent = proj_root()
        child = parent / "src"
        assert is_within(parent, child)
    
    def test_nested_child(self):
        """Deeply nested child should be within parent."""
        parent = proj_root()
        child = parent / "src" / "saaaaaa" / "core" / "file.py"
        assert is_within(parent, child)
    
    def test_sibling_not_within(self):
        """Sibling directory should not be within."""
        base = proj_root() / "src"
        sibling = proj_root() / "tests"
        assert not is_within(base, sibling)
    
    def test_parent_not_within_child(self):
        """Parent should not be within child."""
        parent = proj_root()
        child = parent / "src"
        assert not is_within(child, parent)
    
    def test_outside_not_within(self):
        """Completely outside path should not be within."""
        base = proj_root()
        outside = system_tmp_path("other")
        assert not is_within(base, outside)


class TestSafeJoin:
    """Test safe_join path construction."""
    
    def test_simple_join(self):
        """Simple path joining should work."""
        base = proj_root()
        result = safe_join(base, "src", "file.py")
        assert is_within(base, result)
        assert result == base / "src" / "file.py"
    
    def test_blocks_traversal_up(self):
        """Should block .. traversal outside base."""
        base = proj_root()
        with pytest.raises(PathTraversalError):
            safe_join(base, "..", "other")
    
    def test_blocks_traversal_nested(self):
        """Should block nested .. traversal outside base."""
        base = proj_root() / "src"
        with pytest.raises(PathTraversalError):
            safe_join(base, "subdir", "..", "..", "..", "etc", "passwd")
    
    def test_allows_internal_traversal(self):
        """Should allow .. that stays within base."""
        base = proj_root()
        result = safe_join(base, "src", "subdir", "..", "file.py")
        assert is_within(base, result)
        assert result == base / "src" / "file.py"
    
    def test_absolute_component_blocked(self):
        """Should handle absolute path components safely."""
        base = proj_root()
        # This depends on how resolve() handles absolute components
        # Most implementations will resolve to absolute path which may fail is_within
        try:
            result = safe_join(base, str(system_tmp_path("other")))
            # If it doesn't raise, verify it's still within base
            assert is_within(base, result)
        except PathTraversalError:
            # Expected - absolute path component detected
            pass


class TestNormalizeUnicode:
    """Test Unicode normalization."""
    
    def test_nfc_normalization(self):
        """Should normalize to NFC by default."""
        # Using combining characters vs precomposed
        path_nfd = Path("café")  # NFD: c + combining acute
        result = normalize_unicode(path_nfd, "NFC")
        assert isinstance(result, Path)
    
    def test_preserves_ascii(self):
        """ASCII paths should be unchanged."""
        path = Path("simple/ascii/path.txt")
        result = normalize_unicode(path)
        assert str(result) == str(path)


class TestValidateReadPath:
    """Test read path validation."""
    
    def test_validates_existing_file(self):
        """Should succeed for existing readable file."""
        pyproject = proj_root() / "pyproject.toml"
        validate_read_path(pyproject)  # Should not raise
    
    def test_rejects_nonexistent(self):
        """Should reject non-existent path."""
        nonexistent = proj_root() / "this_does_not_exist_12345.txt"
        with pytest.raises(PathNotFoundError):
            validate_read_path(nonexistent)


class TestValidateWritePath:
    """Test write path validation."""
    
    def test_allows_build_dir(self):
        """Should allow writing to build directory."""
        write_path = build_dir() / "test_output.txt"
        validate_write_path(write_path)  # Should not raise
    
    def test_allows_tmp_dir(self):
        """Should allow writing to tmp directory."""
        write_path = tmp_dir() / "test_output.txt"
        validate_write_path(write_path)  # Should not raise
    
    def test_blocks_src_tree(self):
        """Should block writing to source tree by default."""
        write_path = src_dir() / "generated.py"
        with pytest.raises(ValueError) as exc:
            validate_write_path(write_path)
        assert "source tree" in str(exc.value).lower()
    
    def test_allows_src_tree_with_flag(self):
        """Should allow source tree if explicitly enabled."""
        write_path = src_dir() / "generated.py"
        validate_write_path(write_path, allow_source_tree=True)  # Should not raise
    
    def test_blocks_outside_workspace(self):
        """Should block writing outside workspace."""
        outside = system_tmp_path("outside_workspace.txt")
        with pytest.raises(PathOutsideWorkspaceError):
            validate_write_path(outside)


class TestIntegration:
    """Integration tests combining multiple operations."""
    
    def test_create_file_in_tmp(self):
        """Should be able to create and validate file in tmp."""
        tmp = tmp_dir()
        test_file = tmp / "integration_test.txt"
        
        # Validate we can write
        validate_write_path(test_file)
        
        # Create file
        test_file.write_text("test content")
        
        # Validate we can read
        validate_read_path(test_file)
        
        # Read back
        content = test_file.read_text()
        assert content == "test content"
        
        # Cleanup
        test_file.unlink()
    
    def test_safe_join_with_validation(self):
        """Should be able to safely join and validate."""
        base = build_dir()
        path = safe_join(base, "reports", "test.txt")
        
        # Ensure parent exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Should be valid for writing
        validate_write_path(path)
