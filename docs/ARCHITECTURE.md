# OpenIPE Architecture

OpenIPE is a self-hosted, server-backed productivity system. The server is the
source of truth; clients present its workflows without duplicating business
rules. This keeps the command-line client, REST API, and future Android client
consistent as OpenIPE grows.

## System overview

```text
CLI (same host) ────────────────────────────┐
                                            v
REST API clients ──┐                   Internal API ── Application and core ── SQLite
Flet Android ──────┴── REST API ────────────┘
```

The CLI and Android client are planned first-party clients, but they reach the
server differently. The CLI runs in the same environment as OpenIPE Core and
calls the internal API directly. Android runs on a separate device and calls
the REST API over the network. REST is also available to other HTTP clients.

REST is deliberately a consumer of the internal API, never an alternative
workflow layer. Every capability exposed over HTTP must first exist behind the
internal API, so local and network clients use the same rules and data.

## Current implementation

Phase 9.25 is complete. The current server includes:

- SQLite persistence, schema versioning, configuration, startup, and cleanup.
- Authentication, password handling, user management, and ownership isolation.
- Workflows for Inbox items, goals, projects, tasks, habits, check-ins, habit
  stacks, goal associations, and Today.
- An internal Python API and a FastAPI REST adapter.

The command-line client is the next implementation phase. The Android client
has not started.

## Layer responsibilities

### Composition root

`openipe.api.app.create_app` composes the running server. It resolves settings,
initializes SQLite, constructs the internal API, creates the REST application,
and owns database lifetime.

### Internal API

`openipe.api.internal.InternalAPI` is the public Python-facing façade for
first-party clients. It exposes workflow-oriented namespaces and contracts for
users, Inbox, goals, projects, tasks, habits, habit stacks, and Today. It owns
public authorization handling and converts lower-level failures into stable
internal API errors.

The internal API may use application services and core models. It must not
depend on FastAPI, Starlette, or Pydantic HTTP request/response objects.

### REST API

`openipe.api.REST` is a FastAPI HTTP adapter. It accepts and validates HTTP
input, obtains an internal context, calls the injected `InternalAPI`, maps its
public errors to HTTP responses, and serializes results. Its Pydantic schemas
are transport data-transfer objects, not a location for business behavior.

REST must not import OpenIPE core, application, or persistence modules; access
SQLite, settings, repositories, or services; inspect the actor in an internal
context; or implement validation, authorization, lifecycle, scheduling, or
aggregation rules.

### Application and core

Application services coordinate domain workflows. Core models define the
entities and lifecycle concepts that make up an integrated productivity system:
users, Inbox items, goals, projects, tasks, habits, check-ins, habit stacks,
and Today. This is where domain validation, state transitions, scheduling, and
aggregation belong.

### Persistence

SQLite repositories store and retrieve the models and associations. Persistence
is owned by the server composition and application layers; clients and REST do
not read or write it directly.

## Extension rules

New clients should be thin adapters:

1. Collect and locally validate presentation-specific input.
2. Call the appropriate shared boundary: the internal API for a same-host
   client such as the CLI, or REST for a network client such as Android.
3. Render the returned contract or error for the user.

They must not recreate authorization, lifecycle transitions, schedule
calculation, aggregation, or database access. The Phase 9.5 CLI calls the
internal API directly; the Phase 10 Android client calls REST, which then calls
the internal API.

## Quality boundaries

OpenIPE maintains automated tests across core workflows, internal contracts,
REST behavior and delegation, persistence invariants, state transitions,
ownership isolation, and restart persistence. Boundary tests specifically
guard against REST reaching into internal server layers. See
[`TEST_INVENTORY.md`](TEST_INVENTORY.md) for the current coverage map.
