---
name: stack-detect
description: Detect the project's language, framework, package manager, test runner, linter and deploy target from repo files. Show findings as evidence and ask the user to confirm or change them. Never assume a stack. Use before any A.I.D code or tests, and as the first stack step of /setup-aid.
---

# Stack detect

Agents must not guess the language or setup. This skill only **observes files** and **asks**. Confirmed answers become `TOL` records through `tools-manager` + `ssot-gate`. This skill does not write registries, code, or style rules.

## 1. Scan (read-only)

Walk the project root. Skip `.git`, `node_modules`, `.vmodel`, `__pycache__`, `.venv`, `venv`, `dist`, `build`, `target`. Record which of these exist and the fields you actually read (name, version keys, scripts). If a file is absent, write "not seen" for that probe. Do not treat absence as a default tool.

| Probe | Typical files |
|---|---|
| Node / JS / TS | `package.json`, `tsconfig.json`, `jsconfig.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb` |
| Python | `pyproject.toml`, `requirements.txt`, `Pipfile`, `Pipfile.lock`, `setup.py`, `setup.cfg`, `poetry.lock`, `*.py` |
| Go | `go.mod`, `go.sum` |
| Rust | `Cargo.toml`, `Cargo.lock` |
| JVM | `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `gradle.lockfile` |
| Ruby | `Gemfile`, `Gemfile.lock` |
| PHP | `composer.json`, `composer.lock` |
| .NET | `*.csproj`, `*.fsproj`, `*.sln`, `nuget.config` |
| Deploy | `vercel.json`, `.vercel/`, `netlify.toml`, `Dockerfile`, `fly.toml`, `render.yaml`, `wrangler.toml` |
| CI | `.github/workflows/*`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, `.circleci/config.yml` |
| Lint / test hints | `eslint.config.*`, `.eslintrc*`, `ruff.toml`, `.ruff.toml`, `.prettierrc*`, `pytest.ini`, `conftest.py`, `vitest.config.*`, `jest.config.*`, `phpunit.xml`, `Makefile` |

From `package.json` (if seen): `dependencies` / `devDependencies` names, `packageManager`, `scripts.test`, `scripts.lint`, engines. From `pyproject.toml`: `[project]`, `[tool.poetry]`, `[tool.pytest]`, `[tool.ruff]`. From `vercel.json` or a Vercel CI job: deploy target **candidate** Vercel. From `*.csproj`: `TargetFramework`. From lockfiles: only that a package manager is in use, not a second language.

Several languages may appear (for example a Python API and a TypeScript UI). List each; do not pick a winner.

## 2. Propose a table, then stop for the user

Show a table with one row per slot. Every cell is either a **candidate with evidence** (file + snippet or key) or **unclear**.

| slot | candidate | version | evidence |
|---|---|---|---|
| language | … | … | … |
| framework | … | … | … |
| package_manager | … | … | … |
| test_runner | … | … | … |
| linter | … | … | … |
| deploy_target | … | … | … |

Ask the user to confirm or change the table. Do not proceed until they answer.

## 3. Empty or unclear repo

If there is no source tree, no manifest, and no CI, **do not fill the table with defaults**. Ask directly (plain words):

1. Language
2. Framework (or none)
3. Test tool
4. Deploy target (or none, for example Vercel if they name it)

Then, if still needed: package manager and linter (or none). One question at a time if they do not answer a full table.

## 4. Never

- Assume Python, JavaScript, pytest, npm, Vercel, or any other stack because it is "common".
- Write `.vmodel/` or `.cursor/rules/aid-config.mdc` (the `/setup-aid` runner and `tools-manager` / `ssot-gate` do that after confirmation).
- Set code style (`STD` / `VOC`).
- Treat a guessed comment syntax, test command, or deploy host as confirmed.

## 5. Hand-off

Return the confirmed table (slot, tool, version, command or comment syntax, evidence files) to the caller. `/setup-aid` then has `tools-manager` propose `TOL-{PROJECT}-NNN` and `ssot-gate` publish.
