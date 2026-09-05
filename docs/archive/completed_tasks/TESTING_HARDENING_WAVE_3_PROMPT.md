# Testing Hardening Wave 3: Prove the Server Before Building Clients

## Objective

OpenIPE now has a meaningful automated suite, but broad case counts alone do
not prove that the server is ready for first real use. Complete a third testing
wave that closes the remaining evidence gaps:

* real HTTP workflows rather than abbreviated route-family samples;
* true application restart and durable persistence proof;
* systematic internal-operation and REST-route coverage enforcement;
* repository and SQLite invariant testing; and
* failure atomicity across connected model workflows.

Do not add CLI, Android/Flet, new product features, external integrations, or
speculative abstractions. This wave must test and harden the existing server.

## Required Process

1. Read `AGENTS.md`, the complete testing-hardening prompts, and
   `docs/TEST_INVENTORY.md`.
2. Use Codebase Memory MCP before test changes:
   * verify index freshness with `index_status`;
   * inventory every public `InternalAPI` operation, repository method, and
     REST route with `search_graph`;
   * trace representative HTTP → internal → service → persistence paths;
   * read exact implementations with `get_code_snippet` before testing them;
   * run `check_index_coverage` on every source/test path used as evidence.
3. Preserve unrelated worktree changes. Do not weaken validations or alter
   product behavior merely to simplify tests.
4. Use file-backed temporary SQLite databases for persistence/restart tests and
   fresh isolated databases for every other test.
5. Use controlled dates and deterministic fixtures. Never make assertions that
   depend on wall-clock timing, real network access, or test ordering.

## Completion Gate

Add at least **175 meaningful collected cases** beyond the current baseline of
295, reaching **470 or more collected tests**. Parameterized cases count only
when they vary a meaningful state, input, transition, contract, or invariant.

This count is a floor. Do not stop at it if a public operation, route, or
critical invariant remains without direct coverage.

## 1. Genuine Root-App Restart and Persistence Proof

Replace the current abbreviated REST “restart” sample with genuine restart
tests. Each test must:

1. Create a file-backed temporary database path and `Settings` for it.
2. Build the app with the root `openipe.api.app.create_app` factory.
3. Use a real ASGI client to authenticate and create a connected productivity
   system.
4. Enter and exit the app lifespan so an owned connection is actually closed.
5. Construct a new root app and new ASGI client pointing at the same path.
6. Authenticate again with a persisted user.
7. Assert the reopened application exposes the expected durable state.

Build at least these restart scenarios:

* Inbox item → converted project → tasks → next action → goal associations;
* habits → stacks → ordering → check-in history → selected-date progress;
* completed/cancelled/archived lifecycle states and timestamps;
* multiple users and isolation after restart;
* committed mutation persists, while a deliberately failed/rolled-back
  operation does not appear after restart;
* database migration idempotency across repeated root-app startups.

Verify that the first app’s owned connection is closed and that an injected
connection remains open, without relying on private implementation details in
REST.

## 2. Full Real-ASGI Productivity Scenarios

Implement full end-to-end scenarios through the real root app and HTTP routes.
Do not use an injected spy façade in these tests.

### Capture to completed project

Use HTTP to capture an Inbox item, convert it to a Project, create at least
three project tasks with varied priority/due/Today fields, set/replace/clear a
next action, complete the tasks, observe progress after every change, complete
the project, and verify final status, timestamps, source linkage, task list,
and no invalid next action.

### Goal-backed daily work

Create a goal; associate it with a project, task, and habit; create controlled
Today work; complete task and habit actions; verify evidence before/after;
verify Today goal/project summaries; then remove each association and verify
evidence and Today no longer show it.

### Habit establishment and daily loop

Capture an Inbox idea, convert it to a habit, add/move/remove it across stacks,
reorder stacks and habits, perform completed/skipped/not-done check-ins across
schedule boundaries, inspect history, verify stack progress, and verify Today
before/after each action alongside unstacked habits and overdue tasks.

### Lifecycle/recovery atomicity

Build connected Inbox/Goal/Project/Task/Habit/Stack state. Exercise every
supported lifecycle action. Between valid steps, make invalid requests and
assert both the HTTP error and that every relevant subsequent GET/list/progress/
Today/evidence response is unchanged. Include terminal-state attempts,
cross-user operations, missing IDs, invalid association targets, and invalid
reorder sets.

### Multi-user isolation

Create two full user systems through HTTP. Attempt cross-user reads, updates,
Inbox conversions, project assignment, next-action selection, each goal
association kind, check-ins, stack membership, both reorder endpoints, and
Today retrieval. Assert no cross-user data or aggregate leakage.

For every scenario, assert intermediate states, full response schemas, final
state, and relevant persistence after restart.

## 3. Complete REST Route Contract Matrix

Create a route-by-route table in `docs/TEST_INVENTORY.md`. Every concrete
handler must have exact references to tests that cover:

* one successful request;
* authentication absent, malformed, revoked, and expired where protected;
* relevant authorization failure;
* missing/not-found behavior;
* invalid path/query values;
* malformed/missing/wrong-type body values where it has a body;
* domain validation/lifecycle failure;
* response status and schema; and
* cross-user behavior where it operates on user-owned data.

Parameterize values with descriptive IDs. Cover every association kind, all
task lifecycle actions, all habit/check-in operations, all stack operations,
and both Today query switches.

Add a test that derives the route handler list from the FastAPI app and compares
it against a machine-readable coverage registry maintained in the tests. The
test must fail when a new route lacks declared success/error coverage.

## 4. Internal API Operation and Error Matrix

Build a machine-readable registry of every public operation exposed through
`InternalAPI` namespaces. Add a meta-test that fails when the registry does not
match the actual public callable surface or when an operation lacks exact
success, failure, context/authorization, and ownership/isolation tests.

For each operation, test:

* each input contract field independently;
* omitted versus explicit null updates;
* valid values and representative invalid boundaries;
* output contract type, immutability, and serializability;
* public internal error type, never leaked core error;
* no partial mutation after a failure; and
* cross-user isolation for user-owned resources.

Add direct matrix tests for all schedule forms, lifecycle state transitions,
association kinds, priority/status enums, ordering permutations, history limits,
and Today date/completed-section combinations.

## 5. Persistence and Repository Invariants

Add direct repository/database integration tests for every repository and
association table. These must complement—not replace—service/internal/HTTP
tests.

Cover:

* create/get/list/update behavior and exact ownership predicates;
* ordering and position consistency;
* foreign-key enforcement, `ON DELETE` behavior, and association cleanup;
* unique constraints, duplicate association idempotency, and transaction
  behavior;
* null fields, dates/datetimes/enums round trips, timestamp updates, and
  row-to-model conversion;
* query filters, limits, sort order, empty results, and missing IDs;
* multi-connection sequential visibility after commit; and
* rollback proof: failed mutations leave tables, relationships, counts, and
  public queries unchanged.

Use SQL assertions only to verify persistence invariants; retain higher-level
behavior tests as the primary contract evidence.

## 6. State-Machine and Property-Style Matrices

Add deterministic, parameterized state-machine tests for Goals, Projects,
Tasks, Habits, and HabitStacks. For each status/action pair, assert either the
documented resulting state/timestamp or a public validation error with no
mutation.

Add reusable invariant tests for:

* progress/counts are always non-negative and never exceed totals;
* reorder operations preserve exactly the original IDs and yield contiguous
  deterministic positions;
* ownership cannot cross users through any relation or aggregate;
* failed operations preserve observable state;
* completed/archived records appear only in documented list/Today sections;
* token revocation/expiration/deactivation cannot be reversed by a later read;
* repeated supported operations are idempotent where documented.

## 7. REST Boundary and Delegation Strengthening

Keep AST boundary tests and extend them to reject:

* direct core/application/persistence/SQLite imports;
* non-public internal-module imports;
* reads of internal implementation fields; and
* database/settings state access in REST.

For every route family, maintain focused injected-façade tests that assert the
exact internal method, exact request contract, all converted values, opaque
context identity, exact call count, and public-error-to-HTTP translation.
Include all association kinds, lifecycle actions, check-in operations, stack
operations, and Today options—not only one representative operation per family.

## Deliverables

1. At least 175 meaningful new collected cases, for 470+ total.
2. Real root-app restart tests with actual lifespan shutdown/reconstruction.
3. Full real-ASGI scenarios for connected productivity workflows.
4. Machine-checked internal-operation and REST-route coverage registries.
5. Direct repository/persistence invariant suites.
6. Updated `docs/TEST_INVENTORY.md` with exact test names for every method and
   route, plus any limitations.
7. A final report: collected/pass counts, scenario table, registry results,
   defects found/fixed, remaining risks, test runtime, and Codebase Memory
   coverage evidence.

## Verification

```bash
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src
rg -n '^from openipe\.(core|application|persistence)|^import openipe\.(core|application|persistence)' src/openipe/api/REST
rg -n '(^|[^.])sqlite3' src/openipe/api/REST
```

The suite must collect at least 470 cases, and both REST boundary searches must
produce no matches. Stop after Wave 3. Do not begin any client work without
explicit human approval.
