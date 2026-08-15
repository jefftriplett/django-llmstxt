@_default:
	just --list

@bootstrap:
	uv sync --group docs --group test

@build:
	uv build

@bump *ARGS:
	uv tool run bumpver update --allow-dirty {{ ARGS }}

@bump-dry *ARGS:
	just bump --dry {{ ARGS }}

@docs:
	uv run --group docs zensical serve

@docs-build:
	uv run --group docs zensical build --clean --strict
	uv run --group docs python scripts/gen_llms.py site

# run the example Django project at http://127.0.0.1:8000/
@example *ARGS:
	uv run --group test python example/manage.py runserver {{ ARGS }}

@lint:
	uvx ruff check .
	uvx ruff format --check .

@lock:
	uv lock

# bump the SemVer version, relock, and push the tag; CI publishes to PyPI
release *ARGS:
	#!/usr/bin/env bash
	set -euo pipefail
	just bump {{ ARGS }}
	just lock
	version="$(grep -m1 '^current_version' pyproject.toml | cut -d'"' -f2)"
	git add uv.lock
	git commit --amend --no-edit
	git tag -d "$version"
	git tag -a "$version" -m "$version"
	git push --follow-tags

# lint and fix in place
@ruff:
	-uvx ruff check --fix .
	-uvx ruff format .

@test *ARGS:
	uv run --group test pytest {{ ARGS }}

@types:
	uv run --group test --with mypy --with django-stubs mypy src
