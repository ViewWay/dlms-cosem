# Contributing to dlms-cosem

Thank you for contributing to `dlms-cosem`!

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

---

## Getting Started

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ViewWay/dlms-cosem.git
cd dlms-cosem

# Install dependencies
uv sync --extra dev

# Run pre-commit hooks
uvx pre-commit install

# Run tests
uv run pytest
```

---

## Development Workflow

### 1. Create Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Write Code

- Follow [Code Style](#code-style)
- Add tests for new features
- Update documentation

### 3. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_hdlc.py

# Run with coverage
uv run pytest --cov=dlms_cosem
```

### 4. Type Check

```bash
# Run mypy (if configured)
uv run mypy dlms_cosem/
```

### 5. Lint

```bash
# Run pre-commit hooks
uvx pre-commit run --all-files

# Or manually run formatters
uv run black dlms_cosem/
uv run ruff check dlms_cosem/
```

---

## Code Style

### Python Style

We follow PEP 8 with these tools:

- **black**: Code formatting
- **ruff**: Linting (faster than flake8)
- **mypy**: Type checking (planned)

### Formatting

```bash
# Format code
uv run black dlms_cosem/ tests/

# Check formatting
uv run black --check dlms_cosem/ tests/
```

### Linting

```bash
# Check for issues
uv run ruff check dlms_cosem/ tests/

# Auto-fix issues
uv run ruff check --fix dlms_cosem/ tests/
```

---

## Testing

### Test Structure

```
tests/
├── test_hdlc/           # HDLC tests
├── test_xdlms/          # XDLMS tests
├── test_asce/           # ACSE tests
├── test_*.py            # Module tests
└── conftest.py          # Shared fixtures
```

### Writing Tests

```python
import pytest
from dlms_cosem import DlmsClient

def test_basic_read():
    """Test basic read operation."""
    conn = MockConnection()
    client = DlmsClient(conn)
    result = client.get(obis)
    assert result is not None
```

### Test Rules

1. **All new code must have tests**
2. **Test names should describe behavior**
3. **Use fixtures for common setup**
4. **Test both success and failure cases**

---

## Submitting Changes

### Commit Messages

Use conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Refactoring
- `style`: Code style
- `chore`: Maintenance

Example:

```
feat(hdlc): add sliding window support

Implement sliding window mechanism for HDLC
to improve throughput on high-latency links.

Closes #123
```

### Pull Request Process

1. Push to fork or branch
2. Create pull request
3. Fill PR template:
   - Description of changes
   - Related issues
   - Testing done
   - Screenshots (if UI)
4. Wait for review
5. Address feedback
6. Merge when approved

---

## Code Review Guidelines

### Reviewer Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes without version bump
- [ ] Security implications reviewed

### Author Checklist

- [ ] Tests pass locally
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Self-reviewed diff
- [ ] Documentation updated

---

## Release Process

### Version Bump

Follow semantic versioning:

- `MAJOR`: Breaking changes
- `MINOR`: New features (backwards compatible)
- `PATCH`: Bug fixes (backwards compatible)

### Changelog

Update `CHANGELOG.md`:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

### Publishing

```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Publish to PyPI (if authorized)
uv publish
```

---

## Getting Help

- [Documentation](docs/)
- [Examples](docs/examples.md)
- [Troubleshooting](docs/troubleshooting.md)
- [GitHub Issues](https://github.com/ViewWay/dlms-cosem/issues)
- [Discussions](https://github.com/ViewWay/dlms-cosem/discussions)

---

## License

By contributing, you agree that your code will be licensed under the [Business Source License 1.1](LICENSE).
