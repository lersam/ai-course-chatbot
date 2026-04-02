---
description: 'Python coding conventions and guidelines'
applyTo: "**/*.py"
---

# Python Coding Conventions

This document combines concise, user-preferred Python instructions with repository-level engineering standards. Where items overlap, the user's wording is used and extended with practical rules.

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use the `typing` module for type annotations (prefer modern syntax where applicable, e.g., `list[str]` or `str | None`).
- Break down complex functions into smaller, testable helpers.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include a brief explanation of the approach used.
- Document why certain design decisions were made where they are not obvious.
- Handle edge cases explicitly and write clear exception handling.
- For external libraries, document their purpose and justify inclusion.
- Use consistent naming conventions and follow Python best practices.
- Write concise, efficient, and idiomatic code that remains easy to understand.

## Code Style and Formatting

- Follow the PEP 8 style guide.
- Use 4 spaces for indentation and avoid tabs.
- Keep lines under 79 characters where practical.
- Place function and class docstrings immediately after the `def` or `class` line.
- Use blank lines to separate top-level functions and classes and to improve readability.

## Imports

- Follow PEP 8 import order: standard library, third-party, then local/project imports, with one blank line between groups.
- **Placement:** Place all imports at the top of the file immediately after the module docstring and before constants, classes, or functions.
- **Grouping:** Group imports in three sections with one blank line between groups: standard library, third-party, local/project imports.
- **Ordering:** Sort imports within each group alphabetically. Use `isort` to enforce automatically.
- **Style:** Prefer absolute imports. Avoid wildcard imports (`from module import *`) and avoid deep relative imports when possible.
- **Unused & Linting:** Remove unused imports. Enforce with `ruff`/`flake8`/`pylint` in CI.
- **Type-only imports:** For imports used only for typing that are expensive or cause cycles, use `if TYPE_CHECKING:` or `from __future__ import annotations` and `typing.TYPE_CHECKING`.
- **Conditional imports:** When importing conditionally (platform, optional dependency), add a short comment explaining why.
- **Shared models:** Import shared models at module level.
- **No lazy-import helpers:** Do not use lazy-import helper functions for shared models. Only defer imports when required to avoid a verified import cycle or an expensive optional dependency, and document the reason briefly.
- **Example:**

```
# module docstring

import logging
import math

from fastapi import FastAPI
from starlette.requests import Request

from myproject.utils import helper_function
```

## Python Language and Practical Rules

- Use type hints for all public function signatures and important internal helpers.
- Prefer Python 3.10+ syntax for unions and built-ins (e.g., `str | None`, `list[str]`).
- Use `pathlib.Path` for filesystem work.
- Prefer `dataclasses` (use `@dataclass(frozen=True)` for immutable domain models) for internal models; use `pydantic.BaseModel` only at external boundaries (e.g., FastAPI schemas).

### Logging

**Hard Rule:** All runtime logging must use Python's standard library `logging` module.

- Use module-level loggers only:
	- `logger = logging.getLogger(__name__)`
- Do not use `print()` for runtime diagnostics.
- Do not use third-party logging libraries (e.g., `loguru`) unless explicitly requested.
- Log call message templates must be literal strings.
- Use `%`-style parameterized logging for dynamic values: `logger.info("Processed %s records", count)`.
- Never use f-strings in logging calls.
- Log failures with context using `logger.exception(...)`.

## Data Modeling and Validation

- Prefer `@dataclass(frozen=True)` for application/domain configuration and internal data structures.
- Validate invariants in `__post_init__` for dataclasses.
- For parsing external payloads, use `pydantic` with strict settings (`model_config = ConfigDict(strict=True, extra="forbid")`).
- Never swallow validation errors.
- Propagate or log with full context.

## Edge Cases and Testing

- Always include tests for critical paths and important edge cases (empty inputs, invalid types, large inputs).
- Prefer `pytest`; use fixtures for setup/teardown and `pytest.mark.parametrize` for multiple scenarios.
- For database-related tests, prefer in-memory SQLite or equivalent isolated setups.
- Document the expected behavior for edge cases in tests and source docstrings.

## Testing Standards and CI

- Use `pytest`.
- Write at least one positive and one error-path test for non-trivial functions.
- Use mocks for external integrations and keep tests hermetic.

## Example of Proper Documentation

```python
import math

def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    """
    return math.pi * radius ** 2
```

---
## Completion Criteria

Changes should be considered complete when:
1. Public functions and classes include meaningful docstrings.
2. Type hints are coherent and present for public APIs.
3. Tests cover critical paths and edge cases.
4. Logging and error handling are consistent with rules above.
5. No secrets are hard-coded and external inputs are validated.
