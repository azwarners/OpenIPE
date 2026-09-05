# Phase 9.25 Remediation Plan: Enforce the Internal API Boundary

## Purpose

Complete the Phase 9.25 extraction so `src/openipe/api/REST` is an HTTP-only
adapter over `src/openipe/api/internal`. REST must never depend directly on
core, application services, persistence, repositories, domain models, or
SQLite. The internal API is the shared boundary for REST and the future CLI.

## Non-Negotiable Boundary

REST may import only:

* Python standard-library modules;
* FastAPI, Starlette, Pydantic, and declared HTTP dependencies;
* `openipe.api.REST.*` modules; and
* public `openipe.api.internal.*` modules.

REST must not import `openipe.core.*`, `openipe.application.*`,
`openipe.persistence.*`, repository/domain-model modules, or `sqlite3`.

This command is release-blocking and must produce no output:

```bash
rg -n '^from openipe\.(core|application|persistence)|^import openipe\.(core|application|persistence)' src/openipe/api/REST
```

## Target Architecture

```text
openipe.api.app (composition root)
    ├── resolves Settings
    ├── owns SQLite initialization and cleanup
    ├── creates InternalAPI(connection, settings)
    └── calls REST.create_app(internal_api, lifespan)

REST HTTP adapter ────────────────────────────────► InternalAPI
future OpenIPE CLI ───────────────────────────────► InternalAPI
InternalAPI ─────────────────────────► application services / core / persistence
```

## Required Responsibilities

### `openipe.api.app`

Keep `create_app(settings=None, connection=None, internal_api=None)` as the
composition-root and compatibility entry point. It alone may resolve settings,
initialize SQLite, create the internal façade, and close an owned connection.
It delegates HTTP application creation to `openipe.api.REST.app.create_app`.

### `openipe.api.REST`

`REST.create_app(internal_api, lifespan=None)` accepts a constructed façade.
REST stores only `app.state.internal_api`, installs routes, parses HTTP input,
converts Pydantic values to internal contracts, invokes internal methods, and
serializes internal responses/errors. It owns no business, database,
authorization, lifecycle, schedule, ordering, ownership, or aggregation logic.

Remove database dependencies and state access, including `get_connection`.

### `openipe.api.internal`

`InternalAPI` is the only local-client entry point. It may use existing
application services and core/persistence dependencies behind that boundary.
It owns:

* token authentication and administrator authorization;
* public `InternalContext` creation;
* conversion of domain/service results to internal contracts;
* translation of core/application exceptions to public internal errors; and
* all supported OpenIPE workflows.

Public internal errors must include authentication, inactive-user, permission,
not-found, and validation categories. REST catches only those internal errors.
REST must treat `InternalContext` as opaque: it may pass it to internal methods
but must never inspect `context.actor`.

Expose status, priority, frequency, and check-in values through internal
contracts. REST schemas must import those public internal types rather than
core model enums.

## Implementation Tasks

1. Confirm the root app factory owns settings/database/lifespan behavior and
   that REST receives an injected `InternalAPI` only.
2. Remove every direct REST import of core, application, persistence, model,
   repository, and SQLite modules. Use the release-blocking search above.
3. Delete REST database access and ensure REST code does not inspect connection
   or settings state.
4. Ensure bearer authentication calls `InternalAPI.authenticate`; move admin
   authorization into `InternalAPI.authorize_admin`; remove REST reads of
   `InternalContext.actor`.
5. Ensure all REST error-to-HTTP translation catches only internal errors.
6. Ensure every REST route delegates to an internal operation and preserves all
   existing paths, HTTP methods, request/response fields, status codes, and
   documented error behavior.
7. Keep all domain validation and lifecycle rules in existing application
   services. Internal may orchestrate and shape contracts, but may not
   duplicate business logic.
8. Remove wildcard imports from internal modules and expose deliberate public
   contracts only.

## Required Internal API Coverage

Dedicated tests must cover every public operation with successful behavior and
relevant failures. A single broad happy-path test per namespace is insufficient.

### Authentication and users

Test initial setup, login, logout, current-user lookup, invalid credentials,
inactive users, expired/revoked tokens, password-change revocation, user
create/list/get/update/activation/deactivation, non-admin rejection, and
missing-user behavior.

### Inbox

Test create/list filters/get/edit/process/archive/discard/delete; each task,
project, and habit conversion; invalid text; missing records; and cross-user
isolation.

### Goals and associations

Test list/status filtering/get/create/all update fields/all lifecycle actions,
terminal-state rejection, evidence, source-inbox ownership, and missing or
cross-user records. Test add/remove/idempotency for project, task, and habit
associations, including invalid/missing/cross-user targets.

### Projects and tasks

Test project/task list/get/create/update, project and task lifecycle actions,
task queries, project progress, next-action set/clear, invalid next actions,
project assignment changes, and ownership isolation.

### Habits, check-ins, and stacks

Test habit list/get/create/update/activate/deactivate/archive; every supported
frequency shape and invalid schedules; check-in create/update/get/history
limits/delete; and missing/cross-user behavior.

Test stack list/get/create/update/archive, add/remove membership, stack and
habit reordering, unstacked queries, date-controlled progress, invalid
orderings, inactive/archived stacks, and ownership isolation.

### Today and public errors

Test empty results, selected dates, open/completed/overdue tasks, scheduled and
unscheduled habits, stacks, unstacked habits, linked goal context, and both
values of `include_completed`.

Directly assert that internal operations emit public internal authentication,
inactive-user, permission, not-found, and validation errors—never core errors.

Use controlled dates and isolated temporary or in-memory SQLite databases.

## REST Delegation and Boundary Tests

Create and retain:

* `tests/test_rest_delegation.py`
* `tests/test_rest_boundary.py`

The delegation suite uses injected fake/spy internal APIs. Split broad route
checks into focused route-family tests. Each test must assert the exact internal
operation, converted arguments, and authenticated `InternalContext`; asserting
that an operation name appeared in a call log is not enough.

Cover setup/login, protected Inbox behavior, user administration, every
association kind, project/task operations, habit/check-in or stack ordering,
Today, and representative internal-error-to-HTTP mappings for authentication,
permission, validation, and not-found errors.

The boundary suite must AST-parse every Python file under `api/REST` and fail
on imports of:

* `openipe.core.*`
* `openipe.application.*`
* `openipe.persistence.*`
* `sqlite3`

It must also assert that `get_connection` is absent and that the REST factory
requires an injected `InternalAPI`.

## Verification

Run from the project virtual environment:

```bash
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src
rg -n '^from openipe\.(core|application|persistence)|^import openipe\.(core|application|persistence)' src/openipe/api/REST
```

The final command must return no matches. Also run:

```bash
.venv/bin/python -c "from openipe.api.app import create_app; assert create_app"
.venv/bin/python -c "from openipe.api.internal import InternalAPI; assert InternalAPI"
```

Use Codebase Memory MCP after implementation: confirm a fresh graph generation,
trace the root and REST factories plus representative routes, and run
`check_index_coverage` for every touched REST/internal/test path.

## Completion Criteria

Phase 9.25 remediation is complete only when:

* REST has zero direct core, application, persistence, repository,
  domain-model, or SQLite dependencies;
* the root composition factory owns database/settings lifecycle;
* REST consumes only public internal contexts, contracts, results, and errors;
* internal owns authorization and core-to-internal error translation;
* dedicated internal tests cover every public operation and relevant success,
  failure, and authorization behavior;
* delegation tests assert exact façade calls, arguments, contexts, and error
  mappings;
* boundary tests reject direct SQLite as well as OpenIPE-layer imports;
* existing REST compatibility tests pass; and
* the full suite passes with declared development dependencies installed.

Stop after this remediation. Do not begin Phase 9.5 until human review and
explicit approval.
