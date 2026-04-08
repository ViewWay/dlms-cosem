# Release Process

This document describes the release process for `dlms-cosem`.

## Table of Contents

- [Pre-Release Checklist](#pre-release-checklist)
- [Release Steps](#release-steps)
- [Post-Release Tasks](#post-release-tasks)
- [Emergency Rollback](#emergency-rollback)

---

## Pre-Release Checklist

### Code Quality

- [ ] All tests pass: `uv run pytest`
- [ ] No linting errors: `uv run ruff check`
- [ ] Type checking passes (if enabled)
- [ ] Coverage >= 85%
- [ ] No `TODO` or `FIXME` in production code

### Documentation

- [ ] CHANGELOG.md updated
- [ ] README.md updated
- [ ] API docs generated
- [ ] Examples tested
- [ ] Migration guide updated (if breaking changes)

### Version Bump

- [ ] Version in `pyproject.toml` updated
- [ ] `__version__` in `dlms_cosem/__init__.py` updated
- [ ] Git tag created: `git tag -a v1.0.0 -m "Release v1.0.0"`

---

## Release Steps

### 1. Final Testing

```bash
# Full test suite
uv run pytest --ignore=tests/test_hypothesis --ignore=tests/test_fuzzing

# Integration tests
uv run pytest tests/integration/

# Manual smoke test
python examples/basic_read.py
```

### 2. Build Distribution

```bash
# Build wheel
uv build

# Verify wheel
uv twine check dist/*
```

### 3. Test Installation

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate

# Install wheel
pip install dist/dlms_cosem-1.0.0-py3-none-any.whl

# Run smoke test
python -c "from dlms_cosem import DlmsClient; print('OK')"

# Cleanup
deactivate
rm -rf test_env
```

### 4. Tag and Push

```bash
# Commit final changes
git commit -am "Release v1.0.0"

# Create tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push
git push origin main
git push origin v1.0.0
```

### 5. Publish to PyPI

```bash
# Upload to PyPI (requires PyPI API token)
uv publish dist/*
```

### 6. GitHub Release

1. Go to [GitHub Releases](https://github.com/ViewWay/dlms-cosem/releases)
2. Click "Draft a new release"
3. Select tag `v1.0.0`
4. Copy CHANGELOG content into release notes
5. Attach wheel files
6. Publish release

---

## Post-Release Tasks

### Documentation

- [ ] Build and deploy docs: `mkdocs gh-deploy`
- [ ] Verify docs on GitHub Pages
- [ ] Update www.dlms.dev (if applicable)

### Announcements

- [ ] Tweet release notes
- [ ] Post in Discord/community
- [ ] Email to mailing list (if exists)

### Next Version

- [ ] Bump version in `pyproject.toml` to `1.1.0-dev`
- [ ] Add `[Unreleased]` section to CHANGELOG.md
- [ ] Commit: `git commit -am "Bump to 1.1.0-dev"`

---

## Emergency Rollback

If critical bug is found:

### 1. Quick Fix Branch

```bash
git checkout -b hotfix/v1.0.1
```

### 2. Fix and Test

```bash
# Fix bug
uv run pytest
```

### 3. Release Patch

```bash
# Update version to 1.0.1
# Update CHANGELOG.md
git commit -am "Release v1.0.1"
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main && git push origin v1.0.1
uv publish dist/*
```

### 4. Notify Users

- Announce patch release
- Update issue tracker
- Email to affected users (if applicable)

---

## Versioning Policy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes, API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Deprecation Policy

- Mark deprecated with `warnings.warn`
- Document in migration guide
- Remove in next MAJOR release

---

## Tools

### Release Script (TODO)

```bash
#!/bin/bash
# scripts/release.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh X.Y.Z"
    exit 1
fi

echo "Releasing v$VERSION..."

# Update version
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Update changelog
# ...

# Run tests
uv run pytest

# Build
uv build

# Publish
uv publish dist/*

# Tag
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main
git push origin "v$VERSION"
```

---

## Questions?

- [Contributing Guide](contributing.md)
- [CHANGELOG](../CHANGELOG.md)
- [GitHub Issues](https://github.com/ViewWay/dlms-cosem/issues)
