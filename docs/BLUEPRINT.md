# OpenIPE v0.0.1 Blueprint

## Integrated Productivity Environment

**Status:** Initial implementation blueprint
**Version:** 0.0.1
**Primary client:** Android
**Core architecture:** Self-hosted server with REST API
**Persistence:** SQLite
**Development model:** Phase-based, human-reviewed, human-approved

---

# 1. Project Vision

OpenIPE is an open-source, server-backed Integrated Productivity Environment.

It helps users connect:

* captured ideas
* goals
* projects
* tasks
* habits
* habit stacks
* daily action

Most productivity applications store these concepts separately. OpenIPE is intended to integrate them so users can see not only what they need to do, but also:

* why they are doing it
* which larger outcome it supports
* which repeated behaviors reinforce it
* what action should happen next
* whether their current system is helping

OpenIPE does not impose one universal productivity methodology.

It provides concrete productivity functionality that users can combine, use, observe, and refine.

OpenIPE should help answer:

1. What ideas have I captured?
2. What goals am I pursuing?
3. Which projects support those goals?
4. What tasks should I complete?
5. Which habits am I trying to establish?
6. Which routines organize those habits?
7. What should I do today?
8. Is my current system helping me make progress?

---

# 2. Project Lineage

OpenIPE continues the idea behind Vimat, an Integrated Productivity Environment begun in 2013.

Vimat stood for:

> **Vimat Is More than A To-do list**

The `V` and `M` also represented Victor and Max.

Vimat was designed as a web-based productivity application that could work on both phones and computers. OpenIPE preserves that original pocket-first goal while adopting a modern client-server architecture.

OpenIPE is not intended to be only an Android application.

OpenIPE Core is an independent server application. Android is simply the first client.

Future clients may include:

* Linux desktop
* web
* additional mobile platforms
* command-line tools
* third-party integrations

---

# 3. Core Product Principles

## 3.1 Pocket First

The first client is Android because idea capture, habit tracking, task completion, and daily guidance must be accessible wherever the user is.

## 3.2 Server Backed

OpenIPE Core is the source of truth.

Clients communicate with the core through a documented REST API.

## 3.3 Independent Applications

OpenIPE must not depend on:

* Apmatia
* a specific VPN provider
* a particular cloud platform
* a specific identity provider
* a particular desktop environment
* a proprietary external service

Optional integrations may be added later through stable APIs and explicit authorization.

## 3.4 Low-Friction Capture

Users must be able to capture an idea without first deciding:

* what kind of item it is
* which project it belongs to
* which goal it supports
* when it is due
* whether it should become a habit

Classification happens later.

## 3.5 Integrated, Not Duplicated

The system should connect records through explicit relationships.

Do not create duplicate structures when an existing entity already represents the concept.

Examples:

* Inbox items are captured ideas. Do not create a duplicate Idea entity.
* Tasks belong to projects through `project_id`.
* Projects do not store arrays of task IDs.
* Project task lists are computed from task relationships.
* Goal relationships use association tables rather than serialized ID arrays.

## 3.6 Useful Before Clever

OpenIPE v0.0.1 must be usable.

Avoid speculative abstractions, generalized plugin systems, automation engines, and elaborate productivity theory until concrete usage proves they are needed.

## 3.7 Evolve Through Use

The initial Today screen and other workflows are functional hypotheses.

They should be implemented, used, criticized, and revised.

The application must not assume its first design is final.

## 3.8 Human Approval Is Required

Agents may implement work, run tests, and recommend the next phase.

They may not continue from one implementation phase to the next without explicit human approval.

---

# 4. MVP Scope

OpenIPE v0.0.1 includes:

1. OpenIPE Core server
2. SQLite persistence
3. Users and authentication
4. Inbox idea capture
5. Goals
6. Projects
7. Tasks
8. Habits
9. Habit stacks
10. Habit check-ins
11. Today aggregation
12. REST API
13. Android client
14. Automated tests
15. Initial documentation

---

# 5. System Architecture

```text
OpenIPE Android Client
        │
        │ HTTPS or trusted private network
        │ REST API
        ▼
OpenIPE Core Server
        │
        ├── Authentication
        ├── Application Services
        ├── Domain Models
        ├── Repositories
        └── SQLite
```

Future architecture:

```text
Android Client ─────┐
Linux Client ───────┤
Web Client ─────────┼── OpenIPE Core ── SQLite
CLI Client ─────────┤
Apmatia Integration ┘
```

OpenIPE Core must have no dependency on:

* Android
* Flet
* Linux
* Apmatia
* a VPN product
* a cloud vendor

---

# 6. Recommended Technology

## OpenIPE Core

Use:

* Python
* FastAPI
* Pydantic
* Python standard-library `sqlite3`
* explicit SQL
* repository classes
* pytest

Do not use an ORM in v0.0.1.

## Android Client

Use Flet with Android as the first target.

Separate:

* API communication
* client state
* presentation
* navigation
* reusable UI components

The Android client must not contain core business rules.

## Packaging

Use a modern Python package layout with `pyproject.toml`.

---

# 7. Repository Structure

A single repository may initially contain both the core server and Android client.

Recommended structure:

```text
openipe/
├── BLUEPRINT.md
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── openipe/
│       ├── __init__.py
│       ├── version.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── errors.py
│       │   └── models/
│       │       ├── __init__.py
│       │       ├── base.py
│       │       ├── user.py
│       │       ├── inbox.py
│       │       ├── goal.py
│       │       ├── project.py
│       │       ├── task.py
│       │       ├── habit.py
│       │       ├── habit_stack.py
│       │       └── habit_checkin.py
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── user_service.py
│       │   ├── inbox_service.py
│       │   ├── goal_service.py
│       │   ├── project_service.py
│       │   ├── task_service.py
│       │   ├── habit_service.py
│       │   ├── habit_stack_service.py
│       │   └── today_service.py
│       │
│       ├── persistence/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── schema.py
│       │   ├── migrations.py
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── user_repository.py
│       │       ├── inbox_repository.py
│       │       ├── goal_repository.py
│       │       ├── project_repository.py
│       │       ├── task_repository.py
│       │       ├── habit_repository.py
│       │       ├── habit_stack_repository.py
│       │       └── habit_checkin_repository.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── dependencies.py
│       │   ├── schemas/
│       │   └── routes/
│       │       ├── health.py
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── inbox.py
│       │       ├── goals.py
│       │       ├── projects.py
│       │       ├── tasks.py
│       │       ├── habits.py
│       │       ├── habit_stacks.py
│       │       └── today.py
│       │
│       └── clients/
│           └── android/
│               ├── __init__.py
│               ├── app.py
│               ├── config.py
│               ├── state.py
│               ├── navigation.py
│               ├── api_client/
│               │   ├── __init__.py
│               │   ├── client.py
│               │   ├── auth.py
│               │   └── errors.py
│               ├── components/
│               │   ├── quick_capture.py
│               │   ├── task_card.py
│               │   ├── project_card.py
│               │   ├── habit_card.py
│               │   ├── habit_stack_panel.py
│               │   ├── goal_summary.py
│               │   └── progress_summary.py
│               └── views/
│                   ├── login_view.py
│                   ├── server_setup_view.py
│                   ├── today_view.py
│                   ├── inbox_view.py
│                   ├── goals_view.py
│                   ├── projects_view.py
│                   ├── tasks_view.py
│                   ├── habits_view.py
│                   └── settings_view.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── client/
│
└── docs/
    ├── architecture.md
    ├── api.md
    ├── development.md
    ├── domain-model.md
    ├── security.md
    └── decisions/
```

This structure may be adjusted when justified, but preserve the separation between:

* core models
* application services
* persistence
* API
* Android client

---

# 8. Shared Object Model

A small Python base class may be used for common fields.

```python
@dataclass
class OpenIPEObject:
    id: int | None
    user_id: int
    created_at: datetime
    updated_at: datetime
```

This base class exists only to reduce repetition and establish consistent ownership.

It must not create:

* a universal database table
* polymorphic persistence
* a generic entity repository
* a forced inheritance hierarchy for every record

SQLite tables must define their columns explicitly.

Some infrastructure records may not inherit from `OpenIPEObject`.

---

# 9. Users and Authentication

Users are foundational MVP entities.

Every user-owned record must include `user_id`.

All repository queries and API operations involving personal data must be scoped to the authenticated user.

## User Fields

```text
id
username
display_name
password_hash
is_admin
is_active
created_at
updated_at
last_login_at
```

Email is optional for v0.0.1.

Do not require email-based account recovery in the MVP.

## Required User Features

* initial administrator creation
* login
* logout
* current-user endpoint
* password change
* user creation by an administrator
* user activation and deactivation
* secure password hashing
* bearer-token authentication

## Registration

Open public registration must not be enabled by default.

The initial server setup should create the first administrator.

Additional users may initially be created by an administrator.

Invitation-based registration may be added later.

## Future Account Linking

OpenIPE must remain independent of Apmatia.

A future optional integration may link identities using:

```text
provider_instance
external_subject_id
local_user_id
granted_scopes
```

Do not implement account linking in v0.0.1.

Do not assume matching usernames or email addresses identify the same person across applications.

---

# 10. Inbox Idea Capture

The Inbox stores captured ideas.

An inbox item is already an idea. Do not create a separate Idea entity.

## InboxItem Fields

```text
id
user_id
text
status
created_at
updated_at
processed_at
archived_at
```

## Status Values

```text
unprocessed
processed
archived
discarded
```

## Required Features

Users must be able to:

* capture an idea quickly
* edit an inbox item
* mark it processed
* return it to unprocessed
* archive it
* discard it
* create a task from it
* create a project from it
* create a habit from it

The original inbox item should remain available after producing another record.

The resulting task, project, or habit may store:

```text
source_inbox_item_id
```

This preserves provenance without duplicating the Inbox as another idea system.

## Capture Rule

Creating an inbox item requires only text.

All other fields are optional or system generated.

---

# 11. Goals

Goals explain why projects, tasks, and habits exist.

Goal associations are optional.

Users must not be forced to associate every record with a goal.

Examples:

* Become more physically fit
* Earn a Linux certification
* Publish OpenIPE
* Improve financial stability
* Become a better husband
* Become a better father
* Strengthen friendships
* Learn a new skill

## Goal Fields

```text
id
user_id
title
description
status
target_date
created_at
updated_at
achieved_at
archived_at
source_inbox_item_id
```

## Goal Status Values

```text
active
paused
achieved
abandoned
archived
```

## Goal Relationships

Goals may be associated with:

* projects
* tasks
* habits

These relationships are many-to-many.

Use association tables:

```text
goal_projects
- goal_id
- project_id

goal_tasks
- goal_id
- task_id

goal_habits
- goal_id
- habit_id
```

Each association must be scoped so users cannot connect their records to another user’s goal.

## Required Goal Features

Users must be able to:

* create a goal
* edit a goal
* pause a goal
* resume a goal
* mark a goal achieved
* abandon a goal
* archive a goal
* associate projects
* associate tasks
* associate habits
* view all associated work
* view evidence of progress

## Goal Progress

Do not calculate a universal goal-completion percentage.

Instead, show evidence such as:

```text
Projects
1 of 3 complete

Tasks
8 of 14 complete

Habits this week
11 of 18 scheduled check-ins complete

Active next actions
3
```

This avoids false precision for goals that cannot be meaningfully reduced to one percentage.

---

# 12. Projects

A project represents an outcome requiring multiple tasks.

## Project Fields

```text
id
user_id
title
description
status
next_action_task_id
source_inbox_item_id
created_at
updated_at
completed_at
archived_at
```

## Project Status Values

```text
active
paused
completed
cancelled
archived
```

## Task Relationship

Tasks store one optional `project_id`.

Projects do not store task ID arrays.

A project’s task list is computed from tasks whose `project_id` matches the project.

The project API may return computed values:

```text
task_ids
total_task_count
completed_task_count
open_task_count
```

## Next Action

`next_action_task_id` identifies one open task belonging to the project.

The service layer must enforce:

* the task exists
* the task belongs to the authenticated user
* the task belongs to the project
* the task is open
* the task is not cancelled
* the task is not completed

If the next-action task is completed, cancelled, moved, or archived, the project’s next action must be cleared unless explicitly replaced.

## Required Project Features

Users must be able to:

* create a project
* edit a project
* pause and resume it
* complete it
* cancel it
* archive it
* create tasks inside it
* assign existing tasks to it
* remove tasks from it
* select a next-action task
* view associated goals
* view progress

## Project Progress Summary

Project cards should show:

```text
OpenIPE v0.0.1
7 of 12 tasks complete
Next action: Build habit stack API
```

A progress bar may be included, but the completed and total task counts are the primary progress indicator.

Do not estimate effort or completion dates from task count.

---

# 13. Tasks

A task represents a concrete action.

## Task Fields

```text
id
user_id
title
description
project_id
status
priority
due_date
is_today
source_inbox_item_id
created_at
updated_at
completed_at
archived_at
```

## Task Status Values

```text
open
completed
cancelled
archived
```

## Priority Values

```text
low
normal
high
```

## Required Task Features

Users must be able to:

* create a task
* edit a task
* complete it
* reopen it
* cancel it
* archive it
* assign it to a project
* remove it from a project
* mark or unmark it for Today
* optionally assign a due date
* associate it with one or more goals

## Rules

* Task titles must not be empty.
* Completing a task sets `completed_at`.
* Reopening a task clears `completed_at`.
* Cancelled and archived tasks do not appear in active lists.
* A task may belong to no project.
* A task may belong to only one project.
* A task may support multiple goals.

Recurring tasks are out of scope for v0.0.1.

---

# 14. Habits

A habit represents a behavior the user intends to repeat.

Habits are first-class MVP entities.

## Habit Fields

```text
id
user_id
title
description
frequency_type
frequency_config
minimum_version
stack_id
position
active
source_inbox_item_id
created_at
updated_at
archived_at
```

## Frequency Types

```text
daily
weekdays
selected_days
times_per_week
```

## Examples

```text
Meditate every day
Review work queue on weekdays
Write Monday, Wednesday, and Saturday
Exercise three times per week
```

`frequency_config` may be stored as validated JSON.

## Minimum Version

Each habit may define the smallest acceptable version of the behavior.

Example:

```text
Habit:
Work on a personal project

Minimum version:
Open the project and work for ten minutes
```

## Required Habit Features

Users must be able to:

* create a habit
* edit a habit
* archive it
* activate or deactivate it
* define its schedule
* define its minimum version
* assign it to a habit stack
* remove it from a stack
* reorder it within a stack
* associate it with one or more goals
* perform daily check-ins
* view recent check-in history

## Rules

* Habit titles must not be empty.
* Archived or inactive habits do not appear in Today.
* A habit may belong to one stack.
* A habit may be unstacked.
* A habit may support multiple goals.
* Missing a scheduled habit does not automatically create a failure record.

---

# 15. Habit Stacks

A habit stack is a named, ordered, collapsible group of habits.

In v0.0.1, habit stacks are primarily organizational routine containers.

Examples:

* Morning Routine
* Before Work
* After Work
* After Supper
* Bedtime
* Weekend Reset

## HabitStack Fields

```text
id
user_id
name
description
position
active
created_at
updated_at
archived_at
```

## Required Habit Stack Features

Users must be able to:

* create a stack
* rename it
* edit its description
* archive it
* activate or deactivate it
* reorder stacks
* add habits to it
* remove habits from it
* reorder habits inside it
* expand or collapse it in the Android UI
* view completion progress for the selected date

## Progress Summary

A stack should display:

```text
Morning Routine
3 of 5 complete
```

The summary is based on habits in the stack that are scheduled for the selected date.

## Unstacked Habits

Habits without a `stack_id` must appear under a visible section such as:

```text
Unstacked Habits
```

## Deferred Stack Features

Do not implement in v0.0.1:

* automatic sequential execution
* revealing one habit only after another completes
* trigger automation
* timers for entire routines
* time-of-day notifications
* explicit dependency graphs
* “after X, do Y” automation
* routine templates

The MVP definition is:

> A named, ordered, collapsible group of habits with a daily progress summary.

---

# 16. Habit Check-Ins

A habit check-in records an explicit user action for a particular date.

## HabitCheckIn Fields

```text
id
user_id
habit_id
date
status
note
created_at
updated_at
```

## Status Values

```text
completed
skipped
not_done
```

## Required Features

Users must be able to:

* complete a habit for a date
* mark it skipped
* mark it not done
* add an optional note
* change the status
* undo the check-in
* view recent check-ins

## Rules

* A habit may have only one check-in per date.
* Updating the same date replaces the previous status.
* Dates use the user’s local calendar date.
* A missing check-in is not equivalent to `not_done`.
* `not_done` and `skipped` require explicit user action.
* Check-ins must be owned by the same user who owns the habit.

---

# 17. Today Dashboard

The Today dashboard is the Android client’s primary screen.

The initial design is a functional hypothesis.

It should be implemented cleanly, used in practice, and revised through user-approved changes.

## Initial Today Content

### Quick Capture

A prominent field for capturing an inbox idea.

### Today Tasks

Show open tasks when:

* `is_today` is true
* the due date is today
* the due date is overdue

### Habit Stacks

Show active habit stacks containing habits scheduled today.

Each stack should be collapsible and show:

```text
3 of 5 complete
```

### Unstacked Habits

Show scheduled habits that do not belong to a stack.

### Goal Context

Tasks and habits may display associated goals in a subtle secondary form.

Example:

```text
Study Linux for 30 minutes
Goal: Earn Linux certification
```

Do not overwhelm the screen with goal labels.

### Completed Items

Completed items may move to a collapsed completed section.

## Today Rules

* Today uses the user’s local date.
* Cancelled and archived tasks do not appear.
* Archived or inactive habits do not appear.
* Only habits scheduled for the selected date appear.
* Stack progress counts only scheduled habits.
* Overdue tasks are visibly distinguishable.
* The dashboard must remain usable on a phone.

## Deferred Today Features

Do not implement yet:

* automatic task ranking
* AI recommendations
* calendar appointments
* weather
* location context
* energy-level filtering
* complex daily planning
* automatic rescheduling
* motivational scoring

---

# 18. Android Client

Android is the first OpenIPE client.

The Android app communicates with OpenIPE Core through the REST API.

It must not directly access SQLite.

## Required Android Screens

```text
Server Setup
Login
Today
Inbox
Goals
Projects
Tasks
Habits
Settings
```

## Server Setup

Users must be able to configure:

```text
server_url
```

The client should not assume a VPN product or network topology.

The documentation may state:

> Remote access may be configured through a trusted private network or user-managed VPN. Network configuration is outside OpenIPE’s scope.

Do not recommend or depend on a specific vendor.

## Authentication

The Android client must:

* submit credentials to the server
* receive an access token
* store credentials or tokens using appropriate secure platform storage
* attach the token to API requests
* support logout
* return to login when authentication expires

## Client Responsibilities

The Android client handles:

* rendering
* navigation
* temporary UI state
* forms
* API communication
* user-friendly error messages

The Android client must not implement:

* authorization rules
* ownership validation
* project next-action rules
* habit schedule rules
* goal relationship rules
* persistence logic

---

# 19. REST API

The REST API is the primary application interface.

Recommended base path:

```text
/api/v1
```

OpenAPI documentation should be generated automatically.

## Health

```text
GET /api/v1/health
```

## Authentication

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/change-password
```

## Users

Administrator-only operations:

```text
GET   /api/v1/users
POST  /api/v1/users
GET   /api/v1/users/{user_id}
PATCH /api/v1/users/{user_id}
```

## Inbox

```text
GET    /api/v1/inbox
POST   /api/v1/inbox
GET    /api/v1/inbox/{item_id}
PATCH  /api/v1/inbox/{item_id}
DELETE /api/v1/inbox/{item_id}

POST /api/v1/inbox/{item_id}/create-task
POST /api/v1/inbox/{item_id}/create-project
POST /api/v1/inbox/{item_id}/create-habit
```

The DELETE endpoint may perform archival or soft deletion rather than physical removal.

## Goals

```text
GET   /api/v1/goals
POST  /api/v1/goals
GET   /api/v1/goals/{goal_id}
PATCH /api/v1/goals/{goal_id}

POST   /api/v1/goals/{goal_id}/projects/{project_id}
DELETE /api/v1/goals/{goal_id}/projects/{project_id}

POST   /api/v1/goals/{goal_id}/tasks/{task_id}
DELETE /api/v1/goals/{goal_id}/tasks/{task_id}

POST   /api/v1/goals/{goal_id}/habits/{habit_id}
DELETE /api/v1/goals/{goal_id}/habits/{habit_id}
```

## Projects

```text
GET   /api/v1/projects
POST  /api/v1/projects
GET   /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}

GET  /api/v1/projects/{project_id}/tasks
POST /api/v1/projects/{project_id}/next-action/{task_id}
DELETE /api/v1/projects/{project_id}/next-action
```

## Tasks

```text
GET   /api/v1/tasks
POST  /api/v1/tasks
GET   /api/v1/tasks/{task_id}
PATCH /api/v1/tasks/{task_id}

POST /api/v1/tasks/{task_id}/complete
POST /api/v1/tasks/{task_id}/reopen
POST /api/v1/tasks/{task_id}/cancel
```

## Habit Stacks

```text
GET   /api/v1/habit-stacks
POST  /api/v1/habit-stacks
GET   /api/v1/habit-stacks/{stack_id}
PATCH /api/v1/habit-stacks/{stack_id}

POST /api/v1/habit-stacks/reorder
POST /api/v1/habit-stacks/{stack_id}/habits/reorder
```

## Habits

```text
GET   /api/v1/habits
POST  /api/v1/habits
GET   /api/v1/habits/{habit_id}
PATCH /api/v1/habits/{habit_id}

POST   /api/v1/habits/{habit_id}/check-ins
DELETE /api/v1/habits/{habit_id}/check-ins/{date}
```

## Today

```text
GET /api/v1/today
```

Optional query parameters may include:

```text
date
include_completed
```

## API Security

Every personal-data endpoint must:

* require authentication
* derive the user from the access token
* ignore or reject attempts to specify another `user_id`
* scope every repository query to the authenticated user
* return `404` rather than revealing another user’s record exists

---

# 20. SQLite Schema

Use explicit SQLite tables.

Required tables:

```text
schema_versions
users
auth_tokens
inbox_items
goals
projects
tasks
habits
habit_stacks
habit_checkins
goal_projects
goal_tasks
goal_habits
```

## Database Rules

* Enable foreign keys.
* Use indexes for common user-scoped queries.
* Use unique constraints where appropriate.
* Use transactions for multi-record operations.
* Centralize schema creation and migrations.
* Store timestamps consistently.
* Document local-date handling.
* Do not serialize relationship ID arrays into JSON.

## Important Constraints

Examples:

```text
UNIQUE(habit_id, date)
```

Association tables should enforce uniqueness:

```text
UNIQUE(goal_id, project_id)
UNIQUE(goal_id, task_id)
UNIQUE(goal_id, habit_id)
```

Application services must additionally enforce user ownership across relationships.

---

# 21. Configuration

Core server configuration should include:

```text
database_path
api_host
api_port
token_expiration
log_level
allow_user_creation
```

The default host should be conservative.

Do not assume public internet exposure.

The Android client configuration should include:

```text
server_url
```

Do not include vendor-specific networking configuration.

---

# 22. Logging

Use Python logging.

Log:

* server startup and shutdown
* schema version
* migration execution
* authentication failures without passwords
* API startup
* unexpected exceptions
* repository failures
* configuration errors

Do not log at normal levels:

* passwords
* tokens
* complete inbox contents
* complete task descriptions
* habit notes
* private goal descriptions

---

# 23. Error Handling

Expected errors should produce understandable responses.

Examples:

* invalid credentials
* inactive user
* invalid form input
* record not found
* ownership violation
* invalid next-action task
* duplicate habit check-in
* invalid habit schedule
* unavailable server
* expired token
* database failure

API errors should use consistent structured responses.

The Android client must show user-friendly messages rather than raw stack traces or HTTP payloads.

---

# 24. Testing Requirements

Tests must use temporary databases.

Never run automated tests against the user’s real OpenIPE database.

## Authentication Tests

* initial administrator creation
* successful login
* failed login
* inactive user rejection
* token validation
* current-user endpoint
* password change
* user isolation

## Inbox Tests

* create inbox item
* edit inbox item
* mark processed
* archive item
* create task from inbox item
* create project from inbox item
* create habit from inbox item
* preserve original capture

## Goal Tests

* create and update goal
* pause and resume goal
* achieve and abandon goal
* associate project
* associate task
* associate habit
* prevent cross-user association
* calculate evidence summaries

## Project Tests

* create project
* assign task to project
* remove task from project
* compute task IDs
* compute completed and total counts
* set valid next action
* reject task from another project
* reject completed task as next action
* clear next action when task changes state

## Task Tests

* create task
* complete task
* reopen task
* cancel task
* mark for Today
* overdue selection
* associate multiple goals

## Habit Tests

* create daily habit
* create weekday habit
* create selected-days habit
* create times-per-week habit
* minimum version
* activate and deactivate
* assign to stack
* reorder inside stack
* associate multiple goals

## Habit Stack Tests

* create stack
* rename stack
* reorder stacks
* add and remove habit
* reorder habits
* calculate scheduled progress
* show unstacked habits
* enforce user ownership

## Habit Check-In Tests

* create check-in
* update same-date check-in
* delete check-in
* enforce one check-in per date
* distinguish missing from not done
* reject cross-user check-in

## Today Tests

* include manually selected tasks
* include due-today tasks
* include overdue tasks
* exclude completed active items appropriately
* include scheduled habits
* group habits by stack
* compute stack progress
* include unstacked habits
* use requested local date

## API Tests

Test all major endpoint families, including:

* health
* login
* current user
* inbox creation
* goal creation
* project creation
* task completion
* habit creation
* habit-stack ordering
* habit check-in
* Today response
* user isolation

## Android Client Tests

At minimum:

* API client error mapping
* login state
* expired-token handling
* Today payload rendering logic
* habit-stack expansion state
* progress-summary formatting

---

# 25. Development Phases

See: [OpenIPE/docs/PLAN.md](PLAN.md)

---

# 26. Non-Goals for v0.0.1

Do not implement:

* Linux client
* web client
* public cloud hosting
* vendor-specific VPN integration
* Apmatia dependency
* Apmatia account linking
* OAuth or OpenID Connect
* email-based password recovery
* open public registration
* teams
* shared projects
* collaboration
* comments
* calendar integration
* appointments
* reminders
* push notifications
* recurring tasks
* subtasks
* task dependencies
* tags
* domains
* areas
* workspaces
* generic folders
* goal hierarchies
* key results
* weighted goal percentages
* habit gamification
* badges
* social features
* AI-generated advice
* automatic system revision
* Pomodoro timers
* time tracking
* location awareness
* automatic habit sequencing
* habit triggers
* natural-language task parsing
* file attachments
* rich Markdown editing
* public API exposure by default
* plugin marketplace
* universal productivity-module framework
* ORM
* generic entity persistence

These may be considered only after v0.0.1 proves useful.

---

# 27. API Example: Today

Example:

```json
{
  "date": "2026-08-04",
  "tasks": [
    {
      "id": 41,
      "title": "Review OpenIPE API design",
      "project": {
        "id": 7,
        "title": "Build OpenIPE v0.0.1"
      },
      "goals": [
        {
          "id": 3,
          "title": "Publish OpenIPE"
        }
      ],
      "priority": "high",
      "due_date": null,
      "is_today": true,
      "status": "open"
    }
  ],
  "habit_stacks": [
    {
      "id": 4,
      "name": "Evening Routine",
      "completed_count": 2,
      "scheduled_count": 4,
      "habits": [
        {
          "id": 12,
          "title": "Meditate",
          "minimum_version": "Sit quietly for two minutes",
          "today_status": null,
          "position": 1,
          "goals": []
        }
      ]
    }
  ],
  "unstacked_habits": [],
  "completed": {
    "tasks": [],
    "habits": []
  }
}
```

---

# 28. Acceptance Criteria

OpenIPE v0.0.1 is complete when:

## Core

* The server installs and runs.
* SQLite initializes automatically.
* Migrations are versioned.
* Foreign keys are enabled.
* Logging is configured.
* Configuration is documented.

## Users

* The first administrator can be created.
* An administrator can create another user.
* Users can log in and log out.
* Users can change passwords.
* Inactive users cannot log in.
* Personal data is isolated by user.

## Inbox

* Users can capture ideas quickly.
* Inbox items can be edited and processed.
* Inbox items can produce tasks, projects, and habits.
* Original inbox captures remain preserved.

## Goals

* Users can manage goal lifecycles.
* Goals can associate with projects, tasks, and habits.
* Goal details show evidence summaries.
* Goals do not use a fake universal completion percentage.

## Projects

* Users can create and manage projects.
* Projects display their task lists.
* Projects display completed and total task counts.
* Projects support one valid next-action task.
* Next-action integrity is enforced.

## Tasks

* Users can create, edit, complete, reopen, cancel, and archive tasks.
* Tasks can belong to one project.
* Tasks can support multiple goals.
* Tasks can be selected for Today.
* Due and overdue tasks appear in Today.

## Habits

* Users can create all required schedule types.
* Habits support minimum versions.
* Habits support check-ins.
* Habits show recent history.
* Habits can support multiple goals.

## Habit Stacks

* Users can create, rename, reorder, and archive stacks.
* Habits can be assigned and reordered.
* Stacks are collapsible in Android.
* Stacks display daily completion summaries.
* Unstacked habits remain accessible.

## Today

* Today shows applicable tasks.
* Today shows habit stacks.
* Today shows unstacked habits.
* Today supports task completion and habit check-ins.
* Today includes quick capture.
* Today works cleanly on a phone.

## Android

* Users can configure a server URL.
* Users can log in.
* Tokens are handled securely.
* The client communicates only through the API.
* Major MVP features are accessible.
* Errors are understandable.

## Quality

* Automated tests pass.
* Documentation explains installation and development.
* Security assumptions are documented.
* No agent has skipped an approval gate.
* No non-goal has been silently introduced.

---

# 29. Agent Working Rules

Every coding agent must:

1. Read this blueprint in full.
2. Inspect the current repository before editing.
3. Identify the active phase.
4. Implement only that phase.
5. Use explicit code over speculative abstraction.
6. Keep business rules out of API routes and UI handlers.
7. Add or update tests.
8. Run relevant tests.
9. Report failures honestly.
10. Document deviations.
11. Stop after the phase.
12. Wait for explicit approval.

Agents must not:

* silently expand scope
* add major dependencies without justification
* begin later phases early
* redesign approved concepts without discussion
* claim tests passed without running them
* expose the API publicly by default
* log private user content
* weaken user isolation
* replace explicit models with a generic entity system
* add an ORM
* add domains, areas, or workspaces
* create a duplicate Idea entity
* store relationship ID arrays in SQLite
* continue without human approval

---

# 30. Initial Agent Prompt

Use this prompt when beginning the repository:

> Read `BLUEPRINT.md` in full. Implement Phase 1 only. Do not begin any later phase. Keep the implementation explicit and minimal. Run all relevant tests, report the resulting repository tree, explain any deviations, and stop for review and approval.

For later phases:

> Read `BLUEPRINT.md` and inspect the existing repository. Implement Phase N only. Do not begin Phase N+1. Add or update tests, run them, summarize all changes and deviations, and stop for review and approval.

---

# 31. Final Product Statement

OpenIPE is a self-hosted Integrated Productivity Environment that connects ideas, goals, projects, tasks, habits, routines, and daily action.

Its first client is Android because productivity must be available where life happens.

Its core is independent because users should own their data and choose how their applications communicate.

Its architecture is integrated because goals, projects, tasks, and habits should reinforce one another rather than live as disconnected lists.

Its first design is intentionally unfinished because the system must evolve through use.

Version 0.0.1 is not the final productivity methodology.

It is the first working build.
