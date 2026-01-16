"""
Tests for the Skill Manifest Parser module.

Tests cover:
- SkillManifest model
- ManifestParser class
- YAML parsing and validation
- Checksum computation
"""

from pathlib import Path

import pytest
import yaml

from claude_playwright_agent.skills.manifest import (
    ManifestParser,
    ManifestValidationError,
    SkillManifest,
    parse_manifest,
    parse_manifest_string,
    validate_manifest,
)


# =============================================================================
# SkillManifest Model Tests
# =============================================================================


class TestSkillManifest:
    """Tests for SkillManifest model."""

    def test_create_minimal_manifest(self) -> None:
        """Test creating a minimal manifest."""
        manifest = SkillManifest(
            name="test-skill",
            version="1.0.0",
            description="A test skill",
        )

        assert manifest.name == "test-skill"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test skill"
        assert manifest.author == ""
        assert manifest.enabled is True

    def test_create_full_manifest(self) -> None:
        """Test creating a manifest with all fields."""
        manifest = SkillManifest(
            name="full-skill",
            version="2.0.0",
            description="Full featured skill",
            author="Test Author",
            license="MIT",
            homepage="https://example.com",
            repository="https://github.com/test/skill",
            agent_class="my_module.MyAgent",
            entry_point="main.py",
            enabled=True,
            dependencies=["other-skill"],
            python_dependencies=["requests"],
            tags=["testing", "example"],
            keywords=["test", "automation"],
            category="testing",
        )

        assert manifest.author == "Test Author"
        assert manifest.license == "MIT"
        assert manifest.homepage == "https://example.com"
        assert manifest.dependencies == ["other-skill"]
        assert manifest.tags == ["testing", "example"]

    def test_manifest_to_dict(self) -> None:
        """Test converting manifest to dictionary."""
        manifest = SkillManifest(
            name="test",
            version="1.0.0",
            description="Test skill",
            tags=["tag1", "tag2"],
        )

        data = manifest.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "1.0.0"
        assert data["tags"] == ["tag1", "tag2"]
        assert "checksum" in data


# =============================================================================
# ManifestParser Tests
# =============================================================================


class TestManifestParser:
    """Tests for ManifestParser class."""

    def test_initialization(self) -> None:
        """Test parser initialization."""
        parser = ManifestParser()

        assert parser.REQUIRED_FIELDS == ["name", "version", "description"]

    def test_parse_valid_manifest(self, tmp_path: Path) -> None:
        """Test parsing a valid manifest file."""
        manifest_path = tmp_path / "skill.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: A test skill
""", encoding="utf-8")

        parser = ManifestParser()
        manifest = parser.parse(manifest_path)

        assert manifest.name == "test-skill"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test skill"
        assert manifest.checksum != ""

    def test_parse_manifest_with_optional_fields(self, tmp_path: Path) -> None:
        """Test parsing manifest with optional fields."""
        manifest_path = tmp_path / "skill.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: A test skill
author: Test Author
license: MIT
tags:
  - testing
  - example
dependencies:
  - other-skill
python_dependencies:
  - requests>=2.0
""", encoding="utf-8")

        parser = ManifestParser()
        manifest = parser.parse(manifest_path)

        assert manifest.author == "Test Author"
        assert manifest.license == "MIT"
        assert manifest.tags == ["testing", "example"]
        assert manifest.dependencies == ["other-skill"]
        assert manifest.python_dependencies == ["requests>=2.0"]

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing non-existent file."""
        parser = ManifestParser()

        with pytest.raises(FileNotFoundError):
            parser.parse(tmp_path / "nonexistent.yaml")

    def test_parse_invalid_yaml(self, tmp_path: Path) -> None:
        """Test parsing invalid YAML."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("""
name: test
version: [invalid
description: test
""", encoding="utf-8")

        parser = ManifestParser()

        with pytest.raises(yaml.YAMLError):
            parser.parse(manifest_path)

    def test_parse_missing_required_field(self, tmp_path: Path) -> None:
        """Test parsing manifest with missing required field."""
        manifest_path = tmp_path / "incomplete.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
""", encoding="utf-8")

        parser = ManifestParser()

        with pytest.raises(ManifestValidationError) as exc:
            parser.parse(manifest_path)

        assert any("description" in e.lower() for e in exc.value.errors)

    def test_parse_invalid_name_format(self, tmp_path: Path) -> None:
        """Test parsing manifest with invalid name."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("""
name: 123-invalid
version: 1.0.0
description: Test
""", encoding="utf-8")

        parser = ManifestParser()

        with pytest.raises(ManifestValidationError) as exc:
            parser.parse(manifest_path)

        errors = exc.value.errors
        assert any("start with a letter" in e.lower() for e in errors)

    def test_parse_invalid_type_for_enabled(self, tmp_path: Path) -> None:
        """Test parsing manifest with invalid enabled field."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: Test
enabled: "true"
""", encoding="utf-8")

        parser = ManifestParser()

        with pytest.raises(ManifestValidationError) as exc:
            parser.parse(manifest_path)

        assert any("enabled" in e.lower() and "boolean" in e.lower() for e in exc.value.errors)

    def test_parse_invalid_dependencies_type(self, tmp_path: Path) -> None:
        """Test parsing manifest with invalid dependencies."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: Test
dependencies: "not-a-list"
""", encoding="utf-8")

        parser = ManifestParser()

        with pytest.raises(ManifestValidationError):
            parser.parse(manifest_path)

    def test_parse_string(self) -> None:
        """Test parsing manifest from string."""
        content = """
name: test-skill
version: 1.0.0
description: A test skill
"""

        parser = ManifestParser()
        manifest = parser.parse_string(content)

        assert manifest.name == "test-skill"
        assert manifest.version == "1.0.0"
        assert manifest.checksum != ""

    def test_validate_valid_manifest(self, tmp_path: Path) -> None:
        """Test validating a valid manifest."""
        manifest_path = tmp_path / "valid.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: A test skill
""", encoding="utf-8")

        parser = ManifestParser()
        errors = parser.validate(manifest_path)

        assert errors == []

    def test_validate_missing_fields(self, tmp_path: Path) -> None:
        """Test validating manifest with missing fields."""
        manifest_path = tmp_path / "incomplete.yaml"
        manifest_path.write_text("""
name: test-skill
""", encoding="utf-8")

        parser = ManifestParser()
        errors = parser.validate(manifest_path)

        assert len(errors) > 0
        assert any("version" in e for e in errors)
        assert any("description" in e for e in errors)

    def test_validate_nonexistent_file(self, tmp_path: Path) -> None:
        """Test validating non-existent file."""
        parser = ManifestParser()
        errors = parser.validate(tmp_path / "nonexistent.yaml")

        assert len(errors) > 0
        assert "not found" in errors[0]

    def test_validate_invalid_yaml(self, tmp_path: Path) -> None:
        """Test validating invalid YAML."""
        manifest_path = tmp_path / "invalid.yaml"
        manifest_path.write_text("""
name: [invalid
version: 1.0.0
description: Test
""", encoding="utf-8")

        parser = ManifestParser()
        errors = parser.validate(manifest_path)

        assert len(errors) > 0
        assert "YAML" in errors[0]

    def test_compute_checksum(self) -> None:
        """Test checksum computation."""
        content = "name: test\nversion: 1.0.0"

        parser = ManifestParser()
        checksum1 = parser._compute_checksum(content)
        checksum2 = parser._compute_checksum(content)

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length

    def test_compute_checksum_different_content(self) -> None:
        """Test that different content produces different checksum."""
        parser = ManifestParser()

        checksum1 = parser._compute_checksum("name: test1")
        checksum2 = parser._compute_checksum("name: test2")

        assert checksum1 != checksum2


# =============================================================================
# Convenience Functions Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_manifest(self, tmp_path: Path) -> None:
        """Test parse_manifest convenience function."""
        manifest_path = tmp_path / "skill.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: A test skill
""", encoding="utf-8")

        manifest = parse_manifest(manifest_path)

        assert manifest.name == "test-skill"

    def test_parse_manifest_string(self) -> None:
        """Test parse_manifest_string convenience function."""
        content = """
name: test-skill
version: 1.0.0
description: A test skill
"""

        manifest = parse_manifest_string(content)

        assert manifest.name == "test-skill"

    def test_validate_manifest(self, tmp_path: Path) -> None:
        """Test validate_manifest convenience function."""
        manifest_path = tmp_path / "valid.yaml"
        manifest_path.write_text("""
name: test-skill
version: 1.0.0
description: A test skill
""", encoding="utf-8")

        errors = validate_manifest(manifest_path)

        assert errors == []
