---
name: refresh-virtual-environment
description: Use this skill to rebuild the project's Python virtual environment and clean Python cache artifacts.
tags: [python, virtualenv, environment, cleanup, maintenance]
---

## Use this skill when
- The user asks to recreate or refresh the Python virtual environment.
- Dependency state appears corrupted or inconsistent.
- `__pycache__` directories or compiled `*.pyc` files need to be cleared.
- The user wants a clean reinstall of project requirements.

## Inputs expected
- Optional virtual environment path. Default to a workspace-local environment such as `venv` or `.venv`.
- Optional Python interpreter path or version preference.
- Optional requirement file scope. Default to the root `requirements.txt`, plus any additional requirement files the user explicitly requests.
- Optional confirmation when multiple virtual environment directories exist.

## Procedure
1. Resolve the target environment.
- Detect common workspace-local environment directories such as `venv` and `.venv`.
- If multiple candidates exist, do not guess. Ask the user which one to rebuild.
- Prefer a workspace-local path and avoid touching environments outside the repository unless explicitly requested.

2. Remove the old virtual environment.
- Delete only the resolved environment directory.
- Refuse broad or ambiguous delete targets.
- Report the exact path removed.

3. Remove Python cache artifacts.
- Recursively delete all `__pycache__` directories in the requested scope.
- Recursively delete compiled `*.pyc` files.
- Keep deletions limited to Python cache artifacts unless the user asks for more cleanup.

4. Build a new virtual environment.
- Create a fresh environment with the selected Python interpreter.
- Prefer using the environment's Python and pip directly instead of relying on shell activation.
- Upgrade packaging basics such as `pip`, `setuptools`, and `wheel` unless the repository has a reason not to.

5. Install requirements.
- Install from the root `requirements.txt` by default.
- Install additional requirement files only when the user requests them or the repository workflow clearly requires them.
- Report which requirement files were installed.

6. Verify the result.
- Confirm the new interpreter path.
- Confirm package installation completed successfully.
- Summarize removed cache artifacts and rebuilt environment path.

## Safety rules
- Never delete a path outside the workspace without explicit confirmation.
- Never guess between multiple virtual environment directories.
- Never remove non-cache project files as part of cleanup.
- Prefer direct executable paths over activation-dependent shell state.

## Output expectations
- Return a concise summary of:
  `ENV_PATH | REQUIREMENTS | PYCACHE_REMOVED | PYC_REMOVED | STATUS`
- If any step is skipped, state why.
- If environment recreation fails, report the failing command and the next corrective action.

## Quality checks
- The delete target is explicit and safe.
- `__pycache__` and `*.pyc` cleanup is complete within the requested scope.
- The new environment is created successfully.
- Requirement installation is completed and reported accurately.