# Version Management

This project uses `bump-my-version` for local version management.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Bump patch version (1.0.0 → 1.0.1)
```bash
bump-my-version bump patch
```

### Bump minor version (1.0.0 → 1.1.0)
```bash
bump-my-version bump minor
```

### Bump major version (1.0.0 → 2.0.0)
```bash
bump-my-version bump major
```

## What it does

When you run a bump command, it will:
1. Update version in `pyproject.toml`
2. Update version in `api_extractor/__init__.py`
3. Create a git commit with message: "Bump version: X.Y.Z → X.Y.Z+1"
4. Create a git tag: `vX.Y.Z+1`

## Options

### Dry run (see what would change)
```bash
bump-my-version bump patch --dry-run --verbose
```

### Don't create git tag
```bash
bump-my-version bump patch --no-tag
```

### Don't commit changes
```bash
bump-my-version bump patch --no-commit
```

### Show current version
```bash
bump-my-version show current_version
```
