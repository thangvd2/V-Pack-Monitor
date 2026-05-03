# Plan 68: Create `vpack/` Package Skeleton

> **Status:** READY
> **Priority:** HIGH — Step 1 of restructuring
> **Scope:** 3 new files, 1 config update
> **Estimated Effort:** 10 min

---

## Goal

Create the `vpack/` package structure and build config. **No existing code changes** — just add the skeleton so subsequent plans can move files into it.

---

## Changes

### 1. Create `vpack/__init__.py`

```python
"""V-Pack Monitor — Camera station recording management."""
__version__ = "3.5.0"
```

Read version from `VERSION` file at runtime:
```python
import os
def _get_version():
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip().lstrip("v")
    return "0.0.0"

__version__ = _get_version()
```

### 2. Create `vpack/routes/__init__.py`

Empty file. Route modules register via `app` parameter in their `register_routes(app)` functions.

### 3. Create `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "vpack-monitor"
version = "3.5.0"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
include = ["vpack*"]
```

### 4. Update `ruff.toml`

Add `src = ["vpack"]` so ruff understands the package structure for import resolution.

---

## Verification

1. `pip install -e .` succeeds
2. `python -c "import vpack; print(vpack.__version__)"` prints `3.5.0`
3. `ruff check .` passes
4. Existing tests still pass (nothing moved yet)

## After This Plan

`vpack/` exists as empty package. `api.py`, `routes_*.py`, etc. still at root. Everything works as before.
