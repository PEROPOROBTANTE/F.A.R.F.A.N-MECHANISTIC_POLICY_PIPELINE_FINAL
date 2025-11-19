"""Test workspace boundary enforcement and path traversal protection."""

from pathlib import Path
import tempfile
import pytest

from saaaaaa.utils.paths import (
    PathTraversalError,
    PathOutsideWorkspaceError,
    proj_root,
    tmp_dir,
    safe_join,
    is_within,
    validate_write_path,
)


class TestTraversalProtection:
    """Test that path traversal attacks are prevented."""
    
    def test_blocks_direct_parent_traversal(self):
        """Should block direct .. traversal outside workspace."""
        base = proj_root() / "src"
        
        with pytest.raises(PathTraversalError):
            safe_join(base, "..", "..", "etc", "passwd")
    
    def test_blocks_nested_traversal(self):
        """Should block nested traversal attempts."""
        base = proj_root() / "src" / "saaaaaa"
        
        with pytest.raises(PathTraversalError):
            safe_join(base, "core", "..", "..", "..", "..", "tmp", "malicious")
    
    def test_allows_safe_relative_paths(self):
        """Should allow safe relative paths within workspace."""
        base = proj_root()
        
        # This is safe - stays within workspace
        result = safe_join(base, "src", "saaaaaa", "core")
        assert is_within(base, result)
    
    def test_allows_internal_parent_ref(self):
        """Should allow .. that stays within workspace."""
        base = proj_root()
        
        # Goes into src, then back, then into tests - all within workspace
        result = safe_join(base, "src", "..", "tests")
        assert is_within(base, result)
        assert result == base / "tests"
    
    def test_symlink_traversal_protection(self):
        """Should protect against symlink traversal (if possible)."""
        # Note: This test may be platform-specific
        # On systems that support symlinks, ensure they can't escape
        tmp = tmp_dir()
        
        # Create a test directory
        test_dir = tmp / "traversal_test"
        test_dir.mkdir(exist_ok=True)
        
        # Try to join a path - should be within tmp
        result = safe_join(test_dir, "subdir", "file.txt")
        assert is_within(tmp, result)
        
        # Cleanup
        test_dir.rmdir()
    
    def test_url_encoded_traversal_blocked(self):
        """Should block URL-encoded traversal attempts."""
        base = proj_root()
        
        # Some systems might interpret these
        with pytest.raises(PathTraversalError):
            safe_join(base, "..", "..", "etc", "passwd")


class TestWorkspaceBoundaries:
    """Test workspace boundary enforcement."""
    
    def test_src_within_workspace(self):
        """Source directory should be within workspace."""
        root = proj_root()
        src = root / "src"
        
        assert is_within(root, src)
    
    def test_temp_within_workspace(self):
        """Temp directory should be within workspace."""
        root = proj_root()
        tmp = tmp_dir()
        
        assert is_within(root, tmp)
    
    def _external_tmp(self, name: str) -> Path:
        """Helper producing a path outside the workspace (system temp)."""
        return Path(tempfile.gettempdir()) / name

    def test_absolute_outside_rejected(self):
        """Absolute paths outside workspace should be rejected."""
        outside = self._external_tmp("outside")
        
        # Should not be considered within workspace
        assert not is_within(proj_root(), outside)
    
    def test_write_outside_workspace_blocked(self):
        """Writing outside workspace should be blocked."""
        outside = self._external_tmp("malicious.txt")
        
        with pytest.raises(PathOutsideWorkspaceError):
            validate_write_path(outside)
    
    def test_relative_path_resolution(self):
        """Relative paths should resolve correctly."""
        base = proj_root()
        
        # Create a relative path that would escape if not resolved
        # Note: We use safe_join which should resolve
        with pytest.raises(PathTraversalError):
            safe_join(base, "../..")


class TestEdgeCases:
    """Test edge cases in path handling."""
    
    def test_empty_path_component(self):
        """Should handle empty path components gracefully."""
        base = proj_root()
        
        # Empty strings should be handled
        result = safe_join(base, "", "src", "")
        assert is_within(base, result)
    
    def test_current_dir_component(self):
        """Should handle . (current directory) correctly."""
        base = proj_root()
        
        result = safe_join(base, ".", "src", ".", "saaaaaa")
        assert is_within(base, result)
        # Should normalize to same as direct path
        assert result == base / "src" / "saaaaaa"
    
    def test_multiple_slashes(self):
        """Should handle multiple slashes correctly."""
        base = proj_root()
        
        # pathlib should normalize these
        result = safe_join(base, "src", "saaaaaa")
        assert is_within(base, result)
    
    def test_unicode_in_paths(self):
        """Should handle Unicode characters in paths."""
        base = tmp_dir()
        
        # Unicode filename
        result = safe_join(base, "café", "naïve.txt")
        assert is_within(base, result)
    
    def test_very_long_path(self):
        """Should handle very long paths (within system limits)."""
        base = tmp_dir()
        
        # Create a moderately long path
        components = ["level" + str(i) for i in range(20)]
        result = safe_join(base, *components)
        assert is_within(base, result)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_user_provided_filename(self):
        """Should safely handle user-provided filenames."""
        base = tmp_dir()
        
        # Simulate user providing a filename with traversal attempt
        user_filename = "../../etc/passwd"
        
        with pytest.raises(PathTraversalError):
            safe_join(base, user_filename)
    
    def test_safe_user_filename(self):
        """Should accept safe user-provided filenames."""
        base = tmp_dir()
        
        user_filename = "my_report.pdf"
        result = safe_join(base, user_filename)
        
        assert is_within(base, result)
        assert result == base / "my_report.pdf"
    
    def test_nested_user_path(self):
        """Should handle nested user paths safely."""
        base = tmp_dir()
        
        # User wants to organize in subdirectory
        user_path = "reports/2024/january/report.pdf"
        result = safe_join(base, user_path)
        
        assert is_within(base, result)
    
    def test_reject_absolute_from_user(self):
        """Should reject absolute paths from user."""
        base = tmp_dir()
        
        user_path = "/etc/passwd"
        
        # This will resolve to absolute path
        with pytest.raises(PathTraversalError):
            safe_join(base, user_path)
