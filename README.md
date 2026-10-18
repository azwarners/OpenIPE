# OpenIPE

## Install and API quick start

OpenIPE currently ships a Python REST API, not a finished command-line or mobile client. With Python 3.11 or newer:

```sh
git clone https://github.com/azwarners/OpenIPE.git
cd OpenIPE
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

The application factory is `openipe.api.app:create_app`. Start a development API server with an ASGI runner such as Uvicorn (install it separately if needed):

```sh
python -m pip install uvicorn
uvicorn 'openipe.api.app:create_app' --factory --host 127.0.0.1 --port 8000
```

This exposes the currently implemented API workflows: authenticated, user-owned Inbox capture and processing; goals; projects and tasks; habits, check-ins, and habit stacks; and date-aware Today data. SQLite backs the data. The planned `openipe` CLI and Android client are **not yet shipped**.


OpenIPE is a self-hosted Integrated Productivity Environment: one place to
capture ideas, connect them to meaningful goals, turn them into projects and
tasks, build supporting habits, and decide what deserves attention today.

It is designed to be useful without forcing a single productivity method. Your
Inbox can stay quick and unstructured; you can decide later whether an idea
should become a task, project, or habit, and how it relates to the outcomes you
care about.

## What OpenIPE brings together

- **Inbox** for frictionless idea capture and later processing.
- **Goals** for the outcomes you are pursuing.
- **Projects and tasks** for the work that moves goals forward, including a
  project's next action and progress.
- **Habits, check-ins, and habit stacks** for repeated actions and routines.
- **Today** for a date-aware view of selected tasks, habit progress, and daily
  focus.
- **Private, self-hosted data** backed by SQLite, with user accounts,
  authentication, and ownership isolation.

The data model and REST API for these workflows are implemented now. OpenIPE's
server has comprehensive automated coverage for workflow rules, persistence,
privacy boundaries, lifecycle changes, and recovery after restart.

## Where OpenIPE is today

OpenIPE v0.0.1 has completed its server foundation and REST API. The first
user-facing client is next: an `openipe` command-line application that will
make the available workflows practical to use from a terminal.

The command-line client will be followed by the first pocket-first Android
client. That client will begin with secure sign-in, a Today view, quick Inbox
capture, task completion, habit check-ins, and Inbox processing; it will then
grow into full goal, project, task, habit, and habit-stack management.

Longer term, OpenIPE is intended to support additional independent clients,
including Linux desktop, web, other mobile platforms, command-line tools, and
carefully authorized third-party integrations. Your OpenIPE Core data remains
the source of truth across those clients.

## Product principles

- **Capture first, organize later.** Record the thought before deciding what it
  means.
- **See the connections.** Relate projects, tasks, and habits to the goals they
  support.
- **Useful before clever.** Start with dependable daily workflows instead of
  speculative automation or productivity theory.
- **Own your system.** OpenIPE is open source, self-hosted, and independent of
  a particular cloud, VPN, identity provider, or device platform.

## Learn more

- [Product blueprint](docs/BLUEPRINT.md) — vision, scope, and product
  principles.
- [Architecture](docs/ARCHITECTURE.md) — how OpenIPE Core, the REST API, and
  future clients fit together.
- [Implementation roadmap](docs/PLAN.md) — current work and planned phases.

OpenIPE is being built deliberately: each phase is implemented, tested,
reviewed, and approved before the next one begins.
