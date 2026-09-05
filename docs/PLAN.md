Agents must implement one phase at a time.

A phase is not complete until it has been:

1. implemented
2. tested
3. reviewed
4. explicitly approved by the human maintainer

At the end of every phase, the agent must stop.

It must report:

* work completed
* files changed
* test results
* deviations from this blueprint
* unresolved problems
* security concerns
* recommended next phase

The agent may recommend continuing.

It may not begin the next phase without explicit approval.

---

## Phase 1: Project Foundation

Implement:

* `pyproject.toml`
* package structure
* version metadata
* configuration
* logging
* SQLite connection management
* foreign-key enforcement
* schema-version table
* migration framework
* minimal README
* test configuration

No product entities beyond what is required to prove database initialization.

---

## Phase 2: Users and Authentication

Implement:

* users table
* token table
* user repository
* authentication service
* secure password hashing
* initial administrator setup
* login
* logout
* current-user lookup
* password change
* administrator user creation
* activation and deactivation
* authentication tests

Do not begin productivity features until authentication is reviewed and approved.

---

## Phase 3: Inbox Idea Capture

Implement:

* InboxItem model
* inbox table
* repository
* application service
* API schemas
* API routes
* create, edit, process, archive, and discard behavior
* tests

Do not yet create tasks, projects, or habits from inbox entries.

Those conversion operations should be added after the target entities exist.

---

## Phase 4: Goals

Implement:

* Goal model
* goals table
* repository
* service
* lifecycle operations
* API routes
* goal list and detail responses
* tests

Association tables may be created now, but associations should not be exposed until the related entities exist.

---

## Phase 5: Projects and Tasks

Implement projects and tasks together because their relationship is foundational.

Implement:

* Project model
* Task model
* tables
* repositories
* services
* project task queries
* project progress summaries
* next-action enforcement
* task lifecycle
* Today selection fields
* API routes
* tests

Then add:

* create task from inbox item
* create project from inbox item

---

## Phase 6: Habits and Habit Check-Ins

Implement:

* Habit model
* HabitCheckIn model
* schedule validation
* tables
* repositories
* services
* check-in lifecycle
* recent history
* API routes
* tests

Then add:

* create habit from inbox item

---

## Phase 7: Habit Stacks

Implement:

* HabitStack model
* table
* repository
* service
* stack ordering
* habit ordering inside stacks
* unstacked habits
* stack progress summaries
* API routes
* tests

---

## Phase 8: Goal Associations

Implement:

* goal-project associations
* goal-task associations
* goal-habit associations
* ownership validation
* association API routes
* goal evidence summaries
* tests

---

## Phase 9: Today Aggregation

Implement the Today application service and API response.

Include:

* quick-capture support through Inbox
* Today tasks
* due and overdue tasks
* scheduled habit stacks
* stack progress
* unstacked habits
* associated goal summaries
* completed sections
* date handling
* tests

Treat this as the first dashboard hypothesis.

Do not add speculative recommendation logic.

---

## Phase 9.25: Extract Internal API from REST API

Establish an internal, Python-facing API between OpenIPE Core workflows and
their presentation or transport adapters.  This boundary must be complete
before the CLI is implemented.

Implement:

* move the current REST API package to `src/openipe/api/REST`
* create an empty `src/openipe/api/internal` package as the destination for
  the extracted API implementation
* extract the operation implementation from `api/REST` into `api/internal`,
  organized around the public workflows for User, InboxItem, Goal, Project,
  Task, Habit, HabitCheckIn, HabitStack, associations, and Today
* make `api/REST` a thin HTTP adapter and consumer of `api/internal`: it may
  deserialize requests, translate authentication and errors, and serialize
  responses, but it must not own workflow or business implementation
* preserve the existing documented REST behavior and routes through the new
  adapter boundary
* define a clear internal API contract, error model, authorization context,
  and response types that do not depend on FastAPI, HTTP, or Pydantic request
  objects
* update imports, application wiring, documentation, and tests for the new
  package layout
* add regression tests proving that REST delegates to the internal API and
  that existing REST behavior remains intact

The internal API is the shared client boundary for local first-party clients.
It may invoke OpenIPE application services, but it must not duplicate their
domain validation, lifecycle rules, schedule calculation, or aggregation.

---

## Phase 9.5: OpenIPE CLI

Implement a first-class `openipe` command-line client before beginning the
Android client.  The CLI is a local first-party client of OpenIPE Core: it must
consume `src/openipe/api/internal` and must not call the REST API or read or
write SQLite directly.  Its purpose is to exercise the complete public
workflow for every core model and keep domain and application logic out of the
future Flet client.

Implement:

* installable `openipe` console-command entry point
* internal API initialization and CLI configuration
* safe credential and token handling
* consistent human-readable output, JSON output, errors, and exit statuses
* command help, examples, and CLI configuration documentation
* authentication and user-management commands
* Inbox commands for capture, list, view, edit, process, archive, discard, and
  conversion to a task, project, or habit
* Goal commands for create, list, view, edit, lifecycle operations, evidence,
  and project/task/habit associations
* Project commands for create, list, view, edit, lifecycle operations, task
  listing, progress, and next-action selection
* Task commands for create, list, view, edit, lifecycle operations, Today
  selection, and project assignment
* Habit and check-in commands for create, list, view, edit, schedule-aware
  check-ins, recent history, and lifecycle operations
* Habit-stack commands for create, list, view, edit, archive, stack membership,
  stack and habit reordering, unstacked habits, and progress summaries
* a Today command that exposes the selected-date and completed-section options

Each command must remain a thin adapter: parse input, invoke an internal API
operation, and render the response.  Validation, authorization, state
transitions, schedule calculation, and aggregation remain in OpenIPE Core.

Do not begin the Flet Android client until the CLI can perform the supported
workflows for User, InboxItem, Goal, Project, Task, Habit, HabitCheckIn, and
HabitStack.

---

## Phase 9.75: CLI and Integration Test Expansion

Substantially expand automated coverage around the CLI and its interaction with
OpenIPE Core.

Implement:

* focused CLI unit tests for command parsing, option defaults, validation,
  request construction, output formats, error rendering, and exit statuses
* tests that prevent tokens, passwords, and other credentials from appearing
  in output, errors, logs, or snapshots
* command-by-command coverage for the public workflows of every core model
* integration tests that run the CLI against the internal API with an isolated
  temporary SQLite database
* authenticated and unauthorized paths, ownership isolation, lifecycle
  transitions, conversion flows, associations, ordering, schedules, and Today
  aggregation
* end-to-end workflow tests spanning capture through conversion, association,
  completion/check-in, and Today display
* regression tests for CLI configuration, internal API compatibility, and REST
  adapter compatibility
* a documented test command that runs the complete suite with all declared
  development dependencies installed

Tests should assert observable behavior rather than duplicate implementation
details.  Keep fixtures small, deterministic, date-controlled, and isolated so
the enlarged suite remains fast and trustworthy.

Do not begin Phase 10 until this suite passes and the CLI has been reviewed and
explicitly approved.

---

## Phase 10: Android Client Foundation

Implement:

* Flet Android project setup
* server URL configuration
* API client
* authentication flow
* secure token handling
* navigation shell
* loading states
* error handling
* logout
* Android build documentation
* tests where practical

---

## Phase 11: Android Today and Inbox

Implement:

* Today screen
* quick capture
* Today tasks
* task completion
* collapsible habit stacks
* habit-stack progress
* habit check-ins
* unstacked habits
* Inbox screen
* Inbox item editing and processing

This phase should produce the first daily-usable client.

---

## Phase 12: Android Goals, Projects, Tasks, and Habits

Implement:

* Goals screen
* goal details
* project screen
* project progress
* next-action selection
* task screen
* habit screen
* habit-stack management
* reordering controls appropriate for mobile
* creation and editing forms

---

## Phase 13: Integration and Polish

Implement:

* complete end-to-end testing
* startup and shutdown behavior
* improved empty states
* validation messages
* API documentation
* Android build instructions
* server installation instructions
* known limitations
* screenshots
* architecture documentation
* security documentation
* backup guidance
* release checklist
