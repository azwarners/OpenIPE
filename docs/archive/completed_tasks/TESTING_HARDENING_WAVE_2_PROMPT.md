# Testing Hardening Wave 2: Exhaustive Workflow and Boundary Coverage

## Objective

The first hardening wave added useful tests and brought the suite to 136 cases,
but it is still a first tranche. Implement the next, substantially larger wave
of tests before OpenIPE is trusted with real user productivity data.

This wave must prioritize breadth, depth, and realistic system use over a
modest increase in the test counter. Add a large, well-organized set of
meaningful parameterized cases and scenario tests. The desired direction
remains five to ten distinct behavioral scenarios/assertions per meaningful
production line, without gaming that target through duplicate trivial tests.

Do not implement CLI, Android, Flet, new product features, or speculative
abstractions. Test the existing product thoroughly.

## Required Process

1. Read `AGENTS.md`, `docs/TESTING_HARDENING_PROMPT.md`, and
   `docs/TEST_INVENTORY.md` first.
2. Use Codebase Memory MCP before changing tests:
   * `index_status` for graph freshness;
   * `search_graph` to enumerate public internal methods, REST routes, and
     current tests;
   * `trace_path` for façade-to-service and route-to-façade paths;
   * `get_code_snippet` before adding coverage around behavior;
   * `check_index_coverage` for every touched source and test path.
3. Update `docs/TEST_INVENTORY.md` at a method/route level. Do not claim a
   namespace is covered merely because one broad test touches it.
4. Use controlled dates and isolated temporary/in-memory SQLite databases.
5. Do not weaken tests, production validation, or product behavior to make the
   suite pass.

## Test-Count and Coverage Gate

Raise the suite by **at least 150 collected test cases** beyond the current
baseline of 136. Parameterized cases count when each case exercises a distinct
meaningful input, state, or invariant and has a descriptive test ID.

The final suite should therefore collect at least **286 cases**. This is a
minimum gate, not the definition of completeness.

Report both named test functions and collected test cases. Do not present a
small number of broad tests as exhaustive coverage.

## 1. Internal API Operation Matrix

Create one or more dedicated parameterized test modules per internal namespace.
For every public method, test its successful behavior, at least one relevant
failure, authorization/context behavior where applicable, output contract type,
and user isolation where applicable.

### Auth and users

Cover initial setup, login, logout, current user, password change, user list,
get, create, and update with matrices for:

* blank/whitespace/Unicode/multiline usernames and display names;
* password policy boundaries and malformed credentials;
* case-insensitive duplicate usernames;
* active/inactive users;
* expired, revoked, unknown, malformed, and repeated logout tokens;
* admin/non-admin/missing-user/self-deactivation paths;
* every update-field combination, including omitted versus explicit null;
* secret non-disclosure in every public error/result representation.

### Inbox

Independently cover list/status filtering, get, create, update, process,
archive, discard, delete, create-task, create-project, and create-habit.

Use a parameter matrix for empty/whitespace/Unicode/emoji/combining-character/
multiline/long/SQL-like/JSON-like text. Cover repeated operations, missing
records, cross-user operations, source-item preservation, conversion failure,
and retry/idempotency behavior.

### Goals and associations

Cover every field of create/update, list filters, get, every lifecycle helper,
generic lifecycle dispatch, evidence, association ID lookup, and removal.

For all project/task/habit association kinds, parameterize add/remove,
duplicates, missing targets, cross-user targets, inactive/archived related
records where behavior is defined, and evidence changes after task/project/
habit lifecycle transitions.

### Projects and tasks

Cover every create/update field, list filter, get, lifecycle action, task list,
progress, next-action set/clear, task reassignment, and source inbox link.

Build a status-cross-product matrix for project and task states. Include every
legal/illegal transition, next-action eligibility, task movement, completion,
cancellation, archiving, reopening, due-date boundaries, priorities, and Today
selection values.

### Habits, check-ins, and stacks

Build a schedule matrix for every frequency type and every weekday. Include
valid and invalid selected-day configurations, duplicates, empty days, invalid
values, times-per-week boundaries, date/week boundaries, and absent/completed/
skipped/not-done check-ins.

Cover all habit and check-in public methods, including history-limit matrices
for zero, one, normal, large, and invalid limits. Cover every stack method with
empty/single/multiple stack memberships; add/remove/move behavior; stack/habit
reorder permutations; partial/duplicate/unknown ID lists; inactive/archived
stacks; position consistency; unstacked behavior; and user isolation.

### Today

Create a table-driven matrix covering selected dates, empty state, task status,
due-date relation, Today flag, completed-section switch, every habit frequency,
stacked/unstacked state, every check-in state, associated goal/project context,
and multiple users. Assert complete response contents, not only a count.

## 2. Real REST/ASGI Usability Scenarios

The current productivity scenarios use `InternalAPI` directly. Recreate all of
the following with the real root composition factory and `httpx.ASGITransport`:

1. Inbox capture → project conversion → task creation → next action → task
   completion → project completion.
2. Inbox conversion → goal association → task completion and habit check-in →
   evidence and Today changes.
3. Daily execution loop: Today tasks, due/overdue tasks, stacked/unstacked
   habits, check-ins, completed sections, and refreshed Today response.
4. Habit establishment: Inbox conversion, stack membership, reordering,
   check-in history, goal evidence, and Today.
5. Lifecycle/recovery: pause/resume, complete/reopen, cancel/archive,
   activate/deactivate, association removal, and failed transitions with no
   partial state change.
6. Two-user isolation: attempts at cross-user reads, conversions, associations,
   assignments, check-ins, reorders, and Today requests through HTTP.
7. Restart persistence: perform a connected workflow through the root app with
   file-backed temporary SQLite, close it, reopen it, authenticate again, and
   verify relationships, ordering, evidence, history, and Today output.

Assert status codes, response schemas, and full observable state after each
step. Do not use a fake façade in these tests.

## 3. REST Route Contract Matrix

For each route, add parameterized HTTP tests for:

* absent, malformed, expired, and revoked authentication;
* malformed JSON, missing fields, wrong types, unknown fields according to API
  policy, empty strings, boundary numbers, invalid enums, invalid IDs, and
  invalid dates;
* validation, permission, not-found, and lifecycle error status/detail;
* valid response schema and JSON serialization;
* cross-user access/mutation;
* idempotent or repeated operations where supported.

Test all route families: setup/auth/users, Inbox, Goals/associations, Projects,
Tasks, Habits/check-ins, Habit Stacks/reordering, and Today.

## 4. Focused REST Delegation Tests

Replace the single broad delegation test with focused tests grouped by route
family. Use injected spies only here.

For each representative route in every family, assert:

* the exact internal method invoked;
* the exact immutable request contract and every converted field;
* the same opaque `InternalContext` returned by authentication;
* correct internal-error-to-HTTP mapping; and
* that no extra façade operation is called.

Cover all association kinds and both stack reorder endpoints. Keep real ASGI
workflow coverage separate from spy-based adapter coverage.

## 5. Invariants, State Machines, and Regression Tests

Add deterministic property-style/parameterized tests for these invariants:

* reorder operations preserve exactly the input ID set and a contiguous,
  deterministic position order;
* no progress/completed count is negative or exceeds its total;
* every association and related record remains user-scoped;
* a failed operation leaves all relevant tables and public query results
  unchanged;
* every lifecycle transition either produces the documented state/timestamp or
  fails without mutation;
* tokens cannot become valid after revocation/expiration/deactivation;
* Today never includes records outside the selected user's permitted view;
* restarting the application preserves committed state and no uncommitted state;
* public internal results are immutable contracts and REST never leaks internal
  implementation details.

For every newly discovered defect, add a minimal regression test before or
alongside the production fix.

## 6. Boundary and Test-Quality Enforcement

Expand the AST boundary test to reject REST reads of internal implementation
details, including `.actor`, database-related state names, and non-public
internal modules where feasible. Continue rejecting `openipe.core`,
`openipe.application`, `openipe.persistence`, and `sqlite3` imports.

Add a test that walks the public `InternalAPI` namespaces and compares them to
the test inventory, failing if any public operation lacks explicit test mapping.

Ensure tests do not use wall-clock assertions, real network access, real user
data, or order-dependent shared database state.

## Required Deliverables

1. At least 150 meaningful new collected test cases, reaching 286+ total.
2. Expanded focused internal, REST/ASGI, delegation, invariant, and scenario
   suites.
3. An updated `docs/TEST_INVENTORY.md` mapping each public internal method and
   each REST route to exact test names/files.
4. Any narrowly scoped fixes revealed by tests, with regression tests and a
   documented explanation.
5. A final report with test count before/after, scenario list, coverage matrix,
   commands and results, defects found/fixed, remaining risks, and the exact
   Codebase Memory coverage evidence.

## Verification

Run from the project virtual environment:

```bash
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src
rg -n '^from openipe\.(core|application|persistence)|^import openipe\.(core|application|persistence)' src/openipe/api/REST
rg -n '(^|[^.])sqlite3' src/openipe/api/REST
```

The suite must collect at least 286 cases. Both REST boundary searches must
produce no matches. Stop after Wave 2; do not start Phase 9.5 without explicit
human approval.
