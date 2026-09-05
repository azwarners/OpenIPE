# OpenIPE Agent Guide

You are working on OpenIPE for Nick. Be precise, practical, and kind. Preserve
unrelated worktree changes: this repository can contain work from other agents
or a pending human commit.

## Current phase gate

- **Completed:** Phase 9.25 — extract the internal API from the REST API.
- **Next:** Phase 9.5 — OpenIPE CLI.
- Do not start Phase 9.5, Phase 9.75, or Phase 10 merely because they appear in
  the plan. Start a new phase only when Nick explicitly asks for it.
- Before changing phase work, read `docs/BLUEPRINT.md`, `docs/PLAN.md`, and all
  task/remediation/testing prompts relevant to that phase.

## Architectural boundaries

The dependency direction is:

```text
CLI (same host) -> openipe.api.internal -> application/core -> persistence
Future Flet Android client -> REST -> openipe.api.internal -> application/core -> persistence
```

- `openipe.api.internal.InternalAPI` is the public Python-facing workflow
  façade for first-party clients. It owns public contracts, authorization, and
  translation of internal errors.
- `openipe.api.REST` is an HTTP adapter only. It may parse requests, call an
  injected `InternalAPI`, map public internal errors to HTTP responses, and
  serialize results.
- REST must not import `openipe.core`, `openipe.application`, or
  `openipe.persistence`; inspect an internal context's actor; access settings,
  database connections, repositories, services, or SQLite; or implement
  workflow/lifecycle/authorization rules.
- The root composition factory, `openipe.api.app.create_app`, owns settings,
  SQLite initialization, lifespan, cleanup, and construction/injection of the
  internal API.
- The internal API must not depend on FastAPI, Starlette, or Pydantic HTTP
  request/response objects. Keep domain validation, lifecycle rules, schedule
  calculation, and aggregation in application/core layers.
- Future CLI commands must use only the internal API, never REST or SQLite.
- The future Android client is a network client: it must consume REST, not the
  internal API or SQLite. REST must expose no capability that is absent from
  the internal API.

## Working method

1. Read this file and the relevant phase documents before making changes.
2. Use Codebase Memory MCP first for structural discovery. At a fresh session,
   confirm the OpenIPE graph project and generation. Use graph search, traces,
   and exact snippets for material code claims; then run index-coverage checks
   for the candidate paths. Use `rg` for literals, configuration, docs, and
   other non-code discovery.
3. Make the smallest cohesive change that satisfies the approved scope. Do not
   perform opportunistic redesign or change domain behavior merely to simplify
   tests.
4. Add or update deterministic, isolated tests with each behavioral change.
   Use temporary or in-memory SQLite; do not depend on real user data, network
   services, or wall-clock time in assertions.
5. Run focused tests, then the complete suite when practical. Also run boundary
   checks and compile/import checks appropriate to the touched layers. Report
   commands actually run and their results; distinguish collection from a full
   passing execution.
6. Update relevant docs when a phase status, public contract, command, or
   developer workflow changes.

## Test expectations

- Favor observable behavior and adversarial cases over tests that duplicate
  implementation details.
- Test success, validation, authentication, authorization, ownership isolation,
  missing records, invalid transitions, idempotency, persistence, and error
  mapping where each applies.
- Include multi-model scenarios where supported workflows meet, such as Inbox
  capture through conversion to project/task/habit and eventual completion.
- Keep REST delegation and forbidden-import boundary tests intact. Do not weaken
  a test, registry, or assertion simply to make a change pass.

## Repository hygiene

- Use `apply_patch` for source and documentation edits.
- Never use destructive git commands or discard another contributor's changes.
- Do not commit, push, install packages, contact external services, or begin an
  unapproved phase unless Nick explicitly requests that action.
