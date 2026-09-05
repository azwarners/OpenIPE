# Testing Hardening Prompt: Make OpenIPE Difficult to Break

## Objective

Build an exceptionally deep, adversarial automated test suite for OpenIPE
before a human relies on it for real productivity data. The target is extreme
confidence: exercise every public behavior, every error path, every state
transition, every boundary conversion, and every meaningful combination of
inputs.

Use the aspirational coverage target of **five to ten distinct test scenarios
or assertions per meaningful line of production code**. Do not game this with
repetitive trivial tests. Interpret the target as pressure to test observable
behavior from many angles: normal flow, edge cases, invalid inputs, security,
state boundaries, regression cases, and integration behavior.

The suite must be fast, deterministic, isolated, readable, and safe to run
repeatedly.

## Scope

Cover all current OpenIPE Core code, with special emphasis on:

* `src/openipe/core/`
* `src/openipe/persistence/`
* `src/openipe/application/`
* `src/openipe/api/internal/`
* `src/openipe/api/REST/`
* `src/openipe/api/app.py`

Do not implement Phase 9.5 CLI or any Flet/Android functionality. This work is
about proving the existing server and internal API are robust.

## Working Rules

1. Read `AGENTS.md` before work begins. Actually, it does not seem to exist. Go ahead and create one, noting anything worth telling future agents that you know, having worked with the architect, about behaving in this repo.
2. Use Codebase Memory MCP first:
   * confirm the OpenIPE graph project and generation with `index_status`;
   * use `search_graph` to inventory functions, classes, routes, and tests;
   * use `trace_path` to identify callers/callees and boundary paths;
   * use `get_code_snippet` before changing or creating tests around material
     behavior;
   * use `check_index_coverage` for every tested source path and test scope.
3. Use `rg` for literals, error messages, configuration values, test discovery,
   and non-code files where graph lookup is not appropriate.
4. Do not weaken production validation, remove tests, mock away the behavior
   under test, or change product behavior solely to make testing easy.
5. Test public behavior first. Use focused unit tests only where they expose
   real logic or protect a specific regression.
6. Use test names that state the rule being protected.
7. Prefer parametrization for a family of meaningful cases, but retain clear
   failure output and case IDs.
8. Freeze or inject time/date where behavior depends on it. Never use the real
   clock in assertions without controlling it.

## Test Architecture

Maintain four complementary layers:

```text
1. Domain/core unit tests
2. Persistence and migration integration tests
3. Application-service and internal API workflow tests
4. REST HTTP contract and end-to-end integration tests
5. Cross-model productivity scenario tests
```

Every important business rule should be proven by at least two layers where it
crosses a boundary. For example, test a lifecycle rule through the internal API
and again through REST; test authentication through both service/internal and
HTTP paths.

All test databases must be temporary or in-memory SQLite databases. Tests must
never touch a user database, use a real network, require a running server, or
depend on test order.

## Required Test Work

### A. Foundation, configuration, logging, and database lifecycle

Test all configuration defaults and every supported environment override.
Include malformed booleans, invalid integer values, empty values, missing
values, path handling, token-expiration edge cases, and logging-level errors.

Test database initialization repeatedly, foreign-key enforcement, schema
version recording, migration ordering, duplicate migration versions, invalid
migration versions, partial migration rollback, transaction rollback,
idempotency, failure recovery, connection ownership, app startup/shutdown, and
connection closure behavior for owned versus injected connections.

### B. Security and authentication

Test password hashing/verification with distinct salts; invalid passwords;
username normalization; duplicate names; blank names; blank display names;
password policy boundaries; administrator bootstrap races/second setup;
inactive users; authentication timing-safe failure behavior where practical;
token uniqueness; token hashing; expiration exactly before/at/after the
boundary; logout; double logout; password-change token revocation;
deactivation token revocation; self-deactivation rejection; admin/non-admin
permissions; and all authentication error mappings.

Confirm repeatedly that passwords, token values, password hashes, and secrets
never appear in response payloads, validation errors, logs, exception strings,
test snapshots, or repr output.

### C. Core models and persistence repositories

For every model and repository, test create/read/list/update/delete-or-archive
behavior, ownership scoping, missing records, duplicate records, `NULL` values,
timestamps, date/time round trips, enum round trips, index-supported query
semantics, cascading deletes, foreign-key failures, ordering, pagination or
limits where applicable, and concurrent-looking sequential operations.

Cover User, InboxItem, Goal, Project, Task, Habit, HabitCheckIn, HabitStack,
token records, and all goal association tables.

### D. Inbox workflows

Test capture with Unicode, whitespace, maximum practical length, multiline
text, punctuation, duplicate text, invalid empty/whitespace-only values, list
filters, edits, processing, archive, discard, repeated lifecycle calls,
timestamps, unauthorized/missing records, and cross-user isolation.

Test all three conversion paths—task, project, habit—from inbox items. Verify
source linkage, original item preservation, invalid target parameters, failed
conversions, retry behavior, associations, and cross-user target rejection.

### E. Goals, projects, and tasks

Test every status and legal/illegal transition for Goals, Projects, and Tasks.
Test all update fields individually and in combinations, including explicit
`null` versus omitted values. Cover target dates, due dates, Today selection,
priority, project assignment/reassignment/removal, completion timestamps,
archival, cancellation, reopening where supported, and terminal states.

For projects, test task listing, progress counts under every relevant task
status, next-action assignment, clearing, replacement, task ownership, task
project membership, completed/cancelled/archived task handling, and project
lifecycle effects on next actions.

For goal evidence and associations, test project/task/habit association add,
remove, duplicate/idempotent calls, all association combinations, missing
targets, cross-user records, archived/inactive related records, evidence
counts, selected-date effects, and changes after lifecycle events.

### F. Habits, check-ins, and habit stacks

Test every habit frequency type and a broad schedule matrix:

* daily;
* weekdays, including weekends;
* selected days, every weekday, duplicates, ordering, invalid day values, and
  empty selections;
* times-per-week, zero/negative/excessive values, rolling-week boundaries, and
  completed/skipped/not-done history.

Test habit creation/update/activation/deactivation/archive, minimum versions,
source inbox links, stack membership, position updates, and cross-user access.

Test check-in creation, replacement/upsert behavior, status changes, notes,
missing habits, dates around daylight-saving/timezone-neutral boundaries,
history ordering, limits including zero/one/large limits, deletion, and repeat
deletion.

Test stack creation/update/archive, inactive/archived restrictions, add/remove
membership, duplicate membership, moving a habit between stacks, unstacked
habits, stack and habit reorder permutations, empty/partial/duplicate/unknown
ID lists, position consistency, scheduled progress, completed progress, and
progress with no scheduled habits.

### G. Today aggregation

Build a large table-driven Today test matrix covering:

* default date and explicitly selected dates;
* open Today tasks, due tasks, overdue tasks, future tasks, and unscheduled
  tasks;
* completed sections on and off;
* completed/cancelled/archived tasks;
* scheduled and unscheduled habits;
* each schedule type and boundary day;
* stacked and unstacked habits;
* completed, skipped, not-done, and absent check-ins;
* goal and project context;
* empty state; and
* multiple users with fully isolated output.

Assert full response shape as well as each computed count, flag, ordering rule,
and linked summary.

### H. Internal API contracts and errors

For every public `InternalAPI` namespace operation, test:

* successful result contract shape and immutability;
* conversion of every input contract field;
* omitted versus explicitly provided update fields;
* all relevant public error types;
* authentication and authorization context handling;
* ownership isolation; and
* no leakage of core exceptions, core model instances, SQLite rows, FastAPI
  objects, Pydantic request objects, passwords, or access tokens except the
  deliberate login result token.

Exercise all public methods in auth, users, inbox, goals, projects, tasks,
habits, habit stacks, and Today. Maintain a test inventory mapping every public
method to its tests so omissions are visible in review.

### I. REST adapter and API contract tests

For every REST route, test:

* valid request and response behavior;
* malformed JSON and wrong field types;
* missing required fields;
* empty strings, boundary numbers, invalid enums, invalid dates, and unknown
  fields according to the established API policy;
* authentication absent/malformed/expired/revoked;
* authorization failure;
* not-found behavior;
* validation-error behavior;
* content type, status code, and response schema; and
* cross-user isolation.

Use injected internal API spies to assert exact contract conversion, operation
name, method arguments, and opaque authenticated context for every route family.
Separately run real-internal-API ASGI tests to verify full HTTP-to-SQLite
workflows.

Preserve and strengthen boundary tests. AST-parse all REST modules and reject
imports of `openipe.core`, `openipe.application`, `openipe.persistence`, and
`sqlite3`. Assert that REST neither exposes a database connection nor reads
internal context implementation fields.

### J. End-to-end productivity scenarios

Add scenario-driven integration tests that prove OpenIPE is usable as an
integrated productivity environment, not merely as independent CRUD models.
Run each important scenario through the real `InternalAPI` with isolated SQLite
storage, and cover the main daily-user scenarios again through the real FastAPI
ASGI application.

At minimum, implement and maintain these scenarios:

1. **Capture to completed project**
   * Create an administrator and authenticate.
   * Capture an idea in Inbox.
   * Convert that exact inbox item into a Project.
   * Create multiple Tasks assigned to the project, including a next action,
     Today-selected work, and a due task.
   * Complete the tasks and verify project progress changes after each action.
   * Complete the project and verify its final status, timestamps, next-action
     behavior, task relationship, and source-inbox traceability.
   * Confirm the original inbox item and every created record remain correctly
     user-scoped and linked.

2. **Idea to goal-backed work**
   * Capture an Inbox idea and convert it to a project, task, or habit.
   * Create a Goal and associate it with the resulting project, task, and
     habit as supported.
   * Perform task completion and habit check-ins on controlled dates.
   * Verify goal evidence counts and Today goal summaries change correctly as
     related work progresses.

3. **Daily execution loop**
   * Set up active projects, Today tasks, due/overdue tasks, a habit stack, and
     unstacked habits with varied schedules.
   * Request Today for a controlled date; verify the exact actionable list,
     stack progress, due/overdue flags, and linked goal context.
   * Complete a task and check in a habit.
   * Request Today again and verify completed sections, stack counts, and
     remaining actions accurately reflect the new state.

4. **Habit establishment workflow**
   * Capture an idea, convert it to a Habit, assign it to a HabitStack, and
     associate it with a Goal.
   * Exercise scheduled and unscheduled dates, completed/skipped/not-done
     check-ins, stack reordering, and unstacking/restacking.
   * Verify recent history, stack progress, goal evidence, and Today all remain
     consistent after each mutation.

5. **Lifecycle and recovery workflow**
   * Start with an Inbox item, project, task, habit, and goal relationship.
   * Exercise supported pause/resume, complete/reopen, cancel, archive,
     activate/deactivate, and association-removal operations.
   * Assert legal transitions preserve coherent related records, while illegal
     transitions fail without partial state changes.

6. **Multi-user isolation scenario**
   * Create two users with independently captured ideas, goals, projects,
     tasks, habits, stacks, check-ins, and Today state.
   * Attempt every meaningful cross-user lookup, conversion, association,
     task/project assignment, check-in, reorder, and REST request.
   * Verify no data, progress, evidence, Today results, or tokens cross user
     boundaries.

7. **Restart and persistence scenario**
   * Build a connected productivity system using a file-backed temporary
     SQLite database.
   * Close the application/connection, recreate the composition root, and
     authenticate again.
   * Verify all relationships, lifecycle states, ordering, progress, check-in
     history, goal evidence, and Today output persist exactly.

For every scenario, assert intermediate states as well as the final state.
Include invalid attempts between valid operations to prove failed actions do not
partially mutate the user's system. Give scenario tests descriptive names that
state the user outcome they protect.

### K. Cross-cutting adversarial and regression testing

Add parameterized tests for Unicode (including emoji and combining characters),
long values, whitespace variants, newline-containing content, SQL-like input,
JSON-like text, repeated operations, accidental duplicate submissions, and
unexpected order of valid operations.

Add property-style tests where useful without introducing fragile randomness:
for example, reorder operations preserve the exact ID set, progress is always
between zero and the scheduled count, association operations never cross user
boundaries, and completed counts never exceed totals.

When a bug is found, add the smallest clear regression test before or alongside
the fix. Never close a defect without a test that would have caught it.

## Test Quality and Maintenance Rules

* Prefer behavior assertions over implementation-detail assertions.
* Use fixtures for reusable setup, but avoid fixtures that hide important
  state; each test should make its scenario understandable locally.
* Give every parameterized case a descriptive ID.
* Keep mock-only tests focused on adapter delegation. Do not mock services in
  tests intended to prove workflows.
* Assert negative outcomes as carefully as successful outcomes.
* Test both public interfaces and critical invariants beneath them.
* Keep runtime reasonable: split broad matrices with parametrization and use
  in-memory databases where behavior remains representative.

## Deliverables

1. A substantially expanded, well-organized test suite under `tests/`.
2. A test inventory document mapping all public internal API operations and REST
   routes to their unit, integration, and regression tests.
3. Any narrowly scoped test helpers needed for controlled dates, users, tokens,
   isolated databases, and ASGI clients.
4. No production feature changes unless a tested defect requires one; report
   every such change explicitly.
5. A final report listing tests added, behavior covered, commands run, test
   count before/after, failures fixed, untested risks, and recommended next
   work.

## Verification

Run and report:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src
rg -n '^from openipe\.(core|application|persistence)|^import openipe\.(core|application|persistence)' src/openipe/api/REST
rg -n '(^|[^.])sqlite3' src/openipe/api/REST
```

The REST boundary commands must produce no matches. Stop after testing work is
implemented, tested, reviewed, and reported. Do not begin the CLI phase without
explicit human approval.
