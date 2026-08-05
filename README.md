# OpenIPE

OpenIPE is an open-source, self-hosted Integrated Productivity Environment.
It connects captured ideas, goals, projects, tasks, habits, habit stacks, and
daily action through an independent server and client architecture.

This repository is currently implementing version 0.0.1 according to
[`BLUEPRINT.md`](BLUEPRINT.md). Development is phase-based; each phase is
implemented, tested, reviewed, and explicitly approved before the next phase
begins.

## Development

OpenIPE requires Python 3.11 or newer.

Create an environment and install the project with development dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run the tests with:

```bash
pytest
```

Phase 1 provides the package foundation, configuration, logging, and SQLite
schema-version infrastructure. Product entities are introduced in later
phases.
